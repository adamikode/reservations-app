from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# 1. Adatbázis inicializálása (Létrehozzuk a táblát, ha még nem létezik)
def init_db():
    conn = sqlite3.connect('foglalasok.db')
    cursor = conn.cursor()
    # A 'UNIQUE' kulcsszó biztosítja, hogy egy dátumra csak egy foglalás eshet!
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foglalasok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nev TEXT NOT NULL,
            datum TEXT NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# 2. Főoldal útvonal (Betölti a naptárat)
@app.route('/')
def index():
    return render_template('index.html')

# 3. Foglalás beküldése útvonal (Ide érkeznek az adatok a HTML-ből)
@app.route('/foglal', methods=['POST'])
def foglal():
    # Kiszedjük a beküldött adatokat
    v_nev = request.form['nev']
    v_datum = request.form['datum']
    
    try:
        # Megpróbáljuk elmenteni az adatbázisba
        conn = sqlite3.connect('foglalasok.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO foglalasok (nev, datum) VALUES (?, ?)', (v_nev, v_datum))
        conn.commit()
        conn.close()
        
        return f"<h3>Sikeres foglalás, {v_nev}! Várunk szeretettel: {v_datum}</h3><a href='/'>Vissza a főoldalra</a>"
        
    except sqlite3.IntegrityError:
        # Ez a rész fut le, ha a UNIQUE szabály megsérül (vagyis a dátum már létezik)
        return "<h3>Sajnos ez a nap már foglalt! Kérjük, válassz másik dátumot.</h3><a href='/'>Vissza a naptárhoz</a>"


@app.route('/admin-titkos-lista')
def admin_lista():
    # 1. Kapcsolódunk az adatbázishoz a pontos útvonallal
    conn = sqlite3.connect('/home/reservations/reservations-app/foglalasok.db')
    cursor = conn.cursor()
    
    # 2. Lekérjük az összes sort a foglalasok táblából
    cursor.execute('SELECT id, nev, datum FROM foglalasok')
    adatok = cursor.fetchall() # Ez egy listába gyűjti az összes foglalást
    
    # 3. Bezárjuk a kapcsolatot
    conn.close()
    
    # 4. Átadjuk az adatokat az új admin.html sablonnak
    return render_template('admin.html', foglalások_lista=adatok)



if __name__ == '__main__':
    init_db() # Program indulásakor ellenőrizzük az adatbázist
    app.run(debug=True)
	
