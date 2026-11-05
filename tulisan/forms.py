# ============================================================
# FORMS
# Form adalah penghubung antara isian di halaman HTML dan database.
# Django memakai form untuk: menampilkan kolom isian, memeriksa
# isian (validasi), dan menampilkan pesan kesalahan.
# ============================================================
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Kategori, Tulisan, User


# ------------------------------------------------------------
# 1. REGISTRASI (dipakai pengunjung untuk membuat akun)
# ------------------------------------------------------------
class RegistrasiForm(UserCreationForm):
    # UserCreationForm sudah menyediakan kolom kata sandi dan konfirmasinya,
    # sekaligus mengecek kata sandi yang terlalu pendek atau terlalu umum.
    class Meta(UserCreationForm.Meta):
        model = User
        # Kolom role sengaja tidak dimasukkan, jadi akun baru otomatis "penulis"
        # dan pengguna tidak bisa memilih role sendiri.
        fields = ('first_name', 'username')
        labels = {
            'first_name': 'Nama lengkap',
            'username': 'Nama pengguna',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nama lengkap bawaan Django boleh kosong, di sini kita wajibkan
        self.fields['first_name'].required = True

    def clean_username(self):
        # clean_<nama_kolom>: validasi khusus untuk satu kolom.
        # Mengecek nama pengguna kembar (huruf besar dan kecil dianggap sama)
        # dengan pesan yang lebih rapi daripada pesan bawaan Django.
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Nama pengguna ini sudah digunakan.')
        return username


# ------------------------------------------------------------
# 2. LOGIN
# ------------------------------------------------------------
class MasukForm(AuthenticationForm):
    # Mengganti pesan kesalahan bawaan. Pesannya dibuat umum
    # supaya tidak memberi petunjuk bagian mana yang salah.
    error_messages = {
        'invalid_login': 'Nama pengguna atau sandi salah.',
        'inactive': 'Akun ini sedang dinonaktifkan.',
    }


# ------------------------------------------------------------
# 3. EDITOR TULISAN (dipakai penulis)
# ------------------------------------------------------------
class TulisanForm(forms.ModelForm):
    # ModelForm: form yang kolomnya dibuat otomatis dari model Tulisan
    class Meta:
        model = Tulisan
        fields = ('judul', 'kategori', 'isi', 'pernyataan_orisinal')
        labels = {
            'judul': 'Judul',
            'kategori': 'Kategori',
            'isi': 'Isi tulisan (Markdown)',
            'pernyataan_orisinal': (
                'Saya menyatakan bahwa tulisan ini adalah karya asli saya, '
                'bukan hasil penjiplakan, dan tidak melanggar aturan konten RuangTulis.'
            ),
        }
        # widgets: mengatur bentuk kolom isian di HTML
        widgets = {
            'judul': forms.TextInput(attrs={'placeholder': 'Judul tulisan'}),
            'isi': forms.Textarea(attrs={
                'rows': 16,
                'id': 'isi-markdown',   # id ini dipakai tombol bantu Markdown nanti
                'placeholder': 'Tulis di sini. Gunakan Markdown untuk format.',
            }),
        }

    def __init__(self, *args, aksi='draf', **kwargs):
        # aksi: tombol yang ditekan penulis, "draf" (Simpan Draf) atau "ajukan"
        super().__init__(*args, **kwargs)
        self.aksi = aksi
        self.fields['kategori'].empty_label = 'Pilih kategori'   # teks pilihan kosong di dropdown

    def clean(self):
        # clean(): validasi tambahan setelah semua kolom diperiksa satu per satu
        data = super().clean()
        # Pernyataan orisinalitas hanya wajib saat mengajukan, tidak saat simpan draf
        if self.aksi == 'ajukan' and not data.get('pernyataan_orisinal'):
            self.add_error('pernyataan_orisinal', 'Centang pernyataan orisinalitas sebelum mengajukan.')
        return data


# ------------------------------------------------------------
# 4. KEPUTUSAN MODERATOR (dipakai di halaman tinjau)
# ------------------------------------------------------------
class KeputusanForm(forms.Form):
    # forms.Form biasa (bukan ModelForm), karena isinya menyentuh
    # beberapa tabel sekaligus: riwayat_moderasi, hasil_checklist, tulisan
    PILIHAN = [
        ('terbit', 'Terbitkan'),
        ('perlu_revisi', 'Minta Revisi'),
        ('ditolak', 'Tolak'),
    ]
    keputusan = forms.ChoiceField(choices=PILIHAN, widget=forms.RadioSelect, label='Keputusan')
    catatan = forms.CharField(
        label='Catatan untuk penulis',
        required=False,     # wajib atau tidaknya dicek di clean() di bawah
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Wajib diisi untuk Minta Revisi dan Tolak'}),
    )

    def __init__(self, *args, aturan_list=None, **kwargs):
        # aturan_list: daftar aturan konten yang aktif, dikirim dari view
        super().__init__(*args, **kwargs)
        self.aturan_list = list(aturan_list or [])
        # Membuat satu kotak centang untuk setiap aturan.
        # Nama kolomnya "aturan_<id>", misalnya aturan_1, aturan_2, dst.
        for aturan in self.aturan_list:
            self.fields[f'aturan_{aturan.pk}'] = forms.BooleanField(required=False, label=aturan.nama)

    def kolom_checklist(self):
        # Dipakai di template untuk menampilkan kotak centang satu per satu
        return [self[f'aturan_{aturan.pk}'] for aturan in self.aturan_list]

    def hasil_checklist(self):
        # Mengembalikan pasangan (aturan, dicentang atau tidak) untuk disimpan ke database
        return [(aturan, self.cleaned_data.get(f'aturan_{aturan.pk}', False)) for aturan in self.aturan_list]

    def clean(self):
        data = super().clean()
        keputusan = data.get('keputusan')
        # all(...): True kalau semua kotak centang dicentang
        semua_terpenuhi = all(data.get(f'aturan_{aturan.pk}') for aturan in self.aturan_list)

        # Aturan 1: terbit hanya boleh kalau semua aturan terpenuhi
        if keputusan == 'terbit' and not semua_terpenuhi:
            self.add_error('keputusan', 'Tulisan hanya bisa diterbitkan jika semua aturan terpenuhi.')

        # Aturan 2: revisi dan tolak wajib disertai catatan
        if keputusan in ('perlu_revisi', 'ditolak') and not data.get('catatan', '').strip():
            self.add_error('catatan', 'Catatan wajib diisi untuk Minta Revisi dan Tolak.')
        return data


# ------------------------------------------------------------
# 5. PENARIKAN TULISAN TERBIT (dipakai moderator)
# ------------------------------------------------------------
class TarikForm(forms.Form):
    # required=True (bawaan), jadi alasan wajib diisi.
    # Spasi kosong otomatis dibuang, jadi isian berisi spasi saja tetap ditolak.
    alasan = forms.CharField(
        label='Alasan penarikan',
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Jelaskan aturan yang dilanggar'}),
    )


# ------------------------------------------------------------
# 6. KATEGORI (dipakai admin)
# ------------------------------------------------------------
class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ('nama', 'deskripsi')    # slug dibuat otomatis dari nama di models.py
        labels = {'nama': 'Nama', 'deskripsi': 'Deskripsi (opsional)'}
        widgets = {
            'nama': forms.TextInput(attrs={'placeholder': 'misal: Resensi'}),
            'deskripsi': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Penjelasan singkat kategori'}),
        }


# ------------------------------------------------------------
# 7. UBAH PENGGUNA (dipakai admin)
# ------------------------------------------------------------
class UbahPenggunaForm(forms.ModelForm):
    # Admin hanya boleh memilih penulis atau moderator di sini.
    # Role admin tidak bisa diberikan dari halaman ini.
    role = forms.ChoiceField(choices=[('penulis', 'Penulis'), ('moderator', 'Moderator')])

    class Meta:
        model = User
        fields = ('role', 'is_active')    # is_active: True aktif, False nonaktif