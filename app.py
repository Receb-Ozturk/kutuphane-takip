import sqlite3
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from veritabani import veritabani_baglantisi, tablolari_olustur

app = Flask(__name__)
app.secret_key = "kutuphane-takip-sistemi-gizli-anahtar-12345"

# Uygulama başlarken tabloların hazır olduğundan emin olalım
tablolari_olustur()


# --- YARDIMCI VE YETKİ KONTROL FONKSİYONLARI ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "kullanici_id" not in session:
            flash("Lütfen önce giriş yapınız.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "kullanici_id" not in session:
            flash("Lütfen önce giriş yapınız.", "warning")
            return redirect(url_for("login"))
        if session.get("rol") != "admin":
            flash("Bu sayfaya erişim yetkiniz bulunmamaktadır!", "danger")
            return redirect(url_for("kullanici_paneli"))
        return f(*args, **kwargs)
    return decorated_function

@app.template_filter("kalan_gun_hesapla")
def kalan_gun_hesapla(termin_tarihi_str):
    """Termin tarihine göre kalan gün sayısını ve durum etiketini döner."""
    try:
        termin_tarihi = datetime.strptime(termin_tarihi_str, "%Y-%m-%d").date()
        bugun = date.today()
        fark = (termin_tarihi - bugun).days
        if fark < 0:
            return {"gun": abs(fark), "durum": "gecikti", "metin": f"{abs(fark)} gün gecikti!", "renk": "danger"}
        elif fark == 0:
            return {"gun": 0, "durum": "bugun", "metin": "Bugün son gün!", "renk": "warning"}
        else:
            return {"gun": fark, "durum": "kalan", "metin": f"{fark} gün kaldı", "renk": "success" if fark > 3 else "warning"}
    except Exception:
        return {"gun": 0, "durum": "bilinmiyor", "metin": "Tarih belirtilmedi", "renk": "secondary"}


# --- GİRİŞ / KAYIT / ÇIKIŞ İŞLEMLERİ ---

@app.route("/")
def index():
    if "kullanici_id" in session:
        if session.get("rol") == "admin":
            return redirect(url_for("admin_paneli"))
        return redirect(url_for("kullanici_paneli"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "kullanici_id" in session:
        if session.get("rol") == "admin":
            return redirect(url_for("admin_paneli"))
        return redirect(url_for("kullanici_paneli"))

    if request.method == "POST":
        kullanici_adi = request.form.get("kullanici_adi", "").strip()
        sifre = request.form.get("sifre", "").strip()

        if not kullanici_adi or not sifre:
            flash("Lütfen tüm alanları doldurunuz.", "warning")
            return render_template("login.html")

        baglanti = veritabani_baglantisi()
        kullanici = baglanti.execute(
            "SELECT * FROM kullanicilar WHERE kullanici_adi = ?",
            (kullanici_adi,)
        ).fetchone()
        baglanti.close()

        if kullanici and check_password_hash(kullanici["sifre"], sifre):
            session["kullanici_id"] = kullanici["id"]
            session["kullanici_adi"] = kullanici["kullanici_adi"]
            session["ad_soyad"] = kullanici["ad_soyad"]
            session["rol"] = kullanici["rol"]
            flash(f"Hoş geldiniz, {kullanici['ad_soyad']}!", "success")
            if kullanici["rol"] == "admin":
                return redirect(url_for("admin_paneli"))
            return redirect(url_for("kullanici_paneli"))
        else:
            flash("Kullanıcı adı veya şifre hatalı!", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "kullanici_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        ad_soyad = request.form.get("ad_soyad", "").strip()
        kullanici_adi = request.form.get("kullanici_adi", "").strip().lower()
        sifre = request.form.get("sifre", "").strip()
        sifre_tekrar = request.form.get("sifre_tekrar", "").strip()

        if not ad_soyad or not kullanici_adi or not sifre:
            flash("Lütfen tüm zorunlu alanları doldurunuz.", "warning")
            return render_template("register.html")

        if sifre != sifre_tekrar:
            flash("Girdiğiniz şifreler birbiriyle uyuşmuyor!", "warning")
            return render_template("register.html")

        if len(sifre) < 4:
            flash("Şifre en az 4 karakter olmalıdır.", "warning")
            return render_template("register.html")

        baglanti = veritabani_baglantisi()
        var_mi = baglanti.execute(
            "SELECT id FROM kullanicilar WHERE kullanici_adi = ?",
            (kullanici_adi,)
        ).fetchone()

        if var_mi:
            baglanti.close()
            flash("Bu kullanıcı adı zaten alınmış. Lütfen başka bir kullanıcı adı seçin.", "danger")
            return render_template("register.html")

        sifre_hash = generate_password_hash(sifre)
        baglanti.execute(
            "INSERT INTO kullanicilar (kullanici_adi, sifre, ad_soyad, rol) VALUES (?, ?, ?, 'kullanici')",
            (kullanici_adi, sifre_hash, ad_soyad)
        )
        baglanti.commit()
        baglanti.close()

        flash("Kayıt işleminiz başarıyla tamamlandı! Şimdi giriş yapabilirsiniz.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız.", "info")
    return redirect(url_for("login"))


# --- KULLANICI PANELİ ---

@app.route("/kullanici")
@login_required
def kullanici_paneli():
    kullanici_id = session["kullanici_id"]
    arama_kelimesi = request.args.get("q", "").strip()
    secili_kategori = request.args.get("kategori", "").strip()

    baglanti = veritabani_baglantisi()

    # 1. Kullanıcının şu an elinde olan aktif ödünç kitapları
    aktif_oduncler = baglanti.execute("""
        SELECT o.id as odunc_id, o.odunc_tarihi, o.termin_tarihi, o.durum,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori, k.sayfa_sayisi
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.kullanici_id = ? AND o.durum = 'oduncte'
        ORDER BY o.termin_tarihi ASC
    """, (kullanici_id,)).fetchall()

    # 2. Kullanıcının daha önce teslim ettiği kitaplar (geçmiş)
    gecmis_oduncler = baglanti.execute("""
        SELECT o.id as odunc_id, o.odunc_tarihi, o.termin_tarihi, o.iade_tarihi, o.durum,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.kullanici_id = ? AND o.durum = 'teslim_edildi'
        ORDER BY o.iade_tarihi DESC
    """, (kullanici_id,)).fetchall()

    # 3. Kütüphane Kitap Envanteri & Arama / Filtreleme
    kitap_sorgu = "SELECT * FROM kitaplar WHERE 1=1"
    parametreler = []

    if arama_kelimesi:
        kitap_sorgu += " AND (kitap_adi LIKE ? OR yazar LIKE ?)"
        parametreler.extend([f"%{arama_kelimesi}%", f"%{arama_kelimesi}%"])

    if secili_kategori:
        kitap_sorgu += " AND kategori = ?"
        parametreler.append(secili_kategori)

    kitap_sorgu += " ORDER BY kitap_adi ASC"
    envanter_kitaplar = baglanti.execute(kitap_sorgu, parametreler).fetchall()

    # Mevcut tüm kategoriler (filtre için)
    kategoriler = baglanti.execute("SELECT DISTINCT kategori FROM kitaplar ORDER BY kategori ASC").fetchall()

    # Kullanıcının şu an elinde bulunan kitapların ID listesi
    elindeki_kitap_idleri = [o["kitap_id"] for o in aktif_oduncler]

    baglanti.close()

    return render_template(
        "kullanici.html",
        aktif_oduncler=aktif_oduncler,
        gecmis_oduncler=gecmis_oduncler,
        envanter_kitaplar=envanter_kitaplar,
        kategoriler=kategoriler,
        elindeki_kitap_idleri=elindeki_kitap_idleri,
        arama_kelimesi=arama_kelimesi,
        secili_kategori=secili_kategori
    )

@app.route("/kitap-odunc-al/<int:kitap_id>", methods=["POST"])
@login_required
def kitap_odunc_al(kitap_id):
    kullanici_id = session["kullanici_id"]
    baglanti = veritabani_baglantisi()

    # Kitap var mı ve stokta mı?
    kitap = baglanti.execute("SELECT * FROM kitaplar WHERE id = ?", (kitap_id,)).fetchone()
    if not kitap:
        baglanti.close()
        flash("Seçilen kitap bulunamadı!", "danger")
        return redirect(url_for("kullanici_paneli"))

    if kitap["mevcut_adet"] <= 0:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' şu an kütüphanede kalmamıştır. Başka bir kitap seçebilirsiniz.", "warning")
        return redirect(url_for("kullanici_paneli"))

    # Kullanıcı zaten bu kitabı almış mı?
    zaten_almis = baglanti.execute("""
        SELECT id FROM oduncler
        WHERE kullanici_id = ? AND kitap_id = ? AND durum = 'oduncte'
    """, (kullanici_id, kitap_id)).fetchone()

    if zaten_almis:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' zaten şu an sizin üzerinizde kayıtlı!", "warning")
        return redirect(url_for("kullanici_paneli"))

    # Kullanıcının elinde en fazla 3 aktif kitap sınırı (makul ve gerçekçi kural)
    aktif_sayisi = baglanti.execute("""
        SELECT COUNT(*) as sayi FROM oduncler
        WHERE kullanici_id = ? AND durum = 'oduncte'
    """, (kullanici_id,)).fetchone()["sayi"]

    if aktif_sayisi >= 5:
        baglanti.close()
        flash("Aynı anda en fazla 5 kitap ödünç alabilirsiniz. Lütfen önce elinizdeki kitaplardan birini iade ediniz.", "warning")
        return redirect(url_for("kullanici_paneli"))

    bugun = date.today()
    termin = bugun + timedelta(days=14) # Standart 14 gün termin süresi

    # Ödünç kaydı ekle ve mevcut adedi düşür
    baglanti.execute("""
        INSERT INTO oduncler (kullanici_id, kitap_id, odunc_tarihi, termin_tarihi, durum)
        VALUES (?, ?, ?, ?, 'oduncte')
    """, (kullanici_id, kitap_id, bugun.isoformat(), termin.isoformat()))

    baglanti.execute("""
        UPDATE kitaplar SET mevcut_adet = mevcut_adet - 1 WHERE id = ?
    """, (kitap_id,))

    baglanti.commit()
    baglanti.close()

    flash(f"'{kitap['kitap_adi']}' başarıyla ödünç alındı! Son teslim tarihi (termin): {termin.strftime('%d.%m.%Y')}", "success")
    return redirect(url_for("kullanici_paneli"))

@app.route("/kitap-iade-et/<int:odunc_id>", methods=["POST"])
@login_required
def kitap_iade_et(odunc_id):
    kullanici_id = session["kullanici_id"]
    baglanti = veritabani_baglantisi()

    # Ödünç kaydını getir
    odunc = baglanti.execute("""
        SELECT o.*, k.kitap_adi
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.id = ? AND o.kullanici_id = ? AND o.durum = 'oduncte'
    """, (odunc_id, kullanici_id)).fetchone()

    if not odunc:
        baglanti.close()
        flash("İade edilecek aktif ödünç kaydı bulunamadı!", "danger")
        return redirect(url_for("kullanici_paneli"))

    bugun = date.today().isoformat()

    baglanti.execute("""
        UPDATE oduncler
        SET durum = 'teslim_edildi', iade_tarihi = ?
        WHERE id = ?
    """, (bugun, odunc_id))

    baglanti.execute("""
        UPDATE kitaplar
        SET mevcut_adet = MIN(toplam_adet, mevcut_adet + 1)
        WHERE id = ?
    """, (odunc["kitap_id"],))

    baglanti.commit()
    baglanti.close()

    flash(f"'{odunc['kitap_adi']}' kitabını başarıyla kütüphaneye iade ettiniz. Teşekkür ederiz!", "success")
    return redirect(url_for("kullanici_paneli"))


# --- ADMİN PANELİ ---

@app.route("/admin")
@admin_required
def admin_paneli():
    baglanti = veritabani_baglantisi()

    # İstatistikler
    kullanici_sayisi = baglanti.execute(
        "SELECT COUNT(*) as sayi FROM kullanicilar WHERE rol != 'admin'"
    ).fetchone()["sayi"]

    toplam_kitap_cesidi = baglanti.execute(
        "SELECT COUNT(*) as sayi FROM kitaplar"
    ).fetchone()["sayi"]

    toplam_kitap_stok = baglanti.execute(
        "SELECT COALESCE(SUM(toplam_adet), 0) as toplam FROM kitaplar"
    ).fetchone()["toplam"]

    aktif_odunc_sayisi = baglanti.execute(
        "SELECT COUNT(*) as sayi FROM oduncler WHERE durum = 'oduncte'"
    ).fetchone()["sayi"]

    geciken_odunc_sayisi = baglanti.execute(
        "SELECT COUNT(*) as sayi FROM oduncler WHERE durum = 'oduncte' AND termin_tarihi < date('now')"
    ).fetchone()["sayi"]

    # 1. Kullanıcılar Listesi & Aldıkları Kitap Sayısı (Kaç kullanıcı var?)
    kullanicilar = baglanti.execute("""
        SELECT u.id, u.kullanici_adi, u.ad_soyad, u.rol, u.kayit_tarihi,
               (SELECT COUNT(*) FROM oduncler WHERE kullanici_id = u.id AND durum = 'oduncte') as aktif_kitap_sayisi,
               (SELECT COUNT(*) FROM oduncler WHERE kullanici_id = u.id) as toplam_odunc_sayisi
        FROM kullanicilar u
        ORDER BY u.rol ASC, u.ad_soyad ASC
    """).fetchall()

    # 2. Kullanıcı Hangi Kitapları Almış? (Ödünç Hareketleri)
    filtre_kullanici = request.args.get("kullanici_id", "").strip()
    filtre_durum = request.args.get("durum", "").strip()

    odunc_sorgu = """
        SELECT o.id as odunc_id, o.odunc_tarihi, o.termin_tarihi, o.iade_tarihi, o.durum,
               u.id as kullanici_id, u.kullanici_adi, u.ad_soyad,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori
        FROM oduncler o
        JOIN kullanicilar u ON o.kullanici_id = u.id
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE 1=1
    """
    parametreler = []

    if filtre_kullanici and filtre_kullanici.isdigit():
        odunc_sorgu += " AND u.id = ?"
        parametreler.append(int(filtre_kullanici))

    if filtre_durum:
        if filtre_durum == "gecikti":
            odunc_sorgu += " AND o.durum = 'oduncte' AND o.termin_tarihi < date('now')"
        else:
            odunc_sorgu += " AND o.durum = ?"
            parametreler.append(filtre_durum)

    odunc_sorgu += " ORDER BY o.id DESC"
    odunc_hareketleri = baglanti.execute(odunc_sorgu, parametreler).fetchall()

    # 3. Kitap Envanteri
    envanter = baglanti.execute("""
        SELECT k.*,
               (k.toplam_adet - k.mevcut_adet) as oduncteki_adet
        FROM kitaplar k
        ORDER BY k.id DESC
    """).fetchall()

    baglanti.close()

    return render_template(
        "admin.html",
        kullanici_sayisi=kullanici_sayisi,
        toplam_kitap_cesidi=toplam_kitap_cesidi,
        toplam_kitap_stok=toplam_kitap_stok,
        aktif_odunc_sayisi=aktif_odunc_sayisi,
        geciken_odunc_sayisi=geciken_odunc_sayisi,
        kullanicilar=kullanicilar,
        odunc_hareketleri=odunc_hareketleri,
        envanter=envanter,
        filtre_kullanici=filtre_kullanici,
        filtre_durum=filtre_durum
    )


# --- ADMİN KİTAP ENVANTERİ VE İADE İŞLEMLERİ ---

@app.route("/admin/kitap-ekle", methods=["POST"])
@admin_required
def admin_kitap_ekle():
    kitap_adi = request.form.get("kitap_adi", "").strip()
    yazar = request.form.get("yazar", "").strip() or "Bilinmiyor"
    kategori = request.form.get("kategori", "").strip() or "Genel"
    sayfa_sayisi = request.form.get("sayfa_sayisi", "0").strip()
    toplam_adet = request.form.get("toplam_adet", "1").strip()

    if not kitap_adi:
        flash("Kitap adı zorunludur!", "danger")
        return redirect(url_for("admin_paneli"))

    try:
        sayfa_sayisi = int(sayfa_sayisi) if sayfa_sayisi else 0
        toplam_adet = max(1, int(toplam_adet) if toplam_adet else 1)
    except ValueError:
        flash("Sayfa sayısı veya adet geçerli bir sayı olmalıdır!", "warning")
        return redirect(url_for("admin_paneli"))

    baglanti = veritabani_baglantisi()
    baglanti.execute("""
        INSERT INTO kitaplar (kitap_adi, yazar, kategori, sayfa_sayisi, toplam_adet, mevcut_adet)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (kitap_adi, yazar, kategori, sayfa_sayisi, toplam_adet, toplam_adet))
    baglanti.commit()
    baglanti.close()

    flash(f"'{kitap_adi}' adlı kitap envantere başarıyla eklendi.", "success")
    return redirect(url_for("admin_paneli"))

@app.route("/admin/kitap-duzenle/<int:kitap_id>", methods=["POST"])
@admin_required
def admin_kitap_duzenle(kitap_id):
    kitap_adi = request.form.get("kitap_adi", "").strip()
    yazar = request.form.get("yazar", "").strip() or "Bilinmiyor"
    kategori = request.form.get("kategori", "").strip() or "Genel"
    sayfa_sayisi = request.form.get("sayfa_sayisi", "0").strip()
    yeni_toplam_adet = request.form.get("toplam_adet", "1").strip()

    if not kitap_adi:
        flash("Kitap adı boş bırakılamaz!", "danger")
        return redirect(url_for("admin_paneli"))

    try:
        sayfa_sayisi = int(sayfa_sayisi) if sayfa_sayisi else 0
        yeni_toplam_adet = max(1, int(yeni_toplam_adet) if yeni_toplam_adet else 1)
    except ValueError:
        flash("Geçersiz sayısal değer girdiniz!", "warning")
        return redirect(url_for("admin_paneli"))

    baglanti = veritabani_baglantisi()
    kitap = baglanti.execute("SELECT * FROM kitaplar WHERE id = ?", (kitap_id,)).fetchone()
    if not kitap:
        baglanti.close()
        flash("Kitap bulunamadı!", "danger")
        return redirect(url_for("admin_paneli"))

    # Ödünçteki adet: toplam_adet - mevcut_adet
    oduncteki = kitap["toplam_adet"] - kitap["mevcut_adet"]
    if yeni_toplam_adet < oduncteki:
        baglanti.close()
        flash(f"Toplam stok, şu an ödünçte olan kitap sayısından ({oduncteki}) az olamaz!", "warning")
        return redirect(url_for("admin_paneli"))

    yeni_mevcut_adet = yeni_toplam_adet - oduncteki

    baglanti.execute("""
        UPDATE kitaplar
        SET kitap_adi = ?, yazar = ?, kategori = ?, sayfa_sayisi = ?, toplam_adet = ?, mevcut_adet = ?
        WHERE id = ?
    """, (kitap_adi, yazar, kategori, sayfa_sayisi, yeni_toplam_adet, yeni_mevcut_adet, kitap_id))
    baglanti.commit()
    baglanti.close()

    flash(f"'{kitap_adi}' bilgileri başarıyla güncellendi.", "success")
    return redirect(url_for("admin_paneli"))

@app.route("/admin/kitap-sil/<int:kitap_id>", methods=["POST"])
@admin_required
def admin_kitap_sil(kitap_id):
    baglanti = veritabani_baglantisi()
    
    # Kitap şu an birinde ödünçte mi?
    aktif_odunc = baglanti.execute("""
        SELECT COUNT(*) as sayi FROM oduncler WHERE kitap_id = ? AND durum = 'oduncte'
    """, (kitap_id,)).fetchone()["sayi"]

    if aktif_odunc > 0:
        baglanti.close()
        flash(f"Bu kitap şu an {aktif_odunc} kullanıcıda ödünçtedir. İade alınmadan silinemez!", "danger")
        return redirect(url_for("admin_paneli"))

    baglanti.execute("DELETE FROM kitaplar WHERE id = ?", (kitap_id,))
    baglanti.commit()
    baglanti.close()

    flash("Kitap envanterden silindi.", "info")
    return redirect(url_for("admin_paneli"))

@app.route("/admin/iade-al/<int:odunc_id>", methods=["POST"])
@admin_required
def admin_iade_al(odunc_id):
    baglanti = veritabani_baglantisi()
    odunc = baglanti.execute("""
        SELECT o.*, k.kitap_adi, u.ad_soyad
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        JOIN kullanicilar u ON o.kullanici_id = u.id
        WHERE o.id = ? AND o.durum = 'oduncte'
    """, (odunc_id,)).fetchone()

    if not odunc:
        baglanti.close()
        flash("İade edilecek aktif ödünç kaydı bulunamadı!", "warning")
        return redirect(url_for("admin_paneli"))

    bugun = date.today().isoformat()
    baglanti.execute("""
        UPDATE oduncler
        SET durum = 'teslim_edildi', iade_tarihi = ?
        WHERE id = ?
    """, (bugun, odunc_id))

    baglanti.execute("""
        UPDATE kitaplar
        SET mevcut_adet = MIN(toplam_adet, mevcut_adet + 1)
        WHERE id = ?
    """, (odunc["kitap_id"],))

    baglanti.commit()
    baglanti.close()

    flash(f"{odunc['ad_soyad']} adlı kullanıcının '{odunc['kitap_adi']}' kitabı kütüphaneye teslim alındı.", "success")
    return redirect(url_for("admin_paneli"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
