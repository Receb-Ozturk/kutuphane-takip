# Kütüphane Takip Sistemi

Modern, kullanıcı dostu ve kapsamlı bir Flask + SQLite tabanlı kütüphane yönetim ve takip platformu.

## 🚀 Temel Özellikler

### 👤 1. Kullanıcı Paneli
- **Ödünç Alma Talebi Gönderme**:
  - Kullanıcılar kütüphane envanterindeki kitapları inceleyebilir, arama ve filtreleme yapabilir.
  - Kitaplar doğrudan alınamaz; kullanıcı tek tıkla **"Ödünç Talebi Gönder"** butonuna basarak kütüphane yöneticisine talep iletir.
  - Talep gönderilen kitapta *"Onay Bekliyor"* durumu görüntülenir.
- **Bekleyen Ödünç Taleplerim**:
  - Yöneticinin onayını bekleyen talepler listelenir.
  - Kullanıcı henüz onaylanmamış talebini dilerse tek tıkla **iptal edebilir**.
- **Üzerimdeki Kitaplar & Termin Takibi**:
  - Yöneticinin onayladığı aktif ödünçteki kitaplar listelenir.
  - Alış tarihi ve **son teslim (termin) tarihi** anlık olarak hesaplanır.
  - Kalan gün sayısı durum rozetiyle gösterilir (Örn: `10 gün kaldı`, `Bugün son gün!`, `3 gün gecikti!`).
  - Kullanıcı dilerse tek tıkla **"İade Et"** butonuna basarak kitabı kütüphaneye geri teslim edebilir.
- **Ödünç Geçmişi**:
  - Daha önce teslim edilmiş veya reddedilmiş kayıtların arşivi.

---

### 🛡️ 2. Admin (Yönetici) Paneli
- **Bekleyen Ödünç Talepleri Yönetimi**:
  - Kullanıcılardan gelen tüm ödünç talepleri özel bir sekmede bildirim sayacı ile listelenir.
  - Yönetici tek tıkla talebi **"Onayla"** diyerek onaylayabilir (kitap kullanıcının üzerine geçer, termin süresi başlar ve stok 1 düşer) veya **"Reddet"** işlemi yapabilir.
- **Kullanıcıya Doğrudan Kitap Ödünç Verme**:
  - Yönetici dilediği zaman **"Kullanıcıya Kitap Ödünç Ver"** butonuna tıklayarak açılan modal üzerinden istediği kullanıcıyı, kütüphanedeki kitabı ve özel termin süresini (örn: 14 gün, 21 gün) belirleyip doğrudan ödünç verebilir.
- **Genel İstatistikler**:
  - **Bekleyen Talepler**: Onay bekleyen talep sayısı.
  - **Kaç Kullanıcı Var?**: Sistemdeki toplam kayıtlı aktif üye sayısı.
  - **Kitap Envanteri**: Toplam kitap çeşidi ve kütüphanedeki toplam fiziksel adet.
  - **Ödünçteki Kitaplar**: Şu an kullanıcılarda bulunan aktif kitap sayısı.
  - **Geciken İadeler**: Termin süresi dolduğu halde teslim edilmemiş kitap sayısı.
- **Kullanıcı Takip Paneli (Kaç Kullanıcı Var?)**:
  - Tüm üyelerin ad soyad, kullanıcı adı, rol, kayıt tarihi, elindeki aktif kitap sayısı, bekleyen talepleri ve toplam ödünç hareketleri.
  - Kullanıcıya özel "Kitaplarını Gör" hızlı filtreleme seçeneği.
- **Ödünç Hareketleri (Kullanıcı Hangi Kitapları Almış?)**:
  - Hangi kullanıcının hangi kitabı ne zaman talep ettiği, aldığı, termin tarihi ve iade durumu.
  - Kullanıcıya veya duruma (Bekleyen, Ödünçte, Gecikenler, Teslim Edildi, Reddedildi) göre filtreleme.
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
| **Yönetici (Admin)** | `admin` | `admin123` | Talepleri onaylama/reddetme, doğrudan ödünç verme, envanter yönetimi |
| **Öğrenci (Kullanıcı)** | `ogrenci` | `123456` | Kitap talep etme, termin süresi takibi ve iade |
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

#### -Kurulum yapmadan kullanmak için 35.255.124.16:5000 adresini ziyaret edebilirsiniz.
