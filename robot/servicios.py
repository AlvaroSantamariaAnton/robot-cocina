import sqlite3
from typing import List, Optional, Dict, Tuple

from .modelos import ProcesoCocina, PasoReceta, Receta
from data.init_db import conectar, reinicio_fabrica, inicializar_bd


# ======================================================
# Funciones internas de ayuda
# ======================================================

def _fila_a_proceso_base(fila: Tuple) -> ProcesoCocina:
    """
    Convierte una fila de procesos_base a un objeto ProcesoCocina.
    Estructura de fila: (id, nombre, tipo, temperatura, tiempo_segundos, velocidad)
    """
    id_, nombre, tipo, temperatura, tiempo_segundos, velocidad = fila
    return ProcesoCocina(
        id_=id_,
        nombre=nombre,
        tipo=tipo,
        temperatura=temperatura,
        tiempo_segundos=tiempo_segundos,
        velocidad=velocidad,
        origen="base",
    )


def _fila_a_proceso_usuario(fila: Tuple) -> ProcesoCocina:
    """
    Convierte una fila de procesos_usuario a un objeto ProcesoCocina.
    Estructura de fila: (id, nombre, tipo, temperatura, tiempo_segundos, velocidad)
    """
    id_, nombre, tipo, temperatura, tiempo_segundos, velocidad = fila
    return ProcesoCocina(
        id_=id_,
        nombre=nombre,
        tipo=tipo,
        temperatura=temperatura,
        tiempo_segundos=tiempo_segundos,
        velocidad=velocidad,
        origen="usuario",
    )


# ======================================================
# PROCESOS
# ======================================================

def cargar_procesos_base() -> List[ProcesoCocina]:
    """
    Devuelve una lista de todos los procesos de fábrica (procesos_base).
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, tipo, temperatura, tiempo_segundos, velocidad
            FROM procesos_base
            ORDER BY id;
            """
        )
        filas = cur.fetchall()
        return [_fila_a_proceso_base(f) for f in filas]
    finally:
        conn.close()


def cargar_procesos_usuario() -> List[ProcesoCocina]:
    """
    Devuelve una lista de todos los procesos creados por el usuario (procesos_usuario).
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, tipo, temperatura, tiempo_segundos, velocidad
            FROM procesos_usuario
            ORDER BY id;
            """
        )
        filas = cur.fetchall()
        return [_fila_a_proceso_usuario(f) for f in filas]
    finally:
        conn.close()


def obtener_proceso_base_por_id(id_proceso: int) -> Optional[ProcesoCocina]:
    """
    Devuelve un proceso_base por id, o None si no existe.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, tipo, temperatura, tiempo_segundos, velocidad
            FROM procesos_base
            WHERE id = ?;
            """,
            (id_proceso,),
        )
        fila = cur.fetchone()
        if fila is None:
            return None
        return _fila_a_proceso_base(fila)
    finally:
        conn.close()


def obtener_proceso_usuario_por_id(id_proceso: int) -> Optional[ProcesoCocina]:
    """
    Devuelve un proceso_usuario por id, o None si no existe.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, nombre, tipo, temperatura, tiempo_segundos, velocidad
            FROM procesos_usuario
            WHERE id = ?;
            """,
            (id_proceso,),
        )
        fila = cur.fetchone()
        if fila is None:
            return None
        return _fila_a_proceso_usuario(fila)
    finally:
        conn.close()


def crear_proceso_usuario(
    nombre: str,
    tipo: str,
    temperatura: int,
    tiempo_segundos: int,
    velocidad: int,
) -> ProcesoCocina:
    """
    Crea un nuevo proceso en la tabla procesos_usuario y devuelve el objeto ProcesoCocina.
    No se comprueba aquí nombres duplicados: esto se controla en la capa de UI.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO procesos_usuario (nombre, tipo, temperatura, tiempo_segundos, velocidad)
            VALUES (?, ?, ?, ?, ?);
            """,
            (nombre, tipo, temperatura, tiempo_segundos, velocidad),
        )
        id_nuevo = cur.lastrowid
        conn.commit()
        return ProcesoCocina(
            id_=id_nuevo,
            nombre=nombre,
            tipo=tipo,
            temperatura=temperatura,
            tiempo_segundos=tiempo_segundos,
            velocidad=velocidad,
            origen="usuario",
        )
    finally:
        conn.close()


def eliminar_proceso_usuario(id_proceso: int) -> None:
    """
    Elimina un proceso_usuario por id. También elimina los pasos de recetas_usuario
    que lo usen, para evitar referencias colgantes.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        # Borrar pasos que usan ese proceso
        cur.execute(
            """
            DELETE FROM pasos_receta_usuario
            WHERE id_proceso = ?;
            """,
            (id_proceso,),
        )
        # Borrar el propio proceso
        cur.execute(
            """
            DELETE FROM procesos_usuario
            WHERE id = ?;
            """,
            (id_proceso,),
        )
        conn.commit()
    finally:
        conn.close()


# ======================================================
# RECETAS
# ======================================================

def _cargar_recetas_generico(
    tabla_recetas: str,
    tabla_pasosp: str,
    tabla_procesos: str,
    origen: str,
) -> List[Receta]:
    """
    Función interna para cargar recetas y convertirlas en objetos Receta.
    Parámetros:
        tabla_recetas: 'recetas_base' o 'recetas_usuario'
        tabla_pasosp: 'pasos_receta_base' o 'pasos_receta_usuario'
        tabla_procesos: 'procesos_base' o 'procesos_usuario'
        origen: 'base' o 'usuario'
    """
    conn = conectar()
    try:
        cur = conn.cursor()

        # 1) Cargar todas las recetas
        cur.execute(
            f"""
            SELECT id, nombre, descripcion
            FROM {tabla_recetas}
            ORDER BY id;
            """
        )
        filas_recetas = cur.fetchall()
        if not filas_recetas:
            return []

        # 2) Cargar todos los pasos + procesos asociados de una sola vez
        ids_recetas = [r[0] for r in filas_recetas]
        marcadores = ",".join("?" for _ in ids_recetas)

        cur.execute(
            f"""
            SELECT p.id_receta,
                   p.orden,
                   pr.id,
                   pr.nombre,
                   pr.tipo,
                   pr.temperatura,
                   pr.tiempo_segundos,
                   pr.velocidad
            FROM {tabla_pasosp} AS p
            JOIN {tabla_procesos} AS pr
                ON p.id_proceso = pr.id
            WHERE p.id_receta IN ({marcadores})
            ORDER BY p.id_receta, p.orden;
            """,
            ids_recetas,
        )
        filas_pasos = cur.fetchall()

        # Agrupar por id_receta
        pasos_por_receta: Dict[int, List[PasoReceta]] = {}
        for id_receta, orden, pid, pnombre, ptipo, ptemp, ptiempo, pvel in filas_pasos:
            proceso = ProcesoCocina(
                id_=pid,
                nombre=pnombre,
                tipo=ptipo,
                temperatura=ptemp,
                tiempo_segundos=ptiempo,
                velocidad=pvel,
                origen=origen,
            )
            paso = PasoReceta(orden=orden, proceso=proceso)
            pasos_por_receta.setdefault(id_receta, []).append(paso)

        # 3) Construir objetos Receta
        recetas: List[Receta] = []
        for id_receta, nombre, descripcion in filas_recetas:
            pasos = pasos_por_receta.get(id_receta, [])
            recetas.append(
                Receta(
                    id_=id_receta,
                    nombre=nombre,
                    descripcion=descripcion or "",
                    pasos=pasos,
                    origen=origen,
                )
            )

        return recetas
    finally:
        conn.close()


def cargar_recetas_base() -> List[Receta]:
    """
    Devuelve una lista de todas las recetas de fábrica (recetas_base)
    con sus pasos y procesos asociados.
    """
    return _cargar_recetas_generico(
        tabla_recetas="recetas_base",
        tabla_pasosp="pasos_receta_base",
        tabla_procesos="procesos_base",
        origen="base",
    )


def cargar_recetas_usuario() -> List[Receta]:
    """
    Devuelve una lista de todas las recetas creadas por el usuario (recetas_usuario)
    con sus pasos y procesos asociados.
    """
    return _cargar_recetas_generico(
        tabla_recetas="recetas_usuario",
        tabla_pasosp="pasos_receta_usuario",
        tabla_procesos="procesos_usuario",
        origen="usuario",
    )


def crear_receta_usuario(
    nombre: str,
    descripcion: str,
    pasos: List[Tuple[int, int]],
) -> Receta:
    """
    Crea una nueva receta de usuario.

    Parámetros:
        nombre: nombre de la receta
        descripcion: texto descriptivo
        pasos: lista de tuplas (orden, id_proceso_usuario)
               por ejemplo: [(1, 3), (2, 5), (3, 7)]

    Devuelve:
        Objeto Receta con sus pasos (cada paso incluye ProcesoCocina origen='usuario').
    """
    conn = conectar()
    try:
        cur = conn.cursor()

        # Insertar la receta
        cur.execute(
            """
            INSERT INTO recetas_usuario (nombre, descripcion)
            VALUES (?, ?);
            """,
            (nombre, descripcion),
        )
        id_receta = cur.lastrowid

        # Insertar los pasos
        for orden, id_proceso in pasos:
            cur.execute(
                """
                INSERT INTO pasos_receta_usuario (id_receta, id_proceso, orden)
                VALUES (?, ?, ?);
                """,
                (id_receta, id_proceso, orden),
            )

        conn.commit()

        # Cargar la receta recién creada con sus pasos
        cur.execute(
            """
            SELECT id, nombre, descripcion
            FROM recetas_usuario
            WHERE id = ?;
            """,
            (id_receta,),
        )
        fila_receta = cur.fetchone()
        if fila_receta is None:
            raise RuntimeError("No se pudo recuperar la receta recién creada.")

        # Cargar pasos + procesos
        cur.execute(
            """
            SELECT p.orden,
                   pr.id,
                   pr.nombre,
                   pr.tipo,
                   pr.temperatura,
                   pr.tiempo_segundos,
                   pr.velocidad
            FROM pasos_receta_usuario AS p
            JOIN procesos_usuario AS pr
                ON p.id_proceso = pr.id
            WHERE p.id_receta = ?
            ORDER BY p.orden;
            """,
            (id_receta,),
        )
        filas_pasos = cur.fetchall()

        pasos_obj: List[PasoReceta] = []
        for orden, pid, pnombre, ptipo, ptemp, ptiempo, pvel in filas_pasos:
            proceso = ProcesoCocina(
                id_=pid,
                nombre=pnombre,
                tipo=ptipo,
                temperatura=ptemp,
                tiempo_segundos=ptiempo,
                velocidad=pvel,
                origen="usuario",
            )
            pasos_obj.append(PasoReceta(orden=orden, proceso=proceso))

        return Receta(
            id_=id_receta,
            nombre=fila_receta[1],
            descripcion=fila_receta[2] or "",
            pasos=pasos_obj,
            origen="usuario",
        )
    finally:
        conn.close()


def eliminar_receta_usuario(id_receta: int) -> None:
    """
    Elimina una receta de usuario y sus pasos asociados.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        # Borrar los pasos primero
        cur.execute(
            """
            DELETE FROM pasos_receta_usuario
            WHERE id_receta = ?;
            """,
            (id_receta,),
        )
        # Borrar la receta
        cur.execute(
            """
            DELETE FROM recetas_usuario
            WHERE id = ?;
            """,
            (id_receta,),
        )
        conn.commit()
    finally:
        conn.close()


# ======================================================
# Reinicio de fábrica (envoltura)
# ======================================================

def reinicio_de_fabrica() -> None:
    """
    Envuelve a data.init_db.reinicio_fabrica, para que puedas llamarlo desde
    tu lógica de aplicación (por ejemplo desde la UI) sin importar los detalles
    de conexión.
    """
    conn = conectar()
    try:
        reinicio_fabrica(conn)
    finally:
        conn.close()


# ======================================================
# Inicialización de base de datos
# ======================================================

def inicializar_bd_si_es_necesario() -> None:
    """
    Llama a la función de inicialización de la BD. Es segura; si ya existe no duplica datos.
    Puedes llamarla desde app.py al inicio de la aplicación.
    """
    try:
        inicializar_bd()
    except Exception as e:
        # Mejor diagnóstico en caso de error durante la inicialización.
        raise RuntimeError(f"Error inicializando la base de datos: {e}") from e
