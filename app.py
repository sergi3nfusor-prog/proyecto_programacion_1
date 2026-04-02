import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuración de Conexión
DB_NAME = "tienda_deportiva"
DB_USER = "postgres"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "5432"

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COUNT(*) as total_productos FROM producto")
        res = cur.fetchone()
        total_productos = res['total_productos'] if res else 0
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        total_productos = 0

    return render_template('index.html', total_productos=total_productos)

@app.route('/productos')
def productos():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Novedades (ordenados por fecha desc) y validando campos del esquema provisto
        query = """
            SELECT p.IDProducto, p.nombreProducto, p.marca, p.precio, p.material, p.talla, 
                   i.stockActual, p.fechaIngreso
            FROM producto p
            LEFT JOIN inventario i ON p.IDInventario = i.IDInventario
            ORDER BY p.fechaIngreso DESC NULLS LAST
        """
        cur.execute(query)
        productos_lista = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
        productos_lista = []

    return render_template('productos.html', productos=productos_lista)

@app.route('/club')
def club():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Esquema tiene IDCliente pero no está la tabla cliente completa compartida en el prompt actual 
        # asumiré que cruzo con la tabla fidelización.
        cur.execute("""
            SELECT IDProgramaFidelizacion, nivel, puntosAcumulados
            FROM programaFidelizacion
            ORDER BY puntosAcumulados DESC
        """)
        niveles = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
        niveles = []

    return render_template('club.html', niveles=niveles)

@app.route('/ofertas')
def ofertas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT nombrePromocion, tipo, valor, fechaFin FROM promocion 
            WHERE fechaFin >= CURRENT_DATE
            ORDER BY fechaFin ASC
        """)
        promociones = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        promociones = []

    return render_template('ofertas.html', promociones=promociones)

@app.route('/sedes')
def sedes():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT nombreSucursal, calle, ciudad, telefono, horarioAtencion FROM sucursal")
        sucursales = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sucursales = []

    return render_template('sedes.html', sucursales=sucursales)

@app.route('/contacto', methods=['POST'])
def contacto():
    nombre = request.form.get('nombre')
    correo = request.form.get('correo')
    asunto = request.form.get('asunto')
    mensaje = request.form.get('mensaje')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mensajes_contacto (nombre, correo, asunto, mensaje) 
            VALUES (%s, %s, %s, %s)
        """, (nombre, correo, asunto, mensaje))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error inserting record: {e}")
        
    flash("¡Mensaje enviado con éxito!", "success")
    return redirect(url_for('ver_mensajes'))

@app.route('/mensajes')
def ver_mensajes():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT IDMensaje AS id, nombre, correo AS email, mensaje, fecha_envio FROM mensajes_contacto ORDER BY fecha_envio DESC")
        mensajes = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error querying messages: {e}")
        mensajes = []

    return render_template('mensajes.html', mensajes=mensajes)

@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM mensajes_contacto WHERE IDMensaje = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error deleting message: {e}")

    return redirect(url_for('ver_mensajes'))

if __name__ == '__main__':
    app.run(debug=True)
