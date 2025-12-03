from typing import Dict, List, Tuple, Any, Optional

from nicegui import ui

from robot.modelos import (
    RobotCocina,
    EstadoRobot,
    RobotApagadoError,
    RecetaNoSeleccionadaError,
)
from robot import servicios


def _cabecera(pagina: str) -> None:
    """Barra superior común a todas las vistas."""
    with ui.header().classes('bg-primary text-white q-px-md'):
        with ui.row().classes('items-center justify-between w-full'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('soup_kitchen').classes('text-h5')
                ui.label('Robot de cocina').classes('text-h5')

            with ui.row().classes('gap-1'):
                def boton_nav(texto: str, ruta: str, actual: bool) -> None:
                    color = 'white'
                    estilos = 'text-weight-bold' if actual else 'text-weight-regular'
                    ui.button(
                        texto,
                        on_click=lambda r=ruta: ui.navigate.to(r),
                    ).props(f'flat color={color}').classes(estilos)

                boton_nav('Panel', '/', pagina == 'panel')
                boton_nav('Procesos', '/procesos', pagina == 'procesos')
                boton_nav('Recetas', '/recetas', pagina == 'recetas')


def registrar_vistas(robot: RobotCocina) -> None:
    """
    Registra las páginas de la aplicación NiceGUI.
    Debe llamarse una vez, pasando la instancia de RobotCocina que se va a controlar.
    """

    # ------------------------------------------------------------------
    # Utilidades compartidas: recetas disponibles (para el panel principal)
    # ------------------------------------------------------------------

    RECETAS_DISPONIBLES: Dict[str, object] = {}
    ULTIMA_RECETA_SELECCIONADA: dict[str, Optional[str]] = {'label': None}
    ESTADO_BARRA = {
        'completada': False,
        'ultimo_progreso': 0.0,
        'ultimo_estado': EstadoRobot.ESPERA,
    }

    def construir_etiquetas_recetas() -> List[str]:
        """
        Carga recetas de base y de usuario y devuelve una lista de labels:
        "[Base] Nombre", "[Usuario] Nombre".

        Además rellena RECETAS_DISPONIBLES[label] = Receta
        """
        RECETAS_DISPONIBLES.clear()
        etiquetas: List[str] = []

        recetas_base = servicios.cargar_recetas_base()
        for r in recetas_base:
            label = f"[Base] {r.nombre}"
            RECETAS_DISPONIBLES[label] = r
            etiquetas.append(label)

        recetas_usuario = servicios.cargar_recetas_usuario()
        for r in recetas_usuario:
            label = f"[Usuario] {r.nombre}"
            RECETAS_DISPONIBLES[label] = r
            etiquetas.append(label)

        return etiquetas

    # ------------------------------------------------------------------
    # PÁGINA PRINCIPAL
    # ------------------------------------------------------------------

    @ui.page('/')
    def pagina_principal() -> None:
        _cabecera('panel')
        ui.page_title('Robot de cocina - Panel principal')

        with ui.column().classes('q-pa-md q-gutter-md items-stretch max-w-4xl mx-auto'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('q-gutter-none'):
                    ui.label('Panel de control').classes('text-h4')
                    ui.label(
                        'Enciende el robot, selecciona una receta y controla la cocción guiada.'
                    ).classes('text-body2 text-grey-7')
                ui.icon('kitchen').classes('text-h3 text-primary')

            # --- Encendido / apagado + resumen ---
            with ui.row().classes('q-gutter-md items-stretch w-full'):
                with ui.card().classes('q-pa-md col-12 col-md-7'):
                    ui.label('Energía y estado').classes('text-h6 q-mb-xs')
                    ui.label(
                        'Controla si el robot está encendido y consulta su estado general.'
                    ).classes('text-body2 text-grey-6 q-mb-sm')

                    estado_label = ui.label('Estado: apagado').classes('text-body1 q-mb-xs')
                    receta_label = ui.label('Receta actual: (ninguna)').classes('text-body2 text-grey-7 q-mb-sm')

                    def cambiar_encendido(e):
                        if e.value:
                            robot.encender()
                            ESTADO_BARRA['completada'] = False
                            ui.notify('Robot encendido', color='positive')
                        else:
                            robot.apagar()
                            ESTADO_BARRA['completada'] = False
                            ui.notify('Robot apagado', color='warning')

                    switch_encendido = ui.switch(
                        'Robot encendido',
                        value=(robot.estado != EstadoRobot.APAGADO),  # valor inicial según estado real
                        on_change=cambiar_encendido,
                    )
                    switch_encendido.classes('q-mt-sm')

                # --- Selección de receta ---
                with ui.card().classes('q-pa-md col-12 col-md-7'):
                    ui.label('Selección de receta').classes('text-h6 q-mb-xs')
                    ui.label(
                        'Elige una receta preprogramada o una receta creada por el usuario.'
                    ).classes('text-body2 text-grey-6 q-mb-sm')

                    seleccion = {'label_receta': None}

                    select_receta = ui.select(
                        options=[],
                        label='Receta',
                        with_input=True,
                        clearable=True,
                    ).classes('w-full')

                    def refrescar_recetas():
                        """Rellena el select y restaura la selección si existe."""
                        etiquetas = construir_etiquetas_recetas()
                        select_receta.options = etiquetas
                        select_receta.disabled = not bool(etiquetas)

                        # 1) Intentar restaurar la última selección guardada
                        label_guardado = ULTIMA_RECETA_SELECCIONADA['label']
                        receta_mostrada = None

                        if label_guardado and label_guardado in etiquetas:
                            select_receta.value = label_guardado
                            seleccion['label_receta'] = label_guardado
                            receta_mostrada = RECETAS_DISPONIBLES.get(label_guardado)

                        # 2) Si no hay selección guardada pero el robot tiene receta actual,
                        #    intentar localizarla y marcarla en el select.
                        elif robot.receta_actual is not None:
                            for label, receta in RECETAS_DISPONIBLES.items():
                                if getattr(receta, 'id', None) == getattr(robot.receta_actual, 'id', object()):
                                    select_receta.value = label
                                    seleccion['label_receta'] = label
                                    receta_mostrada = receta
                                    break

                        # 3) Si no se ha podido restaurar nada, dejar el select vacío
                        if receta_mostrada:
                            receta_label.text = f"Receta actual: {receta_mostrada.nombre}"
                        else:
                            if not etiquetas:
                                seleccion['label_receta'] = None
                            select_receta.value = seleccion['label_receta']
                            if seleccion['label_receta']:
                                rec = RECETAS_DISPONIBLES.get(seleccion['label_receta'])
                                receta_label.text = f"Receta actual: {rec.nombre}" if rec else "Receta actual: (ninguna)"
                            else:
                                receta_label.text = "Receta actual: (ninguna)"

                        select_receta.update()
                        ui.notify('Recetas actualizadas', color='primary')

                    def on_cambio_receta(e):
                        label = e.value
                        seleccion['label_receta'] = label
                        ULTIMA_RECETA_SELECCIONADA['label'] = label  # guardar selección globalmente

                        receta = RECETAS_DISPONIBLES.get(label)
                        if receta:
                            receta_label.text = f"Receta actual: {receta.nombre}"
                        else:
                            receta_label.text = "Receta actual: (ninguna)"

                    select_receta.on_value_change(on_cambio_receta)

                    with ui.row().classes('q-mt-sm items-center justify-between'):
                        ui.button(
                            'Refrescar recetas',
                            on_click=refrescar_recetas,
                            color='primary',
                        ).props('unelevated')
                        ui.label(
                            'Consejo: crea tus propias recetas desde la pestaña "Recetas".'
                        ).classes('text-caption text-grey-6')

            # --- Control de cocción y progreso ---
            with ui.card().classes('q-pa-md'):
                ui.label('Cocción y progreso').classes('text-h6 q-mb-xs')
                ui.label(
                    'Inicia, pausa o cancela la cocción. Observa el progreso y el paso actual.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                barra_progreso = ui.linear_progress(
                    value=0.0,
                    show_value=False,
                    size='10px',       
                ).props('striped').classes('w-full q-mt-xs')

                with ui.row().classes('items-center justify-between q-mt-sm'):
                    progreso_label = ui.label('Progreso: 0.0 %').classes('text-body1')
                    texto_paso_label = ui.label('Paso actual: (ninguno)').classes('text-body2 text-grey-7')

                def iniciar_coccion():
                    """
                    - Si el robot está APAGADO: avisar.
                    - Si está PAUSADO: reanudar sin reiniciar progreso.
                    - Si está COCINANDO: no hacer nada, solo avisar.
                    - Si está en ESPERA: iniciar desde 0 con la receta seleccionada.
                    """
                    # 1) Robot apagado
                    if robot.estado == EstadoRobot.APAGADO:
                        ui.notify('El robot está apagado. Enciéndelo primero.', color='negative')
                        return

                    ESTADO_BARRA['completada'] = False

                    # 2) Reanudar desde pausa
                    if robot.estado == EstadoRobot.PAUSADO:
                        try:
                            robot.iniciar_coccion()
                            ui.notify('Reanudando cocción…', color='positive')
                        except Exception as ex:
                            ui.notify(f'Error al reanudar la cocción: {ex}', color='negative')
                        return

                    # 3) Si ya está cocinando, no reiniciar
                    if robot.estado == EstadoRobot.COCINANDO:
                        ui.notify('El robot ya está cocinando.', color='info')
                        return

                    # 4) Estado de espera: iniciar desde cero
                    label = seleccion['label_receta'] or ULTIMA_RECETA_SELECCIONADA['label']
                    if not label:
                        ui.notify('Selecciona una receta primero.', color='negative')
                        return

                    receta = RECETAS_DISPONIBLES.get(label)
                    if not receta:
                        ui.notify('La receta seleccionada no existe.', color='negative')
                        return

                    try:
                        # Desde ESPERA siempre seleccionamos receta e iniciamos desde 0
                        robot.seleccionar_receta(receta)
                        robot.iniciar_coccion()
                        ui.notify(f'Iniciando cocción: {receta.nombre}', color='positive')
                    except RobotApagadoError as ex:
                        ui.notify(str(ex), color='negative')
                    except RecetaNoSeleccionadaError as ex:
                        ui.notify(str(ex), color='negative')
                    except Exception as ex:
                        ui.notify(f'Error al iniciar la cocción: {ex}', color='negative')

                def pausar_coccion():
                    if robot.estado != EstadoRobot.COCINANDO:
                        ui.notify('El robot no está cocinando ahora mismo.', color='warning')
                        return
                    robot.pausar()
                    ui.notify('Pausa solicitada. Se detendrá en breve.', color='warning')

                def cancelar_coccion():
                    if robot.estado not in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, EstadoRobot.ESPERA):
                        ui.notify('No hay cocción en curso que cancelar.', color='warning')
                        return
                    robot.detener_coccion()
                    ESTADO_BARRA['completada'] = False
                    ui.notify('Cocción cancelada y progreso reiniciado.', color='warning')

                with ui.row().classes('q-mt-md q-gutter-sm'):
                    ui.button('Iniciar / Reanudar', on_click=iniciar_coccion, color='green').props('unelevated')
                    ui.button('Pausar', on_click=pausar_coccion, color='orange').props('outline')
                    ui.button('Cancelar', on_click=cancelar_coccion, color='red').props('outline')

            # --- Ajustes / reinicio de fábrica ---
            with ui.card().classes('q-pa-md'):
                ui.label('Ajustes del sistema').classes('text-h6 q-mb-xs')
                ui.label(
                    'Restablece las recetas y procesos de usuario. Los datos de fábrica se mantienen.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                def hacer_reinicio_fabrica():
                    servicios.reinicio_de_fabrica()
                    refrescar_recetas()
                    switch_encendido.value = False
                    ESTADO_BARRA['completada'] = False

                    receta_label.text = "Receta actual: (ninguna)"
                    barra_progreso.value = 0.0
                    progreso_label.text = "Progreso: 0.0 %"
                    texto_paso_label.text = "Paso actual: (ninguno)"
                    ui.notify('Reinicio de fábrica completado.', color='primary')

                ui.button(
                    'Reinicio de fábrica',
                    on_click=hacer_reinicio_fabrica,
                    color='orange',
                ).props('outline icon=restart_alt')

        # --- Timer para refrescar la UI según el estado del robot ---
        def refrescar_ui_desde_robot():
            # Estado
            estado_actual = robot.estado
            if estado_actual == EstadoRobot.APAGADO:
                estado_label.text = 'Estado: apagado'
            elif estado_actual == EstadoRobot.ESPERA:
                estado_label.text = 'Estado: en espera'
            elif estado_actual == EstadoRobot.COCINANDO:
                estado_label.text = 'Estado: cocinando'
            elif estado_actual == EstadoRobot.PAUSADO:
                estado_label.text = 'Estado: pausado'
            else:
                estado_label.text = 'Estado: error'

            # --- Lógica de barra latcheada ---
            prog_actual = float(getattr(robot, 'progreso', 0.0) or 0.0)
            prog_anterior = ESTADO_BARRA.get('ultimo_progreso', 0.0)
            estado_anterior = ESTADO_BARRA.get('ultimo_estado', EstadoRobot.ESPERA)

            # Solo intentamos marcarla como completada si aún no lo está
            if not ESTADO_BARRA.get('completada', False):
                # Caso 1: el modelo llega a 100%
                if prog_actual >= 99.9:
                    ESTADO_BARRA['completada'] = True
                # Caso 2: el modelo resetea a 0 al terminar,
                # pero veníamos de cocinando con progreso > 0
                elif (
                    estado_anterior == EstadoRobot.COCINANDO
                    and estado_actual in (EstadoRobot.ESPERA, EstadoRobot.PAUSADO)
                    and prog_anterior > 0.0
                    and prog_actual == 0.0
                ):
                    ESTADO_BARRA['completada'] = True

            # Guardamos valores para la siguiente iteración del timer
            ESTADO_BARRA['ultimo_progreso'] = prog_actual
            ESTADO_BARRA['ultimo_estado'] = estado_actual

            # Aplicar a la barra
            if ESTADO_BARRA.get('completada', False):
                barra_progreso.value = 1.0
                progreso_label.text = 'Progreso: 100.0 %'
                barra_progreso.props('color=green')
            else:
                barra_progreso.value = prog_actual / 100.0
                progreso_label.text = f'Progreso: {prog_actual:.1f} %'
                barra_progreso.props('color=primary')

            # Receta actual y paso actual
            receta = robot.receta_actual
            if receta:
                receta_label.text = f"Receta actual: {receta.nombre}"
                pasos = receta.pasos
                if pasos:
                    idx = robot.indice_paso_actual
                    if 0 <= idx < len(pasos):
                        paso = pasos[idx]
                    else:
                        paso = pasos[-1]
                    texto_paso_label.text = f"Paso actual: {paso.proceso.nombre}"
                else:
                    texto_paso_label.text = "Paso actual: (ninguno)"
            else:
                receta_label.text = "Receta actual: (ninguna)"
                texto_paso_label.text = "Paso actual: (ninguno)"

        ui.timer(interval=0.5, callback=refrescar_ui_desde_robot)

        # Al entrar en la página, cargamos las recetas
        refrescar_recetas()

    # ------------------------------------------------------------------
    # PÁGINA DE PROCESOS
    # ------------------------------------------------------------------

    @ui.page('/procesos')
    def pagina_procesos() -> None:
        _cabecera('procesos')
        ui.page_title('Robot de cocina - Procesos')

        with ui.column().classes('q-pa-md q-gutter-md max-w-5xl mx-auto'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('q-gutter-none'):
                    ui.label('Procesos de cocina').classes('text-h4')
                    ui.label(
                        'Consulta los procesos de fábrica y define tus propios procesos personalizados.'
                    ).classes('text-body2 text-grey-7')
                ui.icon('precision_manufacturing').classes('text-h3 text-primary')

            # --- Listado procesos base ---
            with ui.card().classes('q-pa-md'):
                ui.label('Procesos de fábrica').classes('text-h6 q-mb-xs')
                ui.label(
                    'Estos procesos vienen preconfigurados y no se pueden modificar ni borrar.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                columnas_procesos = [
                    {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left'},
                    {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left'},
                    {'name': 'temperatura', 'label': 'Temp (ºC)', 'field': 'temperatura', 'align': 'right'},
                    {'name': 'tiempo', 'label': 'Tiempo (s)', 'field': 'tiempo', 'align': 'right'},
                    {'name': 'velocidad', 'label': 'Vel.', 'field': 'velocidad', 'align': 'right'},
                    {'name': 'origen', 'label': 'Origen', 'field': 'origen', 'align': 'left'},
                ]

                tabla_base = ui.table(
                    columns=columnas_procesos,
                    rows=[],
                ).props('flat bordered wrap cell-class="px-4 py-2"').classes('w-full')

            # --- Procesos usuario + borrar ---
            with ui.card().classes('q-pa-md'):
                ui.label('Procesos de usuario').classes('text-h6 q-mb-xs')
                ui.label(
                    'Crea procesos que luego podrás utilizar en tus propias recetas.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                tabla_usuario = ui.table(
                    columns=columnas_procesos,
                    rows=[],
                ).props('flat bordered wrap cell-class="px-4 py-2"').classes('w-full q-mb-md')

                # Mapeo nombre -> proceso usuario (para borrar sin mostrar ID)
                procesos_usuario_por_nombre: Dict[str, object] = {}

                with ui.row().classes('items-end q-gutter-sm'):
                    select_proceso_borrar = ui.select(
                        options=[],
                        label='Proceso a eliminar',
                        clearable=True,
                    ).classes('col-12 col-md-7')

                    # Botón ancho y compacto con encadenado correcto
                    (
                        ui.button(
                            'Eliminar\nproceso seleccionado',
                            on_click=lambda: borrar_proceso(),
                            color='red',
                        )
                        .props('outline icon=delete stack no-caps')
                        .classes('col-12 col-md-4 text-center q-pa-sm')
                        .style('min-width: 260px; height: 65px;')
                    )

                def borrar_proceso():
                    nombre = select_proceso_borrar.value
                    if not nombre:
                        ui.notify('Selecciona un proceso de usuario.', color='warning')
                        return

                    proceso = procesos_usuario_por_nombre.get(nombre)
                    if not proceso:
                        ui.notify('Proceso no encontrado (puede haber cambiado).', color='negative')
                        return

                    servicios.eliminar_proceso_usuario(proceso.id)
                    ui.notify('Proceso eliminado.', color='positive')
                    refrescar_listados()

            # --- Crear proceso usuario ---
            with ui.card().classes('q-pa-md'):
                ui.label('Nuevo proceso de usuario').classes('text-h6 q-mb-xs')
                ui.label(
                    'Define parámetros básicos del proceso. Podrás reutilizarlo en tus recetas.'
                ).classes('text-body2 text-grey-6 q-mb-md')

                with ui.row().classes('q-gutter-md'):
                    input_nombre = ui.input('Nombre del proceso').classes('col-12 col-md-4')
                    input_tipo = ui.input('Tipo (preparación, cocción, amasado, etc.)').classes('col-12 col-md-7')
                    input_temp = ui.number('Temperatura (ºC, 0 si no aplica)', value=0).classes('col-12 col-md-4')

                with ui.row().classes('q-gutter-md q-mt-xs'):
                    input_tiempo = ui.number('Tiempo (segundos)', value=60).classes('col-12 col-md-4')
                    input_velocidad = ui.number('Velocidad (0 si no aplica)', value=0).classes('col-12 col-md-5')

                def crear_proceso():
                    try:
                        nombre = (input_nombre.value or '').strip()
                        tipo = (input_tipo.value or '').strip() or "generico"
                        temperatura = int(input_temp.value or 0)
                        tiempo_segundos = int(input_tiempo.value or 0)
                        velocidad = int(input_velocidad.value or 0)

                        if not nombre:
                            ui.notify('El nombre del proceso es obligatorio.', color='negative')
                            return

                        # Evitar nombres duplicados en procesos de usuario
                        procesos_usuario = servicios.cargar_procesos_usuario()
                        for p in procesos_usuario:
                            if p.nombre == nombre:
                                ui.notify('Ya existe un proceso de usuario con ese nombre.', color='negative')
                                return

                        servicios.crear_proceso_usuario(
                            nombre=nombre,
                            tipo=tipo,
                            temperatura=temperatura,
                            tiempo_segundos=tiempo_segundos,
                            velocidad=velocidad,
                        )
                        ui.notify('Proceso creado correctamente.', color='positive')

                        input_nombre.value = ''
                        input_tipo.value = ''
                        input_temp.value = 0
                        input_tiempo.value = 60
                        input_velocidad.value = 0

                        refrescar_listados()
                    except Exception as ex:
                        ui.notify(f'Error al crear proceso: {ex}', color='negative')

                ui.button('Guardar proceso', on_click=crear_proceso, color='green').props('unelevated q-mt-md')

        # --- Refrescar tablas ---
        def refrescar_listados():
            # Procesos base
            procesos_base = servicios.cargar_procesos_base()
            filas_base = [
                {
                    'nombre': p.nombre,
                    'tipo': p.tipo,
                    'temperatura': p.temperatura,
                    'tiempo': p.tiempo_segundos,
                    'velocidad': p.velocidad,
                    'origen': p.origen,
                }
                for p in procesos_base
            ]
            tabla_base.rows = filas_base
            tabla_base.update()

            # Procesos usuario
            procesos_usuario = servicios.cargar_procesos_usuario()
            filas_usuario = [
                {
                    'nombre': p.nombre,
                    'tipo': p.tipo,
                    'temperatura': p.temperatura,
                    'tiempo': p.tiempo_segundos,
                    'velocidad': p.velocidad,
                    'origen': p.origen,
                }
                for p in procesos_usuario
            ]
            tabla_usuario.rows = filas_usuario
            tabla_usuario.update()

            # Mapeo nombre -> proceso_usuario
            procesos_usuario_por_nombre.clear()
            for p in procesos_usuario:
                procesos_usuario_por_nombre[p.nombre] = p

            select_proceso_borrar.options = list(procesos_usuario_por_nombre.keys())
            select_proceso_borrar.update()

        refrescar_listados()

    # ------------------------------------------------------------------
    # PÁGINA DE RECETAS
    # ------------------------------------------------------------------

    @ui.page('/recetas')
    def pagina_recetas() -> None:
        _cabecera('recetas')
        ui.page_title('Robot de cocina - Recetas')

        with ui.column().classes('q-pa-md q-gutter-md max-w-5xl mx-auto'):
            with ui.row().classes('items-center justify-between w-full'):
                with ui.column().classes('q-gutter-none'):
                    ui.label('Recetas del robot').classes('text-h4')
                    ui.label(
                        'Explora las recetas de fábrica, crea tus propias recetas guiadas y consulta sus pasos.'
                    ).classes('text-body2 text-grey-7')
                ui.icon('menu_book').classes('text-h3 text-primary')

            columnas_recetas = [
                {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left'},
                {'name': 'descripcion', 'label': 'Descripción', 'field': 'descripcion', 'align': 'left'},
                {'name': 'origen', 'label': 'Origen', 'field': 'origen', 'align': 'left'},
            ]

            # --- Recetas base ---
            with ui.card().classes('q-pa-md'):
                ui.label('Recetas de fábrica').classes('text-h6 q-mb-xs')
                ui.label(
                    'Haz clic en una receta de fábrica para ver los pasos detallados.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                tabla_base = ui.table(
                    columns=columnas_recetas,
                    rows=[],
                ).props('flat bordered wrap cell-class="px-4 py-2"').classes('w-full')

            # --- Recetas usuario + borrar ---
            with ui.card().classes('q-pa-md'):
                ui.label('Recetas de usuario').classes('text-h6 q-mb-xs')
                ui.label(
                    'Tus propias recetas guiadas. Haz clic en una fila para ver sus pasos.'
                ).classes('text-body2 text-grey-6 q-mb-sm')

                tabla_usuario = ui.table(
                    columns=columnas_recetas,
                    rows=[],
                ).props('flat bordered wrap cell-class="px-4 py-2"').classes('w-full q-mb-md')

                recetas_base_por_nombre: Dict[str, object] = {}
                recetas_usuario_por_nombre: Dict[str, object] = {}

                with ui.row().classes('items-end q-gutter-sm'):
                    select_receta_borrar = ui.select(
                        options=[],
                        label='Receta de usuario a eliminar',
                        clearable=True,
                    ).classes('col-12 col-md-9')

                    (
                        ui.button(
                            'Eliminar\nreceta seleccionada',
                            on_click=lambda: borrar_receta(),
                            color='red',
                        )
                        .props('outline icon=delete stack no-caps')
                        .classes('col-12 col-md-4 text-center q-pa-sm')
                        .style('min-width: 260px; height: 65px;')
                    )

                def mostrar_pasos_receta(receta) -> None:
                    with ui.dialog() as dialog, ui.card():
                        ui.label(f'Pasos de "{receta.nombre}"').classes('text-h6 q-mb-xs')
                        ui.label(receta.descripcion).classes('text-body2 text-grey-7 q-mb-sm')
                        if not receta.pasos:
                            ui.label('La receta no tiene pasos definidos.')
                        else:
                            for paso in receta.pasos:
                                desc = paso.proceso.descripcion_resumida()
                                ui.label(f"{paso.orden}. {desc}")
                        ui.button('Cerrar', on_click=dialog.close).classes('q-mt-sm')
                    dialog.open()

                def _extraer_nombre_desde_evento(e: Any) -> str | None:
                    """
                    Intenta extraer el 'nombre' de la fila a partir de e.args
                    de forma robusta para varias versiones de NiceGUI.
                    """
                    args = e.args

                    # Caso 1: dict con 'row'
                    if isinstance(args, dict):
                        row = args.get('row') or args
                        if isinstance(row, dict):
                            return row.get('nombre')

                    # Caso 2: lista/tupla de argumentos
                    if isinstance(args, (list, tuple)):
                        # Buscar dict con 'nombre'
                        for item in args:
                            if isinstance(item, dict) and 'nombre' in item:
                                return item.get('nombre')
                        # En algunos ejemplos e.args[1] puede ser la fila
                        if len(args) >= 2 and isinstance(args[1], dict):
                            return args[1].get('nombre')

                    return None

                def on_click_receta_base(e):
                    nombre = _extraer_nombre_desde_evento(e)
                    if not nombre:
                        return
                    receta = recetas_base_por_nombre.get(nombre)
                    if receta:
                        mostrar_pasos_receta(receta)

                def on_click_receta_usuario(e):
                    nombre = _extraer_nombre_desde_evento(e)
                    if not nombre:
                        return
                    receta = recetas_usuario_por_nombre.get(nombre)
                    if receta:
                        mostrar_pasos_receta(receta)

                # Evento correcto: 'row-click'
                tabla_base.on('row-click', on_click_receta_base)
                tabla_usuario.on('row-click', on_click_receta_usuario)

                def borrar_receta():
                    nombre = select_receta_borrar.value
                    if not nombre:
                        ui.notify('Selecciona una receta de usuario.', color='warning')
                        return
                    receta = recetas_usuario_por_nombre.get(nombre)
                    if not receta:
                        ui.notify('Receta de usuario no encontrada.', color='negative')
                        return

                    servicios.eliminar_receta_usuario(receta.id)
                    ui.notify('Receta eliminada.', color='positive')
                    refrescar_listados_recetas()

            # --- Crear receta usuario ---
            with ui.card().classes('q-pa-md'):
                ui.label('Nueva receta de usuario').classes('text-h6 q-mb-xs')
                ui.label(
                    'Construye una receta añadiendo pasos en el orden en que deben ejecutarse.'
                ).classes('text-body2 text-grey-6 q-mb-md')

                with ui.row().classes('q-gutter-md'):
                    input_nombre = ui.input('Nombre de la receta').classes('col-12 col-md-6')
                    input_descripcion = ui.textarea('Descripción').classes('col-12')

                # Procesos (base + usuario) para formar pasos
                procesos_label_a_obj: Dict[str, object] = {}

                with ui.row().classes('q-gutter-md q-mt-sm items-end'):
                    select_proceso = ui.select(
                        options=[],
                        label='Proceso (base o usuario) a añadir',
                        clearable=True,
                    ).classes('col-12 col-md-10')

                    (
                        ui.button(
                            'Añadir\npaso',
                            on_click=lambda: anadir_paso(),
                            color='primary',
                        )
                        .props('outline icon=add stack no-caps')
                        .classes('col-12 col-md-3 text-center q-pa-sm')
                        .style('min-width: 260px; height: 65px;')
                    )

                ui.label(
                    'Los pasos se añaden al final. Puedes eliminar un paso concreto en cualquier momento.'
                ).classes('text-caption text-grey-6 q-mt-xs')

                # Lista temporal de pasos: (orden, proceso_obj)
                pasos_temp: List[Tuple[int, object]] = []

                columnas_pasos = [
                    {'name': 'orden', 'label': 'Orden', 'field': 'orden'},
                    {'name': 'proceso', 'label': 'Proceso', 'field': 'proceso'},
                    {'name': 'origen', 'label': 'Origen', 'field': 'origen'},
                ]

                tabla_pasos = ui.table(
                    columns=columnas_pasos,
                    rows=[],
                ).props('flat bordered dense').classes('w-full q-mt-md')

                with ui.row().classes('items-end q-gutter-sm q-mt-sm'):
                    select_paso_borrar = ui.select(
                        options=[],
                        label='Paso a eliminar',
                        clearable=True,
                    ).classes('col-12 col-md-6')

                    (
                        ui.button(
                            'Eliminar\npaso seleccionado',
                            on_click=lambda: eliminar_paso(),
                            color='orange',
                        )
                        .props('outline icon=delete stack no-caps')
                        .classes('col-12 col-md-4 text-center q-pa-sm')
                        .style('min-width: 260px; height: 65px;')
                    )

                def refrescar_tabla_pasos():
                    filas = [
                        {
                            'orden': idx + 1,
                            'proceso': p.nombre,
                            'origen': p.origen,
                        }
                        for idx, (_, p) in enumerate(pasos_temp)
                    ]
                    tabla_pasos.rows = filas
                    tabla_pasos.update()

                    opciones_borrar = [f"{idx + 1}. {p.nombre}" for idx, (_, p) in enumerate(pasos_temp)]
                    select_paso_borrar.options = opciones_borrar
                    select_paso_borrar.update()

                def anadir_paso():
                    label = select_proceso.value
                    if not label:
                        ui.notify('Selecciona un proceso para el paso.', color='warning')
                        return
                    proceso = procesos_label_a_obj.get(label)
                    if not proceso:
                        ui.notify('Proceso no encontrado (puede haber cambiado).', color='negative')
                        return

                    # Añadir al final: orden = len(pasos_temp) + 1
                    pasos_temp.append((len(pasos_temp) + 1, proceso))
                    refrescar_tabla_pasos()
                    ui.notify('Paso añadido.', color='positive')

                def eliminar_paso():
                    etiqueta = select_paso_borrar.value
                    if not etiqueta:
                        ui.notify('Selecciona un paso para eliminar.', color='warning')
                        return
                    try:
                        numero_str = etiqueta.split('.', 1)[0]
                        numero = int(numero_str)
                    except Exception:
                        ui.notify('Formato de paso no válido.', color='negative')
                        return

                    indice = numero - 1
                    if not (0 <= indice < len(pasos_temp)):
                        ui.notify('Paso seleccionado fuera de rango.', color='negative')
                        return

                    pasos_temp.pop(indice)
                    # Reasignar órdenes
                    pasos_temp[:] = [(idx + 1, p) for idx, (_, p) in enumerate(pasos_temp)]
                    refrescar_tabla_pasos()
                    ui.notify('Paso eliminado.', color='positive')

                def obtener_o_crear_proceso_usuario_desde_base(proceso_base) -> object:
                    """
                    A partir de un proceso base, busca si ya existe un proceso de usuario
                    con mismos parámetros; si no, lo crea y lo devuelve.
                    """
                    procesos_usuario = servicios.cargar_procesos_usuario()
                    for p in procesos_usuario:
                        if (
                            p.nombre == proceso_base.nombre
                            and p.tipo == proceso_base.tipo
                            and p.temperatura == proceso_base.temperatura
                            and p.tiempo_segundos == proceso_base.tiempo_segundos
                            and p.velocidad == proceso_base.velocidad
                        ):
                            return p

                    # No existe, lo creamos como proceso de usuario "clonado"
                    servicios.crear_proceso_usuario(
                        nombre=proceso_base.nombre,
                        tipo=proceso_base.tipo,
                        temperatura=proceso_base.temperatura,
                        tiempo_segundos=proceso_base.tiempo_segundos,
                        velocidad=proceso_base.velocidad,
                    )

                    procesos_usuario = servicios.cargar_procesos_usuario()
                    for p in procesos_usuario:
                        if (
                            p.nombre == proceso_base.nombre
                            and p.tipo == proceso_base.tipo
                            and p.temperatura == proceso_base.temperatura
                            and p.tiempo_segundos == proceso_base.tiempo_segundos
                            and p.velocidad == proceso_base.velocidad
                        ):
                            return p

                    raise RuntimeError('No se pudo localizar el proceso de usuario creado a partir del base.')

                def crear_receta():
                    nombre = (input_nombre.value or '').strip()
                    descripcion = (input_descripcion.value or '').strip()

                    if not nombre:
                        ui.notify('El nombre de la receta es obligatorio.', color='negative')
                        return
                    if not pasos_temp:
                        ui.notify('Añade al menos un paso a la receta.', color='negative')
                        return

                    # Evitar nombres duplicados en recetas de usuario
                    recetas_usuario = servicios.cargar_recetas_usuario()
                    for r in recetas_usuario:
                        if r.nombre == nombre:
                            ui.notify('Ya existe una receta de usuario con ese nombre.', color='negative')
                            return

                    # Construir lista de (orden, id_proceso_usuario)
                    pasos_para_guardar: List[Tuple[int, int]] = []
                    try:
                        for orden, proceso in pasos_temp:
                            if proceso.origen == 'usuario':
                                pasos_para_guardar.append((orden, proceso.id))
                            else:
                                # Es un proceso base; creamos/obtenemos el equivalente de usuario
                                proceso_usr = obtener_o_crear_proceso_usuario_desde_base(proceso)
                                pasos_para_guardar.append((orden, proceso_usr.id))
                    except Exception as ex:
                        ui.notify(f'Error preparando los pasos: {ex}', color='negative')
                        return

                    try:
                        servicios.crear_receta_usuario(
                            nombre=nombre,
                            descripcion=descripcion,
                            pasos=pasos_para_guardar,
                        )
                        ui.notify('Receta creada correctamente.', color='positive')

                        input_nombre.value = ''
                        input_descripcion.value = ''
                        pasos_temp.clear()
                        refrescar_tabla_pasos()
                        refrescar_listados_recetas()
                    except Exception as ex:
                        ui.notify(f'Error al crear receta: {ex}', color='negative')

                ui.button(
                    'Guardar receta',
                    on_click=crear_receta,
                    color='green',
                ).props('unelevated q-mt-md')

        # --- Refrescar tablas y opciones de selects ---
        def refrescar_listados_recetas():
            # Recetas base
            recetas_base = servicios.cargar_recetas_base()
            filas_base = [
                {
                    'nombre': r.nombre,
                    'descripcion': r.descripcion,
                    'origen': r.origen,
                }
                for r in recetas_base
            ]
            tabla_base.rows = filas_base
            tabla_base.update()

            # Recetas usuario
            recetas_usuario = servicios.cargar_recetas_usuario()
            filas_usuario = [
                {
                    'nombre': r.nombre,
                    'descripcion': r.descripcion,
                    'origen': r.origen,
                }
                for r in recetas_usuario
            ]
            tabla_usuario.rows = filas_usuario
            tabla_usuario.update()

            # Mapear nombres -> recetas
            recetas_base_por_nombre.clear()
            for r in recetas_base:
                recetas_base_por_nombre[r.nombre] = r

            recetas_usuario_por_nombre.clear()
            for r in recetas_usuario:
                recetas_usuario_por_nombre[r.nombre] = r

            select_receta_borrar.options = list(recetas_usuario_por_nombre.keys())
            select_receta_borrar.update()

            # Actualizar lista de procesos (base + usuario) para crear pasos
            procesos_label_a_obj.clear()
            procesos_base = servicios.cargar_procesos_base()
            procesos_usuario_ref = servicios.cargar_procesos_usuario()

            etiquetas_proc: List[str] = []
            for p in procesos_base:
                label = f"[Base] {p.nombre}"
                procesos_label_a_obj[label] = p
                etiquetas_proc.append(label)
            for p in procesos_usuario_ref:
                label = f"[Usuario] {p.nombre}"
                procesos_label_a_obj[label] = p
                etiquetas_proc.append(label)

            select_proceso.options = etiquetas_proc
            select_proceso.update()

        refrescar_listados_recetas()
