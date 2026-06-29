from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime  # ÚJ: A pontos idő lekéréséhez

app = Flask(__name__)

DB_PATH = 'foglalasok.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Szolgáltatások tábla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS szolgaltatasok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nev TEXT NOT NULL UNIQUE,
            ar INTEGER NOT NULL,
            idotartam TEXT
        )
    ''')
    
    # 2. Időpontok tábla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS idopontok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datum TEXT NOT NULL UNIQUE,
            statusz TEXT NOT NULL DEFAULT 'szabad'
        )
    ''')
    
    # 3. Foglalások tábla (CASCADING DELETE: ha törlődik az időpont, törlődik a foglalás is)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foglalasok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nev TEXT NOT NULL,
            idopont_id INTEGER NOT NULL,
            szolgaltatas_id INTEGER NOT NULL,
            FOREIGN KEY (idopont_id) REFERENCES idopontok(id) ON DELETE CASCADE,
            FOREIGN KEY (szolgaltatas_id) REFERENCES szolgaltatasok(id)
        )
    ''')
    
    # Alapértelmezett szolgáltatások feltöltése
    cursor.execute('SELECT COUNT(*) FROM szolgaltatasok')
    if cursor.fetchone()[0] == 0:
        mintak = [
            ("Alap Hajvágás", 15, "30 perc"),
            ("Prémium Hajvágás & Szakáll", 25, "60 perc"),
            ("Hajfestés", 40, "90 perc")
        ]
        cursor.executemany('INSERT INTO szolgaltatasok (nev, ar, idotartam) VALUES (?, ?, ?)', mintak)
    
    conn.commit()
    conn.close()

# Főoldal
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, datum FROM idopontok WHERE statusz = 'szabad' ORDER BY datum ASC")
    szabad_napok = cursor.fetchall()
    
    cursor.execute('SELECT id, nev, ar, idotartam FROM szolgaltatasok')
    szolgaltatasok_lista = cursor.fetchall()
    conn.close()
    return render_template('index.html', szabad_idopontok=szabad_napok, szolgaltatasok=szolgaltatasok_lista)

# Foglalás mentése
@app.route('/foglal', methods=['POST'])
def foglal():
    v_nev = request.form['nev']
    v_szolgaltatas_id = request.form['szolgaltatas']
    v_idopont_id = request.form['idopont']
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO foglalasok (nev, idopont_id, szolgaltatas_id) VALUES (?, ?, ?)', (v_nev, v_idopont_id, v_szolgaltatas_id))
        cursor.execute("UPDATE idopontok SET statusz = 'foglalt' WHERE id = ?", (v_idopont_id,))
        conn.commit()
        conn.close()
        return f"<h3>Sikeres foglalás, {v_nev}! Köszönjük!</h3><a href='/'>Vissza a főoldalra</a>"
    except Exception as e:
        return f"<h3>Hiba történt: {e}</h3><a href='/'>Vissza</a>"

# Admin felület (Takarítással kiegészítve)
@app.route('/admin-titkos-lista')
def admin_lista():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # ÚJ: AUTOMATIKUS TAKARÍTÁS
    # Lekérjük a mostani időt olyan formátumban, ahogy az adatbázisban van (ÉÉÉÉ-MM-NN ÓÓ:PP)
    most = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # Kitöröljük azokat az időpontokat, amiknél a dátum kisebb (korábbi), mint a mostani idő
    cursor.execute("DELETE FROM idopontok WHERE datum < ?", (most,))
    conn.commit()
    
    # 1. Szabad időpontok lekérése
    cursor.execute("SELECT id, datum FROM idopontok WHERE statusz = 'szabad' ORDER BY datum ASC")
    szabadok = cursor.fetchall()
    
    # 2. Aktív foglalások lekérése
    cursor.execute('''
        SELECT f.id, f.nev, i.datum, sz.nev, sz.ar, i.id
        FROM foglalasok f
        JOIN idopontok i ON f.idopont_id = i.id
        JOIN szolgaltatasok sz ON f.szolgaltatas_id = sz.id
        ORDER BY i.datum ASC
    ''')
    foglaltak = cursor.fetchall()
    conn.close()
    
    return render_template('admin.html', szabad_idopontok=szabadok, foglalások_lista=foglaltak)

# Új időpont hozzáadása
@app.route('/admin/uj-idopont', methods=['POST'])
def uj_idopont():
    uj_datum = request.form['uj_datum'].replace('T', ' ')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO idopontok (datum, statusz) VALUES (?, "szabad")', (uj_datum,))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass
    return redirect('/admin-titkos-lista')

# ÚJ ÚTVONAL: Időpont törlése / lemondása az admin által
@app.route('/admin/torol/<int:idopont_id>')
def torol_idopont(idopont_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Bekapcsoljuk a Foreign Key támogatást, hogy a Cascade Delete működjön
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Kitöröljük az időpontot (ez automatikusan törli a hozzá tartozó foglalást is a cascade miatt)
    cursor.execute("DELETE FROM idopontok WHERE id = ?", (idopont_id,))
    
    conn.commit()
    conn.close()
    return redirect('/admin-titkos-lista')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
