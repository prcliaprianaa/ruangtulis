# ============================================================
# FILTER TEMPLATE UNTUK TULISAN
# Filter adalah fungsi kecil yang bisa dipakai langsung di file HTML,
# contohnya: {{ tulisan.isi|markdown_aman }}
# Supaya bisa dipakai, di atas file HTML perlu ditulis:
#   {% load markdown_filter %}
# ============================================================
from html import unescape                       # mengubah kode seperti &amp; kembali jadi &

import markdown                                 # library pengubah Markdown ke HTML
import nh3                                      # library pembersih HTML dari script berbahaya
from django import template
from django.utils.html import strip_tags        # membuang semua tag HTML, menyisakan teksnya saja
from django.utils.safestring import mark_safe   # menandai HTML sudah aman untuk ditampilkan apa adanya

# Wadah pendaftaran filter. Nama variabelnya harus "register".
register = template.Library()


@register.filter
def markdown_aman(teks):
    # Mengubah isi tulisan (Markdown) menjadi HTML yang aman ditampilkan.
    # Ekstensi yang dipakai:
    #   extra      : mendukung tabel, catatan kaki, dan fitur Markdown tambahan
    #   sane_lists : daftar bernomor dan butir tidak tercampur
    #   nl2br      : setiap Enter jadi baris baru, penting untuk puisi
    html = markdown.markdown(teks or '', extensions=['extra', 'sane_lists', 'nl2br'])
    # nh3.clean membuang tag berbahaya seperti <script> atau atribut onclick,
    # tapi tetap menyisakan tag aman seperti <p>, <strong>, <blockquote>, <ul>
    bersih = nh3.clean(html)
    # Tanpa mark_safe, Django akan menampilkan tag HTML sebagai teks biasa
    return mark_safe(bersih)


@register.filter
def teks_polos(teks):
    # Mengubah Markdown jadi teks biasa tanpa simbol, untuk cuplikan di beranda.
    # Contoh: "**Halo** dunia" jadi "Halo dunia"
    return unescape(strip_tags(markdown.markdown(teks or '')))


@register.filter
def waktu_baca(teks):
    # Memperkirakan lama membaca dalam menit.
    # Asumsi rata-rata membaca 200 kata per menit, minimal 1 menit.
    jumlah_kata = len((teks or '').split())
    return max(1, round(jumlah_kata / 200))