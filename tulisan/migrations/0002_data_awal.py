# ============================================================
# MIGRASI DATA AWAL
# File ini mengisi tabel kategori dan aturan_konten secara otomatis
# saat "python manage.py migrate" dijalankan.
# ============================================================
from django.db import migrations


def isi_data_awal(apps, schema_editor):
    # apps.get_model: mengambil model versi migrasi.
    # Di dalam migrasi kita tidak boleh import langsung dari models.py.
    Kategori = apps.get_model('tulisan', 'Kategori')
    AturanKonten = apps.get_model('tulisan', 'AturanKonten')

    # Daftar kategori: (nama, slug).
    # Slug ditulis manual karena fungsi save() di models.py
    # tidak ikut jalan di dalam migrasi.
    kategori = [
        ('Cerpen', 'cerpen'),
        ('Esai', 'esai'),
        ('Artikel', 'artikel'),
        ('Puisi', 'puisi'),
        ('Cerita Pengalaman', 'cerita-pengalaman'),
    ]
    for nama, slug in kategori:
        # get_or_create: buat data kalau belum ada, lewati kalau sudah ada
        Kategori.objects.get_or_create(nama=nama, defaults={'slug': slug})

    # Enam aturan konten sesuai proposal, dipakai sebagai checklist moderator
    aturan = [
        'Bebas konten seksual eksplisit',
        'Bebas kekerasan berlebihan',
        'Bebas ujaran kebencian',
        'Bukan promosi terselubung',
        'Karya asli, bukan jiplakan',
        'Tidak menyebarkan data pribadi orang lain',
    ]
    # enumerate(..., start=1): memberi nomor urut 1, 2, 3, dst untuk kolom "urutan"
    for urutan, nama in enumerate(aturan, start=1):
        AturanKonten.objects.get_or_create(nama=nama, defaults={'urutan': urutan})


def hapus_data_awal(apps, schema_editor):
    # Dijalankan kalau migrasi ini dibatalkan (migrate mundur).
    # Menghapus lagi data yang tadi dibuat.
    apps.get_model('tulisan', 'AturanKonten').objects.all().delete()
    apps.get_model('tulisan', 'Kategori').objects.all().delete()


class Migration(migrations.Migration):
    # Migrasi ini baru boleh jalan setelah tabel dibuat oleh 0001_initial
    dependencies = [
        ('tulisan', '0001_initial'),
    ]

    # RunPython: menjalankan fungsi Python di atas.
    # Argumen pertama untuk maju, argumen kedua untuk mundur.
    operations = [
        migrations.RunPython(isi_data_awal, hapus_data_awal),
    ]