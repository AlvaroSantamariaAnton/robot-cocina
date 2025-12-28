import sqlite3
import json
from typing import List, Optional, Dict, Tuple, Any

from .modelos import (
    ProcesoCocina, ProcesoManual, ProcesoAutomatico, 
    PasoReceta, Receta, RecetaBase, RecetaUsuario
)
from data.init_db import conectar, reinicio_fabrica, inicializar_bd


# ======================================================
# Funciones internas de ayuda
# ======================================================

def _fila_a_proceso_base(fila: Tuple) -> ProcesoCocina:
    """
    Convierte una fila de procesos_base a un objeto ProcesoCocina.
    Estructura de fila: (id, nombre, tipo, tipo_ejecucion, instrucciones)
    """
    id_, nombre, tipo, tipo_ejecucion, instrucciones = fila
    
    # Polimorfismo: Instanciar la subclase correcta según tipo_ejecucion
    if tipo_ejecucion == "manual":
        return ProcesoManual(
            id_=id_,
            nombre=nombre,
            tipo=tipo,
            tipo_ejecucion=tipo_ejecucion,
            instrucciones=instrucciones,
            origen="base",
        )
    else:
        return ProcesoAutomatico(
            id_=id_,
            nombre=nombre,
            tipo=tipo,
            tipo_ejecucion=tipo_ejecucion,
            instrucciones=instrucciones,
            origen="base",
        )


def _fila_a_proceso_usuario(fila: Tuple) -> ProcesoCocina:
    """
    Convierte una fila de procesos_usuario a un objeto ProcesoCocina.
    Estructura de fila: (id, nombre, tipo, tipo_ejecucion, instrucciones)
    """
    id_, nombre, tipo, tipo_ejecucion, instrucciones = fila
    
    # Polimorfismo: Instanciar la subclase correcta según tipo_ejecucion
    if tipo_ejecucion == "manual":
        return ProcesoManual(
            id_=id_,
            nombre=nombre,
            tipo=tipo,
            tipo_ejecucion=tipo_ejecucion,
            instrucciones=instrucciones,
            origen="usuario",
        )
    else:
        return ProcesoAutomatico(
            id_=id_,
            nombre=nombre,
            tipo=tipo,
            tipo_ejecucion=tipo_ejecucion,
            instrucciones=instrucciones,
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
            SELECT id, nombre, tipo, tipo_ejecucion, instrucciones
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
            SELECT id, nombre, tipo, tipo_ejecucion, instrucciones
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
            SELECT id, nombre, tipo, tipo_ejecucion, instrucciones
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
            SELECT id, nombre, tipo, tipo_ejecucion, instrucciones
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
    tipo_ejecucion: str,
    instrucciones: str,
) -> ProcesoCocina:
    """
    Crea un nuevo proceso en la tabla procesos_usuario y devuelve el objeto ProcesoCocina.
    
    CAMBIO: Ya NO acepta temperatura, tiempo_segundos, velocidad.
    Esos parámetros ahora van en los pasos de las recetas.
    
    No se comprueba aquí nombres duplicados: esto se controla en la capa de UI.
    """
    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO procesos_usuario (nombre, tipo, tipo_ejecucion, instrucciones)
            VALUES (?, ?, ?, ?);
            """,
            (nombre, tipo, tipo_ejecucion, instrucciones),
        )
        id_nuevo = cur.lastrowid
        conn.commit()
        # Polimorfismo: Retornar la subclase correcta
        if tipo_ejecucion == "manual":
            return ProcesoManual(
                id_=id_nuevo,
                nombre=nombre,
                tipo=tipo,
                tipo_ejecucion=tipo_ejecucion,
                instrucciones=instrucciones,
                origen="usuario",
            )
        else:
            return ProcesoAutomatico(
                id_=id_nuevo,
                nombre=nombre,
                tipo=tipo,
                tipo_ejecucion=tipo_ejecucion,
                instrucciones=instrucciones,
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
    tabla_pasos: str,
    tabla_procesos: str,
    origen: str,
) -> List[Receta]:
    """
    Función interna para cargar recetas y convertirlas en objetos Receta.
    
    CAMBIO IMPORTANTE: Ahora lee temperatura, tiempo_segundos, velocidad, instrucciones
    desde las tablas de PASOS, no de PROCESOS.
    
    Parámetros:
        tabla_recetas: 'recetas_base' o 'recetas_usuario'
        tabla_pasos: 'pasos_receta_base' o 'pasos_receta_usuario'
        tabla_procesos: 'procesos_base' o 'procesos_usuario'
        origen: 'base' o 'usuario'
    """
    conn = conectar()
    try:
        cur = conn.cursor()

        # 1) Cargar todas las recetas
        cur.execute(
            f"""
            SELECT id, nombre, descripcion, ingredientes
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

        # Si son recetas de usuario, buscar en ambas tablas de procesos
        if tabla_pasos == "pasos_receta_usuario":
            cur.execute(
                f"""
                SELECT p.id_receta,
                       p.orden,
                       p.temperatura,
                       p.tiempo_segundos,
                       p.velocidad,
                       p.instrucciones,
                       COALESCE(pr_user.id, pr_base.id) as id,
                       COALESCE(pr_user.nombre, pr_base.nombre) as nombre,
                       COALESCE(pr_user.tipo, pr_base.tipo) as tipo,
                       COALESCE(pr_user.tipo_ejecucion, pr_base.tipo_ejecucion) as tipo_ejecucion,
                       COALESCE(pr_user.instrucciones, pr_base.instrucciones) as proc_instrucciones,
                       CASE WHEN pr_user.id IS NOT NULL THEN 'usuario' ELSE 'base' END as origen
                FROM {tabla_pasos} AS p
                LEFT JOIN procesos_usuario AS pr_user
                    ON p.id_proceso = pr_user.id
                LEFT JOIN procesos_base AS pr_base
                    ON p.id_proceso = pr_base.id
                WHERE p.id_receta IN ({marcadores})
                ORDER BY p.id_receta, p.orden;
                """,
                ids_recetas,
            )
            filas_pasos = cur.fetchall()
            # Procesar con origen dinámico
            pasos_por_receta: Dict[int, List[PasoReceta]] = {}
            for fila in filas_pasos:
                (id_receta, orden, paso_temp, paso_tiempo, paso_vel, paso_instr,
                 pid, pnombre, ptipo, ptipo_ej, proc_instr, origen_proc) = fila
                
                proceso = ProcesoCocina(
                    id_=pid,
                    nombre=pnombre,
                    tipo=ptipo,
                    tipo_ejecucion=ptipo_ej,
                    instrucciones=proc_instr,
                    origen=origen_proc,
                )
                paso = PasoReceta(
                    orden=orden,
                    proceso=proceso,
                    temperatura=paso_temp,
                    tiempo_segundos=paso_tiempo,
                    velocidad=paso_vel,
                    instrucciones=paso_instr,
                )
                pasos_por_receta.setdefault(id_receta, []).append(paso)
        else:
            # Recetas de base: solo buscar en procesos_base
            cur.execute(
                f"""
                SELECT p.id_receta,
                       p.orden,
                       p.temperatura,
                       p.tiempo_segundos,
                       p.velocidad,
                       p.instrucciones,
                       pr.id,
                       pr.nombre,
                       pr.tipo,
                       pr.tipo_ejecucion,
                       pr.instrucciones
                FROM {tabla_pasos} AS p
                JOIN {tabla_procesos} AS pr
                    ON p.id_proceso = pr.id
                WHERE p.id_receta IN ({marcadores})
                ORDER BY p.id_receta, p.orden;
                """,
                ids_recetas,
            )
            filas_pasos = cur.fetchall()
            pasos_por_receta: Dict[int, List[PasoReceta]] = {}
            for fila in filas_pasos:
                (id_receta, orden, paso_temp, paso_tiempo, paso_vel, paso_instr,
                 pid, pnombre, ptipo, ptipo_ej, proc_instr) = fila
                
                # Polimorfismo: Instanciar la subclase correcta
                if ptipo_ej == "manual":
                    proceso = ProcesoManual(
                        id_=pid,
                        nombre=pnombre,
                        tipo=ptipo,
                        tipo_ejecucion=ptipo_ej,
                        instrucciones=proc_instr,
                        origen=origen,
                    )
                else:
                    proceso = ProcesoAutomatico(
                        id_=pid,
                        nombre=pnombre,
                        tipo=ptipo,
                        tipo_ejecucion=ptipo_ej,
                        instrucciones=proc_instr,
                        origen=origen,
                    )
                paso = PasoReceta(
                    orden=orden,
                    proceso=proceso,
                    temperatura=paso_temp,
                    tiempo_segundos=paso_tiempo,
                    velocidad=paso_vel,
                    instrucciones=paso_instr,
                )
                pasos_por_receta.setdefault(id_receta, []).append(paso)

        # 3) Construir objetos Receta
        recetas: List[Receta] = []
        for id_receta, nombre, descripcion, ingredientes_json in filas_recetas:
            pasos = pasos_por_receta.get(id_receta, [])
            
            # Parsear ingredientes JSON
            ingredientes = []
            if ingredientes_json:
                try:
                    ingredientes = json.loads(ingredientes_json)
                except Exception:
                    pass
            
            # Polimorfismo: Instanciar la subclase correcta según origen
            if origen == "base":
                receta = RecetaBase(
                    id_=id_receta,
                    nombre=nombre,
                    descripcion=descripcion or "",
                    ingredientes=ingredientes,
                    pasos=pasos,
                )
            else:
                receta = RecetaUsuario(
                    id_=id_receta,
                    nombre=nombre,
                    descripcion=descripcion or "",
                    ingredientes=ingredientes,
                    pasos=pasos,
                )
            recetas.append(receta)

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
        tabla_pasos="pasos_receta_base",
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
        tabla_pasos="pasos_receta_usuario",
        tabla_procesos="procesos_usuario",
        origen="usuario",
    )


def crear_receta_usuario(
    nombre: str,
    descripcion: str,
    ingredientes: List[Dict[str, Any]],
    pasos: List[Tuple[int, int, Optional[int], Optional[int], Optional[int], Optional[str]]],
) -> Receta:
    """
    Crea una nueva receta de usuario.

    CAMBIO IMPORTANTE: Ahora acepta pasos con parámetros de ejecución.

    Parámetros:
        nombre: nombre de la receta
        descripcion: texto descriptivo
        ingredientes: lista de dicts con {nombre, cantidad, unidad, nota}
        pasos: lista de tuplas (orden, id_proceso, temperatura, tiempo_segundos, velocidad, instrucciones)
               por ejemplo: [
                   (1, 3, None, None, None, "Añadir ingredientes secos"),  # Manual
                   (2, 5, 100, 180, 2, None),  # Automático
               ]

    Devuelve:
        Objeto Receta con sus pasos (cada paso incluye ProcesoCocina origen='usuario' o 'base').
    """
    conn = conectar()
    try:
        cur = conn.cursor()

        # Convertir ingredientes a JSON
        ingredientes_json = json.dumps(ingredientes, ensure_ascii=False)

        # Insertar la receta
        cur.execute(
            """
            INSERT INTO recetas_usuario (nombre, descripcion, ingredientes)
            VALUES (?, ?, ?);
            """,
            (nombre, descripcion, ingredientes_json),
        )
        id_receta = cur.lastrowid

        # Insertar los pasos CON parámetros
        for orden, id_proceso, temp, tiempo, vel, instr in pasos:
            cur.execute(
                """
                INSERT INTO pasos_receta_usuario 
                    (id_receta, id_proceso, orden, temperatura, tiempo_segundos, velocidad, instrucciones)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (id_receta, id_proceso, orden, temp, tiempo, vel, instr),
            )

        conn.commit()

        # Cargar la receta recién creada con sus pasos
        cur.execute(
            """
            SELECT id, nombre, descripcion, ingredientes
            FROM recetas_usuario
            WHERE id = ?;
            """,
            (id_receta,),
        )
        fila_receta = cur.fetchone()
        if fila_receta is None:
            raise RuntimeError("No se pudo recuperar la receta recién creada.")

        # Cargar pasos + procesos (buscar tanto en base como en usuario)
        cur.execute(
            """
            SELECT p.orden,
                   p.temperatura,
                   p.tiempo_segundos,
                   p.velocidad,
                   p.instrucciones,
                   COALESCE(pr_user.id, pr_base.id) as id,
                   COALESCE(pr_user.nombre, pr_base.nombre) as nombre,
                   COALESCE(pr_user.tipo, pr_base.tipo) as tipo,
                   COALESCE(pr_user.tipo_ejecucion, pr_base.tipo_ejecucion) as tipo_ejecucion,
                   COALESCE(pr_user.instrucciones, pr_base.instrucciones) as proc_instrucciones,
                   CASE WHEN pr_user.id IS NOT NULL THEN 'usuario' ELSE 'base' END as origen
            FROM pasos_receta_usuario AS p
            LEFT JOIN procesos_usuario AS pr_user
                ON p.id_proceso = pr_user.id
            LEFT JOIN procesos_base AS pr_base
                ON p.id_proceso = pr_base.id
            WHERE p.id_receta = ?
            ORDER BY p.orden;
            """,
            (id_receta,),
        )
        filas_pasos = cur.fetchall()

        pasos_obj: List[PasoReceta] = []
        for fila in filas_pasos:
            (orden, paso_temp, paso_tiempo, paso_vel, paso_instr,
             pid, pnombre, ptipo, ptipo_ej, proc_instr, origen) = fila
            
            # Polimorfismo: Instanciar la subclase correcta
            if ptipo_ej == "manual":
                proceso = ProcesoManual(
                    id_=pid,
                    nombre=pnombre,
                    tipo=ptipo,
                    tipo_ejecucion=ptipo_ej,
                    instrucciones=proc_instr,
                    origen=origen,
                )
            else:
                proceso = ProcesoAutomatico(
                    id_=pid,
                    nombre=pnombre,
                    tipo=ptipo,
                    tipo_ejecucion=ptipo_ej,
                    instrucciones=proc_instr,
                    origen=origen,
                )
            pasos_obj.append(
                PasoReceta(
                    orden=orden,
                    proceso=proceso,
                    temperatura=paso_temp,
                    tiempo_segundos=paso_tiempo,
                    velocidad=paso_vel,
                    instrucciones=paso_instr,
                )
            )

        # Parsear ingredientes
        ingredientes_parsed = []
        if fila_receta[3]:
            try:
                ingredientes_parsed = json.loads(fila_receta[3])
            except Exception:
                pass

        return RecetaUsuario(
            id_=id_receta,
            nombre=fila_receta[1],
            descripcion=fila_receta[2] or "",
            ingredientes=ingredientes_parsed,
            pasos=pasos_obj,
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