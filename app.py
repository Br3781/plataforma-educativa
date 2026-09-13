import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, request

app = Flask(__name__)

CARRERAS = {
    'industrial': {
        'nombre': 'Ingeniería Industrial',
        'cursos': {
            1: ['Química General', 'Comunicación I', 'Cálculo I', 'Dibujo Técnico'],
            2: ['Física I', 'Cálculo II', 'Economía General', 'Química Orgánica'],
        }
    },
    'informatica': {
        'nombre': 'Ingeniería Informática',
        'cursos': {
            1: ['Algoritmos y Programación', 'Matemática Discreta', 'Comunicación I', 'Cálculo I'],
            2: ['Estructura de Datos', 'Física I', 'Cálculo II', 'Arquitectura de Computadoras'],
        }
    },
    'psicologia': {
        'nombre': 'Psicología',
        'cursos': {
            1: ['Introducción a la Psicología', 'Biología Humana', 'Taller de Expresión'],
            2: ['Psicología del Desarrollo', 'Neuroanatomía', 'Estadística General'],
        }
    },
    'medicina': {
        'nombre': 'Medicina',
        'cursos': {
            1: ['Anatomía Humana I', 'Biología Celular', 'Química Médica'],
            2: ['Histología', 'Embriología', 'Bioquímica'],
        }
    }
}

def init_db():
    conn = sqlite3.connect('codigos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accesos (
            codigo TEXT PRIMARY KEY,
            fecha_activacion TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO accesos (codigo, fecha_activacion, activo) VALUES (?, ?, ?)",
                   ('ING2026', None, 1))
    conn.commit()
    conn.close()

init_db()

# 1. Selección de Carrera
@app.route('/')
def inicio():
    return render_template('inicio.html', carreras=CARRERAS)

# 2. Selección de Ciclo
@app.route('/carrera/<id_carrera>')
def ver_ciclos(id_carrera):
    carrera = CARRERAS.get(id_carrera)
    if not carrera:
        return "Carrera no encontrada", 404
    ciclos = list(range(1, 11))
    return render_template('ciclos.html', carrera=carrera, id_carrera=id_carrera, ciclos=ciclos)

# 3. Selección de Curso
@app.route('/carrera/<id_carrera>/ciclo/<int:num_ciclo>')
def ver_cursos(id_carrera, num_ciclo):
    carrera = CARRERAS.get(id_carrera)
    if not carrera:
        return "Carrera no encontrada", 404
    cursos = carrera['cursos'].get(num_ciclo, [
        f'Curso General A (Ciclo {num_ciclo})',
        f'Curso General B (Ciclo {num_ciclo})'
    ])
    return render_template('cursos.html', carrera=carrera, num_ciclo=num_ciclo, id_carrera=id_carrera, cursos=cursos)

# 4. Selección de Año (NUEVO PASO)
@app.route('/carrera/<id_carrera>/ciclo/<int:num_ciclo>/curso/<nombre_curso>')
def ver_anios(id_carrera, num_ciclo, nombre_curso):
    carrera = CARRERAS.get(id_carrera)
    anios = [2024, 2025, 2026] # Puedes cambiar o agregar más años aquí
    return render_template('anios.html', carrera=carrera, num_ciclo=num_ciclo, curso=nombre_curso, id_carrera=id_carrera, anios=anios)

# 5. Confirmación, QR e Ingreso de Código
@app.route('/carrera/<id_carrera>/ciclo/<int:num_ciclo>/curso/<nombre_curso>/anio/<int:num_anio>')
def ver_opciones_curso(id_carrera, num_ciclo, nombre_curso, num_anio):
    carrera = CARRERAS.get(id_carrera)
    return render_template('opciones_curso.html', carrera=carrera, num_ciclo=num_ciclo, curso=nombre_curso, anio=num_anio)

# 6. Validación del Código
@app.route('/verificar', methods=['POST'])
def verificar():
    codigo_ingresado = request.form.get('codigo', '').strip()
    curso = request.form.get('curso', '')
    anio = request.form.get('anio', '')
    
    conn = sqlite3.connect('codigos.db')
    cursor = conn.cursor()
    cursor.execute("SELECT fecha_activacion, activo FROM accesos WHERE codigo = ?", (codigo_ingresado,))
    resultado = cursor.fetchone()
    
    if not resultado:
        conn.close()
        return "El código ingresado no existe o es incorrecto.", 403

    fecha_activacion_str, activo = resultado

    if activo == 0:
        conn.close()
        return "Este código ya ha expirado.", 403

    ahora = datetime.now()

    if fecha_activacion_str is None:
        fecha_activacion = ahora
        cursor.execute("UPDATE accesos SET fecha_activacion = ? WHERE codigo = ?", 
                       (fecha_activacion.strftime('%Y-%m-%d %H:%M:%S'), codigo_ingresado))
        conn.commit()
    else:
        fecha_activacion = datetime.strptime(fecha_activacion_str, '%Y-%m-%d %H:%M:%S')

    if ahora > fecha_activacion + timedelta(days=30):
        cursor.execute("UPDATE accesos SET activo = 0 WHERE codigo = ?", (codigo_ingresado,))
        conn.commit()
        conn.close()
        return "Tu acceso de 30 días ha finalizado.", 403

    conn.close()
    return render_template('hoja_protegida.html', curso=curso, anio=anio)

if __name__ == '__main__':
    app.run(debug=True)
