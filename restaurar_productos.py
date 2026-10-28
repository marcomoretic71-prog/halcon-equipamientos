import sqlite3
import os
import psycopg2

# 1. Lee de tu sqlite local
con_sqlite = sqlite3.connect('db.sqlite3')
con_sqlite.row_factory = sqlite3.Row
cur = con_sqlite.cursor()
cur.execute('SELECT codigo, barcode, nombre, categoria, precio, stock FROM equipamientos_producto')
productos = cur.fetchall()
print(f"Leídos {len(productos)} productos de tu db.sqlite3 local")

# 2. Conecta a Postgres de Railway
DATABASE_URL = input("Pegá acá el DATABASE_URL de Railway y apretá Enter: ").strip()
conn = psycopg2.connect(DATABASE_URL)
cur_pg = conn.cursor()

# 3. Inserta
for p in productos:
    try:
        cur_pg.execute("""
            INSERT INTO equipamientos_producto (codigo, barcode, nombre, categoria, precio, stock, fecha_ultimo_cambio_precio, fecha_ultimo_cambio_stock)
            VALUES (%s,%s,%s,%s,%s,%s, NOW(), NOW())
            ON CONFLICT (codigo) DO UPDATE SET nombre=EXCLUDED.nombre, precio=EXCLUDED.precio, stock=EXCLUDED.stock, categoria=EXCLUDED.categoria
        """, (p['codigo'], p['barcode'], p['nombre'], p['categoria'], float(p['precio']), int(p['stock'] or 0)))
    except Exception as e:
        print(f"Error {p['codigo']}: {e}")

conn.commit()
print(f"¡Listo! {len(productos)} productos restaurados en Postgres de Railway")