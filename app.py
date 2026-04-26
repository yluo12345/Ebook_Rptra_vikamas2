import os
import psycopg2
import cloudinary
import cloudinary.uploader

from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)

# =========================
# DATABASE
# =========================
def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )
    return conn

# =========================
# CREATE TABLE
# =========================
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()

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

with app.app_context():
    create_table()

# =========================
# HOME
# =========================
@app.route("/")
def index():
    search = request.args.get("search", "")

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if search:
        cur.execute("""
            SELECT * FROM ebooks
            WHERE title ILIKE %s
            ORDER BY id DESC
        """, ("%" + search + "%",))
    else:
        cur.execute("""
            SELECT * FROM ebooks
            ORDER BY id DESC
        """)

    ebooks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", ebooks=ebooks, search=search)

# =========================
# UPLOAD (CLOUDINARY)
# =========================
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        title = request.form["title"]
        file = request.files.get("file")
        image = request.files.get("image")

        if not file or file.filename == "" or not image or image.filename == "":
             return "File ebook dan gambar wajib diupload"

        # upload PDF ke cloudinary
        pdf_upload = cloudinary.uploader.upload(
            file,
            resource_type="raw"
        )

        # upload gambar
        image_upload = cloudinary.uploader.upload(
            image,
            folder="ebook_covers"
        )

        pdf_url = pdf_upload["secure_url"]
        image_url = image_upload["secure_url"]

        # simpan ke database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO ebooks (title, filename, image)
            VALUES (%s, %s, %s)
        """, (title, pdf_url, image_url))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("upload.html")

# =========================
# EDIT PAGE
# =========================
@app.route("/edit")
def edit():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM ebooks ORDER BY id DESC")
    ebooks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("edit.html", ebooks=ebooks)

# =========================
# UPDATE (hanya judul / gambar optional)
# =========================
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    title = request.form["title"]
    image = request.files.get("image")

    conn = get_db_connection()
    cur = conn.cursor()

    if image and image.filename != "":
        upload = cloudinary.uploader.upload(
            image,
            folder="ebook_covers"
        )
        image_url = upload["secure_url"]

        cur.execute("""
            UPDATE ebooks
            SET title = %s, image = %s
            WHERE id = %s
        """, (title, image_url, id))

    else:
        cur.execute("""
            UPDATE ebooks
            SET title = %s
            WHERE id = %s
        """, (title, id))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/edit")

# =========================
# DELETE (hapus dari DB saja)
# =========================
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM ebooks WHERE id = %s", (id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/edit")

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)