import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# =========================
# FOLDER PENYIMPANAN
# =========================
UPLOAD_FOLDER = "static/ebooks"
IMAGE_FOLDER = "static/images"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["IMAGE_FOLDER"] = IMAGE_FOLDER

# Pastikan folder ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)


# =========================
# KONEKSI DATABASE
# =========================
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL tidak ditemukan di Railway!")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )

    return conn


# =========================
# BUAT TABEL JIKA BELUM ADA
# =========================
def create_table():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ebooks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            image TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


# =========================
# BUAT TABEL OTOMATIS SAAT APP START
# =========================
with app.app_context():
    create_table()


# =========================
# HALAMAN UTAMA
# =========================
@app.route("/")
def index():
    search = request.args.get("search", "")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if search:
        cur.execute(
            """
            SELECT * FROM ebooks
            WHERE title ILIKE %s
            ORDER BY id DESC
            """,
            ("%" + search + "%",)
        )
    else:
        cur.execute(
            """
            SELECT * FROM ebooks
            ORDER BY id DESC
            """
        )

    ebooks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "index.html",
        ebooks=ebooks,
        search=search
    )


# =========================
# UPLOAD EBOOK
# =========================
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        file = request.files["file"]
        image = request.files["image"]

        if not file or not image:
            return "File ebook dan gambar wajib diupload"

        # Nama file aman
        filename = secure_filename(file.filename)
        image_name = secure_filename(image.filename)

        # Simpan file ebook
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
        file.save(file_path)

        # Simpan gambar cover
        image_path = os.path.join(
            app.config["IMAGE_FOLDER"],
            image_name
        )
        image.save(image_path)

        # Simpan ke database
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            INSERT INTO ebooks (title, filename, image)
            VALUES (%s, %s, %s)
        """, (
            title,
            filename,
            image_name
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("upload.html")


# =========================
# DOWNLOAD EBOOK
# =========================
@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    if not os.path.exists(file_path):
        return f"File tidak ditemukan: {file_path}"

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )


# =========================
# HALAMAN EDIT
# =========================
@app.route("/edit")
def edit():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT * FROM ebooks
        ORDER BY id DESC
    """)

    ebooks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "edit.html",
        ebooks=ebooks
    )


# =========================
# UPDATE EBOOK
# =========================
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    title = request.form["title"]
    image = request.files.get("image")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if image and image.filename != "":
        image_name = secure_filename(image.filename)
        image_path = os.path.join(
            app.config["IMAGE_FOLDER"],
            image_name
        )
        image.save(image_path)

        cur.execute("""
            UPDATE ebooks
            SET title = %s, image = %s
            WHERE id = %s
        """, (
            title,
            image_name,
            id
        ))

    else:
        cur.execute("""
            UPDATE ebooks
            SET title = %s
            WHERE id = %s
        """, (
            title,
            id
        ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/edit")


# =========================
# HAPUS EBOOK
# =========================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT filename, image
        FROM ebooks
        WHERE id = %s
    """, (id,))

    ebook = cur.fetchone()

    if ebook:
        # Hapus file ebook
        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            ebook["filename"]
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        # Hapus gambar cover
        if ebook["image"]:
            image_path = os.path.join(
                app.config["IMAGE_FOLDER"],
                ebook["image"]
            )

            if os.path.exists(image_path):
                os.remove(image_path)

        # Hapus dari database
        cur.execute("""
            DELETE FROM ebooks
            WHERE id = %s
        """, (id,))

        conn.commit()

    cur.close()
    conn.close()

    return redirect("/edit")


# =========================
# JALANKAN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
