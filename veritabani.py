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

    # Kitaplar Tablosu kontrolü - eğer eski şema ise baştan oluşturalım
    imlec.execute("PRAGMA table_info(kitaplar)")
    kitap_sutunlar = [col["name"] for col in imlec.fetchall()]
    
    if kitap_sutunlar and "yazar" not in kitap_sutunlar:
        # Eski basit tablo var, yenisiyle değiştirelim
        imlec.execute("DROP TABLE IF EXISTS kitaplar")

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

    # Ödünç İşlemleri Tablosu
    imlec.execute("""
        CREATE TABLE IF NOT EXISTS oduncler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kullanici_id INTEGER NOT NULL,
            kitap_id INTEGER NOT NULL,
            odunc_tarihi TEXT NOT NULL,
            termin_tarihi TEXT NOT NULL,
            iade_tarihi TEXT,
            durum TEXT NOT NULL DEFAULT 'oduncte',
            FOREIGN KEY (kullanici_id) REFERENCES kullanicilar (id) ON DELETE CASCADE,
            FOREIGN KEY (kitap_id) REFERENCES kitaplar (id) ON DELETE CASCADE
        )
    """)

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

    # Örnek kitaplar ekleyelim
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

        # Örnek bir ödünç kaydı ekleyelim (ogrenci bir kitap almış olsun)
        ogrenci_id = imlec.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = 'ogrenci'").fetchone()["id"]
        elif_id = imlec.execute("SELECT id FROM kullanicilar WHERE kullanici_adi = 'elif'").fetchone()["id"]
        
        suc_ve_ceza_id = imlec.execute("SELECT id FROM kitaplar WHERE kitap_adi = 'Suç ve Ceza'").fetchone()["id"]
        orwell_id = imlec.execute("SELECT id FROM kitaplar WHERE kitap_adi = '1984'").fetchone()["id"]
        
        # 1. Ödünç: ogrenci -> Suç ve Ceza (termin: 10 gün sonrası)
        imlec.execute("""
            INSERT INTO oduncler (kullanici_id, kitap_id, odunc_tarihi, termin_tarihi, durum)
            VALUES (?, ?, date('now', '-4 days'), date('now', '+10 days'), 'oduncte')
        """, (ogrenci_id, suc_ve_ceza_id))

        # 2. Ödünç: elif -> 1984 (termin: 5 gün sonrası)
        imlec.execute("""
            INSERT INTO oduncler (kullanici_id, kitap_id, odunc_tarihi, termin_tarihi, durum)
            VALUES (?, ?, date('now', '-9 days'), date('now', '+5 days'), 'oduncte')
        """, (elif_id, orwell_id))

    baglanti.commit()
    baglanti.close()
    print("Veritabanı tabloları ve örnek veriler başarıyla hazırlandı.")

if __name__ == "__main__":
    tablolari_olustur()
