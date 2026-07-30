import os
import math
from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env (solo para desarrollo local)
load_dotenv()

app = Flask(__name__)

# Lee la clave secreta desde las variables de entorno de Render, o usa una por defecto local
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mi_clave_secreta_super_segura_12345')

# Configuración de conexión dinámica para Render y FreeSQLDatabase
def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "Hd4vbr4tqk09MDB"),
        database=os.environ.get("DB_NAME", "listado_pelicula"),
        port=int(os.environ.get("DB_PORT", 3306)),
        autocommit=True # Para que los cambios se apliquen sin necesidad de conn.commit() explícito en cada consulta simple
    )

# --- READ (Leer) ---
@app.route('/')
@app.route('/index')
def index():
    page = request.args.get('page', 1, type=int)
    REGISTROS_POR_PAGINA = 6
    offset = (page - 1) * REGISTROS_POR_PAGINA
    
    conn = get_db_connection()
    # Usamos DictCursor para mantener la compatibilidad con tu código estructurado como diccionario
    cursor = conn.cursor(pymysql.cursors.DictCursor)
   
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM registros")
        total_registros = cursor.fetchone()['total']
        
        total_paginas = math.ceil(total_registros / REGISTROS_POR_PAGINA)
        if total_paginas == 0:
            total_paginas = 1

        query = "SELECT id, nombre, valor FROM registros LIMIT %s OFFSET %s"
        cursor.execute(query, (REGISTROS_POR_PAGINA, offset))
        registros = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al consultar la Base de Datos: {e}")
        registros = []
        total_paginas = 1
    finally:
        cursor.close()
        conn.close()

    return render_template(
        'index.html', 
        registros=registros, 
        pagina_actual=page, 
        total_paginas=total_paginas
    )

# --- CREATE (Crear) ---
@app.route('/agregar', methods=('GET', 'POST'))
def agregar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        valor = request.form['valor']

        conn = get_db_connection()
        cursor = conn.cursor()
        # PyMySQL usa %s como marcador de posición en lugar de ?
        cursor.execute("INSERT INTO registros (nombre, valor) VALUES (%s, %s)", (nombre, valor))
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    
    return render_template('nuevo.html')

# --- UPDATE (Actualizar) ---
@app.route('/editar/<int:id>', methods=('GET', 'POST'))
def editar(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        valor = request.form['valor']
        
        cursor = conn.cursor()
        # Cambiado ? por %s
        cursor.execute("UPDATE registros SET nombre = %s, valor = %s WHERE id = %s", (nombre, valor, id))
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
        
    else:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        # Cambiado ? por %s
        cursor.execute("SELECT * FROM registros WHERE id = %s", (id,))
        registro = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if registro is None:
            return "Registro no encontrado", 404
            
        return render_template('editar.html', registro=registro)

# --- DELETE (Eliminar) ---
@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cambiado ? por %s
    cursor.execute("DELETE FROM registros WHERE id = %s", (id,))
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/contactanos')
def contactanos():
    return render_template('contactanos.html')

# NUEVA RUTA: GUARDAR LOS DATOS DE CONTACTO
@app.route('/guardar', methods=['POST'])
def guardar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        telefono = request.form['telefono']
        mensaje = request.form['mensaje']
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Cambiados los ? por %s para compatibilidad con PyMySQL
            sql = """
                INSERT INTO contactos (nombre, apellido, correo, telefono, mensaje) 
                VALUES (%s, %s, %s, %s, %s)
            """
            valores = (nombre, apellido, correo, telefono, mensaje)
            
            cursor.execute(sql, valores)
            flash('Registro guardado exitosamente, próximamente te contactaremos', 'success')
            
        except Exception as e:
            flash(f'Hubo un error al guardar tus datos: {e}', 'error')
            
        finally:
            if conn:
                cursor.close()
                conn.close()
                
        return redirect(url_for('contactanos'))

if __name__ == '__main__':
    app.run(debug=True)
