import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE ebooks ADD COLUMN image TEXT")
    print("Kolom image berhasil ditambahkan!")
except Exception as e:
    print("Error:", e)

conn.commit()
conn.close()