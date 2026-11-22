import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "kutuphane.db"

def veritabani_baglantisi():
    baglanti = sqlite3.connect(DB_NAME)
    baglanti.row_factory = sqlite3.Row
    baglanti.execute("PRAGMA foreign_keys = ON")
    return baglanti

def tablolari_olustur():
    baglanti = veritabani_baglantisi()
    imlec = baglanti.cursor()

    # Kullanıcılar Tablosu
    imlec.execute("""
        CREATE TABLE IF NOT EXISTS kullanicilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_adi TEXT UNIQUE NOT NULL,
            sifre TEXT NOT NULL,
            ad_soyad TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'kullanici',
            kayit_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Kitaplar Tablosu
    imlec.execute("""
        CREATE TABLE IF NOT EXISTS kitaplar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kitap_adi TEXT NOT NULL,
            yazar TEXT NOT NULL DEFAULT 'Bilinmiyor',
            kategori TEXT NOT NULL DEFAULT 'Genel',
            sayfa_sayisi INTEGER DEFAULT 0,
            toplam_adet INTEGER NOT NULL DEFAULT 1,
            mevcut_adet INTEGER NOT NULL DEFAULT 1,
            eklenme_tarihi TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Ödünç ve Talep İşlemleri Tablosu
    imlec.execute("""
        CREATE TABLE IF NOT EXISTS oduncler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            kitap_id INTEGER NOT NULL,
            talep_tarihi TEXT DEFAULT (date('now', 'localtime')),
            odunc_tarihi TEXT,
            termin_tarihi TEXT,
            iade_tarihi TEXT,
            durum TEXT NOT NULL DEFAULT 'beklemede',
            FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id) ON DELETE CASCADE,
            FOREIGN KEY (kitap_id) REFERENCES kitaplar (id) ON DELETE CASCADE
        )
    """)

    # Sütun kontrolü - migration
    imlec.execute("PRAGMA table_info(oduncler)")
    odunc_sutunlar = [col["name"] for col in imlec.fetchall()]
    if "talep_tarihi" not in odunc_sutunlar:
        imlec.execute("ALTER TABLE oduncler ADD COLUMN talep_tarihi TEXT")
        imlec.execute("UPDATE oduncler SET talep_tarihi = odunc_tarihi WHERE talep_tarihi IS NULL")

    # Varsayılan Admin ve Kullanıcı Hesapları
    # Admin: admin / admin123
    admin_var_mi = imlec.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = ?", ("admin",)).fetchone()
    if not admin_var_mi:
        admin_sifre = generate_password_hash("admin123")
        imlec.execute("""
            INSERT INTO kullanicilar (kullanici_adi, sifre, ad_soyad, rol)
            VALUES (?, ?, ?, ?)
        """, ("admin", admin_sifre, "Kütüphane Yöneticisi", "admin"))

    # Örnek Öğrenci Kullanıcısı: ogrenci / 123456
    ogrenci_var_mi = imlec.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = ?", ("ogrenci",)).fetchone()
    if not ogrenci_var_mi:
        ogrenci_sifre = generate_password_hash("123456")
        imlec.execute("""
            INSERT INTO kullanicilar (kullanici_adi, sifre, ad_soyad, rol)
            VALUES (?, ?, ?, ?)
        """, ("ogrenci", ogrenci_sifre, "Ahmet Yılmaz", "kullanici"))

    # Örnek 2. Kullanıcı: elif / 123456
    elif_var_mi = imlec.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = ?", ("elif",)).fetchone()
    if not elif_var_mi:
        elif_sifre = generate_password_hash("123456")
        imlec.execute("""
            INSERT INTO kullanicilar (kullanici_adi, sifre, ad_soyad, rol)
            VALUES (?, ?, ?, ?)
        """, ("elif", elif_sifre, "Elif Demir", "kullanici"))

    # Örnek kitaplar ekleyelim (eğer hiç kitap yoksa)
    kitap_sayisi = imlec.execute("SELECT COUNT(*) as sayi FROM kitaplar").fetchone()["sayi"]
    if kitap_sayisi == 0:
        ornek_kitaplar = [
            ("Suç ve Ceza", "Fyodor Dostoyevski", "Dünya Klasikleri", 687, 4, 3),
            ("1984", "George Orwell", "Distopya / Bilim Kurgu", 352, 3, 2),
            ("Kürk Mantolu Madonna", "Sabahattin Ali", "Türk Edebiyatı", 160, 5, 5),
            ("Simyacı", "Paulo Coelho", "Felsefi Roman", 188, 3, 3),
            ("Dönüşüm", "Franz Kafka", "Dünya Klasikleri", 104, 4, 4),
            ("Nutuk", "Mustafa Kemal Atatürk", "Tarih", 599, 2, 2),
            ("Küçük Prens", "Antoine de Saint-Exupéry", "Çocuk / Felsefe", 112, 6, 6),
            ("Satranç", "Stefan Zweig", "Dünya Edebiyatı", 96, 4, 4),
            ("Fahrenheit 451", "Ray Bradbury", "Bilim Kurgu", 256, 3, 3),
            ("Beyaz Zambaklar Ülkesinde", "Grigory Petrov", "Kişisel Gelişim", 224, 3, 3)
        ]
        imlec.executemany("""
            INSERT INTO kitaplar (kitap_adi, yazar, kategori, sayfa_sayisi, toplam_adet, mevcut_adet)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ornek_kitaplar)

    baglanti.commit()
    baglanti.close()
    print("Veritabanı tabloları ve örnek veriler başarıyla hazırlandı.")

if __name__ == "__main__":
    tablolari_olustur()
