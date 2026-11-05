# ============================================================
# IMPORT
# ============================================================
from django.conf import settings                     # mengambil pengaturan project, termasuk AUTH_USER_MODEL
from django.contrib.auth.models import AbstractUser  # model akun bawaan Django yang bisa kita kembangkan
from django.db import models                         # kumpulan tipe kolom: CharField, ForeignKey, dll
from django.utils.text import slugify                # mengubah teks jadi slug, misal "Hujan di Bandung" jadi "hujan-di-bandung"


# ============================================================
# 1. PENGGUNA
# Akun semua pengguna (penulis, moderator, admin).
# Mewarisi AbstractUser, jadi kolom username, password, first_name,
# email, is_active, dan lainnya sudah otomatis ada.
# Kita cuma menambahkan kolom "role".
# ============================================================
class User(AbstractUser):
    # Pilihan role. Kiri: nilai yang disimpan di database. Kanan: teks yang tampil.
    ROLE_CHOICES = [
        ('penulis', 'Penulis'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]
    # Setiap akun baru otomatis jadi penulis
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='penulis')

    class Meta:
        db_table = 'pengguna'             # nama tabel di database
        verbose_name = 'Pengguna'         # nama tunggal yang tampil di panel admin
        verbose_name_plural = 'Pengguna'  # nama jamak, supaya tidak jadi "Penggunas"

    def save(self, *args, **kwargs):
        # Fungsi ini jalan setiap kali akun disimpan.
        # Akun yang dibuat lewat createsuperuser otomatis ber-role admin.
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)  # lanjut menyimpan ke database seperti biasa

    def __str__(self):
        # Teks yang muncul saat akun ditampilkan, misalnya di panel admin.
        # Pakai nama lengkap, kalau kosong pakai username.
        return self.first_name or self.username


# ============================================================
# 2. KATEGORI
# Jenis tulisan: Cerpen, Esai, Artikel, Puisi, Cerita Pengalaman.
# ============================================================
class Kategori(models.Model):
    nama = models.CharField(max_length=50, unique=True)                # unique: tidak boleh ada nama kembar
    slug = models.SlugField(max_length=60, unique=True, blank=True)    # versi nama untuk URL, misal ?kategori=cerpen
    deskripsi = models.TextField(blank=True)                           # blank=True: boleh dikosongkan

    class Meta:
        db_table = 'kategori'
        ordering = ['nama']               # urutkan berdasarkan nama (A ke Z)
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategori'

    def save(self, *args, **kwargs):
        # Kalau slug belum diisi, buat otomatis dari nama
        if not self.slug:
            self.slug = slugify(self.nama)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama


# ============================================================
# 3. TULISAN
# Inti aplikasi: karya yang ditulis penulis dan ditinjau moderator.
# ============================================================
class Tulisan(models.Model):
    # Alur status: draf -> diajukan -> (perlu_revisi / ditolak / terbit) -> ditarik
    STATUS_CHOICES = [
        ('draf', 'Draf'),
        ('diajukan', 'Diajukan'),
        ('perlu_revisi', 'Perlu Revisi'),
        ('ditolak', 'Ditolak'),
        ('terbit', 'Terbit'),
        ('ditarik', 'Ditarik'),
    ]

    # ForeignKey: menghubungkan tulisan ke akun penulisnya.
    # on_delete=CASCADE: kalau akun penulis dihapus, tulisannya ikut terhapus.
    # related_name='tulisan': supaya bisa ambil semua tulisan seseorang dengan user.tulisan.all()
    penulis = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tulisan')

    # on_delete=PROTECT: kategori tidak bisa dihapus selama masih dipakai tulisan
    kategori = models.ForeignKey(Kategori, on_delete=models.PROTECT, related_name='tulisan')

    judul = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)     # untuk tautan /baca/<slug>/ yang bisa dibagikan
    isi = models.TextField()                                             # isi tulisan dalam format Markdown
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draf')
    pernyataan_orisinal = models.BooleanField(default=False)             # True kalau penulis mencentang pernyataan karya asli
    dibuat = models.DateTimeField(auto_now_add=True)                     # diisi otomatis saat tulisan pertama kali dibuat
    diperbarui = models.DateTimeField(auto_now=True)                     # diisi otomatis setiap tulisan disimpan
    diajukan_pada = models.DateTimeField(null=True, blank=True)          # waktu diajukan, untuk mengurutkan antrean moderator
    diterbitkan_pada = models.DateTimeField(null=True, blank=True)       # waktu terbit, untuk mengurutkan beranda

    class Meta:
        db_table = 'tulisan'
        ordering = ['-dibuat']            # tanda minus: urutkan dari yang terbaru
        verbose_name = 'Tulisan'
        verbose_name_plural = 'Tulisan'
        # Index mempercepat pencarian data yang sering dipakai:
        indexes = [
            models.Index(fields=['status', 'diterbitkan_pada']),  # untuk beranda (tulisan terbit, terbaru)
            models.Index(fields=['status', 'diajukan_pada']),     # untuk antrean moderasi (diajukan, terlama)
        ]

    def save(self, *args, **kwargs):
        # Buat slug otomatis dari judul, cukup sekali saat pertama disimpan.
        # Kalau sudah ada tulisan dengan slug sama, tambahkan angka: judul-2, judul-3, dst.
        if not self.slug:
            dasar = slugify(self.judul)[:200] or 'tulisan'
            slug = dasar
            n = 2
            while Tulisan.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{dasar}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    # @property: fungsi yang bisa dipanggil seperti kolom biasa, misal tulisan.bisa_diedit
    @property
    def bisa_diedit(self):
        # Penulis hanya boleh mengedit saat status draf atau perlu revisi
        return self.status in ('draf', 'perlu_revisi')

    @property
    def catatan_terakhir(self):
        # Mengambil keputusan moderator yang paling baru untuk tulisan ini
        return self.riwayat.first()

    def __str__(self):
        return self.judul


# ============================================================
# 4. RIWAYAT MODERASI
# Setiap kali moderator mengambil keputusan, dicatat 1 baris di sini.
# Dari sini penulis bisa membaca catatan moderator.
# ============================================================
class RiwayatModerasi(models.Model):
    KEPUTUSAN_CHOICES = [
        ('terbit', 'Terbitkan'),
        ('perlu_revisi', 'Minta Revisi'),
        ('ditolak', 'Tolak'),
        ('ditarik', 'Tarik'),
    ]
    tulisan = models.ForeignKey(Tulisan, on_delete=models.CASCADE, related_name='riwayat')
    # PROTECT: akun moderator tidak bisa dihapus selama punya riwayat, supaya catatan tetap utuh
    # (kalau mau "menghapus" moderator, cukup dinonaktifkan)
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='keputusan_moderasi')
    keputusan = models.CharField(max_length=20, choices=KEPUTUSAN_CHOICES)
    catatan = models.TextField(blank=True)               # wajib diisi untuk revisi, tolak, dan tarik (dicek di form nanti)
    dibuat = models.DateTimeField(auto_now_add=True)     # waktu keputusan diambil

    class Meta:
        db_table = 'riwayat_moderasi'
        ordering = ['-dibuat']            # keputusan terbaru di paling atas
        verbose_name = 'Riwayat Moderasi'
        verbose_name_plural = 'Riwayat Moderasi'

    def __str__(self):
        # get_keputusan_display() mengubah 'perlu_revisi' jadi 'Minta Revisi'
        return f'{self.tulisan} : {self.get_keputusan_display()}'


# ============================================================
# 5. ATURAN KONTEN
# Daftar aturan yang dicentang moderator saat meninjau (checklist).
# ============================================================
class AturanKonten(models.Model):
    nama = models.CharField(max_length=100)                 # teks aturan, misal "Bebas ujaran kebencian"
    deskripsi = models.TextField(blank=True)                # penjelasan tambahan, opsional
    urutan = models.PositiveSmallIntegerField(default=0)    # urutan tampil di checklist
    aktif = models.BooleanField(default=True)               # aturan nonaktif tidak muncul di checklist baru

    class Meta:
        db_table = 'aturan_konten'
        ordering = ['urutan']
        verbose_name = 'Aturan Konten'
        verbose_name_plural = 'Aturan Konten'

    def __str__(self):
        return self.nama


# ============================================================
# 6. HASIL CHECKLIST
# Menyimpan hasil centang moderator untuk setiap aturan
# pada satu keputusan (satu riwayat moderasi).
# ============================================================
class HasilChecklist(models.Model):
    riwayat = models.ForeignKey(RiwayatModerasi, on_delete=models.CASCADE, related_name='hasil_checklist')
    aturan = models.ForeignKey(AturanKonten, on_delete=models.PROTECT)
    terpenuhi = models.BooleanField()     # True: tulisan memenuhi aturan ini

    class Meta:
        db_table = 'hasil_checklist'
        verbose_name = 'Hasil Checklist'           # nama tunggal di panel admin
        verbose_name_plural = 'Hasil Checklist'    # nama jamak, supaya tidak jadi "Hasil checklists"
        constraints = [
            # Satu aturan hanya boleh dinilai sekali dalam satu keputusan
            models.UniqueConstraint(fields=['riwayat', 'aturan'], name='satu_aturan_per_riwayat'),
        ]


# ============================================================
# 7. SUKA
# Mencatat siapa menyukai tulisan apa.
# ============================================================
class Suka(models.Model):
    pengguna = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suka')
    tulisan = models.ForeignKey(Tulisan, on_delete=models.CASCADE, related_name='suka')
    dibuat = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'suka'
        verbose_name = 'Suka'             # nama tunggal di panel admin
        verbose_name_plural = 'Suka'      # nama jamak, supaya tidak jadi "Sukas"
        constraints = [
            # Satu pengguna hanya bisa menyukai satu tulisan sekali
            models.UniqueConstraint(fields=['pengguna', 'tulisan'], name='satu_suka_per_pengguna'),
        ]