import sqlite3
con = sqlite3.connect('db.sqlite3')
cur = con.cursor()

def contar(tabla):
    try:
        cur.execute(f'SELECT count(*) FROM {tabla}')
        return cur.fetchone()[0]
    except Exception as e:
        return f"Error: {e}"

print("=== TU DB.SQLITE3 LOCAL ===")
print("PRODUCTOS:", contar('equipamientos_producto'))
print("CLIENTES:", contar('equipamientos_cliente'))
print("VENTAS:", contar('equipamientos_venta'))
print("ITEMS VENTA:", contar('equipamientos_itemventa'))
print("CAJA:", contar('equipamientos_movimientocaja'))
print("PRESUPUESTOS:", contar('equipamientos_presupuesto'))