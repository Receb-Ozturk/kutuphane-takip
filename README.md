# Kütüphane Takip Sistemi

Modern, kullanıcı dostu ve kapsamlı bir Flask + SQLite tabanlı kütüphane yönetim ve takip platformu.

## 🚀 Temel Özellikler

### 👤 1. Kullanıcı Paneli
- **Ödünç Alınan Kitaplar & Termin Takibi**:
  - Kullanıcının elinde bulunan aktif kitaplar listelenir.
  - Alış tarihi ve **son teslim (termin) tarihi** anlık olarak hesaplanır.
  - Kalan gün sayısı durum rozetiyle gösterilir (Örn: `10 gün kaldı`, `Bugün son gün!`, `3 gün gecikti!`).
  - Kullanıcı dilerse tek tıkla **"İade Et"** butonuna basarak kitabı kütüphaneye geri teslim edebilir.
- **Kütüphane Kitap Envanteri & Ödünç Alma**:
  - Kütüphanedeki tüm kitapların güncel envanteri (kitap adı, yazar, kategori, sayfa sayısı).
  - Raftaki mevcut adet ve toplam stok durumu.
  - Kitap ve yazar adına göre anlık arama ile kategoriye göre filtreleme.
  - Stokta olan kitaplar için tek tıkla **"Ödünç Al"** işlemi (varsayılan 14 günlük termin süresi).
  - Zaten kullanıcının elinde olan veya stoğu tükenmiş kitaplar için akıllı buton durumu.
- **Ödünç Geçmişi**:
  - Daha önce teslim edilmiş kitapların tam arşivi ve teslim tarihleri.

---

### 🛡️ 2. Admin (Yönetici) Paneli
- **Genel İstatistikler**:
  - **Kaç Kullanıcı Var?**: Sistemdeki toplam kayıtlı aktif üye sayısı.
  - **Kitap Envanteri**: Toplam kitap çeşidi ve kütüphanedeki toplam fiziksel adet.
  - **Ödünçteki Kitaplar**: Şu an kullanıcılarda bulunan aktif kitap sayısı.
  - **Geciken İadeler**: Termin süresi dolduğu halde teslim edilmemiş kitap sayısı.
- **Kullanıcı Takip Paneli (Kaç Kullanıcı Var?)**:
  - Tüm üyelerin ad soyad, kullanıcı adı, rol, kayıt tarihi, elindeki aktif kitap sayısı ve toplam ödünç hareketleri.
  - Kullanıcıya özel "Kitaplarını Gör" hızlı filtreleme seçeneği.
- **Ödünç Hareketleri (Kullanıcı Hangi Kitapları Almış?)**:
  - Hangi kullanıcının hangi kitabı ne zaman aldığı, termin tarihi ve iade durumu.
  - Kullanıcıya veya duruma (Ödünçte / Gecikenler / Teslim Edildi) göre filtreleme.
  - Yöneticinin elden teslim alabilmesi için tek tıkla **"İade Al"** işlemi.
- **Kitap Envanteri Yönetimi**:
  - **Yeni Kitap Ekleme**: Ad, yazar, kategori, sayfa sayısı ve stok adedi ile modal üzerinden hızlı kayıt.
  - **Kitap Düzenleme**: Bilgileri ve toplam stok adedini güncelleme (ödünçteki adet kontrolü ile güvenli düzenleme).
  - **Kitap Silme**: Ödünçte olmayan kitapları güvenle envanterden çıkarma (ödünçteyse silinmeyi engeller).

---

## 🔑 Hazır Demo Hesap Bilgileri

Sistem ilk çalıştığında otomatik olarak aşağıdaki test hesaplarını ve zengin kitap envanterini hazırlar:

| Rol | Kullanıcı Adı | Şifre | Açıklama |
|---|---|---|---|
| **Yönetici (Admin)** | `admin` | `admin123` | Tüm istatistikler, kullanıcılar ve envanter yönetimi |
| **Öğrenci (Kullanıcı)** | `ogrenci` | `123456` | Kitap alma, termin süresi takibi ve iade |
| **Kullanıcı 2** | `elif` | `123456` | İkinci örnek öğrenci hesabı |

*(Giriş sayfasında yer alan "Hızlı Test Girişi" butonlarıyla tek tıkla bu hesaplara giriş yapabilirsiniz.)*

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Sanal Ortamı Aktif Edin (Gerekirse):
```bash
source venv/bin/activate
```

### 2. Uygulamayı Başlatın:
```bash
python app.py
```
*(veya `./venv/bin/python app.py`)*

### 3. Tarayıcınızda Açın:
Tarayıcınızdan **`http://127.0.0.1:5000`** adresine giderek sistemi kullanmaya başlayabilirsiniz.

