import os
import sqlite3
import json

# Ruta de la base de datos: data/robot.db
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot.db")


def conectar() -> sqlite3.Connection:
    """Devuelve una conexión a la base de datos SQLite."""
    return sqlite3.connect(DB_PATH)


# ======================
# Creación de tablas
# ======================

def crear_tablas(conn: sqlite3.Connection) -> None:
    """Crea las tablas necesarias si no existen."""
    cur = conn.cursor()

    # Tabla de procesos de fábrica (SIN parámetros de ejecución)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS procesos_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tipo_ejecucion TEXT NOT NULL DEFAULT 'automatico',
            instrucciones TEXT
        );
    """)

    # Tabla de procesos creados por el usuario (SIN parámetros de ejecución)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS procesos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL,
            tipo_ejecucion TEXT NOT NULL DEFAULT 'automatico',
            instrucciones TEXT
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

    # Pasos de las recetas de fábrica (CON parámetros de ejecución)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pasos_receta_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receta INTEGER NOT NULL,
            id_proceso INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            temperatura INTEGER DEFAULT NULL,
            tiempo_segundos INTEGER DEFAULT NULL,
            velocidad INTEGER DEFAULT NULL,
            instrucciones TEXT DEFAULT NULL,
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

    # Pasos de las recetas del usuario (CON parámetros de ejecución)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pasos_receta_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_receta INTEGER NOT NULL,
            id_proceso INTEGER NOT NULL,
            orden INTEGER NOT NULL,
            temperatura INTEGER DEFAULT NULL,
            tiempo_segundos INTEGER DEFAULT NULL,
            velocidad INTEGER DEFAULT NULL,
            instrucciones TEXT DEFAULT NULL,
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


# ========================================
# Datos de fábrica (procesos y recetas)
# ========================================

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

    # ============================================================
    # Insertar PROCESOS de fábrica (SIN parámetros de ejecución)
    # ============================================================
    # Formato: (nombre, tipo, tipo_ejecucion, instrucciones)

    procesos_base = [
        # ===== PROCESOS MANUALES =====
        
        # --- Preparación inicial ---
        ("Añadir ingredientes secos", "Preparación", "manual", 
         "Añadir al vaso todos los ingredientes secos indicados en la receta (harina, azúcar, sal, especias, etc.)"),
        
        ("Añadir ingredientes líquidos", "Preparación", "manual",
         "Añadir al vaso todos los líquidos indicados (agua, leche, aceite, caldo, etc.)"),
        
        ("Añadir verduras preparadas", "Preparación", "manual",
         "Incorporar las verduras ya peladas y cortadas según indicaciones de la receta"),
        
        ("Añadir proteína", "Preparación", "manual",
         "Incorporar la carne, pescado o proteína vegetal indicada, previamente limpia y troceada"),
        
        ("Añadir lácteos", "Preparación", "manual",
         "Añadir los productos lácteos necesarios (leche, nata, queso, mantequilla, etc.)"),
        
        ("Añadir aromáticos", "Preparación", "manual",
         "Incorporar hierbas aromáticas, ajo, cebolla u otros elementos que den sabor base"),
        
        # --- Verificación y control ---
        ("Verificar punto de cocción", "Verificación", "manual",
         "Probar el alimento y verificar que está en su punto. Ajustar sal y especias si es necesario"),
        
        ("Verificar textura", "Verificación", "manual",
         "Comprobar que la textura es la deseada. Si es necesario, continuar procesando"),
        
        ("Retirar líquido de cocción", "Manipulación", "manual",
         "Con cuidado de no quemarse, retirar el líquido sobrante usando el vaso medidor o escurriendo"),
        
        ("Añadir ingredientes finales", "Preparación", "manual",
         "Incorporar los ingredientes que se añaden al final (hierbas frescas, aceite en crudo, etc.)"),
        
        ("Transferir a recipiente", "Manipulación", "manual",
         "Verter el contenido del vaso al recipiente de servir indicado"),
        
        ("Reservar porción", "Manipulación", "manual",
         "Sacar y reservar aparte la cantidad indicada de la preparación para uso posterior"),
        
        # ===== PROCESOS AUTOMÁTICOS =====
        
        # --- Picado y triturado (frío) ---
        ("Picar verduras finamente", "Manipulación", "automatico", "Proceso automático de picado fino"),
        ("Picar verduras groseramente", "Manipulación", "automatico", "Proceso automático de picado grueso"),
        ("Picar carne", "Manipulación", "automatico", "Proceso automático de picado de carne"),
        ("Rallar queso", "Manipulación", "automatico", "Proceso automático de rallado"),
        ("Triturar grueso", "Manipulación", "automatico", "Proceso automático de triturado grueso (trozos visibles)"),
        ("Triturar fino", "textura", "automatico", "Proceso automático de triturado fino (textura suave)"),
        ("Pulverizar", "textura", "automatico", "Proceso automático de pulverización (polvo fino)"),
        ("Picar frutos secos", "Manipulación", "automatico", "Proceso automático de picado de frutos secos"),
        ("Moler especias", "Manipulación", "automatico", "Proceso automático de molido de especias"),
        
        # --- Mezcla (frío) ---
        ("Mezclar suave", "mezcla", "automatico", "Proceso automático de mezclado suave"),
        ("Mezclar intenso", "mezcla", "automatico", "Proceso automático de mezclado intenso"),
        ("Amasar", "amasado", "automatico", "Proceso automático de amasado"),
        ("Emulsionar", "textura", "automatico", "Proceso automático de emulsión (salsas, mayonesas)"),
        ("Batir claras", "textura", "automatico", "Proceso automático de montado de claras"),
        ("Montar nata", "textura", "automatico", "Proceso automático de montado de nata"),
        
        # --- Cocción con temperatura baja-media ---
        ("Calentar suave", "Cocción", "automatico", "Proceso automático de calentamiento suave"),
        ("Templar", "Cocción", "automatico", "Proceso automático para templar mezclas"),
        ("Sofreír suave", "Cocción", "automatico", "Proceso automático de sofrito suave"),
        ("Sofreír intenso", "Cocción", "automatico", "Proceso automático de sofrito intenso"),
        ("Pochar", "Cocción", "automatico", "Proceso automático de pochado"),
        
        # --- Cocción con temperatura alta ---
        ("Hervir suave", "Cocción", "automatico", "Proceso automático de hervido suave"),
        ("Hervir", "Cocción", "automatico", "Proceso automático de hervido"),
        ("Cocción al vapor", "Cocción", "automatico", "Proceso automático de cocción al vapor"),
        ("Reducir líquido", "Cocción", "automatico", "Proceso automático de reducción"),
        ("Cocer a fuego lento", "Cocción", "automatico", "Proceso automático de cocción lenta"),
        
        # --- Cocciónes especiales ---
        ("Confitar", "Cocción", "automatico", "Proceso automático de confitado"),
        ("Cocción lenta prolongada", "Cocción", "automatico", "Proceso automático de cocción muy lenta"),
        
        # --- Texturas finales ---
        ("Preparar puré", "textura", "automatico", "Proceso automático de triturado para puré"),
        ("Preparar crema fina", "textura", "automatico", "Proceso automático de triturado fino para cremas"),
        ("Preparar mousse", "textura", "automatico", "Proceso automático de mezclado suave para mousses"),
        ("Ligar salsa", "textura", "automatico", "Proceso automático para ligar salsas"),
        
        # --- Repostería ---
        ("Mezclar masa pastelera", "Repostería", "automatico", "Proceso automático de mezclado para masas de pastelería"),
        ("Fundir chocolate", "Repostería", "automatico", "Proceso automático de fundido de chocolate"),
        ("Hacer caramelo", "Repostería", "automatico", "Proceso automático de caramelización"),
        ("Templar chocolate", "Repostería", "automatico", "Proceso automático de templado de chocolate"),
        
        # --- Procesos de enfriamiento ---
        ("Enfriar rápido", "enfriamiento", "automatico", "Proceso de mezclado suave para enfriar rápidamente"),
        ("Remover en frío", "enfriamiento", "automatico", "Proceso de removido suave sin temperatura"),
    ]

    cur.executemany(
        """
        INSERT INTO procesos_base (nombre, tipo, tipo_ejecucion, instrucciones)
        VALUES (?, ?, ?, ?);
        """,
        procesos_base,
    )

    # Mapa nombre -> id
    cur.execute("SELECT id, nombre FROM procesos_base;")
    filas = cur.fetchall()
    procesos_por_nombre = {nombre: id_ for (id_, nombre) in filas}

    # =============================
    # Insertar RECETAS de fábrica
    # =============================

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
                # (orden, nombre_proceso, temp, tiempo_seg, vel, instrucciones)
                (1, "Añadir verduras preparadas", None, None, None, "Añadir las patatas troceadas al vaso"),
                (2, "Añadir ingredientes líquidos", None, None, None, "Añadir el agua hasta cubrir las patatas"),
                (3, "Hervir", 100, 600, 1, None),
                (4, "Retirar líquido de cocción", None, None, None, "Escurrir el agua de cocción con cuidado"),
                (5, "Añadir lácteos", None, None, None, "Añadir la leche y mantequilla"),
                (6, "Preparar puré", 0, 35, 6, None),
                (7, "Verificar textura", None, None, None, "Probar y ajustar sal si es necesario"),
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
                (1, "Añadir aromáticos", None, None, None, "Añadir el puerro troceado"),
                (2, "Añadir ingredientes líquidos", None, None, None, "Añadir el aceite de oliva"),
                (3, "Sofreír suave", 100, 240, 1, None),
                (4, "Añadir verduras preparadas", None, None, None, "Incorporar zanahoria, calabacín y patata"),
                (5, "Añadir ingredientes líquidos", None, None, None, "Añadir el caldo de verduras"),
                (6, "Hervir suave", 100, 420, 1, None),
                (7, "Triturar fino", 0, 40, 8, None),
                (8, "Preparar crema fina", 0, 50, 8, None),
                (9, "Verificar punto de cocción", None, None, None, "Probar y ajustar sal y especias"),
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
                (1, "Añadir ingredientes líquidos", None, None, None, "Añadir agua tibia y aceite"),
                (2, "Añadir ingredientes secos", None, None, None, "Incorporar harina, levadura y sal"),
                (3, "Mezclar suave", 0, 30, 2, None),
                (4, "Amasar", 0, 180, 3, None),
                (5, "Verificar textura", None, None, None, "La masa debe estar elástica y no pegajosa"),
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
                (1, "Añadir lácteos", None, None, None, "Añadir leche y mantequilla"),
                (2, "Añadir ingredientes secos", None, None, None, "Incorporar harina, sal y nuez moscada"),
                (3, "Calentar suave", 60, 120, 1, None),
                (4, "Ligar salsa", 80, 120, 4, None),
                (5, "Verificar textura", None, None, None, "La salsa debe cubrir el dorso de una cuchara"),
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
                (1, "Añadir aromáticos", None, None, None, "Añadir albahaca y ajo"),
                (2, "Añadir ingredientes secos", None, None, None, "Incorporar piñones y parmesano"),
                (3, "Triturar grueso", 0, 25, 6, None),
                (4, "Añadir ingredientes líquidos", None, None, None, "Añadir el aceite de oliva"),
                (5, "Emulsionar", 0, 40, 4, None),
                (6, "Verificar textura", None, None, None, "El pesto debe ser cremoso pero con textura"),
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
                (1, "Añadir ingredientes secos", None, None, None, "Añadir garbanzos, comino y sal"),
                (2, "Añadir ingredientes líquidos", None, None, None, "Incorporar tahini, zumo de limón y aceite"),
                (3, "Añadir aromáticos", None, None, None, "Añadir los dientes de ajo"),
                (4, "Triturar fino", 0, 40, 8, None),
                (5, "Emulsionar", 0, 40, 4, None),
                (6, "Verificar textura", None, None, None, "El hummus debe ser cremoso y homogéneo"),
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
                (1, "Añadir aromáticos", None, None, None, "Añadir cebolla picada"),
                (2, "Añadir ingredientes líquidos", None, None, None, "Añadir aceite de oliva"),
                (3, "Sofreír suave", 100, 240, 1, None),
                (4, "Añadir verduras preparadas", None, None, None, "Incorporar las setas laminadas"),
                (5, "Sofreír intenso", 120, 180, 2, None),
                (6, "Añadir ingredientes secos", None, None, None, "Añadir el arroz arborio"),
                (7, "Añadir ingredientes líquidos", None, None, None, "Añadir vino blanco y caldo poco a poco"),
                (8, "Cocer a fuego lento", 95, 1200, 1, None),
                (9, "Añadir lácteos", None, None, None, "Incorporar mantequilla y parmesano"),
                (10, "Mezclar suave", 0, 30, 2, None),
                (11, "Verificar punto de cocción", None, None, None, "El arroz debe estar al dente y cremoso"),
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
                (1, "Añadir verduras preparadas", None, None, None, "Añadir tomates, pepino y pimiento"),
                (2, "Añadir aromáticos", None, None, None, "Incorporar el diente de ajo"),
                (3, "Añadir ingredientes secos", None, None, None, "Añadir el pan duro y la sal"),
                (4, "Añadir ingredientes líquidos", None, None, None, "Añadir aceite y vinagre"),
                (5, "Triturar fino", 0, 40, 8, None),
                (6, "Verificar punto de cocción", None, None, None, "Probar y ajustar sal y vinagre"),
                (7, "Enfriar rápido", 0, 180, 2, None),
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

        # Insertar pasos de la receta CON parámetros
        for paso_tupla in receta_def["pasos"]:
            orden, nombre_proceso, temp, tiempo, vel, instr = paso_tupla
            id_proceso = procesos_por_nombre.get(nombre_proceso)
            if id_proceso is None:
                raise ValueError(f"Proceso de fábrica '{nombre_proceso}' no encontrado al crear recetas base.")
            
            cur.execute(
                """
                INSERT INTO pasos_receta_base 
                    (id_receta, id_proceso, orden, temperatura, tiempo_segundos, velocidad, instrucciones)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (id_receta, id_proceso, orden, temp, tiempo, vel, instr),
            )

    conn.commit()


# ==================================
# Configuración / estado del robot
# ==================================

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


# =====================
# Reinicio de fábrica
# =====================

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


# ===============================
# Inicialización global de la BD
# ===============================

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