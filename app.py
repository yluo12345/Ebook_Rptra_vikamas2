import os
import sqlite3
from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)

conn = sqlite3.connect('database.db')


UPLOAD_FOLDER = 'ebooks'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# koneksi database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# halaman utama
@app.route('/')
def index():
    conn = get_db_connection()
    ebooks = conn.execute('SELECT * FROM ebooks').fetchall()
    conn.close()
    return render_template('index.html', ebooks=ebooks)

# upload ebook
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['file']

        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        conn.execute('INSERT INTO ebooks (title, filename) VALUES (?, ?)', (title, filename))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('upload.html')

# download ebook
@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
