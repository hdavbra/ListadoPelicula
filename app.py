from flask import Flask, render_template, request, redirect, url_for, flash
import mariadb
import math

app = Flask(__name__)

# OBLIGATORIO: Agrega una clave secreta si no la tienes.
# Flask la necesita para poder manejar las sesiones de los mensajes flash().
app.config['SECRET_KEY'] = 'mi_clave_secreta_super_segura_12345'

# Aquí ya debes tener tu configuración de conexión actual, algo similar a esto:

# Configuración de conexión a MariaDB
def get_db_connection():
    return mariadb.connect(
        user="root",
        password="Hd4vbr4tqk09MDB",
        host="localhost",
        port=3306,
        database="listado_pelicula"
    )

# --- READ (Leer) ---
@app.route('/')
@app.route('/index')


def index():
    # 1. Obtener el número de página actual desde la URL (por defecto es 1)
    page = request.args.get('page', 1, type=int)
    
    # Definir el límite de registros por página
    REGISTROS_POR_PAGINA = 6
    
    # 2. Calcular el desplazamiento (OFFSET) para la consulta SQL
    offset = (page - 1) * REGISTROS_POR_PAGINA
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
   
    try:
        # 3. Obtener el número total de registros en la tabla para calcular el total de páginas
        cursor.execute("SELECT COUNT(*) AS total FROM registros")
        total_registros = cursor.fetchone()['total']
        
        # Calcular el número total de páginas (redondeando hacia arriba)
        total_paginas = math.ceil(total_registros / REGISTROS_POR_PAGINA)
        if total_paginas == 0:
            total_paginas = 1

        # 4. Consultar solo los 6 registros correspondientes a la página actual
        # Usamos LIMIT para la cantidad y OFFSET para saber desde dónde empezar a leer
        query = "SELECT id, nombre, valor FROM registros LIMIT %s OFFSET %s"
        cursor.execute(query, (REGISTROS_POR_PAGINA, offset))
        registros = cursor.fetchall()
        
    except Exception as e:
        print(f"Error al consultar MariaDB: {e}")
        registros = []
        total_paginas = 1
    finally:
        cursor.close()
        conn.close()

    # 5. Enviar las variables de paginación al frontend
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
        cursor.execute("INSERT INTO registros (nombre, valor) VALUES (?, ?)", (nombre, valor))
        conn.commit()
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
        
        # 1. Usamos un cursor normal para actualizar
        cursor = conn.cursor()
        cursor.execute("UPDATE registros SET nombre = ?, valor = ? WHERE id = ?", (nombre, valor, id))
        conn.commit()
        cursor.close()
        conn.close()
        
        # CRUCIAL: Detener la función aquí y redirigir
        return redirect(url_for('index'))
        
    else:
        # 2. Si el método es GET, aquí SÍ hacemos la consulta SELECT primero
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registros WHERE id = ?", (id,)) # <-- ¡Faltaba esto!
        registro = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Validamos que el registro realmente exista en la base de datos
        if registro is None:
            return "Registro no encontrado", 404
            
        return render_template('editar.html', registro=registro)

# --- DELETE (Eliminar) ---
@app.route('/eliminar/<int:id>')
def eliminar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registros WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# AGREGA ESTA RUTA PARA "NOSOTROS"
@app.route('/nosotros')
def nosotros():
    # 'nosotros.html' debe ser el nombre exacto de tu archivo dentro de /templates
    return render_template('nosotros.html')

@app.route('/contactanos')
def contactanos():
    # 'nosotros.html' debe ser el nombre exacto de tu archivo dentro de /templates
    return render_template('contactanos.html')

# RUTA PRINCIPAL (Donde muestras el formulario)
#@app.route('/contact')
#def contac():
 #   return render_template('contactanos.html')


# NUEVA RUTA: AGREGAR ESTO PARA GUARDAR LOS DATOS DE CONTACTO
@app.route('/guardar', methods=['POST'])
def guardar():
    if request.method == 'POST':
        # 1. Capturar los datos enviados desde el formulario HTML
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        telefono = request.form['telefono']
        mensaje = request.form['mensaje']
        
        conn = None
        try:
            # 2. Conectarse a la base de datos a través de tu método existente
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 3. Sentencia SQL con marcadores de posición (?) para evitar inyecciones SQL
            sql = """
                INSERT INTO contactos (nombre, apellido, correo, telefono, mensaje) 
                VALUES (?, ?, ?, ?, ?)
            """
            valores = (nombre, apellido, correo, telefono, mensaje)
            
            # 4. Ejecutar y guardar los cambios
            cursor.execute(sql, valores)
            conn.commit()
            
            # 5. Definir el mensaje de éxito requerido
            flash('Registro guardado exitosamente, próximamente te contactaremos', 'success')
            
        except mariadb.Error as e:
            if conn:
                conn.rollback()  # Deshacer cambios si algo falla
            flash(f'Hubo un error al guardar tus datos: {e}', 'error')
            
        finally:
            # 6. Asegurar el cierre del cursor y la conexión siempre
            if conn:
                cursor.close()
                conn.close()
                
        # 7. Redireccionar de vuelta al formulario limpio
        return redirect(url_for('contactanos'))

if __name__ == '__main__':
    app.run(debug=True)

