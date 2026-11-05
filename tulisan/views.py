# ============================================================
# VIEWS
# View adalah fungsi yang dijalankan setiap kali sebuah URL dibuka.
# Tugasnya: mengambil atau mengubah data, lalu menampilkan halaman
# (render) atau mengarahkan ke halaman lain (redirect).
#
# Urutan isi file ini:
#   1. Akun      : registrasi, login
#   2. Publik    : beranda, baca, suka
#   3. Penulis   : dasbor, tulis baru, edit
#   4. Moderator : antrean, tinjau, tarik
#   5. Admin     : kelola pengguna, kelola kategori
# ============================================================
from django.contrib import messages                      # pesan singkat, misal "Tulisan berhasil diajukan"
from django.contrib.auth.views import LoginView          # view login bawaan Django
from django.core.paginator import Paginator              # membagi daftar panjang menjadi beberapa halaman
from django.db import transaction                        # menyimpan beberapa perubahan sekaligus: semua berhasil atau tidak sama sekali
from django.db.models import Count, Q                    # Count: menghitung jumlah, Q: membuat syarat "atau"
from django.http import Http404                          # memunculkan halaman 404 Not Found
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse                          # mengubah nama URL jadi alamat, misal 'login' jadi '/login/'
from django.utils import timezone                        # waktu sekarang sesuai TIME_ZONE di settings
from django.utils.text import slugify                    # mengubah teks jadi slug
from django.views.decorators.http import require_POST    # hanya menerima kiriman form (POST)

from .forms import (
    KategoriForm, KeputusanForm, MasukForm, RegistrasiForm,
    TarikForm, TulisanForm, UbahPenggunaForm,
)
from .hak_akses import halaman_awal, role_required
from .models import (
    AturanKonten, HasilChecklist, Kategori, RiwayatModerasi,
    Suka, Tulisan, User,
)


# ============================================================
# 1. AKUN
# ============================================================
def registrasi(request):
    # Kalau sudah login, tidak perlu daftar lagi
    if request.user.is_authenticated:
        return redirect(halaman_awal(request.user))

    # request.POST or None: form terisi kalau tombol Daftar ditekan, kosong kalau baru dibuka
    form = RegistrasiForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()   # membuat akun baru, role otomatis "penulis"
        messages.success(request, 'Registrasi berhasil, silakan login.')
        return redirect('login')

    return render(request, 'registrasi.html', {'form': form})


class MasukView(LoginView):
    # Memakai view login bawaan Django dengan beberapa penyesuaian
    template_name = 'login.html'
    form_class = MasukForm                 # form login dengan pesan kesalahan yang rapi
    redirect_authenticated_user = True     # kalau sudah login lalu buka /login/, langsung dialihkan

    def get_default_redirect_url(self):
        # Halaman tujuan setelah login, sesuai role (lihat hak_akses.py)
        return reverse(halaman_awal(self.request.user))


# ============================================================
# 2. PUBLIK (bisa dibuka tanpa login)
# ============================================================
def beranda(request):
    # Ambil hanya tulisan berstatus terbit, urut dari yang terakhir terbit
    daftar = (
        Tulisan.objects.filter(status='terbit')
        .select_related('penulis', 'kategori')     # ambil data penulis dan kategori sekaligus, lebih hemat query
        .annotate(jumlah_suka=Count('suka'))       # tambahkan kolom sementara berisi jumlah suka
        .order_by('-diterbitkan_pada')
    )

    # Filter kategori dari URL, misal /?kategori=cerpen
    kategori_aktif = request.GET.get('kategori', '')
    if kategori_aktif:
        daftar = daftar.filter(kategori__slug=kategori_aktif)

    # Tampilkan 10 tulisan per halaman, nomor halaman dari URL, misal ?halaman=2
    halaman = Paginator(daftar, 10).get_page(request.GET.get('halaman'))

    return render(request, 'beranda.html', {
        'halaman': halaman,
        'daftar_kategori': Kategori.objects.all(),
        'kategori_aktif': kategori_aktif,
    })


def baca(request, slug):
    tulisan = get_object_or_404(Tulisan.objects.select_related('penulis', 'kategori'), slug=slug)

    # Tulisan yang belum terbit hanya boleh dibuka oleh:
    #   - pemilik tulisan
    #   - moderator, kalau tulisannya sedang diajukan
    # Selain itu tampil 404, supaya keberadaan tulisan tidak ketahuan.
    if tulisan.status != 'terbit':
        user = request.user
        boleh = user.is_authenticated and (
            tulisan.penulis_id == user.id
            or (user.role == 'moderator' and tulisan.status == 'diajukan')
        )
        if not boleh:
            raise Http404

    # Cek apakah pengguna yang sedang login sudah menyukai tulisan ini
    sudah_suka = (
        request.user.is_authenticated
        and tulisan.suka.filter(pengguna=request.user).exists()
    )

    return render(request, 'baca.html', {
        'tulisan': tulisan,
        'jumlah_suka': tulisan.suka.count(),
        'sudah_suka': sudah_suka,
    })


@require_POST
def suka(request, slug):
    # Pengunjung yang belum login diarahkan ke login,
    # lalu setelah login kembali ke halaman baca tulisan ini
    if not request.user.is_authenticated:
        messages.info(request, 'Masuk terlebih dahulu untuk menyukai tulisan.')
        return redirect(f"{reverse('login')}?next={reverse('baca', args=[slug])}")

    tulisan = get_object_or_404(Tulisan, slug=slug, status='terbit')

    # get_or_create: kalau belum pernah suka, buat baris baru (dibuat=True).
    # Kalau sudah pernah, hapus barisnya (batal suka).
    baris, dibuat = Suka.objects.get_or_create(pengguna=request.user, tulisan=tulisan)
    if not dibuat:
        baris.delete()

    return redirect('baca', slug=slug)


# ============================================================
# 3. PENULIS
# ============================================================
@role_required('penulis')
def dasbor(request):
    # Hanya tulisan milik penulis yang sedang login
    milik_saya = Tulisan.objects.filter(penulis=request.user)

    daftar = (
        milik_saya.select_related('kategori')
        .prefetch_related('riwayat')     # ambil riwayat moderasi sekaligus, untuk menampilkan catatan terakhir
        .order_by('-diperbarui')
    )

    # Hitung jumlah tulisan per status, misal {'draf': 2, 'terbit': 5, ...}
    jumlah = {kode: 0 for kode, _ in Tulisan.STATUS_CHOICES}
    for baris in milik_saya.order_by().values('status').annotate(n=Count('id')):
        jumlah[baris['status']] = baris['n']
    # Ubah jadi daftar (label, jumlah) untuk ditampilkan sebagai kartu ringkasan
    ringkasan = [(label, jumlah[kode]) for kode, label in Tulisan.STATUS_CHOICES]

    return render(request, 'dasbor.html', {'daftar': daftar, 'ringkasan': ringkasan})


@role_required('penulis')
def tulis_baru(request):
    # Tulisan baru yang belum disimpan, langsung dipasangkan ke penulis yang login
    return _editor(request, Tulisan(penulis=request.user))


@role_required('penulis')
def edit_tulisan(request, pk):
    # penulis=request.user: tulisan milik orang lain akan menghasilkan 404
    tulisan = get_object_or_404(Tulisan, pk=pk, penulis=request.user)

    # Hanya draf dan perlu revisi yang boleh diedit
    if not tulisan.bisa_diedit:
        messages.error(request, 'Tulisan ini sedang ditinjau atau sudah final, jadi tidak bisa diedit.')
        return redirect('dasbor')

    return _editor(request, tulisan)


def _editor(request, tulisan):
    # Fungsi bantu yang dipakai bersama oleh tulis_baru dan edit_tulisan.
    # Diawali garis bawah karena bukan view yang dipasang langsung ke URL.

    # Tombol yang ditekan: "draf" (Simpan Draf) atau "ajukan" (Ajukan ke Moderator)
    aksi = request.POST.get('aksi', 'draf')
    form = TulisanForm(request.POST or None, instance=tulisan, aksi=aksi)

    if request.method == 'POST' and form.is_valid():
        tulisan = form.save(commit=False)   # isi data dari form, tapi belum disimpan ke database

        if aksi == 'ajukan':
            tulisan.status = 'diajukan'
            tulisan.diajukan_pada = timezone.now()
            pesan = 'Tulisan berhasil diajukan ke moderator.'
        else:
            # Simpan draf: status tidak berubah (tetap draf atau perlu revisi)
            pesan = 'Tulisan berhasil disimpan.'

        tulisan.save()
        messages.success(request, pesan)
        return redirect('dasbor')

    return render(request, 'editor.html', {
        'form': form,
        'tulisan': tulisan,
        'aturan_list': AturanKonten.objects.filter(aktif=True),   # ditampilkan sebagai panduan di samping editor
    })


# ============================================================
# 4. MODERATOR
# ============================================================
@role_required('moderator')
def antrean(request):
    # Tab yang dipilih dari URL: menunggu (bawaan), terbit, atau riwayat
    tab = request.GET.get('tab', 'menunggu')
    kategori_aktif = request.GET.get('kategori', '')
    cari = request.GET.get('cari', '').strip()

    daftar = None
    riwayat = None

    if tab == 'riwayat':
        # 50 keputusan terakhir dari semua moderator
        riwayat = RiwayatModerasi.objects.select_related('tulisan', 'moderator')[:50]
    else:
        if tab == 'terbit':
            daftar = Tulisan.objects.filter(status='terbit').order_by('-diterbitkan_pada')
        else:
            tab = 'menunggu'
            # Urut dari pengajuan terlama, supaya tidak ada yang menunggu terlalu lama
            daftar = Tulisan.objects.filter(status='diajukan').order_by('diajukan_pada')

        daftar = daftar.select_related('penulis', 'kategori').annotate(
            # Berapa kali tulisan ini pernah diminta revisi, untuk menghitung "pengajuan ke-berapa"
            jumlah_revisi=Count('riwayat', filter=Q(riwayat__keputusan='perlu_revisi'))
        )

        if kategori_aktif:
            daftar = daftar.filter(kategori__slug=kategori_aktif)
        if cari:
            # Q(...) | Q(...): cocok dengan judul ATAU nama pengguna ATAU nama lengkap penulis
            daftar = daftar.filter(
                Q(judul__icontains=cari)
                | Q(penulis__username__icontains=cari)
                | Q(penulis__first_name__icontains=cari)
            )

    return render(request, 'antrean.html', {
        'tab': tab,
        'daftar': daftar,
        'riwayat': riwayat,
        'daftar_kategori': Kategori.objects.all(),
        'kategori_aktif': kategori_aktif,
        'cari': cari,
        'jumlah_menunggu': Tulisan.objects.filter(status='diajukan').count(),
        'form_tarik': TarikForm(),
    })


@role_required('moderator')
def tinjau(request, pk):
    # Hanya tulisan berstatus diajukan yang bisa ditinjau
    tulisan = get_object_or_404(
        Tulisan.objects.select_related('penulis', 'kategori'), pk=pk, status='diajukan'
    )

    # Moderator tidak boleh meninjau tulisannya sendiri
    if tulisan.penulis_id == request.user.id:
        messages.error(request, 'Kamu tidak bisa meninjau tulisanmu sendiri.')
        return redirect('antrean')

    aturan_list = AturanKonten.objects.filter(aktif=True)
    form = KeputusanForm(request.POST or None, aturan_list=aturan_list)

    if request.method == 'POST' and form.is_valid():
        keputusan = form.cleaned_data['keputusan']

        # transaction.atomic: tiga penyimpanan di bawah dianggap satu paket.
        # Kalau salah satu gagal, semuanya dibatalkan, jadi data tidak setengah tersimpan.
        with transaction.atomic():
            # 1) Catat keputusan di riwayat moderasi
            riwayat = RiwayatModerasi.objects.create(
                tulisan=tulisan,
                moderator=request.user,
                keputusan=keputusan,
                catatan=form.cleaned_data['catatan'].strip(),
            )
            # 2) Simpan hasil centang untuk setiap aturan sekaligus (bulk_create)
            HasilChecklist.objects.bulk_create([
                HasilChecklist(riwayat=riwayat, aturan=aturan, terpenuhi=terpenuhi)
                for aturan, terpenuhi in form.hasil_checklist()
            ])
            # 3) Ubah status tulisan sesuai keputusan
            tulisan.status = keputusan
            if keputusan == 'terbit':
                tulisan.diterbitkan_pada = timezone.now()
            if keputusan == 'perlu_revisi':
                # Penulis wajib mencentang ulang pernyataan saat mengajukan lagi
                tulisan.pernyataan_orisinal = False
            tulisan.save()

        messages.success(request, f'Keputusan "{riwayat.get_keputusan_display()}" untuk "{tulisan.judul}" tersimpan.')
        return redirect('antrean')

    return render(request, 'tinjau.html', {
        'tulisan': tulisan,
        'form': form,
        'riwayat': tulisan.riwayat.select_related('moderator'),
        # Pengajuan ke-berapa = jumlah permintaan revisi sebelumnya + 1
        'pengajuan_ke': tulisan.riwayat.filter(keputusan='perlu_revisi').count() + 1,
    })


@role_required('moderator')
@require_POST
def tarik(request, pk):
    # Hanya tulisan terbit yang bisa ditarik
    tulisan = get_object_or_404(Tulisan, pk=pk, status='terbit')
    form = TarikForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            RiwayatModerasi.objects.create(
                tulisan=tulisan,
                moderator=request.user,
                keputusan='ditarik',
                catatan=form.cleaned_data['alasan'],
            )
            tulisan.status = 'ditarik'
            # update_fields: hanya menyimpan kolom yang disebut, lebih hemat
            tulisan.save(update_fields=['status', 'diperbarui'])
        messages.success(request, f'"{tulisan.judul}" sudah ditarik dari publik.')
    else:
        messages.error(request, 'Alasan penarikan wajib diisi.')

    # Kembali ke tab "Sudah Terbit"
    return redirect(f"{reverse('antrean')}?tab=terbit")


# ============================================================
# 5. ADMIN
# ============================================================
@role_required('admin')
def panel_pengguna(request):
    cari = request.GET.get('cari', '').strip()
    role_aktif = request.GET.get('role', '')

    daftar = User.objects.order_by('date_joined')
    if cari:
        daftar = daftar.filter(Q(username__icontains=cari) | Q(first_name__icontains=cari))
    if role_aktif:
        daftar = daftar.filter(role=role_aktif)

    return render(request, 'panel_pengguna.html', {
        'daftar': daftar,
        'cari': cari,
        'role_aktif': role_aktif,
        'pilihan_role': User.ROLE_CHOICES,
    })


@role_required('admin')
@require_POST
def ubah_pengguna(request, pk):
    pengguna = get_object_or_404(User, pk=pk)

    # Akun admin (termasuk diri sendiri) tidak bisa diubah dari halaman ini
    if pengguna.role == 'admin':
        messages.error(request, 'Akun admin tidak dapat diubah dari halaman ini.')
        return redirect('panel_pengguna')

    form = UbahPenggunaForm(request.POST, instance=pengguna)
    if form.is_valid():
        form.save()
        messages.success(request, f'Data akun "{pengguna.username}" berhasil diperbarui.')
    else:
        messages.error(request, 'Perubahan gagal disimpan.')

    return redirect('panel_pengguna')


@role_required('admin')
def panel_kategori(request):
    # Kalau URL berisi ?ubah=<id>, form dipakai untuk mengubah kategori itu.
    # Kalau tidak, form dipakai untuk menambah kategori baru.
    kategori_diubah = None
    if request.GET.get('ubah'):
        kategori_diubah = get_object_or_404(Kategori, pk=request.GET['ubah'])

    form = KategoriForm(request.POST or None, instance=kategori_diubah)
    if request.method == 'POST' and form.is_valid():
        kategori = form.save(commit=False)
        kategori.slug = slugify(kategori.nama)   # slug selalu mengikuti nama terbaru
        kategori.save()
        messages.success(request, f'Kategori "{kategori.nama}" berhasil disimpan.')
        return redirect('panel_kategori')

    return render(request, 'panel_kategori.html', {
        'form': form,
        'kategori_diubah': kategori_diubah,
        # jumlah_tulisan dipakai untuk menentukan tombol Hapus aktif atau tidak
        'daftar': Kategori.objects.annotate(jumlah_tulisan=Count('tulisan')),
    })


@role_required('admin')
@require_POST
def hapus_kategori(request, pk):
    kategori = get_object_or_404(Kategori, pk=pk)

    # Kategori yang masih dipakai tulisan tidak boleh dihapus
    if kategori.tulisan.exists():
        messages.error(request, f'Kategori "{kategori.nama}" masih dipakai tulisan, jadi tidak bisa dihapus.')
    else:
        kategori.delete()
        messages.success(request, f'Kategori "{kategori.nama}" berhasil dihapus.')

    return redirect('panel_kategori')