# ============================================================
# HAK AKSES
# Berisi alat bantu untuk membatasi halaman berdasarkan role.
# Pengecekan dilakukan di server, jadi meskipun seseorang
# mengetik URL secara langsung, tetap ditolak kalau role-nya salah.
# ============================================================
from functools import wraps                                    # menjaga nama dan info fungsi asli saat dibungkus decorator

from django.contrib.auth.decorators import login_required     # memaksa login sebelum membuka halaman
from django.core.exceptions import PermissionDenied           # memunculkan halaman 403 Forbidden


def role_required(*roles):
    # Decorator untuk membatasi view hanya untuk role tertentu.
    # Cara pakai, ditulis tepat di atas fungsi view:
    #   @role_required('moderator')
    #   @role_required('penulis')
    #   @role_required('admin')
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Kalau role pengguna tidak ada di daftar yang diizinkan, tolak dengan 403
            if request.user.role not in roles:
                raise PermissionDenied
            # Kalau diizinkan, jalankan view aslinya
            return view_func(request, *args, **kwargs)
        # login_required: kalau belum login, diarahkan dulu ke halaman login
        return login_required(wrapper)
    return decorator


def halaman_awal(user):
    # Menentukan halaman tujuan setelah login sesuai role.
    # Nilai yang dikembalikan adalah nama URL (dibuat nanti di urls.py).
    if user.role == 'moderator':
        return 'antrean'
    if user.role == 'admin':
        return 'panel_pengguna'
    return 'dasbor'