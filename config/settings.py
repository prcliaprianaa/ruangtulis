# ============================================================
# SETTINGS.PY: pengaturan utama project RuangTulis
# ============================================================
from pathlib import Path

# BASE_DIR: folder utama project (folder yang berisi manage.py).
# Dipakai sebagai patokan lokasi file lain, misalnya database.
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------
# KEAMANAN
# ------------------------------------------------------------
# Kunci rahasia untuk mengamankan sesi login dan token CSRF.
# Jangan dibagikan ke publik. Saat deploy nanti kita pindahkan ke tempat yang lebih aman.
SECRET_KEY = 'django-insecure-m_qir_0x-_jecoz%lrd%wu@zm#%uq%x%)k*vdc6cd(bnm_!uh'

# DEBUG = True: mode pengembangan (dipakai selama ngoding di laptop).
# - Kalau ada error, Django menampilkan halaman error lengkap
# - File CSS di folder static otomatis ditampilkan oleh runserver
# Nanti saat aplikasi di-deploy online, nilai ini WAJIB diganti jadi False.
DEBUG = True

# Daftar alamat yang boleh membuka aplikasi. Di laptop cukup dua ini.
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# ------------------------------------------------------------
# APLIKASI YANG DIPAKAI
# ------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',          # panel admin bawaan (/admin/)
    'django.contrib.auth',           # sistem akun: login, logout, password
    'django.contrib.contenttypes',   # pendukung auth dan admin
    'django.contrib.sessions',       # menyimpan status login pengguna
    'django.contrib.messages',       # pesan singkat seperti "Tulisan berhasil disimpan"
    'django.contrib.staticfiles',    # pengelola file CSS, gambar, JavaScript
    'tulisan',                       # aplikasi kita
]

# Middleware: "penyaring" yang dilewati setiap request sebelum sampai ke views.py.
# Urutannya penting, jangan ditukar.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',            # header keamanan
    'django.contrib.sessions.middleware.SessionMiddleware',     # membaca sesi login
    'django.middleware.common.CommonMiddleware',                # pengaturan umum URL
    'django.middleware.csrf.CsrfViewMiddleware',                # memeriksa csrf_token di setiap form
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # mengisi request.user
    'django.contrib.messages.middleware.MessageMiddleware',      # mengaktifkan messages
    'django.middleware.clickjacking.XFrameOptionsMiddleware',   # mencegah halaman disisipkan di situs lain
]

# File daftar URL utama (config/urls.py)
ROOT_URLCONF = 'config.urls'

# Pengaturan template HTML
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,   # Django otomatis mencari template di folder tulisan/templates/
        'OPTIONS': {
            # context_processors: variabel yang otomatis tersedia di semua template
            'context_processors': [
                'django.template.context_processors.request',     # {{ request }}
                'django.contrib.auth.context_processors.auth',    # {{ user }}
                'django.contrib.messages.context_processors.messages',  # {{ messages }}
            ],
        },
    },
]

# Titik masuk aplikasi saat dijalankan di server (dipakai saat deploy)
WSGI_APPLICATION = 'config.wsgi.application'


# ------------------------------------------------------------
# DATABASE
# Sementara pakai SQLite (file db.sqlite3). Nanti diganti PostgreSQL.
# ------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ------------------------------------------------------------
# VALIDASI KATA SANDI (dipakai saat registrasi)
# ------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},  # tidak boleh mirip nama pengguna
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},           # minimal 8 karakter
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},          # tidak boleh terlalu umum, misal "12345678"
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},         # tidak boleh angka semua
]


# ------------------------------------------------------------
# BAHASA DAN WAKTU
# ------------------------------------------------------------
LANGUAGE_CODE = 'id'            # pesan bawaan Django dalam Bahasa Indonesia
TIME_ZONE = 'Asia/Jakarta'      # jam mengikuti WIB
USE_I18N = True                 # mengaktifkan terjemahan
USE_TZ = True                   # menyimpan waktu dengan zona waktu


# ------------------------------------------------------------
# FILE STATIS (CSS, gambar, JavaScript)
# ------------------------------------------------------------
STATIC_URL = 'static/'          # awalan alamat file statis, misal /static/tulisan/style.css

# Tipe kolom id otomatis untuk setiap tabel
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------
# AKUN DAN LOGIN
# ------------------------------------------------------------
# Model akun yang dipakai: model User buatan kita di app "tulisan", bukan bawaan Django
AUTH_USER_MODEL = 'tulisan.User'

# Halaman login, dipakai saat orang yang belum login membuka halaman yang butuh login
LOGIN_URL = 'login'

# Tujuan cadangan setelah login. Sebenarnya sudah diatur per role di MasukView,
# jadi ini hanya dipakai kalau suatu saat MasukView tidak dipakai.
LOGIN_REDIRECT_URL = 'beranda'

# Tujuan setelah logout: kembali ke beranda
LOGOUT_REDIRECT_URL = 'beranda'