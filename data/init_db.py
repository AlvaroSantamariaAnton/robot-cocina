import os
import sqlite3

# Ruta de la base de datos: data/robot.db
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot.db")


def conectar() -> sqlite3.Connection:
    """Devuelve una conexión a la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)


# ======================================================
# Creación de tablas
# ======================================================

def crear_tablas(conn: sqlite3.Connection) -> None:
    """Crea las tablas necesarias si no existen."""
    cur = conn.cursor()

    # Tabla de procesos de fábrica
    cur.execute("""
        CREATE TABLE IF NOT EXISTS procesos_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            temperatura INTEGER NOT NULL,
            tiempo_segundos INTEGER NOT NULL,
            velocidad INTEGER NOT NULL
        );
    """)

    # Tabla de procesos creados por el usuario
    cur.execute("""
        CREATE TABLE IF NOT EXISTS procesos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            temperatura INTEGER NOT NULL,
            tiempo_segundos INTEGER NOT NULL,
            velocidad INTEGER NOT NULL
        );
    """)

    # Tabla de recetas de fábrica
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recetas_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT
        );
    """)

    # Pasos de las recetas de fábrica
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pasos_receta_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receta INTEGER NOT NULL,
            id_proceso INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            FOREIGN KEY (id_receta) REFERENCES recetas_base(id),
            FOREIGN KEY (id_proceso) REFERENCES procesos_base(id)
        );
    """)

    # Tabla de recetas creadas por el usuario
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recetas_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT
        );
    """)

    # Pasos de las recetas del usuario
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pasos_receta_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receta INTEGER NOT NULL,
            id_proceso INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            FOREIGN KEY (id_receta) REFERENCES recetas_usuario(id),
            FOREIGN KEY (id_proceso) REFERENCES procesos_usuario(id)
        );
    """)

    # Tabla de configuración / estado del robot
    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            estado TEXT NOT NULL,
            programa_actual TEXT,
            progreso REAL NOT NULL
        );
    """)

    conn.commit()


# ======================================================
# Datos de fábrica (procesos y recetas)
# ======================================================

def insertar_datos_base(conn: sqlite3.Connection) -> None:
    """
    Inserta los procesos y recetas de fábrica si todavía no existen.
    Se comprueba si ya hay recetas_base para no duplicar datos.
    """
    cur = conn.cursor()

    # Comprobamos si ya hay datos de fábrica
    cur.execute("SELECT COUNT(*) FROM recetas_base;")
    count_recetas = cur.fetchone()[0]
    if count_recetas > 0:
        # Ya hay datos de fábrica, no hacemos nada
        return

    # ============================
    # Insertar PROCESOS de fábrica
    # ============================

    procesos_base = [
        # nombre, tipo, temperatura, tiempo_segundos, velocidad
        ("Picar verduras", "manipulacion", 0, 30, 4),
        ("Trocear verduras", "manipulacion", 0, 40, 3),
        ("Rallar queso", "manipulacion", 0, 30, 5),
        ("Triturar frutos secos", "manipulacion", 0, 45, 7),
        ("Triturar fino", "textura", 0, 45, 6),
        ("Mezclar suave", "mezcla", 0, 90, 2),
        ("Amasar masa", "amasado", 0, 600, 2),
        ("Sofreír suave", "coccion", 120, 300, 1),
        ("Sofreír intenso", "coccion", 140, 240, 2),
        ("Cocinar al vapor", "coccion", 100, 600, 0),
        ("Hervir", "coccion", 100, 900, 0),
        ("Rehogar verduras", "coccion", 110, 420, 1),
        ("Calentar salsa", "coccion", 90, 300, 0),
        ("Emulsionar salsa", "textura", 0, 60, 3),
        ("Pesar ingredientes", "pesaje", 0, 30, 0),
    ]

    cur.executemany(
        """
        INSERT INTO procesos_base (nombre, tipo, temperatura, tiempo_segundos, velocidad)
        VALUES (?, ?, ?, ?, ?);
        """,
        procesos_base,
    )

    # Mapa nombre -> id
    cur.execute("SELECT id, nombre FROM procesos_base;")
    filas = cur.fetchall()
    procesos_por_nombre = {nombre: id_ for (id_, nombre) in filas}

    # ============================
    # Insertar RECETAS de fábrica
    # ============================

    # Cada receta tiene: nombre, descripcion, lista de pasos (orden, nombre_proceso)
    recetas_definicion = [
        {
            "nombre": "Verduras salteadas",
            "descripcion": "Verduras picadas y salteadas con un sofrito suave.",
            "pasos": [
                (1, "Picar verduras"),
                (2, "Sofreír suave"),
            ],
        },
        {
            "nombre": "Verduras al vapor",
            "descripcion": "Verduras cocinadas al vapor para una textura ligera.",
            "pasos": [
                (1, "Picar verduras"),
                (2, "Cocinar al vapor"),
            ],
        },
        {
            "nombre": "Crema de verduras",
            "descripcion": "Crema suave de verduras trituradas.",
            "pasos": [
                (1, "Picar verduras"),
                (2, "Rehogar verduras"),
                (3, "Hervir"),
                (4, "Triturar fino"),
            ],
        },
        {
            "nombre": "Masa de pan básica",
            "descripcion": "Masa base para pan o pizza.",
            "pasos": [
                (1, "Mezclar suave"),
                (2, "Amasar masa"),
            ],
        },
        {
            "nombre": "Salsa caliente",
            "descripcion": "Salsa calentada lentamente sin llegar a hervir.",
            "pasos": [
                (1, "Mezclar suave"),
                (2, "Calentar salsa"),
            ],
        },
        {
            "nombre": "Frutos secos triturados",
            "descripcion": "Frutos secos triturados finos, listos para postres.",
            "pasos": [
                (1, "Triturar frutos secos"),
            ],
        },
        {
            "nombre": "Puré de patata cremoso",
            "descripcion": "Puré de patata con textura suave, listo para acompañar.",
            "pasos": [
                (1, "Pesar ingredientes"),
                (2, "Cocinar al vapor"),
                (3, "Triturar fino"),
            ],
        },
        {
            "nombre": "Salsa de queso rallado",
            "descripcion": "Salsa cremosa a base de queso rallado.",
            "pasos": [
                (1, "Rallar queso"),
                (2, "Mezclar suave"),
                (3, "Calentar salsa"),
                (4, "Emulsionar salsa"),
            ],
        },
        {
            "nombre": "Guiso de verduras completo",
            "descripcion": "Receta guiada que combina sofrito, vapor y cocción.",
            "pasos": [
                (1, "Pesar ingredientes"),
                (2, "Picar verduras"),
                (3, "Sofreír intenso"),
                (4, "Cocinar al vapor"),
                (5, "Hervir"),
            ],
        },
        {
            "nombre": "Masa de pizza especial",
            "descripcion": "Masa de pizza lista para hornear, con amasado prolongado.",
            "pasos": [
                (1, "Pesar ingredientes"),
                (2, "Mezclar suave"),
                (3, "Amasar masa"),
            ],
        },
    ]

    for receta_def in recetas_definicion:
        # Insertar receta
        cur.execute(
            """
            INSERT INTO recetas_base (nombre, descripcion)
            VALUES (?, ?);
            """,
            (receta_def["nombre"], receta_def["descripcion"]),
        )
        id_receta = cur.lastrowid

        # Insertar pasos de la receta
        for orden, nombre_proceso in receta_def["pasos"]:
            id_proceso = procesos_por_nombre.get(nombre_proceso)
            if id_proceso is None:
                raise ValueError(f"Proceso de fábrica '{nombre_proceso}' no encontrado al crear recetas base.")
            cur.execute(
                """
                INSERT INTO pasos_receta_base (id_receta, id_proceso, orden)
                VALUES (?, ?, ?);
                """,
                (id_receta, id_proceso, orden),
            )

    conn.commit()


# ======================================================
# Configuración / estado del robot
# ======================================================

def inicializar_configuracion(conn: sqlite3.Connection) -> None:
    """
    Asegura que existe la fila de configuración con id=1.
    """
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM configuracion WHERE id = 1;")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute(
            """
            INSERT INTO configuracion (id, estado, programa_actual, progreso)
            VALUES (1, 'apagado', NULL, 0.0);
            """
        )
        conn.commit()


# ======================================================
# Reinicio de fábrica
# ======================================================

def reinicio_fabrica(conn: sqlite3.Connection) -> None:
    """
    Elimina los datos creados por el usuario y resetea la configuración,
    pero mantiene intactas las recetas y procesos de fábrica.
    Esta función se usa desde la lógica de aplicación para el botón
    'Reinicio de fábrica'.
    """
    cur = conn.cursor()

    # Borrar pasos de recetas de usuario
    cur.execute("DELETE FROM pasos_receta_usuario;")
    # Borrar recetas de usuario
    cur.execute("DELETE FROM recetas_usuario;")
    # Borrar procesos de usuario
    cur.execute("DELETE FROM procesos_usuario;")

    # Resetear configuración
    cur.execute("UPDATE configuracion SET estado='apagado', programa_actual=NULL, progreso=0.0 WHERE id=1;")

    conn.commit()


# ======================================================
# Inicialización global de la BD
# ======================================================

def inicializar_bd() -> None:
    """
    Crea el directorio (si es necesario), la base de datos, las tablas
    y los datos de fábrica. Es segura de llamar múltiples veces.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = conectar()
    try:
        crear_tablas(conn)
        insertar_datos_base(conn)
        inicializar_configuracion(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    inicializar_bd()
    print(f"Base de datos inicializada en: {DB_PATH}")
