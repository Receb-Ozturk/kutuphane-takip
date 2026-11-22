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
    if not termin_tarihi_str:
        return {"gun": 0, "durum": "beklemede", "metin": "Onay Bekliyor", "renk": "info"}
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

    # 1. Kullanıcının onay bekleyen ödünç talepleri
    bekleyen_talepler = baglanti.execute("""
        SELECT o.id as odunc_id, o.talep_tarihi, o.durum,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori, k.sayfa_sayisi
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.kullanici_id = ? AND o.durum = 'beklemede'
        ORDER BY o.id DESC
    """, (kullanici_id,)).fetchall()

    # 2. Kullanıcının şu an elinde olan aktif ödünç kitapları (Admin onaylamış olanlar)
    aktif_oduncler = baglanti.execute("""
        SELECT o.id as odunc_id, o.talep_tarihi, o.odunc_tarihi, o.termin_tarihi, o.durum,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori, k.sayfa_sayisi
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.kullanici_id = ? AND o.durum = 'oduncte'
        ORDER BY o.termin_tarihi ASC
    """, (kullanici_id,)).fetchall()

    # 3. Kullanıcının geçmiş hareketleri (Teslim edilenler ve reddedilenler)
    gecmis_oduncler = baglanti.execute("""
        SELECT o.id as odunc_id, o.talep_tarihi, o.odunc_tarihi, o.termin_tarihi, o.iade_tarihi, o.durum,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.kullanici_id = ? AND o.durum IN ('teslim_edildi', 'reddedildi')
        ORDER BY o.id DESC
    """, (kullanici_id,)).fetchall()

    # 4. Kütüphane Kitap Envanteri & Arama / Filtreleme
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

    # Kullanıcının şu an bekleyen talep ve elindeki kitap ID listeleri
    talep_edilen_kitap_idleri = [t["kitap_id"] for t in bekleyen_talepler]
    elindeki_kitap_idleri = [o["kitap_id"] for o in aktif_oduncler]

    baglanti.close()

    return render_template(
        "kullanici.html",
        bekleyen_talepler=bekleyen_talepler,
        aktif_oduncler=aktif_oduncler,
        gecmis_oduncler=gecmis_oduncler,
        envanter_kitaplar=envanter_kitaplar,
        kategoriler=kategoriler,
        talep_edilen_kitap_idleri=talep_edilen_kitap_idleri,
        elindeki_kitap_idleri=elindeki_kitap_idleri,
        arama_kelimesi=arama_kelimesi,
        secili_kategori=secili_kategori
    )

@app.route("/kitap-talep-et/<int:kitap_id>", methods=["POST"])
@login_required
def kitap_talep_et(kitap_id):
    kullanici_id = session["kullanici_id"]
    baglanti = veritabani_baglantisi()

    # Kitap var mı?
    kitap = baglanti.execute("SELECT * FROM kitaplar WHERE id = ?", (kitap_id,)).fetchone()
    if not kitap:
        baglanti.close()
        flash("Seçilen kitap bulunamadı!", "danger")
        return redirect(url_for("kullanici_paneli"))

    if kitap["mevcut_adet"] <= 0:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' şu an kütüphanede kalmamıştır.", "warning")
        return redirect(url_for("kullanici_paneli"))

    # Kullanıcının bu kitapta zaten bekleyen talebi var mı?
    bekleyen_var_mi = baglanti.execute("""
        SELECT id FROM oduncler
        WHERE kullanici_id = ? AND kitap_id = ? AND durum = 'beklemede'
    """, (kullanici_id, kitap_id)).fetchone()

    if bekleyen_var_mi:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' için zaten onay bekleyen bir talebiniz bulunmaktadır.", "warning")
        return redirect(url_for("kullanici_paneli"))

    # Kullanıcının elinde zaten bu kitap var mı?
    elinde_var_mi = baglanti.execute("""
        SELECT id FROM oduncler
        WHERE kullanici_id = ? AND kitap_id = ? AND durum = 'oduncte'
    """, (kullanici_id, kitap_id)).fetchone()

    if elinde_var_mi:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' zaten şu an sizin üzerinizde kayıtlı!", "warning")
        return redirect(url_for("kullanici_paneli"))

    # Kullanıcının bekleyen + aktif ödünç toplam sınırı (en fazla 5)
    toplam_aktif = baglanti.execute("""
        SELECT COUNT(*) as sayi FROM oduncler
        WHERE kullanici_id = ? AND durum IN ('oduncte', 'beklemede')
    """, (kullanici_id,)).fetchone()["sayi"]

    if toplam_aktif >= 5:
        baglanti.close()
        flash("Aynı anda en fazla 5 aktif kitap / talep hakkınız bulunmaktadır.", "warning")
        return redirect(url_for("kullanici_paneli"))

    bugun = date.today().isoformat()

    # Talep oluştur (durum = 'beklemede')
    baglanti.execute("""
        INSERT INTO oduncler (kullanici_id, kitap_id, talep_tarihi, odunc_tarihi, termin_tarihi, durum)
        VALUES (?, ?, ?, '', '', 'beklemede')
    """, (kullanici_id, kitap_id, bugun))

    baglanti.commit()
    baglanti.close()

    flash(f"'{kitap['kitap_adi']}' için ödünç alma talebiniz kütüphane yöneticisine iletildi. Talebiniz onaylandığında kitabınızı teslim alabilirsiniz.", "success")
    return redirect(url_for("kullanici_paneli"))

# Geriye uyumluluk için eski route
@app.route("/kitap-odunc-al/<int:kitap_id>", methods=["POST"])
@login_required
def kitap_odunc_al_eski(kitap_id):
    return kitap_talep_et(kitap_id)

@app.route("/talep-iptal-et/<int:odunc_id>", methods=["POST"])
@login_required
def talep_iptal_et(odunc_id):
    kullanici_id = session["kullanici_id"]
    baglanti = veritabani_baglantisi()

    talep = baglanti.execute("""
        SELECT o.*, k.kitap_adi FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.id = ? AND o.kullanici_id = ? AND o.durum = 'beklemede'
    """, (odunc_id, kullanici_id)).fetchone()

    if not talep:
        baglanti.close()
        flash("İptal edilecek bekleyen talep bulunamadı!", "danger")
        return redirect(url_for("kullanici_paneli"))

    baglanti.execute("DELETE FROM oduncler WHERE id = ?", (odunc_id,))
    baglanti.commit()
    baglanti.close()

    flash(f"'{talep['kitap_adi']}' için ödünç talebiniz başarıyla iptal edildi.", "info")
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

    bekleyen_talep_sayisi = baglanti.execute(
        "SELECT COUNT(*) as sayi FROM oduncler WHERE durum = 'beklemede'"
    ).fetchone()["sayi"]

    # 1. Bekleyen Ödünç Talepleri Listesi (Admin Onayı Gerekenler)
    bekleyen_talepler = baglanti.execute("""
        SELECT o.id as talep_id, o.talep_tarihi,
               u.id as kullanici_id, u.ad_soyad, u.kullanici_adi,
               k.id as kitap_id, k.kitap_adi, k.yazar, k.kategori, k.mevcut_adet, k.toplam_adet
        FROM oduncler o
        JOIN kullanicilar u ON o.kullanici_id = u.id
        JOIN kitaplar k ON o.kitap_id = k.id
        WHERE o.durum = 'beklemede'
        ORDER BY o.id ASC
    """).fetchall()

    # 2. Kullanıcılar Listesi & Aldıkları Kitap Sayısı (Kaç kullanıcı var?)
    kullanicilar = baglanti.execute("""
        SELECT u.id, u.kullanici_adi, u.ad_soyad, u.rol, u.kayit_tarihi,
               (SELECT COUNT(*) FROM oduncler WHERE kullanici_id = u.id AND durum = 'oduncte') as aktif_kitap_sayisi,
               (SELECT COUNT(*) FROM oduncler WHERE kullanici_id = u.id AND durum = 'beklemede') as bekleyen_talep_sayisi,
               (SELECT COUNT(*) FROM oduncler WHERE kullanici_id = u.id) as toplam_odunc_sayisi
        FROM kullanicilar u
        ORDER BY u.rol ASC, u.ad_soyad ASC
    """).fetchall()

    # 3. Kullanıcı Hangi Kitapları Almış? (Ödünç Hareketleri)
    filtre_kullanici = request.args.get("kullanici_id", "").strip()
    filtre_durum = request.args.get("durum", "").strip()

    odunc_sorgu = """
        SELECT o.id as odunc_id, o.talep_tarihi, o.odunc_tarihi, o.termin_tarihi, o.iade_tarihi, o.durum,
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

    # 4. Kitap Envanteri
    envanter = baglanti.execute("""
        SELECT k.*,
               (k.toplam_adet - k.mevcut_adet) as oduncteki_adet
        FROM kitaplar k
        ORDER BY k.id DESC
    """).fetchall()

    # Admin'in doğrudan kitap ödünç verebilmesi için stokta olan kitaplar ve üyeler
    stoktaki_kitaplar = baglanti.execute("SELECT * FROM kitaplar WHERE mevcut_adet > 0 ORDER BY kitap_adi ASC").fetchall()
    uyeler = baglanti.execute("SELECT * FROM kullanicilar WHERE rol != 'admin' ORDER BY ad_soyad ASC").fetchall()

    baglanti.close()

    return render_template(
        "admin.html",
        kullanici_sayisi=kullanici_sayisi,
        toplam_kitap_cesidi=toplam_kitap_cesidi,
        toplam_kitap_stok=toplam_kitap_stok,
        aktif_odunc_sayisi=aktif_odunc_sayisi,
        geciken_odunc_sayisi=geciken_odunc_sayisi,
        bekleyen_talep_sayisi=bekleyen_talep_sayisi,
        bekleyen_talepler=bekleyen_talepler,
        kullanicilar=kullanicilar,
        odunc_hareketleri=odunc_hareketleri,
        envanter=envanter,
        stoktaki_kitaplar=stoktaki_kitaplar,
        uyeler=uyeler,
        filtre_kullanici=filtre_kullanici,
        filtre_durum=filtre_durum
    )


# --- ADMİN TALEPLERİ VE ÖDÜNÇ YÖNETİMİ ---

@app.route("/admin/talep-onayla/<int:odunc_id>", methods=["POST"])
@admin_required
def admin_talep_onayla(odunc_id):
    baglanti = veritabani_baglantisi()
    talep = baglanti.execute("""
        SELECT o.*, k.kitap_adi, k.mevcut_adet, u.ad_soyad
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        JOIN kullanicilar u ON o.kullanici_id = u.id
        WHERE o.id = ? AND o.durum = 'beklemede'
    """, (odunc_id,)).fetchone()

    if not talep:
        baglanti.close()
        flash("Onaylanacak bekleyen talep bulunamadı!", "warning")
        return redirect(url_for("admin_paneli"))

    if talep["mevcut_adet"] <= 0:
        baglanti.close()
        flash(f"'{talep['kitap_adi']}' adlı kitabın raftaki stoku tükendiği için talep onaylanamıyor!", "danger")
        return redirect(url_for("admin_paneli"))

    bugun = date.today()
    termin = bugun + timedelta(days=14)

    # Durumu 'oduncte' yap ve termin süresini başlat
    baglanti.execute("""
        UPDATE oduncler
        SET durum = 'oduncte', odunc_tarihi = ?, termin_tarihi = ?
        WHERE id = ?
    """, (bugun.isoformat(), termin.isoformat(), odunc_id))

    # Kitap stokunu 1 azalt
    baglanti.execute("""
        UPDATE kitaplar SET mevcut_adet = mevcut_adet - 1 WHERE id = ?
    """, (talep["kitap_id"],))

    baglanti.commit()
    baglanti.close()

    flash(f"{talep['ad_soyad']} adlı kullanıcının '{talep['kitap_adi']}' kitabı ödünç talebi onaylandı. Son teslim (termin): {termin.strftime('%d.%m.%Y')}", "success")
    return redirect(url_for("admin_paneli"))

@app.route("/admin/talep-reddet/<int:odunc_id>", methods=["POST"])
@admin_required
def admin_talep_reddet(odunc_id):
    baglanti = veritabani_baglantisi()
    talep = baglanti.execute("""
        SELECT o.*, k.kitap_adi, u.ad_soyad
        FROM oduncler o
        JOIN kitaplar k ON o.kitap_id = k.id
        JOIN kullanicilar u ON o.kullanici_id = u.id
        WHERE o.id = ? AND o.durum = 'beklemede'
    """, (odunc_id,)).fetchone()

    if not talep:
        baglanti.close()
        flash("Reddedilecek bekleyen talep bulunamadı!", "warning")
        return redirect(url_for("admin_paneli"))

    baglanti.execute("""
        UPDATE oduncler SET durum = 'reddedildi' WHERE id = ?
    """, (odunc_id,))

    baglanti.commit()
    baglanti.close()

    flash(f"{talep['ad_soyad']} adlı kullanıcının '{talep['kitap_adi']}' kitabı ödünç talebi reddedildi.", "info")
    return redirect(url_for("admin_paneli"))

@app.route("/admin/kitap-odunc-ver", methods=["POST"])
@admin_required
def admin_kitap_odunc_ver():
    """Adminin kendi istediği kullanıcıya doğrudan kitap ödünç vermesi."""
    kullanici_id = request.form.get("kullanici_id", "").strip()
    kitap_id = request.form.get("kitap_id", "").strip()
    termin_gun = request.form.get("termin_gun", "14").strip()

    if not kullanici_id or not kitap_id:
        flash("Lütfen kullanıcı ve kitap seçimini eksiksiz yapınız!", "warning")
        return redirect(url_for("admin_paneli"))

    try:
        kullanici_id = int(kullanici_id)
        kitap_id = int(kitap_id)
        termin_gun = max(1, int(termin_gun) if termin_gun else 14)
    except ValueError:
        flash("Geçersiz değer girildi!", "danger")
        return redirect(url_for("admin_paneli"))

    baglanti = veritabani_baglantisi()
    kitap = baglanti.execute("SELECT * FROM kitaplar WHERE id = ?", (kitap_id,)).fetchone()
    kullanici = baglanti.execute("SELECT * FROM kullanicilar WHERE id = ?", (kullanici_id,)).fetchone()

    if not kitap or not kullanici:
        baglanti.close()
        flash("Seçilen kullanıcı veya kitap bulunamadı!", "danger")
        return redirect(url_for("admin_paneli"))

    if kitap["mevcut_adet"] <= 0:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' adlı kitabın kütüphanede mevcut stoku yok!", "danger")
        return redirect(url_for("admin_paneli"))

    # Kullanıcının elinde zaten bu kitap var mı?
    zaten_var = baglanti.execute("""
        SELECT id FROM oduncler
        WHERE kullanici_id = ? AND kitap_id = ? AND durum = 'oduncte'
    """, (kullanici_id, kitap_id)).fetchone()

    if zaten_var:
        baglanti.close()
        flash(f"'{kitap['kitap_adi']}' zaten şu an {kullanici['ad_soyad']} adlı kullanıcının üzerinde ödünçte!", "warning")
        return redirect(url_for("admin_paneli"))

    bugun = date.today()
    termin = bugun + timedelta(days=termin_gun)

    # Varsa bekleyen bir talep, onu doğrudan 'oduncte'ye çevirelim
    bekleyen = baglanti.execute("""
        SELECT id FROM oduncler
        WHERE kullanici_id = ? AND kitap_id = ? AND durum = 'beklemede'
    """, (kullanici_id, kitap_id)).fetchone()

    if bekleyen:
        baglanti.execute("""
            UPDATE oduncler
            SET durum = 'oduncte', odunc_tarihi = ?, termin_tarihi = ?
            WHERE id = ?
        """, (bugun.isoformat(), termin.isoformat(), bekleyen["id"]))
    else:
        baglanti.execute("""
            INSERT INTO oduncler (kullanici_id, kitap_id, talep_tarihi, odunc_tarihi, termin_tarihi, durum)
            VALUES (?, ?, ?, ?, ?, 'oduncte')
        """, (kullanici_id, kitap_id, bugun.isoformat(), bugun.isoformat(), termin.isoformat()))

    # Stok düş
    baglanti.execute("UPDATE kitaplar SET mevcut_adet = mevcut_adet - 1 WHERE id = ?", (kitap_id,))

    baglanti.commit()
    baglanti.close()

    flash(f"'{kitap['kitap_adi']}' adlı kitap başarıyla {kullanici['ad_soyad']} adlı kullanıcıya ödünç verildi. Son teslim tarihi: {termin.strftime('%d.%m.%Y')}", "success")
    return redirect(url_for("admin_paneli"))


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
