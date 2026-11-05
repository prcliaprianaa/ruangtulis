# ============================================================
# PANEL ADMIN BAWAAN DJANGO (/admin/)
# File ini mendaftarkan model ke panel admin, supaya datanya
# bisa dilihat dan diubah lewat browser tanpa menulis SQL.
# Panel ini dipakai untuk pemeliharaan; moderasi harian nanti
# lewat halaman moderator yang kita buat sendiri.
# ============================================================
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin   # tampilan admin bawaan untuk akun

from .models import (
    User, Kategori, Tulisan, RiwayatModerasi,
    AturanKonten, HasilChecklist, Suka,
)


# ------------------------------------------------------------
# PENGGUNA
# ------------------------------------------------------------
@admin.register(User)   # mendaftarkan model User dengan pengaturan di class ini
class PenggunaAdmin(UserAdmin):
    # Menambahkan bagian "Role" di halaman edit pengguna
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role',)}),)
    # Kolom yang tampil di daftar pengguna
    list_display = ('username', 'first_name', 'role', 'is_active')
    # Filter di sisi kanan halaman daftar
    list_filter = ('role', 'is_active')


# ------------------------------------------------------------
# KATEGORI
# ------------------------------------------------------------
@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ('nama', 'slug')
    # Kolom slug terisi otomatis saat mengetik nama
    prepopulated_fields = {'slug': ('nama',)}


# ------------------------------------------------------------
# TULISAN (beserta riwayat moderasinya)
# ------------------------------------------------------------
class RiwayatInline(admin.TabularInline):
    # Inline: menampilkan riwayat moderasi di dalam halaman tulisan
    model = RiwayatModerasi
    extra = 0                      # tidak menampilkan baris kosong tambahan
    can_delete = False             # riwayat tidak boleh dihapus
    readonly_fields = ('moderator', 'keputusan', 'catatan', 'dibuat')   # hanya bisa dibaca

    def has_add_permission(self, request, obj=None):
        # Riwayat hanya boleh dibuat dari halaman moderator, bukan dari sini
        return False


@admin.register(Tulisan)
class TulisanAdmin(admin.ModelAdmin):
    list_display = ('judul', 'penulis', 'kategori', 'status', 'diperbarui')
    list_filter = ('status', 'kategori')
    search_fields = ('judul', 'penulis__username')   # kotak pencarian: judul atau username penulis
    # Kolom yang diisi otomatis oleh sistem, jadi cukup ditampilkan
    readonly_fields = ('slug', 'dibuat', 'diperbarui', 'diajukan_pada', 'diterbitkan_pada')
    inlines = [RiwayatInline]


# ------------------------------------------------------------
# RIWAYAT MODERASI (beserta hasil checklist-nya)
# ------------------------------------------------------------
class HasilChecklistInline(admin.TabularInline):
    model = HasilChecklist
    extra = 0


@admin.register(RiwayatModerasi)
class RiwayatModerasiAdmin(admin.ModelAdmin):
    list_display = ('tulisan', 'moderator', 'keputusan', 'dibuat')
    list_filter = ('keputusan',)
    inlines = [HasilChecklistInline]


# ------------------------------------------------------------
# ATURAN KONTEN
# ------------------------------------------------------------
@admin.register(AturanKonten)
class AturanKontenAdmin(admin.ModelAdmin):
    list_display = ('urutan', 'nama', 'aktif')
    list_display_links = ('nama',)          # klik nama untuk membuka halaman edit
    list_editable = ('urutan', 'aktif')     # urutan dan status aktif bisa diubah langsung dari daftar


# ------------------------------------------------------------
# SUKA
# ------------------------------------------------------------
@admin.register(Suka)
class SukaAdmin(admin.ModelAdmin):
    list_display = ('pengguna', 'tulisan', 'dibuat')


# ------------------------------------------------------------
# JUDUL PANEL ADMIN
# ------------------------------------------------------------
admin.site.site_header = 'Admin RuangTulis'   # judul besar di atas halaman
admin.site.site_title = 'Admin RuangTulis'    # judul di tab browser
admin.site.index_title = 'Panel Admin'        # judul halaman utama admin
admin.site.site_url = '/'                     # tautan "Lihat Situs" mengarah ke beranda