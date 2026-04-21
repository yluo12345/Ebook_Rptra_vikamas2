import os
import sqlite3
from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)


# Folder penyimpanan file ebook
UPLOAD_FOLDER = 'ebooks'
IMAGE_FOLDER = 'static/images'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

# Pastikan folder ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)


# =========================
# KONEKSI DATABASE
# =========================
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# HALAMAN UTAMA
# =========================
@app.route('/')
def index():
    search = request.args.get('search', '')

    conn = get_db_connection()

    if search:
        ebooks = conn.execute(
            "SELECT * FROM ebooks WHERE title LIKE ?",
            ('%' + search + '%',)
        ).fetchall()
    else:
        ebooks = conn.execute(
            "SELECT * FROM ebooks"
        ).fetchall()

    conn.close()

    return render_template(
        'index.html',
        ebooks=ebooks,
        search=search
    )


# =========================
# UPLOAD EBOOK
# =========================
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']
        image = request.files['image']

        # Validasi sederhana
        if not file or not image:
            return "File ebook dan gambar wajib diupload"

        # Simpan file ebook
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Simpan gambar cover
        image_path = os.path.join(app.config['IMAGE_FOLDER'], image.filename)
        image.save(image_path)

        # Simpan ke database
        conn = get_db_connection()
        conn.execute(
            '''
            INSERT INTO ebooks (title, filename, image)
            VALUES (?, ?, ?)
            ''',
            (title, file.filename, image.filename)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('upload.html')


# =========================
# DOWNLOAD EBOOK
# =========================
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

# =========================
# HALAMAN EDIT EBOOK
# =========================
@app.route('/edit')
def edit():
    conn = get_db_connection()
    ebooks = conn.execute("SELECT * FROM ebooks").fetchall()
    conn.close()

    return render_template("edit.html", ebooks=ebooks)


# =========================
# UPDATE EBOOK
# =========================
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    title = request.form['title']
    image = request.files['image']

    conn = get_db_connection()

    # Jika upload gambar baru
    if image and image.filename != "":
        image.save(os.path.join(app.config['IMAGE_FOLDER'], image.filename))

        conn.execute("""
            UPDATE ebooks
            SET title = ?, image = ?
            WHERE id = ?
        """, (title, image.filename, id))

    else:
        conn.execute("""
            UPDATE ebooks
            SET title = ?
            WHERE id = ?
        """, (title, id))

    conn.commit()
    conn.close()

    return redirect('/edit')


# =========================
# HAPUS EBOOK
# =========================
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()

    # Ambil nama file sebelum dihapus
    ebook = conn.execute(
        "SELECT filename, image FROM ebooks WHERE id = ?",
        (id,)
    ).fetchone()

    if ebook:
        # Hapus file ebook
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], ebook['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)

        # Hapus gambar cover
        if ebook['image']:
            image_path = os.path.join(app.config['IMAGE_FOLDER'], ebook['image'])
            if os.path.exists(image_path):
                os.remove(image_path)

        # Hapus dari database
        conn.execute(
            "DELETE FROM ebooks WHERE id = ?",
            (id,)
        )
        conn.commit()

    conn.close()

    return redirect('/edit')


# =========================
# JALANKAN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)

