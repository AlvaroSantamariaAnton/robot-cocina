import os
import sqlite3
import json

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
            tipo_ejecucion TEXT NOT NULL DEFAULT 'automatico',
            instrucciones TEXT,
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
            tipo_ejecucion TEXT NOT NULL DEFAULT 'automatico',
            instrucciones TEXT,
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
            descripcion TEXT,
            ingredientes TEXT
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
            descripcion TEXT,
            ingredientes TEXT
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
    # Formato: (nombre, tipo, tipo_ejecucion, instrucciones, temperatura, tiempo_segundos, velocidad)

    procesos_base = [
        # ===== PROCESOS MANUALES =====
        
        # --- Preparación inicial ---
        ("Añadir ingredientes secos", "preparacion", "manual", 
         "Añadir al vaso todos los ingredientes secos indicados en la receta (harina, azúcar, sal, especias, etc.)", 
         0, 0, 0),
        
        ("Añadir ingredientes líquidos", "preparacion", "manual",
         "Añadir al vaso todos los líquidos indicados (agua, leche, aceite, caldo, etc.)",
         0, 0, 0),
        
        ("Añadir verduras preparadas", "preparacion", "manual",
         "Incorporar las verduras ya peladas y cortadas según indicaciones de la receta",
         0, 0, 0),
        
        ("Añadir proteína", "preparacion", "manual",
         "Incorporar la carne, pescado o proteína vegetal indicada, previamente limpia y troceada",
         0, 0, 0),
        
        ("Añadir lácteos", "preparacion", "manual",
         "Añadir los productos lácteos necesarios (leche, nata, queso, mantequilla, etc.)",
         0, 0, 0),
        
        ("Añadir aromáticos", "preparacion", "manual",
         "Incorporar hierbas aromáticas, ajo, cebolla u otros elementos que den sabor base",
         0, 0, 0),
        
        # --- Verificación y control ---
        ("Verificar punto de cocción", "verificacion", "manual",
         "Probar el alimento y verificar que está en su punto. Ajustar sal y especias si es necesario",
         0, 0, 0),
        
        ("Verificar textura", "verificacion", "manual",
         "Comprobar que la textura es la deseada. Si es necesario, continuar procesando",
         0, 0, 0),
        
        ("Retirar líquido de cocción", "manipulacion", "manual",
         "Con cuidado de no quemarse, retirar el líquido sobrante usando el vaso medidor o escurriendo",
         0, 0, 0),
        
        ("Añadir ingredientes finales", "preparacion", "manual",
         "Incorporar los ingredientes que se añaden al final (hierbas frescas, aceite en crudo, etc.)",
         0, 0, 0),
        
        ("Transferir a recipiente", "manipulacion", "manual",
         "Verter el contenido del vaso al recipiente de servir indicado",
         0, 0, 0),
        
        ("Reservar porción", "manipulacion", "manual",
         "Sacar y reservar aparte la cantidad indicada de la preparación para uso posterior",
         0, 0, 0),
        
        # ===== PROCESOS AUTOMÁTICOS =====
        
        # --- Picado y triturado (frío) ---
        ("Picar verduras finamente", "manipulacion", "automatico",
         "Proceso automático de picado fino",
         0, 15, 5),
        
        ("Picar verduras groseramente", "manipulacion", "automatico",
         "Proceso automático de picado grueso",
         0, 10, 4),
        
        ("Picar carne", "manipulacion", "automatico",
         "Proceso automático de picado de carne",
         0, 20, 5),
        
        ("Rallar queso", "manipulacion", "automatico",
         "Proceso automático de rallado",
         0, 20, 5),
        
        ("Triturar grueso", "manipulacion", "automatico",
         "Proceso automático de triturado grueso (trozos visibles)",
         0, 25, 6),
        
        ("Triturar fino", "textura", "automatico",
         "Proceso automático de triturado fino (textura suave)",
         0, 40, 8),
        
        ("Pulverizar", "textura", "automatico",
         "Proceso automático de pulverización (polvo fino)",
         0, 45, 10),
        
        ("Picar frutos secos", "manipulacion", "automatico",
         "Proceso automático de picado de frutos secos",
         0, 15, 4),
        
        ("Moler especias", "manipulacion", "automatico",
         "Proceso automático de molido de especias",
         0, 30, 10),
        
        # --- Mezcla (frío) ---
        ("Mezclar suave", "mezcla", "automatico",
         "Proceso automático de mezclado suave",
         0, 30, 2),
        
        ("Mezclar intenso", "mezcla", "automatico",
         "Proceso automático de mezclado intenso",
         0, 45, 4),
        
        ("Amasar", "amasado", "automatico",
         "Proceso automático de amasado",
         0, 180, 3),
        
        ("Emulsionar", "textura", "automatico",
         "Proceso automático de emulsión (salsas, mayonesas)",
         0, 40, 4),
        
        ("Batir claras", "textura", "automatico",
         "Proceso automático de montado de claras",
         0, 120, 3),
        
        ("Montar nata", "textura", "automatico",
         "Proceso automático de montado de nata",
         0, 90, 3),
        
        # --- Cocción con temperatura baja-media ---
        ("Calentar suave", "coccion", "automatico",
         "Proceso automático de calentamiento suave",
         60, 120, 1),
        
        ("Templar", "coccion", "automatico",
         "Proceso automático para templar mezclas",
         50, 180, 2),
        
        ("Sofreír suave", "coccion", "automatico",
         "Proceso automático de sofrito suave",
         100, 240, 1),
        
        ("Sofreír intenso", "coccion", "automatico",
         "Proceso automático de sofrito intenso",
         120, 180, 2),
        
        ("Pochar", "coccion", "automatico",
         "Proceso automático de pochado",
         90, 300, 1),
        
        # --- Cocción con temperatura alta ---
        ("Hervir suave", "coccion", "automatico",
         "Proceso automático de hervido suave",
         100, 420, 1),
        
        ("Hervir", "coccion", "automatico",
         "Proceso automático de hervido",
         100, 600, 1),
        
        ("Cocción al vapor", "coccion", "automatico",
         "Proceso automático de cocción al vapor",
         100, 900, 0),
        
        ("Reducir líquido", "coccion", "automatico",
         "Proceso automático de reducción",
         100, 480, 2),
        
        ("Cocer a fuego lento", "coccion", "automatico",
         "Proceso automático de cocción lenta",
         95, 1200, 1),
        
        # --- Cocciones especiales ---
        ("Confitar", "coccion", "automatico",
         "Proceso automático de confitado",
         80, 1800, 0),
        
        ("Cocción lenta prolongada", "coccion", "automatico",
         "Proceso automático de cocción muy lenta",
         90, 3600, 0),
        
        # --- Texturas finales ---
        ("Preparar puré", "textura", "automatico",
         "Proceso automático de triturado para puré",
         0, 35, 6),
        
        ("Preparar crema fina", "textura", "automatico",
         "Proceso automático de triturado fino para cremas",
         0, 50, 8),
        
        ("Preparar mousse", "textura", "automatico",
         "Proceso automático de mezclado suave para mousses",
         0, 60, 3),
        
        ("Ligar salsa", "textura", "automatico",
         "Proceso automático para ligar salsas",
         80, 120, 4),
        
        # --- Repostería ---
        ("Mezclar masa pastelera", "reposteria", "automatico",
         "Proceso automático de mezclado para masas de pastelería",
         0, 60, 3),
        
        ("Fundir chocolate", "reposteria", "automatico",
         "Proceso automático de fundido de chocolate",
         50, 180, 2),
        
        ("Hacer caramelo", "reposteria", "automatico",
         "Proceso automático de caramelización",
         110, 420, 2),
        
        ("Templar chocolate", "reposteria", "automatico",
         "Proceso automático de templado de chocolate",
         45, 300, 2),
        
        # --- Procesos de enfriamiento ---
        ("Enfriar rápido", "enfriamiento", "automatico",
         "Proceso de mezclado suave para enfriar rápidamente",
         0, 180, 2),
        
        ("Remover en frío", "enfriamiento", "automatico",
         "Proceso de removido suave sin temperatura",
         0, 120, 1),
    ]

    cur.executemany(
        """
        INSERT INTO procesos_base (nombre, tipo, tipo_ejecucion, instrucciones, temperatura, tiempo_segundos, velocidad)
        VALUES (?, ?, ?, ?, ?, ?, ?);
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

    recetas_definicion = [
        {
            "nombre": "Puré de patata cremoso",
            "descripcion": "Puré suave y cremoso, ideal como guarnición",
            "ingredientes": [
                {"nombre": "Patatas", "cantidad": 600, "unidad": "g", "nota": "peladas y troceadas"},
                {"nombre": "Agua", "cantidad": 500, "unidad": "ml", "nota": "para cubrir"},
                {"nombre": "Leche", "cantidad": 100, "unidad": "ml", "nota": ""},
                {"nombre": "Mantequilla", "cantidad": 40, "unidad": "g", "nota": ""},
                {"nombre": "Sal", "cantidad": 1, "unidad": "cucharadita", "nota": "al gusto"},
            ],
            "pasos": [
                (1, "Añadir verduras preparadas"),
                (2, "Añadir ingredientes líquidos"),
                (3, "Hervir"),
                (4, "Retirar líquido de cocción"),
                (5, "Añadir lácteos"),
                (6, "Preparar puré"),
                (7, "Verificar textura"),
            ],
        },
        {
            "nombre": "Crema de verduras",
            "descripcion": "Crema suave y nutritiva de verduras variadas",
            "ingredientes": [
                {"nombre": "Puerro", "cantidad": 1, "unidad": "unidad", "nota": "limpio y troceado"},
                {"nombre": "Zanahoria", "cantidad": 2, "unidad": "unidades", "nota": "peladas y troceadas"},
                {"nombre": "Calabacín", "cantidad": 1, "unidad": "unidad", "nota": "troceado"},
                {"nombre": "Patata", "cantidad": 1, "unidad": "unidad", "nota": "pelada y troceada"},
                {"nombre": "Caldo de verduras", "cantidad": 800, "unidad": "ml", "nota": ""},
                {"nombre": "Aceite de oliva", "cantidad": 30, "unidad": "ml", "nota": ""},
                {"nombre": "Sal", "cantidad": 1, "unidad": "cucharadita", "nota": "al gusto"},
            ],
            "pasos": [
                (1, "Añadir aromáticos"),
                (2, "Añadir ingredientes líquidos"),
                (3, "Sofreír suave"),
                (4, "Añadir verduras preparadas"),
                (5, "Añadir ingredientes líquidos"),
                (6, "Hervir suave"),
                (7, "Triturar fino"),
                (8, "Preparar crema fina"),
                (9, "Verificar punto de cocción"),
            ],
        },
        {
            "nombre": "Masa de pan básica",
            "descripcion": "Masa versátil para pan casero",
            "ingredientes": [
                {"nombre": "Harina de fuerza", "cantidad": 500, "unidad": "g", "nota": ""},
                {"nombre": "Agua tibia", "cantidad": 300, "unidad": "ml", "nota": ""},
                {"nombre": "Levadura fresca", "cantidad": 15, "unidad": "g", "nota": "o 5g de seca"},
                {"nombre": "Sal", "cantidad": 10, "unidad": "g", "nota": ""},
                {"nombre": "Aceite de oliva", "cantidad": 30, "unidad": "ml", "nota": ""},
            ],
            "pasos": [
                (1, "Añadir ingredientes líquidos"),
                (2, "Añadir ingredientes secos"),
                (3, "Mezclar suave"),
                (4, "Amasar"),
                (5, "Verificar textura"),
            ],
        },
        {
            "nombre": "Salsa bechamel",
            "descripcion": "Bechamel cremosa y sin grumos",
            "ingredientes": [
                {"nombre": "Leche", "cantidad": 500, "unidad": "ml", "nota": ""},
                {"nombre": "Mantequilla", "cantidad": 50, "unidad": "g", "nota": ""},
                {"nombre": "Harina", "cantidad": 50, "unidad": "g", "nota": ""},
                {"nombre": "Sal", "cantidad": 1, "unidad": "pizca", "nota": ""},
                {"nombre": "Nuez moscada", "cantidad": 1, "unidad": "pizca", "nota": "opcional"},
            ],
            "pasos": [
                (1, "Añadir lácteos"),
                (2, "Añadir ingredientes secos"),
                (3, "Calentar suave"),
                (4, "Ligar salsa"),
                (5, "Verificar textura"),
            ],
        },
        {
            "nombre": "Pesto de albahaca",
            "descripcion": "Salsa italiana aromática y versátil",
            "ingredientes": [
                {"nombre": "Albahaca fresca", "cantidad": 100, "unidad": "g", "nota": "hojas limpias"},
                {"nombre": "Piñones", "cantidad": 50, "unidad": "g", "nota": ""},
                {"nombre": "Ajo", "cantidad": 2, "unidad": "dientes", "nota": ""},
                {"nombre": "Parmesano rallado", "cantidad": 80, "unidad": "g", "nota": ""},
                {"nombre": "Aceite de oliva", "cantidad": 150, "unidad": "ml", "nota": "virgen extra"},
                {"nombre": "Sal", "cantidad": 1, "unidad": "pizca", "nota": "al gusto"},
            ],
            "pasos": [
                (1, "Añadir aromáticos"),
                (2, "Añadir ingredientes secos"),
                (3, "Triturar grueso"),
                (4, "Añadir ingredientes líquidos"),
                (5, "Emulsionar"),
                (6, "Verificar textura"),
            ],
        },
        {
            "nombre": "Hummus cremoso",
            "descripcion": "Paté de garbanzos estilo oriental",
            "ingredientes": [
                {"nombre": "Garbanzos cocidos", "cantidad": 400, "unidad": "g", "nota": "escurridos"},
                {"nombre": "Tahini", "cantidad": 80, "unidad": "g", "nota": "pasta de sésamo"},
                {"nombre": "Ajo", "cantidad": 2, "unidad": "dientes", "nota": ""},
                {"nombre": "Zumo de limón", "cantidad": 60, "unidad": "ml", "nota": ""},
                {"nombre": "Aceite de oliva", "cantidad": 60, "unidad": "ml", "nota": ""},
                {"nombre": "Comino", "cantidad": 1, "unidad": "cucharadita", "nota": ""},
                {"nombre": "Sal", "cantidad": 1, "unidad": "cucharadita", "nota": ""},
            ],
            "pasos": [
                (1, "Añadir ingredientes secos"),
                (2, "Añadir ingredientes líquidos"),
                (3, "Añadir aromáticos"),
                (4, "Triturar fino"),
                (5, "Emulsionar"),
                (6, "Verificar textura"),
            ],
        },
        {
            "nombre": "Risotto de setas",
            "descripcion": "Arroz cremoso con setas variadas",
            "ingredientes": [
                {"nombre": "Arroz arborio", "cantidad": 300, "unidad": "g", "nota": ""},
                {"nombre": "Setas variadas", "cantidad": 400, "unidad": "g", "nota": "limpias y laminadas"},
                {"nombre": "Cebolla", "cantidad": 1, "unidad": "unidad", "nota": "picada"},
                {"nombre": "Caldo de verduras", "cantidad": 1000, "unidad": "ml", "nota": "caliente"},
                {"nombre": "Vino blanco", "cantidad": 100, "unidad": "ml", "nota": ""},
                {"nombre": "Mantequilla", "cantidad": 50, "unidad": "g", "nota": ""},
                {"nombre": "Parmesano rallado", "cantidad": 80, "unidad": "g", "nota": ""},
                {"nombre": "Aceite de oliva", "cantidad": 40, "unidad": "ml", "nota": ""},
            ],
            "pasos": [
                (1, "Añadir aromáticos"),
                (2, "Añadir ingredientes líquidos"),
                (3, "Sofreír suave"),
                (4, "Añadir verduras preparadas"),
                (5, "Sofreír intenso"),
                (6, "Añadir ingredientes secos"),
                (7, "Añadir ingredientes líquidos"),
                (8, "Cocer a fuego lento"),
                (9, "Añadir lácteos"),
                (10, "Mezclar suave"),
                (11, "Verificar punto de cocción"),
            ],
        },
        {
            "nombre": "Gazpacho andaluz",
            "descripcion": "Sopa fría de verduras, refrescante y nutritiva",
            "ingredientes": [
                {"nombre": "Tomates maduros", "cantidad": 1000, "unidad": "g", "nota": "troceados"},
                {"nombre": "Pepino", "cantidad": 150, "unidad": "g", "nota": "pelado y troceado"},
                {"nombre": "Pimiento verde", "cantidad": 100, "unidad": "g", "nota": "limpio y troceado"},
                {"nombre": "Ajo", "cantidad": 1, "unidad": "diente", "nota": ""},
                {"nombre": "Pan duro", "cantidad": 50, "unidad": "g", "nota": "sin corteza"},
                {"nombre": "Aceite de oliva", "cantidad": 80, "unidad": "ml", "nota": "virgen extra"},
                {"nombre": "Vinagre de jerez", "cantidad": 30, "unidad": "ml", "nota": ""},
                {"nombre": "Sal", "cantidad": 1, "unidad": "cucharadita", "nota": "al gusto"},
            ],
            "pasos": [
                (1, "Añadir verduras preparadas"),
                (2, "Añadir aromáticos"),
                (3, "Añadir ingredientes secos"),
                (4, "Añadir ingredientes líquidos"),
                (5, "Triturar fino"),
                (6, "Verificar punto de cocción"),
                (7, "Enfriar rápido"),
            ],
        },
    ]

    for receta_def in recetas_definicion:
        # Convertir ingredientes a JSON
        ingredientes_json = json.dumps(receta_def["ingredientes"], ensure_ascii=False)
        
        # Insertar receta
        cur.execute(
            """
            INSERT INTO recetas_base (nombre, descripcion, ingredientes)
            VALUES (?, ?, ?);
            """,
            (receta_def["nombre"], receta_def["descripcion"], ingredientes_json),
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