from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from functools import wraps
from werkzeug.utils import secure_filename
from config import SIFRE, SECRET_KEY, UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS
from PIL import Image
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/webalet/stoktakip/stok.db'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # Beni hatırla için 30 günlük session

db = SQLAlchemy(app)

# Login gerektiren sayfalar için decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Upload klasörünü oluştur
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class MetalStok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kalinlik = db.Column(db.Float, nullable=False)
    tur = db.Column(db.String(50), nullable=False)
    adet = db.Column(db.Integer, nullable=False)
    uzunluk = db.Column(db.Integer)
    genislik = db.Column(db.Integer)
    tarih = db.Column(db.DateTime, default=lambda: datetime.now() + timedelta(hours=3))

class FireSac(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kalinlik = db.Column(db.Float, nullable=False)
    tur = db.Column(db.String(50), nullable=False)
    uzunluk = db.Column(db.Integer)
    genislik = db.Column(db.Integer)
    notlar = db.Column(db.Text)
    foto = db.Column(db.String(255))
    tarih = db.Column(db.DateTime, default=lambda: datetime.now() + timedelta(hours=3))
    kullaniliyor = db.Column(db.Boolean, default=False)

class MetalTuru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False, unique=True)
    tarih = db.Column(db.DateTime, default=lambda: datetime.now() + timedelta(hours=3))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Veritabanını oluştur
with app.app_context():
    db.create_all()
    varsayilan_turler = ['DKP Sac', 'Galvaniz Sac', 'Paslanmaz Sac', 'Siyah Sac']
    for tur_adi in varsayilan_turler:
        if not MetalTuru.query.filter_by(ad=tur_adi).first():
            db.session.add(MetalTuru(ad=tur_adi))
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Hata: {str(e)}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sifre = request.form.get('sifre')
        remember = request.form.get('remember') == 'on'
        
        if sifre == SIFRE:
            session.permanent = remember  # Beni hatırla seçeneği
            session['logged_in'] = True
            return redirect(url_for('ana_sayfa'))
        else:
            flash('Hatalı şifre!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def ana_sayfa():
    stoklar = MetalStok.query.all()
    turler = MetalTuru.query.order_by(MetalTuru.ad).all()
    return render_template('index.html', stoklar=stoklar, turler=turler)

@app.route('/fire-sac')
@login_required
def fire_sac():
    fire_saclar = FireSac.query.order_by(FireSac.tarih.desc()).all()
    turler = MetalTuru.query.all()
    
    # Fire sacları kalınlıklarına göre grupla
    grouped_fire_saclar = {}
    for fire in fire_saclar:
        kalinlik = fire.kalinlik
        if kalinlik not in grouped_fire_saclar:
            grouped_fire_saclar[kalinlik] = []
        grouped_fire_saclar[kalinlik].append(fire)
    
    # Kalınlıkları sırala
    sorted_kalinliklar = sorted(grouped_fire_saclar.keys())
    
    return render_template('fire_sac.html', 
                         fire_saclar=fire_saclar,
                         grouped_fire_saclar=grouped_fire_saclar,
                         sorted_kalinliklar=sorted_kalinliklar,
                         turler=turler)

# Resim sıkıştırma fonksiyonu
def compress_image(image_file, max_size=(800, 800), quality=85):
    try:
        # Resmi aç
        img = Image.open(image_file)
        
        # EXIF bilgisine göre resmi döndür
        try:
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif is not None:
                    orientation = exif.get(274)  # 274: Orientation tag
                    if orientation == 3:
                        img = img.rotate(180, expand=True)
                    elif orientation == 6:
                        img = img.rotate(270, expand=True)
                    elif orientation == 8:
                        img = img.rotate(90, expand=True)
        except:
            pass  # EXIF okuma hatalarını yoksay
        
        # Resmi boyutlandır
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Resmi JPEG formatına dönüştür ve sıkıştır
        output = io.BytesIO()
        
        # PNG dosyalarını JPEG'e dönüştür
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        print(f"Resim sıkıştırma hatası: {str(e)}")
        return None

# Genel hata yönetimi için yardımcı fonksiyon
def handle_error(e, default_message="Bir hata oluştu"):
    db.session.rollback()
    error_message = str(e) if str(e) else default_message
    return jsonify({
        'success': False,
        'error': error_message
    }), 500

# Veritabanı işlemleri için yardımcı fonksiyon
def safe_commit():
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Veritabanı hatası: {str(e)}")
        return False

@app.route('/fire-sac/ekle', methods=['POST'])
@login_required
def fire_sac_ekle():
    try:
        kalinlik = float(request.form['kalinlik'])
        tur = request.form['tur']
        uzunluk = request.form.get('uzunluk', type=int)
        genislik = request.form.get('genislik', type=int)
        notlar = request.form.get('notlar', '').strip()
        
        foto = request.files.get('foto')
        foto_adi = None
        
        if foto and foto.filename:
            if not allowed_file(foto.filename):
                flash('Geçersiz dosya türü!', 'error')
                return redirect(url_for('fire_sac'))
            
            compressed_image = compress_image(foto)
            if compressed_image is None:
                flash('Resim sıkıştırma hatası!', 'error')
                return redirect(url_for('fire_sac'))
            
            foto_adi = secure_filename(foto.filename)
            foto_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_adi}"
            foto_adi = foto_adi.rsplit('.', 1)[0] + '.jpg'
            
            with open(os.path.join(app.config['UPLOAD_FOLDER'], foto_adi), 'wb') as f:
                f.write(compressed_image.getvalue())
        
        yeni_fire = FireSac(
            kalinlik=kalinlik,
            tur=tur,
            uzunluk=uzunluk,
            genislik=genislik,
            notlar=notlar,
            foto=foto_adi
        )
        
        db.session.add(yeni_fire)
        if not safe_commit():
            if foto_adi:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], foto_adi))
                except:
                    pass
            flash('Fire sac eklenirken bir hata oluştu!', 'error')
            return redirect(url_for('fire_sac'))
            
        flash('Fire sac başarıyla eklendi!', 'success')
        return redirect(url_for('fire_sac'))
        
    except Exception as e:
        return handle_error(e, "Fire sac eklenirken bir hata oluştu")

@app.route('/fire-sac/sil/<int:id>', methods=['GET', 'POST'])
@login_required
def fire_sac_sil(id):
    try:
        fire = FireSac.query.get_or_404(id)
        
        # Fotoğraf varsa sil
        if fire.foto:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], fire.foto))
            except:
                pass  # Dosya silinirken hata olursa devam et
        
        db.session.delete(fire)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Fire sac başarıyla silindi!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/ekle', methods=['POST'])
@login_required
def stok_ekle():
    try:
        kalinlik = float(request.form['kalinlik'])
        tur = request.form['tur']
        adet = int(request.form['adet'])
        uzunluk = int(request.form['uzunluk'])
        genislik = int(request.form['genislik'])
        
        # Aynı kalınlık, tür ve boyutta stok var mı kontrol et
        mevcut_stok = MetalStok.query.filter_by(
            kalinlik=kalinlik,
            tur=tur,
            uzunluk=uzunluk,
            genislik=genislik
        ).first()
        
        if mevcut_stok:
            # Mevcut stok varsa adeti güncelle
            mevcut_stok.adet += adet
            mevcut_stok.tarih = datetime.utcnow()
        else:
            # Yeni stok ekle
            yeni_stok = MetalStok(
                kalinlik=kalinlik, 
                tur=tur, 
                adet=adet,
                uzunluk=uzunluk,
                genislik=genislik
            )
            db.session.add(yeni_stok)
        
        db.session.commit()
        return redirect(url_for('ana_sayfa'))
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/azalt', methods=['POST'])
@login_required
def stok_azalt():
    try:
        id = int(request.form['id'])
        miktar = int(request.form['miktar'])
        
        stok = MetalStok.query.get_or_404(id)
        
        if miktar <= 0:
            return jsonify({'success': False, 'error': 'Geçersiz miktar'}), 400
        
        if miktar > stok.adet:
            return jsonify({'success': False, 'error': 'Stokta yeterli ürün yok'}), 400
        
        stok.adet -= miktar
        stok.tarih = datetime.utcnow()  # Son güncelleme tarihini güncelle
        
        if stok.adet == 0:
            db.session.delete(stok)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/sil/<int:id>')
@login_required
def sil(id):
    try:
        stok = MetalStok.query.get_or_404(id)
        db.session.delete(stok)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Stok başarıyla silindi!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/fire-sac/durum-degistir/<int:id>')
@login_required
def fire_sac_durum_degistir(id):
    fire = FireSac.query.get_or_404(id)
    fire.kullaniliyor = not fire.kullaniliyor
    db.session.commit()
    
    return jsonify({
        'success': True,
        'kullaniliyor': fire.kullaniliyor
    })

@app.route('/turler', methods=['GET'])
@login_required
def get_turler():
    turler = MetalTuru.query.all()
    return jsonify([{'id': tur.id, 'ad': tur.ad} for tur in turler])

@app.route('/tur/ekle', methods=['POST'])
@login_required
def tur_ekle():
    try:
        tur_adi = request.form['tur_adi'].strip()
        if not tur_adi:
            return jsonify({'success': False, 'error': 'Tür adı boş olamaz!'})

        # Aynı isimde tür var mı kontrol et
        mevcut_tur = MetalTuru.query.filter_by(ad=tur_adi).first()
        if mevcut_tur:
            return jsonify({'success': False, 'error': 'Bu tür zaten mevcut!'})
        
        yeni_tur = MetalTuru(ad=tur_adi)
        db.session.add(yeni_tur)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Tür başarıyla eklendi!',
            'tur': {'id': yeni_tur.id, 'ad': yeni_tur.ad}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/tur/sil/<int:id>', methods=['DELETE'])
@login_required
def tur_sil(id):
    try:
        tur = MetalTuru.query.get_or_404(id)
        
        # Bu türde stok var mı kontrol et
        stok_sayisi = MetalStok.query.filter_by(tur=tur.ad).count()
        if stok_sayisi > 0:
            return jsonify({
                'success': False, 
                'error': f'Bu türde {stok_sayisi} adet stok bulunuyor. Önce stokları silmelisiniz.'
            })
        
        db.session.delete(tur)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Tür başarıyla silindi!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/istatistikler')
def istatistikler():
    try:
        stoklar = MetalStok.query.all()
        toplam_plaka = sum(stok.adet for stok in stoklar)
        return jsonify({
            'toplam_cesit': len(stoklar),
            'toplam_plaka': toplam_plaka,
            'kritik_stok': len([stok for stok in stoklar if stok.adet < 5])
        })
    except Exception as e:
        print(f"İstatistikler hesaplanırken hata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stok-guncelle', methods=['POST'])
@login_required
def stok_guncelle():
    try:
        stok_id = request.form.get('id', type=int)
        yeni_adet = request.form.get('miktar', type=int)
        
        if not stok_id or yeni_adet is None:
            return jsonify({
                'success': False,
                'error': 'Geçersiz parametreler'
            }), 400
            
        stok = MetalStok.query.get_or_404(stok_id)
        stok.adet = yeni_adet
        stok.tarih = datetime.now() + timedelta(hours=3)  # Türkiye saati
        
        if safe_commit():
            return jsonify({
                'success': True,
                'message': 'Stok başarıyla güncellendi'
            })
        return handle_error(None, "Stok güncellenirken bir hata oluştu")
        
    except Exception as e:
        return handle_error(e)

@app.route('/fire-sac/durum/<int:id>', methods=['POST'])
@login_required
def fire_sac_durum(id):
    try:
        fire = FireSac.query.get_or_404(id)
        fire.kullaniliyor = not fire.kullaniliyor
        db.session.commit()
        return jsonify({
            'success': True,
            'kullaniliyor': fire.kullaniliyor
        })
    except Exception as e:
        return handle_error(e, "Durum güncellenirken bir hata oluştu")

if __name__ == '__main__':
    app.run(debug=True)