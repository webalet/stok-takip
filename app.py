from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from functools import wraps
from werkzeug.utils import secure_filename
from config import SIFRE, SECRET_KEY, UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stok.db'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

class FireSac(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kalinlik = db.Column(db.Float, nullable=False)
    tur = db.Column(db.String(50), nullable=False)
    uzunluk = db.Column(db.Integer)
    genislik = db.Column(db.Integer)
    notlar = db.Column(db.Text)
    foto = db.Column(db.String(255))
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    kullaniliyor = db.Column(db.Boolean, default=False)

class MetalTuru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False, unique=True)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

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
        if sifre == SIFRE:
            session['logged_in'] = True
            return redirect(url_for('ana_sayfa'))
        else:
            flash('Hatalı şifre!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
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
                
            foto_adi = secure_filename(foto.filename)
            foto_adi = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto_adi}"
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_adi))
        
        yeni_fire = FireSac(
            kalinlik=kalinlik,
            tur=tur,
            uzunluk=uzunluk,
            genislik=genislik,
            notlar=notlar,
            foto=foto_adi
        )
        
        db.session.add(yeni_fire)
        db.session.commit()
        
        return redirect(url_for('fire_sac'))
        
    except Exception as e:
        flash(f'Fire sac eklenirken bir hata oluştu: {str(e)}', 'error')
        return redirect(url_for('fire_sac'))

@app.route('/fire-sac/sil/<int:id>')
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
    kalinlik = float(request.form['kalinlik'])
    tur = request.form['tur']
    adet = int(request.form['adet'])
    
    # Aynı kalınlık ve türde stok var mı kontrol et
    mevcut_stok = MetalStok.query.filter_by(
        kalinlik=kalinlik,
        tur=tur
    ).first()
    
    if mevcut_stok:
        # Mevcut stok varsa adeti güncelle
        mevcut_stok.adet += adet
        mevcut_stok.tarih = datetime.utcnow()  # Son güncelleme tarihini güncelle
    else:
        # Yeni stok ekle
        yeni_stok = MetalStok(kalinlik=kalinlik, tur=tur, adet=adet)
        db.session.add(yeni_stok)
    
    db.session.commit()
    return redirect(url_for('ana_sayfa'))

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
        id = int(request.form['id'])
        yeni_miktar = int(request.form['miktar'])
        
        if yeni_miktar < 0:
            return jsonify({'success': False, 'error': 'Stok miktarı 0 veya daha büyük olmalıdır'}), 400
        
        stok = MetalStok.query.get_or_404(id)
        
        if yeni_miktar == 0:
            # Stok sıfırsa kaydı sil
            db.session.delete(stok)
        else:
            # Stok miktarını güncelle
            stok.adet = yeni_miktar
            stok.tarih = datetime.utcnow()  # Son güncelleme tarihini güncelle
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 