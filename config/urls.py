# ============================================================
# URLS
# Daftar alamat (URL) aplikasi dan view yang menanganinya.
# Format: path('alamat/', fungsi_view, name='nama_url')
#   - 'alamat/'  : yang diketik di browser setelah http://127.0.0.1:8000/
#   - fungsi_view: fungsi di views.py yang dijalankan
#   - name       : nama pendek untuk dipanggil di template, misal {% url 'dasbor' %}
# ============================================================
from django.contrib import admin
from django.contrib.auth import views as auth_views   # view bawaan Django untuk logout
from django.urls import path

from tulisan import views   # semua view yang kita tulis di tulisan/views.py

urlpatterns = [
    # ---------------- Panel admin bawaan Django ----------------
    path('admin/', admin.site.urls),

    # ---------------- Publik (tanpa login) ----------------
    path('', views.beranda, name='beranda'),
    # <slug:slug>: bagian URL yang berubah-ubah, misal /baca/hujan-di-bandung/
    # nilainya dikirim ke view sebagai parameter "slug"
    path('baca/<slug:slug>/', views.baca, name='baca'),
    path('baca/<slug:slug>/suka/', views.suka, name='suka'),

    # ---------------- Akun ----------------
    path('registrasi/', views.registrasi, name='registrasi'),
    # .as_view(): cara memasang view berbentuk class (MasukView) ke URL
    path('login/', views.MasukView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ---------------- Penulis ----------------
    path('dasbor/', views.dasbor, name='dasbor'),
    path('tulisan/baru/', views.tulis_baru, name='tulis_baru'),
    # <int:pk>: angka id tulisan, misal /tulisan/3/edit/
    path('tulisan/<int:pk>/edit/', views.edit_tulisan, name='edit_tulisan'),

    # ---------------- Moderator ----------------
    path('moderasi/', views.antrean, name='antrean'),
    path('moderasi/<int:pk>/', views.tinjau, name='tinjau'),
    path('moderasi/<int:pk>/tarik/', views.tarik, name='tarik'),

    # ---------------- Admin ----------------
    path('panel/pengguna/', views.panel_pengguna, name='panel_pengguna'),
    path('panel/pengguna/<int:pk>/ubah/', views.ubah_pengguna, name='ubah_pengguna'),
    path('panel/kategori/', views.panel_kategori, name='panel_kategori'),
    path('panel/kategori/<int:pk>/hapus/', views.hapus_kategori, name='hapus_kategori'),
]