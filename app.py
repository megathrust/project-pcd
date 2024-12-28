# Import Module yang digunakan
import os
from flask import Flask, render_template, request, send_file
from PIL import Image
import cv2
import numpy as np
from rembg import remove
from werkzeug.utils import secure_filename

# Import module flask
app = Flask(__name__)
# Mengambil Semua Jenis File Yang Sifatnya Di Upload
app.config['UPLOAD_FOLDER'] = 'uploads'
# Membatasi Besarnya File Yaitu 16Mb
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Memastikan folder untuk upload Ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Fungsi Untuk Meningkatkan citra gambar dengan tetap mempertahankan detail
def enhance_image(image_path):
    try:
        # Membaca Gambar Yang Di Upload
        img = cv2.imread(image_path)
        
        # Berikan Peringatan Jika gagal membaca gambar
        if img is None:
            raise ValueError("Gagal membaca gambar")
        
        # Perbaikan kontras dengan CLAHE
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_eq = clahe.apply(l)
        
        lab_enhanced = cv2.merge((l_eq, a, b))
        enhanced_img = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        # Reduksi noise dengan bilateral filter
        enhanced_img = cv2.bilateralFilter(enhanced_img, 9, 75, 75)
        
        return enhanced_img
    
    except Exception as e:
        print(f"Error dalam enhance_image: {e}")
        # mengembalikan gambar asli jika gagal
        return cv2.imread(image_path)

# Fungsi untuk melakukan kompres image
def compress_image(image_path, quality=80):
    # Membuka file gambar yang di upload
    img = Image.open(image_path)
    # Melakukan kompres file gambar
    compressed_path = os.path.join(app.config['UPLOAD_FOLDER'], 'compressed_' + os.path.basename(image_path))
    # Save gambar yang telah dikompres
    img.save(compressed_path, optimize=True, quality=quality)
    # Mengembalikan file gambar yang telah di kompres
    return compressed_path

# Rute untuk memanggil tampilan depan (index.html)
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# Rute untuk memanggil menghapus latar belakang dengan metode POST
@app.route('/remove_background', methods=['POST'])
# Fungsi untuk menghapus latar belakang
def remove_background():
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    
    # save gambar yang telah di upload
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Hapus background
    input_image = Image.open(filepath)
    output_image = remove(input_image)
    
    # Simpan sebagai PNG untuk mendukung transparansi
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'nobg_' + os.path.splitext(filename)[0] + '.png')
    output_image.save(output_path, format='PNG')
    
    # mengembalikan path gambar yang telah dihapus latar belakang
    return send_file(output_path, mimetype='image/png')

# Rute untuk memanggil peningkatan citra gambar dengan metode POST
@app.route('/enhance_image', methods=['POST'])
# Fungsi untuk memperbaiki citra gambar
def enhance_photo():
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    
    # Simpan gambar yang telah di upload
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        # Proses enhance
        enhanced_img = enhance_image(filepath)
        # Simpan gambar hasil
        enhanced_path = os.path.join(app.config['UPLOAD_FOLDER'], 'enhanced_' + filename)
        cv2.imwrite(enhanced_path, enhanced_img)
        # Kembalikan path gambar hasil enhance
        return send_file(enhanced_path, mimetype='image/png')
    except Exception as e:
        # Jika terjadi kesalahan maka akan muncul peringatan dengan status 500
        print(f"Error dalam proses enhance: {e}")
        return f'Gagal meningkatkan kualitas gambar: {str(e)}', 500

# rute untuk memanggil fungsi kompress gambar dengan metode POST
@app.route('/compress_image', methods=['POST'])
# Fungsi untuk mengompresi gambar
def compress_photo():
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    if 'file' not in request.files:
        return 'Tidak ada file yang diunggah', 400
    # Jika file tidak ada maka akan muncul peringatan dengan status 400
    file = request.files['file']
    if file.filename == '':
        return 'Tidak ada file yang dipilih', 400
    # Simpan gambar yang telah di upload
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Kompres foto
    compressed_path = compress_image(filepath)
    # Kembalikan path gambar hasil kompresi
    return send_file(compressed_path, mimetype='image/png')

if __name__ == '__main__':
    # Jalankan aplikasi dengan mode debug
    app.run(debug=True)