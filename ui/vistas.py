from typing import Dict, List, Optional

from nicegui import ui

from robot.modelos import (
    RobotCocina,
    EstadoRobot,
    RobotApagadoError,
    RecetaNoSeleccionadaError,
    ModoManualError,
    ConflictoEjecucionError,
)
from robot import servicios
from utils.utils_tiempo import mmss_a_segundos, segundos_a_mmss

THEME_STATE = {'dark': False}

def aplicar_tema_global():
    ui.dark_mode().value = THEME_STATE['dark']


# Paleta de colores
COLORS = {
    'primary': '#4F46E5',      # Indigo moderno
    'secondary': '#7C3AED',    # Purple
    'success': '#10B981',      # Green
    'warning': '#F59E0B',      # Amber
    'danger': '#EF4444',       # Red
    'info': '#3B82F6',         # Blue
    'dark': '#1F2937',         # Gray-800
    'light': '#F9FAFB',        # Gray-50
}

# Estilos reutilizables (consistencia de tamaños/espaciados)
CARD_BASE = '!bg-white dark:!bg-gray-800 shadow-lg rounded-xl'
CARD_MIN_H = 'min-h-[170px]'

def _card_classes(extra: str = '') -> str: 
    return f'{CARD_BASE} {CARD_MIN_H} {extra}'.strip()


def _crear_navegacion(robot: RobotCocina, refrescar_callback=None):
    """Drawer lateral de navegación moderna."""
    with ui.left_drawer(fixed=True, bordered=True).classes(
        '!bg-gradient-to-b !from-indigo-50 !to-white dark:!from-gray-800 dark:!to-gray-700 overflow-y-auto'
    ) as drawer:
        drawer.classes('shadow-lg')

        with ui.column().classes('w-full p-4 gap-2'):
            # Logo/Header
            with ui.row().classes('items-center gap-3 mb-6 pb-4 border-b border-indigo-200 dark:border-gray-700'):
                ui.icon('soup_kitchen', size='xl').classes('text-indigo-600 dark:text-indigo-400')
                with ui.column().classes('gap-0'):
                    ui.label('Robot de Cocina').classes('text-xl font-bold text-gray-800 dark:text-white')
                    ui.label('Sistema de Control').classes('text-xs text-gray-600 dark:text-gray-400')

            # Items de navegación
            def nav_item(icono: str, texto: str, ruta: str, badge: str = None):
                with ui.button(on_click=lambda r=ruta: ui.navigate.to(r)).props(
                    'flat align=left no-caps'
                ).classes('w-full justify-start'):
                    with ui.row().classes('items-center gap-3 w-full'):
                        ui.icon(icono, size='sm').classes('text-indigo-600 dark:text-indigo-400')
                        ui.label(texto).classes('text-gray-700 dark:text-gray-200 font-medium')
                        if badge:
                            ui.badge(badge, color='red').props('floating')

            nav_item('dashboard', 'Panel de Control', '/')
            nav_item('precision_manufacturing', 'Procesos', '/procesos')
            nav_item('menu_book', 'Recetas', '/recetas')

            ui.separator().classes('my-4')

            # Toggle tema
            with ui.row().classes('items-center gap-2 p-2 rounded !bg-white dark:!bg-gray-800 shadow-sm'):
                ui.icon('light_mode').classes('text-amber-500 dark:text-amber-400')

                def cambiar_tema(e):
                    THEME_STATE['dark'] = e.value
                    ui.dark_mode().value = e.value

                ui.switch(value=THEME_STATE['dark'], on_change=cambiar_tema).props('dense color=indigo').tooltip('Modo Claro / Oscuro')
                ui.icon('dark_mode').classes('text-black-600 dark:text-white')

            ui.separator().classes('my-4')

            # Zona de Ajustes en el drawer
            with ui.expansion('Ajustes', icon='settings').classes(
                'w-full rounded-xl !bg-white dark:!bg-gray-800 shadow-sm'
            ) as peligro_expansion:
                peligro_expansion.set_value(False)
                
                with ui.column().classes('p-4 gap-3'):
                    ui.label('Reinicia el robot a la configuración de fábrica').classes(
                        'text-sm text-gray-600 dark:text-gray-400 mb-3'
                    )

                    def hacer_reinicio():
                        servicios.reinicio_de_fabrica()
                        robot.apagar()
                        if refrescar_callback:
                            refrescar_callback()
                        ui.notify('Reinicio de fábrica completado.', type='positive')

                    with ui.dialog() as dialog_reset:
                        with ui.card().classes('p-6'):
                            ui.label('¿Confirmar reinicio de fábrica?').classes('text-xl font-bold mb-4')
                            ui.label('Esta acción eliminará todas las recetas y procesos de usuario.').classes(
                                'text-red-600 dark:text-red-400 mb-4'
                            )
                            with ui.row().classes('gap-2'):
                                ui.button('Cancelar', on_click=dialog_reset.close).props('flat')
                                ui.button(
                                    'Sí, resetear',
                                    on_click=lambda: [dialog_reset.close(), hacer_reinicio()]
                                ).props('unelevated color=red')

                    ui.button('Reinicio de Fábrica', on_click=dialog_reset.open).props(
                        'outline color=orange icon=restart_alt'
                    ).classes('w-full')

    return drawer


def registrar_vistas(robot: RobotCocina) -> None:
    """Registra las vistas con diseño renovado y layout consistente."""

    RECETAS_DISPONIBLES: Dict[str, object] = {}
    ULTIMA_RECETA_SELECCIONADA: dict[str, Optional[str]] = {'label': None}
    ESTADO_RECETA = {'nombre': '(ninguna)'}
    ESTADO_BARRA = {
        'completada': False,
        'ultimo_progreso': 0.0,
        'ultimo_estado': EstadoRobot.ESPERA,
        'ultimo_paso_index': -1,
        'total_pasos_receta': 0,
        'manual_estaba_activo': False,
    }
    ESTADO_COMPLETADO = {
        'mostrar': False,
        'receta_nombre': None,
        'receta_label': None
    }

    NOTIFICACIONES_MOSTRADAS = set()

    def construir_etiquetas_recetas() -> List[str]:
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
    
    def calcular_tiempo_estimado(receta):
        """Calcula el tiempo estimado de una receta usando los parámetros del PASO."""
        tiempo_total_segundos = 0
        pasos_manuales = 0

        for paso in receta.pasos:
            if paso.proceso.es_manual():
                pasos_manuales += 1
            else:
                # CAMBIO: Ahora usamos paso.tiempo_segundos en lugar de proceso.tiempo_segundos
                tiempo_total_segundos += paso.tiempo_segundos or 0

        if tiempo_total_segundos <= 0:
            return None

        horas = tiempo_total_segundos // 3600
        minutos = (tiempo_total_segundos % 3600) // 60
        segundos = tiempo_total_segundos % 60

        if horas > 0:
            tiempo_str = f"{horas}h {minutos}m"
        elif minutos > 0:
            tiempo_str = f"{minutos}m {segundos}s" if segundos > 0 else f"{minutos}m"
        else:
            tiempo_str = f"{segundos}s"

        nota_manual = (
            f" (+ {pasos_manuales} paso{'s' if pasos_manuales != 1 else ''} "
            f"manual{'es' if pasos_manuales != 1 else ''})"
            if pasos_manuales > 0 else ""
        )

        return f"Tiempo estimado: {tiempo_str}{nota_manual}"
    
    # NUEVO: Función de monitoreo mejorada
    def monitor_global_recetas():
        """
        Monitorea el robot y dispara notificaciones cuando detecta una receta completada
        o cuando el modo manual se completa.
        
        Lógica receta completada:
        1. El robot está en ESPERA (no cocinando)
        2. Hay una receta actual cargada
        3. El progreso es 0% o cercano a 100%
        4. La receta NO ha sido notificada todavía
        
        Lógica modo manual completado:
        1. El robot está en ESPERA
        2. El modo manual NO está activo (acaba de terminar)
        3. Aún no se ha notificado
        """
        estado_actual = robot.estado
        receta_actual = robot.receta_actual
        
        # ===== DETECTAR RECETA COMPLETADA =====
        # Solo notificar si hay una receta y el robot está en espera
        if estado_actual == EstadoRobot.ESPERA and receta_actual is not None:
            # Obtener progreso
            prog_actual = float(getattr(robot, 'progreso', 0.0) or 0.0)
            
            # Detectar receta completada: progreso en 0 o cercano a 100
            # (el robot resetea a 0 después de completar)
            receta_completada = (prog_actual >= 99.0) or (prog_actual == 0.0 and ESTADO_BARRA.get('ultimo_progreso', 0.0) > 50.0)
            
            if receta_completada:
                # Verificar si ya fue notificada
                receta_id = receta_actual.id
                if receta_id not in NOTIFICACIONES_MOSTRADAS:
                    # ¡Notificar!
                    NOTIFICACIONES_MOSTRADAS.add(receta_id)
                    ui.notify(
                        f'¡Receta "{receta_actual.nombre}" completada!',
                        type='positive',
                        position='top',
                        timeout=5000,
                        close_button=False
                    )
        
        # ===== DETECTAR MODO MANUAL COMPLETADO =====
        # Detectar cuando el modo manual acaba de terminar
        if estado_actual == EstadoRobot.ESPERA and not robot.manual_activo:
            # Si antes estaba activo y ahora no, significa que acaba de terminar
            if ESTADO_BARRA.get('manual_estaba_activo', False):
                # Verificar si ya fue notificada
                if 'manual_completado' not in NOTIFICACIONES_MOSTRADAS:
                    NOTIFICACIONES_MOSTRADAS.add('manual_completado')
                    ui.notify(
                        '¡Cocción manual completada!',
                        type='positive',
                        position='top',
                        timeout=5000,
                        close_button=False
                    )
                # Limpiar flag
                ESTADO_BARRA['manual_estaba_activo'] = False
        
        # Actualizar flag de manual activo para detectar transiciones
        if robot.manual_activo:
            ESTADO_BARRA['manual_estaba_activo'] = True

    # ==================================================================================
    # PANEL PRINCIPAL - DASHBOARD
    # ==================================================================================

    @ui.page('/')
    def pagina_dashboard() -> None:
        aplicar_tema_global()
        ui.page_title('Dashboard - Robot de Cocina')
        
        # Función de refresco completo para el dashboard
        def refrescar_dashboard_completo():
            refrescar_recetas()
            switch_encendido.value = False
            ESTADO_BARRA['completada'] = False
            ESTADO_BARRA['ultimo_paso_index'] = -1
            ESTADO_BARRA['total_pasos_receta'] = 0
            ESTADO_COMPLETADO['mostrar'] = False
            ESTADO_COMPLETADO['receta_nombre'] = None
            ESTADO_COMPLETADO['receta_label'] = None
            ESTADO_RECETA['nombre'] = "(ninguna)"
            NOTIFICACIONES_MOSTRADAS.clear()
            pasos_expansion.set_visibility(False)
            ingredientes_expansion.set_visibility(False)
            pasos_expansion.set_visibility(False)
            barra_progreso.value = 0.0
            progreso_label.text = "0%"
            paso_card.set_visibility(False)
            completado_card.set_visibility(False)
            boton_confirmar.set_visibility(False)
        
        drawer = _crear_navegacion(robot, refrescar_dashboard_completo)

        # Header
        with ui.header().classes('!bg-white dark:!bg-gray-900 shadow-sm'):
            with ui.row().classes('w-full items-center justify-between px-6 py-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.button(icon='menu', on_click=lambda: drawer.toggle()).props('flat dense round')
                    ui.label('Panel de Control').classes('text-2xl font-bold text-gray-800 dark:text-white')

                with ui.row().classes('items-center gap-2'):
                    ui.icon('circle', size='xs').classes('text-green-500 dark:text-green-400 animate-pulse')
                    ui.label('Sistema activo').classes('text-sm text-gray-600 dark:text-gray-400')

        # Contenedor principal
        with ui.column().classes('p-6 max-w-7xl mx-auto gap-6 w-full min-h-screen bg-gray-50 dark:bg-gray-900'):

            # ================== MODO DE OPERACIÓN ==================
            modo = {'valor': 'Guiado'}

            def on_cambio_modo(e):
                modo['valor'] = e.value
                
                if modo['valor'] == 'Manual':
                    # MODO MANUAL
                    # Mostrar card de controles manuales
                    card_controles_manual.set_visibility(True)
                    
                    # Bloquear card de receta (ya tiene el overlay)
                    select_receta.set_enabled(False)
                    boton_actualizar.set_enabled(False)
                    boton_nueva.set_enabled(False)
                    card_receta.classes(add='opacity-50 pointer-events-none')
                    mensaje_modo_manual.set_visibility(True)
                    
                    # Limpiar selección de receta
                    select_receta.value = None
                    seleccion['label_receta'] = None
                    ULTIMA_RECETA_SELECCIONADA['label'] = None
                    ESTADO_RECETA['nombre'] = "(ninguna)"
                    tiempo_row.set_visibility(False)
                    ingredientes_expansion.set_visibility(False)
                    pasos_expansion.set_visibility(False)
                    
                else:
                    # MODO GUIADO
                    # Ocultar card de controles manuales
                    card_controles_manual.set_visibility(False)
                    
                    # Habilitar card de receta
                    robot_apagado = robot.estado == EstadoRobot.APAGADO
                    select_receta.set_enabled(not robot_apagado)
                    boton_actualizar.set_enabled(not robot_apagado)
                    boton_nueva.set_enabled(not robot_apagado)
                    card_receta.classes(remove='opacity-50 pointer-events-none')
                    mensaje_modo_manual.set_visibility(False)
                    
                    # ← AGREGAR ESTO: Resetear controles manuales al salir del modo manual
                    from utils.utils_tiempo import segundos_a_mmss
                    
                    # Resetear temperatura a 0
                    estado_manual['temperatura'] = 0
                    temp_slider.value = 0
                    temp_display.text = "0°C"
                    temp_gauge.value = 0.0
                    
                    # Resetear velocidad a 0
                    estado_manual['velocidad'] = 0
                    vel_slider.value = 0
                    vel_display.text = "0"
                    vel_gauge.value = 0.0
                    
                    # Resetear tiempo a 00:00
                    estado_manual['tiempo_segundos'] = 0
                    tiempo_display.text = "00:00"
                    tiempo_gauge.value = 0.0

            # ============ BANNER DE ADVERTENCIA - ROBOT APAGADO ============
            banner_apagado = ui.card().classes(
                'w-full bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 '
                'border-l-4 border-amber-500 shadow-lg'
            )
            with banner_apagado:
                with ui.row().classes('items-center gap-4 p-4'):
                    ui.icon('power_off', size='lg').classes('text-amber-600 dark:text-amber-400')
                    with ui.column().classes('gap-1 flex-grow'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label('Robot Apagado').classes('text-xl font-bold text-amber-800 dark:text-amber-300')
                            ui.icon('warning', size='md').classes('text-amber-500 animate-pulse')
                        ui.label('Enciende el robot para comenzar a cocinar y acceder a todas las funciones.').classes(
                            'text-sm text-amber-700 dark:text-amber-400'
                        )
            
            # Mostrar banner solo si el robot está apagado
            banner_apagado.set_visibility(robot.estado == EstadoRobot.APAGADO)

            # ============ FILA 1: MÉTRICAS PRINCIPALES ============
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-3 gap-4 w-full'):

                # Card Estado del Robot (gradiente)
                with ui.card().classes(_card_classes('shadow-xl')):
                    with ui.column().classes('p-6 gap-3 h-full flex flex-col justify-between'):
                        with ui.row().classes('items-center justify-between'):
                            color_inicial = 'text-green-600' if robot.estado != EstadoRobot.APAGADO else 'text-red-600'
                            icon_power = ui.icon('power_settings_new', size='md').classes(color_inicial)
                            ui.label('Estado del Robot').classes('text-lg font-bold opacity-90')

                        estado_label = ui.label('APAGADO').classes('text-3xl font-bold')

                        def cambiar_encendido(e):
                            if e.value:
                                try:
                                    robot.encender()
                                except Exception as ex:
                                    ui.notify(f'Error al encender: {ex}', type='negative')
                                    e.value = False  # Revertir switch
                                    return
                                icon_power.classes(remove='text-red-600')
                                icon_power.classes(add='text-green-600')
                                ESTADO_BARRA['completada'] = False
                                banner_apagado.set_visibility(False)
                                ui.notify('Robot encendido', type='positive', position='top')
                            else:
                                # Si hay una cocción activa, cancelarla SIEMPRE
                                if robot.estado in (
                                    EstadoRobot.COCINANDO,
                                    EstadoRobot.PAUSADO,
                                    EstadoRobot.ESPERANDO_CONFIRMACION,
                                ):
                                    robot.detener_coccion()

                                # Ahora sí: apagar de verdad
                                try:
                                    robot.apagar()
                                except Exception as ex:
                                    ui.notify(f'Error al apagar: {ex}', type='negative')
                                    e.value = True  # Revertir switch
                                    return
                                icon_power.classes(remove='text-green-600')
                                icon_power.classes(add='text-red-600')

                                ESTADO_BARRA['completada'] = False
                                
                                # Resetear estado de completado
                                ESTADO_COMPLETADO['mostrar'] = False
                                ESTADO_COMPLETADO['receta_nombre'] = None
                                ESTADO_COMPLETADO['receta_label'] = None
                                completado_card.set_visibility(False)

                                NOTIFICACIONES_MOSTRADAS.clear()

                                # Limpiar selección de receta al apagar
                                select_receta.value = None
                                tiempo_row.set_visibility(False)
                                seleccion['label_receta'] = None
                                ULTIMA_RECETA_SELECCIONADA['label'] = None
                                ESTADO_RECETA['nombre'] = "(ninguna)"

                                ingredientes_expansion.set_visibility(False)
                                pasos_expansion.set_visibility(False)

                                barra_progreso.value = 0.0
                                progreso_label.text = "0%"

                                banner_apagado.set_visibility(True)
                                paso_auto_card.set_visibility(False)
                                
                                # Resetear selector de modo a Guiado
                                modo['valor'] = 'Guiado'
                                toggle_modo.value = 'Guiado'
                                card_controles_manual.set_visibility(False)
                                mensaje_modo_manual.set_visibility(False)
                                
                                # Resetear todos los gauges manuales a 0
                                from utils.utils_tiempo import segundos_a_mmss
                                
                                # Resetear temperatura
                                estado_manual['temperatura'] = 0
                                temp_slider.value = 0
                                temp_display.text = "0°C"
                                temp_gauge.value = 0.0
                                
                                # Resetear velocidad
                                estado_manual['velocidad'] = 0
                                vel_slider.value = 0
                                vel_display.text = "0"
                                vel_gauge.value = 0.0
                                
                                # Resetear tiempo a 00:00
                                estado_manual['tiempo_segundos'] = 0
                                tiempo_display.text = "00:00"
                                tiempo_gauge.value = 0.0

                                ui.notify('Robot apagado', type='warning', position='top')
                            refrescar_ui()

                        with ui.row().classes('items-center gap-3'):
                            ui.label('O').classes('text-xs text-gray-600 dark:text-gray-400 select-none')
                            switch_encendido = ui.switch(
                                value=(robot.estado != EstadoRobot.APAGADO),
                                on_change=cambiar_encendido
                            ).props('color=green').tooltip('O = Apagado · I = Encendido').classes('scale-125')
                            ui.label('I').classes('text-xs text-gray-600 dark:text-gray-400 select-none')

                # Card Progreso
                with ui.card().classes(_card_classes('shadow-xl')):
                    with ui.column().classes('p-6 gap-3 h-full flex flex-col justify-between'):
                        with ui.row().classes('items-center justify-between'):
                            ui.icon('schedule', size='md').classes('text-indigo-600 dark:text-indigo-400')
                            ui.label('Progreso de Cocción').classes('text-xl font-bold text-gray-800 dark:text-white')

                        progreso_label = ui.label('0%').classes('text-3xl font-bold text-indigo-500 dark:text-indigo-400')
                        barra_progreso = ui.linear_progress(value=0.0, show_value=False, size='lg').props(
                            'rounded stripe animated color=indigo'
                        ).classes('w-full')

                # Card Receta Actual
                with ui.card().classes(_card_classes('shadow-xl')):
                    with ui.column().classes('p-6 gap-4 h-full'):
                        with ui.row().classes('items-center justify-between'):
                            ui.icon('restaurant', size='md').classes('text-indigo-600 dark:text-indigo-400')
                            ui.label('Receta Actual').classes(
                                'text-lg font-semibold text-gray-700 dark:text-gray-200'
                            )

                        # Nombre receta
                        receta_label = ui.label().classes(
                            'text-xl font-medium text-gray-600 dark:text-gray-400'
                        )
                        receta_label.bind_text_from(ESTADO_RECETA, 'nombre')

                        # Bloque tiempo estimado (se controla dinámicamente)
                        tiempo_row = ui.row().classes(
                            'items-center gap-2 bg-indigo-50 dark:bg-gray-700 p-3 rounded-lg'
                        )
                        with tiempo_row:
                            ui.icon('schedule', size='sm').classes(
                                'text-indigo-600 dark:text-indigo-400'
                            )
                            tiempo_label = ui.label().classes(
                                'text-sm font-medium text-gray-700 dark:text-gray-300'
                            )

                        tiempo_row.set_visibility(False)

            # ============ FILA 2: SELECCIÓN, MODO Y CONTROL ============
            with ui.element('div').classes('grid grid-cols-1 md:grid-cols-3 gap-4 w-full'):

                # Card Selector de receta
                card_receta = ui.card().classes(_card_classes())
                with card_receta:
                    # Añadir position relative al contenedor principal
                    with ui.column().classes('p-6 gap-4 h-full flex flex-col justify-between relative'):
                        with ui.row().classes('items-center justify-between'):
                            ui.icon('menu_book', size='md').classes('text-indigo-600 dark:text-indigo-400')
                            ui.label('Seleccionar Receta').classes('text-xl font-bold text-gray-800 dark:text-white')

                        seleccion = {'label_receta': None}

                        select_receta = ui.select(
                            options=[],
                            label='Buscar y seleccionar receta',
                            with_input=True,
                            clearable=True,
                        ).props('outlined').classes('w-full min-h-[56px]')

                        with ui.row().classes('gap-2'):
                            boton_actualizar = ui.button('Actualizar Lista', on_click=lambda: refrescar_recetas(), color='indigo').props('outline icon=refresh')
                            boton_nueva = ui.button('Nueva Receta', on_click=lambda: ui.navigate.to('/recetas'), color='green').props('outline icon=add_circle')

                        # Mensaje superpuesto con position absolute
                        mensaje_modo_manual = ui.card().classes(
                            'absolute inset-0 m-4 flex items-center justify-center '
                            'bg-amber-50/95 dark:bg-amber-900/95 backdrop-blur-sm '
                            'border-2 border-amber-500 rounded-xl shadow-xl z-10'
                        )
                        with mensaje_modo_manual:
                            with ui.column().classes('items-center gap-3 p-6 text-center'):
                                ui.icon('info', size='xl').classes('text-amber-600 dark:text-amber-400')
                                ui.label('Esta función no está disponible en Modo Manual').classes(
                                    'text-lg font-bold text-amber-800 dark:text-amber-200'
                                )
                                ui.label('Cambia a Modo Guiado para seleccionar recetas').classes(
                                    'text-sm text-amber-700 dark:text-amber-300'
                                )
                        mensaje_modo_manual.set_visibility(False)     

                # Card Modo
                card_modo = ui.card().classes(_card_classes())
                with card_modo:
                    with ui.column().classes('p-6 gap-4 h-full flex flex-col justify-between'):
                        with ui.row().classes('items-center justify-between'):
                            ui.icon('tune', size='md').classes('text-indigo-600 dark:text-indigo-400')
                            ui.label('Modo de Operación').classes('text-xl font-bold text-gray-800 dark:text-white')

                        with ui.column().classes('gap-2 text-sm text-gray-600 dark:text-gray-400'):
                            ui.label('Selecciona cómo quieres cocinar.')

                            ui.label('• Modo guiado: Selecciona una receta y el robot te guiará paso a paso.')
                            ui.label('• Modo manual: Controla todo tú mismo.')

                        # Toggle Guiado / Manual (solo UI por ahora)
                        toggle_modo = ui.toggle(
                            ['Guiado', 'Manual'],
                            value='Guiado',
                            on_change=on_cambio_modo
                        ).props('unelevated toggle-color=indigo color=grey-5').classes('w-full')

                # Controles principales
                with ui.card().classes(_card_classes()):
                    with ui.column().classes('p-6 gap-4 h-full flex flex-col justify-between'):
                        with ui.row().classes('items-center justify-between'):
                            ui.icon('touch_app', size='md').classes('text-indigo-600 dark:text-indigo-400')
                            ui.label('Control de Cocción').classes('text-xl font-bold text-gray-800 dark:text-white')

                        def iniciar_coccion():
                            # Verificar modo de operación
                            if modo['valor'] == 'Manual':
                                # ===== MODO MANUAL =====
                                if robot.estado == EstadoRobot.APAGADO:
                                    ui.notify('Enciende el robot primero', type='warning')
                                    return
                                
                                # Validar que haya tiempo configurado (no 00:00)
                                if estado_manual['tiempo_segundos'] == 0:
                                    ui.notify('Debes ingresar tiempo en el temporizador antes de iniciar', type='warning')
                                    return
                                
                                # Si ya está en manual y activo, no hacer nada
                                if robot.manual_activo and robot.estado == EstadoRobot.COCINANDO:
                                    ui.notify('La cocción manual ya está en curso', type='info')
                                    return
                                
                                # Si está pausado, reanudar
                                if robot.estado == EstadoRobot.PAUSADO and robot.manual_activo:
                                    try:
                                        # Reanudar con los valores actuales
                                        robot.iniciar_manual(
                                            temperatura=estado_manual['temperatura'],
                                            velocidad=estado_manual['velocidad'],
                                            tiempo=robot.manual_tiempo_restante or estado_manual['tiempo_segundos'],
                                            forzar=True
                                        )
                                        ui.notify('Reanudando cocción manual...', type='positive')
                                    except Exception as ex:
                                        ui.notify(f'Error: {ex}', type='negative')
                                    return
                                
                                # Iniciar nueva cocción manual
                                try:
                                    forzar = False
                                    # Si hay una receta activa, preguntar
                                    if robot.estado == EstadoRobot.COCINANDO and robot.receta_actual:
                                        forzar = True  # Por ahora forzamos automáticamente
                                    
                                    robot.iniciar_manual(
                                        temperatura=estado_manual['temperatura'],
                                        velocidad=estado_manual['velocidad'],
                                        tiempo=estado_manual['tiempo_segundos'],
                                        forzar=forzar
                                    )
                                    ui.notify('Iniciando cocción manual', type='positive')
                                    
                                except ConflictoEjecucionError as ex:
                                    ui.notify(str(ex), type='warning')
                                except ModoManualError as ex:
                                    ui.notify(str(ex), type='negative')
                                except RobotApagadoError:
                                    ui.notify('El robot debe estar encendido', type='negative')
                                except Exception as ex:
                                    ui.notify(f'Error: {ex}', type='negative')
                                return

                            # ===== MODO GUIADO =====
                            # Verificar si hay una receta completada pendiente
                            if ESTADO_COMPLETADO['mostrar']:
                                ui.notify('Primero descarta la receta completada', type='warning')
                                return
                            
                            if robot.estado == EstadoRobot.APAGADO:
                                ui.notify('Enciende el robot primero', type='warning')
                                return

                            ESTADO_BARRA['completada'] = False

                            if robot.estado == EstadoRobot.ESPERANDO_CONFIRMACION:
                                try:
                                    robot.confirmar_paso_manual()
                                    ui.notify('Paso confirmado, continuando...', type='positive')
                                except Exception as ex:
                                    ui.notify(f'Error: {ex}', type='negative')
                                return
                            
                            if robot.estado == EstadoRobot.PAUSADO:
                                try:
                                    forzar = False
                                    # Si hay manual activo, forzar
                                    if robot.manual_activo:
                                        forzar = True
                                    robot.iniciar_coccion(forzar=forzar)
                                    ui.notify('Reanudando...', type='positive')
                                except ConflictoEjecucionError as ex:
                                    ui.notify(str(ex), type='warning')
                                except RobotApagadoError:
                                    ui.notify('Error: El robot debe estar encendido', type='negative')
                                except RecetaNoSeleccionadaError:
                                    ui.notify('Error: No hay receta seleccionada', type='warning')
                                except Exception as ex:
                                    ui.notify(f'Error inesperado: {ex}', type='negative')
                                return

                            if robot.estado == EstadoRobot.COCINANDO:
                                ui.notify('El robot ya está cocinando', type='info')
                                return

                            label = seleccion['label_receta'] or ULTIMA_RECETA_SELECCIONADA['label']
                            if not label:
                                ui.notify('Selecciona una receta', type='warning')
                                return

                            receta = RECETAS_DISPONIBLES.get(label)
                            if not receta:
                                ui.notify('Receta no encontrada', type='negative')
                                return

                            try:
                                forzar = False
                                # Si hay manual activo, forzar
                                if robot.manual_activo:
                                    forzar = True
                                    
                                robot.seleccionar_receta(receta)
                                robot.iniciar_coccion(forzar=forzar)
                                ui.notify(f'Iniciando: {receta.nombre}', type='positive')
                            except ConflictoEjecucionError as ex:
                                ui.notify(str(ex), type='warning')
                            except RobotApagadoError:
                                ui.notify('El robot debe estar encendido para cocinar', type='negative')
                            except RecetaNoSeleccionadaError:
                                ui.notify('Error al seleccionar la receta', type='warning')
                            except Exception as ex:
                                ui.notify(f'Error inesperado: {ex}', type='negative')

                        def pausar_coccion():
                            if robot.estado != EstadoRobot.COCINANDO:
                                ui.notify('No está cocinando', type='warning')
                                return
                            robot.pausar()
                            ui.notify('Pausando...', type='info')

                        def cancelar_coccion():
                            # Validar que el robot está en un estado de cocción
                            if robot.estado not in (
                                EstadoRobot.COCINANDO,
                                EstadoRobot.PAUSADO,
                                EstadoRobot.ESPERANDO_CONFIRMACION
                            ):
                                ui.notify('No hay cocción en curso', type='warning')
                                return
                            
                            robot.detener_coccion()

                            # Restablecer selección de receta
                            select_receta.value = None
                            tiempo_row.set_visibility(False)
                            seleccion['label_receta'] = None
                            ULTIMA_RECETA_SELECCIONADA['label'] = None
                            ESTADO_RECETA['nombre'] = "(ninguna)"

                            # Ocultar receta actual
                            ingredientes_expansion.set_visibility(False)
                            pasos_expansion.set_visibility(False)
                            
                            ESTADO_BARRA['completada'] = False
                            ESTADO_BARRA['ultimo_progreso'] = 0.0
                            ESTADO_BARRA['ultimo_estado'] = EstadoRobot.ESPERA
                            ESTADO_BARRA['ultimo_paso_index'] = -1
                            ESTADO_BARRA['total_pasos_receta'] = 0 
                            
                            # Resetear estado de completado
                            ESTADO_COMPLETADO['mostrar'] = False
                            ESTADO_COMPLETADO['receta_nombre'] = None
                            ESTADO_COMPLETADO['receta_label'] = None
                            completado_card.set_visibility(False)

                            barra_progreso.value = 0.0
                            progreso_label.text = "0%"

                            paso_card.set_visibility(False)
                            paso_auto_card.set_visibility(False)
                            paso_label.text = 'Paso Actual'
                            boton_confirmar.set_visibility(False)
                            
                            # Resetear controles manuales a 0 (incluido el tiempo a 00:00)
                            from utils.utils_tiempo import segundos_a_mmss
                            
                            # Resetear temperatura
                            estado_manual['temperatura'] = 0
                            temp_slider.value = 0
                            temp_display.text = "0°C"
                            temp_gauge.value = 0.0
                            
                            # Resetear velocidad
                            estado_manual['velocidad'] = 0
                            vel_slider.value = 0
                            vel_display.text = "0"
                            vel_gauge.value = 0.0
                            
                            # Resetear tiempo a 00:00
                            estado_manual['tiempo_segundos'] = 0
                            tiempo_display.text = "00:00"
                            tiempo_gauge.value = 0.0

                            # Desbloquear cards de selección y modo
                            set_cards_bloqueadas(False)

                            ui.notify('Cocción cancelada', type='warning')

                        # Diálogo de confirmación para cancelar
                        with ui.dialog() as dialog_cancelar:
                            with ui.card().classes('p-6'):
                                ui.label('¿Cancelar cocción?').classes('text-xl font-bold mb-4')
                                ui.label('Se perderá el progreso actual de la receta.').classes('text-orange-600 dark:text-orange-400 mb-4')
                                
                                with ui.row().classes('gap-2 justify-end'):
                                    ui.button('No', on_click=dialog_cancelar.close).props('flat')
                                    ui.button(
                                        'Sí, cancelar',
                                        on_click=lambda: [dialog_cancelar.close(), cancelar_coccion()]
                                    ).props('unelevated color=red icon=stop')

                        def abrir_dialogo_cancelar():
                            # Validar estado antes de abrir el diálogo
                            if robot.estado not in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, EstadoRobot.ESPERANDO_CONFIRMACION):
                                ui.notify('No hay cocción en curso', type='warning')
                                return
                            dialog_cancelar.open()

                        with ui.column().classes('gap-2 w-full'):
                            boton_iniciar = ui.button('INICIAR / REANUDAR', on_click=iniciar_coccion).props(
                                'unelevated color=green icon=play_arrow size=lg'
                            ).classes('w-full')
                            boton_pausar = ui.button('PAUSAR', on_click=pausar_coccion).props(
                                'outline color=orange icon=pause'
                            ).classes('w-full')
                            boton_cancelar = ui.button('CANCELAR', on_click=abrir_dialogo_cancelar).props(
                                'outline color=red icon=stop'
                            ).classes('w-full')

            # ============ CONTROLES MANUALES CON GAUGES ============
            card_controles_manual = ui.card().classes(
                'w-full !bg-gradient-to-br !from-slate-50 !to-gray-100 '
                'dark:!from-gray-800 dark:!to-gray-900 '
                'shadow-2xl !border-2 !border-purple-200 dark:!border-purple-800 rounded-2xl'
            )
            
            with card_controles_manual:
                with ui.column().classes('p-8 gap-6 w-full'):
                    # ===== HEADER =====
                    with ui.row().classes('items-center justify-between w-full'):
                        with ui.row().classes('items-center gap-3'):
                            ui.icon('tune', size='xl').classes('text-purple-600 dark:text-purple-400')
                            ui.label('Controles Manuales').classes('text-3xl font-bold text-gray-800 dark:text-white')
                    
                    ui.separator().classes('my-2')
                    
                    # Estado de parámetros
                    estado_manual = {
                        'temperatura': 0,
                        'velocidad': 0,
                        'tiempo_segundos': 0,
                    }
                    
                    # ===== GRID DE GAUGES (3 columnas) =====
                    with ui.element('div').classes('grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl mx-auto'):
                        
                        # ========== TEMPERATURA ==========
                        with ui.column().classes('items-center gap-4'):
                            ui.label('Temperatura').classes('text-xl font-bold text-gray-700 dark:text-gray-300')
                            
                            # Contenedor del gauge circular
                            with ui.column().classes('relative items-center justify-center'):
                                # Gauge circular
                                temp_gauge = ui.circular_progress(
                                    value=0.0,
                                    min=0,
                                    max=1,
                                    size='180px',
                                    show_value=False
                                ).props('color=red thickness=0.15 track-color=grey-4').classes('mb-4')
                                
                                # Valor en el centro - NEGRO/BLANCO según tema
                                with ui.element('div').classes('absolute inset-0 flex items-center justify-center'):
                                    temp_display = ui.label('0°C').classes(
                                        'text-4xl font-bold text-gray-700 dark:text-gray-300'
                                    )
                            
                            # Slider debajo del gauge con botones horizontales
                            with ui.row().classes('items-center gap-3 w-full justify-center'):
                                ui.button(icon='remove', on_click=lambda: ajustar_temp(-5)).props(
                                    'flat dense round size=sm color=red'
                                )
                                
                                def on_temp_change(e):
                                    valor = int(e.value)
                                    estado_manual['temperatura'] = valor
                                    temp_display.text = f"{valor}°C"
                                    temp_gauge.value = valor / 120.0
                                    
                                    if robot.manual_activo:
                                        try:
                                            robot.ajustar_manual(temperatura=valor)
                                        except Exception as ex:
                                            ui.notify(f'Error: {ex}', type='negative')
                                
                                temp_slider = ui.slider(
                                    min=0, max=120, step=5, value=0,
                                    on_change=on_temp_change
                                ).props('color=red').classes('w-48')
                                
                                ui.button(icon='add', on_click=lambda: ajustar_temp(5)).props(
                                    'flat dense round size=sm color=red'
                                )
                            
                            def ajustar_temp(delta):
                                nuevo = max(0, min(120, estado_manual['temperatura'] + delta))
                                temp_slider.value = nuevo
                                on_temp_change(type('obj', (), {'value': nuevo})())
                        
                        # ========== TIEMPO ==========
                        with ui.column().classes('items-center gap-4'):
                            ui.label('Tiempo').classes('text-xl font-bold text-gray-700 dark:text-gray-300')
                            
                            # Gauge circular
                            with ui.column().classes('relative items-center justify-center'):
                                tiempo_gauge = ui.circular_progress(
                                    value=0.0,
                                    min=0,
                                    max=1,
                                    size='180px',
                                    show_value=False
                                ).props('color=orange thickness=0.15 track-color=grey-4').classes('mb-4')
                                
                                # Valor en el centro - NEGRO/BLANCO según tema
                                with ui.element('div').classes('absolute inset-0 flex items-center justify-center'):
                                    tiempo_display = ui.label('00:00').classes(
                                        'text-4xl font-bold text-gray-700 dark:text-gray-300'
                                    )
                            
                            # Botones de ajuste (2 filas)
                            with ui.column().classes('gap-3 items-center'):
                                # Fila 1: -10s, -1m, -10m
                                with ui.row().classes('gap-3'):
                                    ui.button('-10m', on_click=lambda: ajustar_tiempo(-600)).props(
                                        'outline size=md color=orange'
                                    ).classes('min-w-[75px]')
                                    ui.button('-1m', on_click=lambda: ajustar_tiempo(-60)).props(
                                        'outline size=md color=orange'
                                    ).classes('min-w-[75px]')
                                    ui.button('-10s', on_click=lambda: ajustar_tiempo(-10)).props(
                                        'outline size=md color=orange'
                                    ).classes('min-w-[75px]')
                                
                                # Fila 2: +10s, +1m, +10m
                                with ui.row().classes('gap-3'):
                                    ui.button('+10s', on_click=lambda: ajustar_tiempo(10)).props(
                                        'unelevated size=md color=orange'
                                    ).classes('min-w-[75px]')
                                    ui.button('+1m', on_click=lambda: ajustar_tiempo(60)).props(
                                        'unelevated size=md color=orange'
                                    ).classes('min-w-[75px]')
                                    ui.button('+10m', on_click=lambda: ajustar_tiempo(600)).props(
                                        'unelevated size=md color=orange'
                                    ).classes('min-w-[75px]')
                            
                            def ajustar_tiempo(delta_segundos):
                                from utils.utils_tiempo import segundos_a_mmss
                                nuevo_tiempo = max(0, min(5400, estado_manual['tiempo_segundos'] + delta_segundos))
                                estado_manual['tiempo_segundos'] = nuevo_tiempo
                                tiempo_str = segundos_a_mmss(nuevo_tiempo)
                                tiempo_display.text = tiempo_str
                                tiempo_gauge.value = nuevo_tiempo / 5400.0
                                
                                if robot.manual_activo:
                                    try:
                                        robot.ajustar_manual(tiempo=nuevo_tiempo)
                                    except Exception as ex:
                                        ui.notify(f'Error: {ex}', type='negative')
                        
                        # ========== VELOCIDAD ==========
                        with ui.column().classes('items-center gap-4'):
                            ui.label('Velocidad').classes('text-xl font-bold text-gray-700 dark:text-gray-300')
                            
                            # Gauge circular
                            with ui.column().classes('relative items-center justify-center'):
                                vel_gauge = ui.circular_progress(
                                    value=0.0,
                                    min=0,
                                    max=1,
                                    size='180px',
                                    show_value=False
                                ).props('color=blue thickness=0.15 track-color=grey-4').classes('mb-4')
                                
                                # Valor en el centro - NEGRO/BLANCO según tema
                                with ui.element('div').classes('absolute inset-0 flex items-center justify-center'):
                                    vel_display = ui.label('0').classes(
                                        'text-4xl font-bold text-gray-700 dark:text-gray-300'
                                    )
                            
                            # Slider debajo del gauge con botones horizontales
                            with ui.row().classes('items-center gap-3 w-full justify-center'):
                                ui.button(icon='remove', on_click=lambda: ajustar_vel(-1)).props(
                                    'flat dense round size=sm color=blue'
                                )
                                
                                def on_vel_change(e):
                                    valor = int(e.value)
                                    estado_manual['velocidad'] = valor
                                    vel_display.text = str(valor)
                                    vel_gauge.value = valor / 10.0
                                    
                                    if robot.manual_activo:
                                        try:
                                            robot.ajustar_manual(velocidad=valor)
                                        except Exception as ex:
                                            ui.notify(f'Error: {ex}', type='negative')
                                
                                vel_slider = ui.slider(
                                    min=0, max=10, step=1, value=0,
                                    on_change=on_vel_change
                                ).props('color=blue').classes('w-48')
                                
                                ui.button(icon='add', on_click=lambda: ajustar_vel(1)).props(
                                    'flat dense round size=sm color=blue'
                                )
                            
                            def ajustar_vel(delta):
                                nuevo = max(0, min(10, estado_manual['velocidad'] + delta))
                                vel_slider.value = nuevo
                                on_vel_change(type('obj', (), {'value': nuevo})())
            
            card_controles_manual.set_visibility(False)
            
            # ============ FILA 3: INGREDIENTES (expandible) ============
            ingredientes_expansion = ui.expansion(
                'Ingredientes Necesarios',
                icon='shopping_cart'
            ).classes('w-full rounded-xl !bg-white dark:!bg-gray-800 shadow-lg')

            with ingredientes_expansion:
                with ui.column().classes('p-4 gap-2'):
                    ingredientes_lista = ui.html('<div></div>', sanitize=False).classes('text-gray-700 dark:text-gray-300')

            ingredientes_expansion.set_visibility(False)

            # ============ FILA 3.5: PASOS (expandible) ============
            pasos_expansion = ui.expansion(
                'Pasos de la Receta',
                icon='list'
            ).classes('w-full rounded-xl !bg-white dark:!bg-gray-800 shadow-lg')

            with pasos_expansion:
                with ui.column().classes('gap-2'):
                    pasos_contenedor = ui.column().classes('space-y-3')

            pasos_expansion.set_visibility(False)

            def renderizar_pasos_receta(receta):
                """Renderiza los pasos manteniendo el diseño original."""
                # Limpiar contenido anterior
                pasos_contenedor.clear()
                
                if not receta or not getattr(receta, 'pasos', None):
                    pasos_expansion.set_visibility(False)
                    return
                
                from utils.utils_tiempo import segundos_a_mmss
                
                with pasos_contenedor:
                    for paso in receta.pasos:
                        # Contenedor del paso con borde izquierdo
                        with ui.column().classes('border-l-4 border-indigo-500 pl-4 py-2 gap-1'):
                            # Línea 1: "Paso X:" + Badge
                            with ui.row().classes('items-center gap-2'):
                                ui.label(f'Paso {paso.orden}:').classes(
                                    'font-bold text-indigo-600 dark:text-indigo-400'
                                )
                                if paso.proceso.es_manual():
                                    ui.badge('Manual').props('color=purple')
                                else:
                                    ui.badge('Automático').props('color=green')
                            
                            # Línea 2: Nombre del proceso
                            ui.label(paso.proceso.nombre).classes('font-medium')
                            
                            # Línea 3: Parámetros/Instrucciones
                            if paso.proceso.es_manual():
                                # Paso manual: icono + instrucciones en línea
                                instr = paso.instrucciones or paso.proceso.instrucciones or ""
                                if instr:
                                    with ui.row().classes('items-center gap-1'):
                                        ui.icon('edit_note').classes(
                                            'text-purple-500 dark:text-purple-400'
                                        ).style('font-size: 1.125rem')
                                        ui.label(instr).classes(
                                            'text-sm text-gray-600 dark:text-gray-400 italic'
                                        )
                            else:
                                # Paso automático: iconos + parámetros en línea horizontal
                                temp = paso.temperatura if paso.temperatura is not None else 0
                                tiempo = paso.tiempo_segundos if paso.tiempo_segundos is not None else 0
                                vel = paso.velocidad if paso.velocidad is not None else 0
                                
                                with ui.row().classes('items-center gap-2 text-sm text-gray-600 dark:text-gray-400'):
                                    # Temperatura
                                    ui.icon('thermostat').classes(
                                        'text-red-500 dark:text-red-400'
                                    ).style('font-size: 1.125rem')
                                    ui.label(f'{temp}°C')
                                    
                                    ui.label('·')
                                    
                                    # Tiempo
                                    ui.icon('timer').classes(
                                        'text-orange-500 dark:text-orange-400'
                                    ).style('font-size: 1.125rem')
                                    ui.label(segundos_a_mmss(tiempo))
                                    
                                    ui.label('·')
                                    
                                    # Velocidad
                                    ui.icon('speed').classes(
                                        'text-blue-500 dark:text-blue-400'
                                    ).style('font-size: 1.125rem')
                                    ui.label(f'{vel}')
                
                pasos_expansion.set_visibility(True)

            # ============ FILA 4: PASO ACTUAL ============
            paso_card = ui.card().classes(
                'w-full !bg-gradient-to-r !from-purple-50 !to-pink-50 '
                'dark:!from-gray-800 dark:!to-gray-900 '
                'shadow-xl !border-2 !border-purple-300 dark:!border-purple-700 rounded-xl'
            )

            with paso_card:
                with ui.column().classes('p-6 gap-4'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('list', size='lg').classes('text-purple-600 dark:text-purple-400')
                        paso_label = ui.label('Paso Actual').classes('text-2xl font-bold text-gray-800 dark:text-white')

                    instrucciones_label = ui.label('').classes('text-lg text-gray-700 dark:text-gray-300')

                    boton_confirmar = ui.button(
                        'CONFIRMAR Y CONTINUAR',
                        on_click=lambda: confirmar_paso()
                    ).props('unelevated color=green size=xl icon=check_circle').classes('w-full')
                    boton_confirmar.set_visibility(False)

            paso_card.set_visibility(False)

            def confirmar_paso():
                robot.confirmar_paso_manual()
                ui.notify('Paso confirmado, continuando...', type='positive')
                boton_confirmar.set_visibility(False)
                paso_card.set_visibility(False)

            # ============ FILA 4.5: PASO AUTOMÁTICO ============
            paso_auto_card = ui.card().classes(
                'w-full bg-gradient-to-r from-green-50 to-emerald-50 '
                'dark:from-gray-800 dark:to-gray-900 '
                'shadow-xl border-2 border-green-300 dark:border-green-700 rounded-xl'
            )
            with paso_auto_card:
                with ui.column().classes('p-6 gap-5'):

                    # 🔹 Título: Paso X/Y: Nombre
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('list', size='lg').classes('text-green-600 dark:text-green-400')
                        paso_auto_titulo = ui.label(
                            'Paso 1/1: -'
                        ).classes('text-2xl font-bold text-gray-800 dark:text-white')

                    # 🔹 Parámetros del paso (temperatura, velocidad, tiempo restante)
                    with ui.row().classes('w-full justify-around items-center gap-4 !bg-white dark:!bg-gray-700 p-4 rounded-lg'):
                        # Temperatura
                        with ui.column().classes('items-center gap-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('thermostat', size='sm').classes('text-red-500 dark:text-red-400')
                                ui.label('Temperatura').classes('text-xs text-gray-600 dark:text-gray-400')
                            paso_auto_temperatura = ui.label('0°C').classes(
                                'text-lg font-bold text-gray-800 dark:text-white'
                            )
                        
                        # Tiempo restante
                        with ui.column().classes('items-center gap-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('timer', size='sm').classes('text-orange-500 dark:text-orange-400')
                                ui.label('Tiempo restante').classes('text-xs text-gray-600 dark:text-gray-400')
                            paso_auto_tiempo_restante = ui.label('00:00').classes(
                                'text-lg font-bold text-gray-800 dark:text-white'
                            )

                        # Velocidad
                        with ui.column().classes('items-center gap-1'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('speed', size='sm').classes('text-blue-500 dark:text-blue-400')
                                ui.label('Velocidad').classes('text-xs text-gray-600 dark:text-gray-400')
                            paso_auto_velocidad = ui.label('0').classes(
                                'text-lg font-bold text-gray-800 dark:text-white'
                            )

                    # 🔹 Zona de progreso (porcentaje + barra)
                    with ui.column().classes('w-full gap-2'):

                        # Porcentaje centrado
                        paso_auto_progreso = ui.label('0%').classes(
                            'text-lg font-semibold text-green-700 dark:text-green-400 text-center'
                        )

                        # Barra de progreso más alta y ancha
                        paso_auto_barra = ui.linear_progress(
                            value=0.0,
                            show_value=False,
                            size='lg',
                        ).props(
                            'rounded stripe animated color=green'
                        ).classes('w-full')

            paso_auto_card.set_visibility(False)

            # ============ FILA 5: RECETA COMPLETADA ============
            completado_card = ui.card().classes(
                'w-full bg-gradient-to-r from-emerald-50 to-green-50 '
                'dark:from-emerald-900/30 dark:to-green-900/30 '
                'shadow-2xl border-4 border-emerald-400 dark:border-emerald-600 rounded-2xl'
            )
            with completado_card:
                with ui.column().classes('p-8 gap-6 w-full h-full items-center justify-center text-center'):
                    # Ícono de éxito
                    with ui.row().classes('items-center justify-center gap-4'):
                        ui.icon('check_circle', size='3xl').classes('text-emerald-600 dark:text-emerald-400 animate-pulse')
                        completado_titulo = ui.label('¡Receta Completada!').classes(
                            'text-4xl font-bold text-emerald-700 dark:text-emerald-300'
                        )
                        ui.icon('check_circle', size='3xl').classes('text-emerald-600 dark:text-emerald-400 animate-pulse')
                    
                    # Nombre de la receta completada
                    completado_receta = ui.label(' ').classes(
                        'text-2xl font-semibold text-gray-700 dark:text-gray-300 text-center min-h-[2.5rem]'
                    )
                    
                    # Mensaje
                    ui.label('La cocción ha finalizado exitosamente').classes(
                        'text-lg text-gray-600 dark:text-gray-400 text-center'
                    )
                    
                    # Botón para descartar
                    def descartar_completado():
                        # Limpiar el flag en el robot
                        robot.limpiar_receta_completada()
                        
                        # Limpiar estado de completado en la UI
                        ESTADO_COMPLETADO['mostrar'] = False
                        ESTADO_COMPLETADO['receta_nombre'] = None
                        ESTADO_COMPLETADO['receta_label'] = None

                        NOTIFICACIONES_MOSTRADAS.clear()
                        
                        # Ocultar card
                        completado_card.set_visibility(False)
                        
                        # Limpiar selección de receta
                        select_receta.value = None
                        tiempo_row.set_visibility(False)
                        seleccion['label_receta'] = None
                        ULTIMA_RECETA_SELECCIONADA['label'] = None
                        ESTADO_RECETA['nombre'] = "(ninguna)"
                        
                        # Ocultar expansiones
                        ingredientes_expansion.set_visibility(False)
                        pasos_expansion.set_visibility(False)
                        
                        # Resetear ESTADO_BARRA completamente
                        ESTADO_BARRA['completada'] = False
                        ESTADO_BARRA['ultimo_progreso'] = 0.0
                        ESTADO_BARRA['ultimo_estado'] = EstadoRobot.ESPERA
                        ESTADO_BARRA['ultimo_paso_index'] = -1
                        ESTADO_BARRA['total_pasos_receta'] = 0
                        
                        # Resetear barra de progreso visualmente
                        barra_progreso.value = 0.0
                        progreso_label.text = "0%"
                        barra_progreso.props('color=indigo')
                        
                        # Ocultar cards de pasos
                        paso_card.set_visibility(False)
                        paso_auto_card.set_visibility(False)
                        
                        # Liberar cards bloqueadas
                        set_cards_bloqueadas(False)
                        
                        ui.notify('Listo para una nueva receta', type='positive')
                    
                    ui.button(
                        'ENTENDIDO',
                        on_click=descartar_completado
                    ).props('unelevated color=green size=xl icon=thumb_up').classes('w-full max-w-md')
            
            completado_card.set_visibility(False)

            # ============ FUNCIONES DE ACTUALIZACIÓN ============
            def actualizar_paso_automatico():
                # No actualizar si hay receta completada
                if ESTADO_COMPLETADO.get('mostrar', False):
                    paso_auto_card.set_visibility(False)
                    return
                
                receta = robot.receta_actual
                if not receta:
                    paso_auto_card.set_visibility(False)
                    return

                pasos = receta.pasos
                total_pasos = len(pasos)
                idx = robot.indice_paso_actual

                if not (0 <= idx < total_pasos):
                    paso_auto_card.set_visibility(False)
                    return

                paso = pasos[idx]

                # Si es manual, esta card no aplica
                if paso.proceso.es_manual():
                    paso_auto_card.set_visibility(False)
                    return

                # Calcular progreso del paso
                progreso_global = float(robot.progreso or 0.0)
                progreso_por_paso = 100 / total_pasos
                inicio_paso = idx * progreso_por_paso

                progreso_paso = (progreso_global - inicio_paso) / progreso_por_paso
                progreso_paso = max(0.0, min(1.0, progreso_paso))

                # Actualizar título
                paso_auto_titulo.text = f'Paso {idx + 1}/{total_pasos}: {paso.proceso.nombre}'
                
                # Actualizar parámetros del paso (vienen de PasoReceta, no del Proceso)
                temperatura = paso.temperatura if paso.temperatura is not None else 0
                velocidad = paso.velocidad if paso.velocidad is not None else 0
                tiempo_total_segundos = paso.tiempo_segundos if paso.tiempo_segundos is not None else 0
                
                paso_auto_temperatura.text = f'{temperatura}°C'
                paso_auto_velocidad.text = f'{velocidad}'
                
                # Calcular tiempo restante (cuenta atrás sincronizada con la barra)
                tiempo_transcurrido = progreso_paso * tiempo_total_segundos
                tiempo_restante_segundos = max(0, tiempo_total_segundos - tiempo_transcurrido)
                paso_auto_tiempo_restante.text = segundos_a_mmss(int(tiempo_restante_segundos))
                
                # Actualizar barra y porcentaje
                paso_auto_barra.value = progreso_paso
                paso_auto_progreso.text = f'{int(progreso_paso * 100)}%'

                paso_auto_card.set_visibility(True)

            def set_cards_bloqueadas(bloquear: bool):
                # --- Card Selección de receta ---
                # Solo permitir habilitar si estamos en modo Guiado
                if modo['valor'] == 'Guiado':
                    select_receta.set_enabled(not bloquear)
                    boton_actualizar.set_enabled(not bloquear)
                    boton_nueva.set_enabled(not bloquear)
                else:
                    # En modo manual, siempre bloqueada
                    select_receta.set_enabled(False)
                    boton_actualizar.set_enabled(False)
                    boton_nueva.set_enabled(False)

                # --- Card Modo ---
                toggle_modo.set_enabled(not bloquear)

                # --- Efecto visual ---
                if bloquear or modo['valor'] == 'Manual':
                    card_receta.classes(add='opacity-50 pointer-events-none')
                else:
                    card_receta.classes(remove='opacity-50 pointer-events-none')
                    
                if bloquear:
                    card_modo.classes(add='opacity-50 pointer-events-none')
                else:
                    card_modo.classes(remove='opacity-50 pointer-events-none')

            def refrescar_recetas():
                etiquetas = construir_etiquetas_recetas()
                select_receta.options = etiquetas
                select_receta.disabled = not bool(etiquetas)

                label_guardado = ULTIMA_RECETA_SELECCIONADA['label']
                receta_mostrada = None

                if label_guardado and label_guardado in etiquetas:
                    select_receta.value = label_guardado
                    seleccion['label_receta'] = label_guardado
                    receta_mostrada = RECETAS_DISPONIBLES.get(label_guardado)
                elif robot.receta_actual is not None:
                    for label, receta in RECETAS_DISPONIBLES.items():
                        if getattr(receta, 'id', None) == getattr(robot.receta_actual, 'id', object()):
                            select_receta.value = label
                            seleccion['label_receta'] = label
                            receta_mostrada = receta
                            break

                if receta_mostrada:
                    ESTADO_RECETA['nombre'] = receta_mostrada.nombre
                    
                    if getattr(receta_mostrada, 'ingredientes', None):
                        html_ings = '<div class="space-y-2">'
                        for ing in receta_mostrada.ingredientes:
                            nota = f' <span class="text-gray-500">({ing["nota"]})</span>' if ing.get('nota') else ''
                            html_ings += (
                                f'<div class="flex items-center gap-2">'
                                f'<span class="text-indigo-600 dark:text-indigo-400">•</span>'
                                f'<b>{ing["nombre"]}</b>: {ing["cantidad"]} {ing["unidad"]}{nota}'
                                f'</div>'
                            )
                        html_ings += '</div>'
                        ingredientes_lista.set_content(html_ings)
                        ingredientes_expansion.set_visibility(True)
                    else:
                        ingredientes_expansion.set_visibility(False)
                    
                    # Mostrar pasos de la receta
                    renderizar_pasos_receta(receta_mostrada)
                else:
                    ESTADO_RECETA['nombre'] = "(ninguna)"
                    ingredientes_expansion.set_visibility(False)
                    pasos_expansion.set_visibility(False)

                select_receta.update()
                ui.notify('Recetas actualizadas', type='info')

            def on_cambio_receta(e):
                """Maneja el cambio de receta seleccionada."""
                label = e.value
                seleccion['label_receta'] = label
                ULTIMA_RECETA_SELECCIONADA['label'] = label

                receta = RECETAS_DISPONIBLES.get(label)
                if receta:
                    ESTADO_RECETA['nombre'] = receta.nombre
                    texto_tiempo = calcular_tiempo_estimado(receta)

                    if texto_tiempo:
                        tiempo_label.text = texto_tiempo
                        tiempo_row.set_visibility(True)
                    else:
                        tiempo_row.set_visibility(False)
                    
                    # Mostrar ingredientes
                    if getattr(receta, 'ingredientes', None):
                        html_ings = '<div class="space-y-2">'
                        for ing in receta.ingredientes:
                            nota = f' <span class="text-gray-500">({ing["nota"]})</span>' if ing.get('nota') else ''
                            html_ings += (
                                f'<div class="flex items-center gap-2">'
                                f'<span class="text-indigo-600 dark:text-indigo-400">•</span>'
                                f'<b>{ing["nombre"]}</b>: {ing["cantidad"]} {ing["unidad"]}{nota}'
                                f'</div>'
                            )
                        html_ings += '</div>'
                        ingredientes_lista.set_content(html_ings)
                        ingredientes_expansion.set_visibility(True)
                    else:
                        ingredientes_expansion.set_visibility(False)
                    
                    # ========== MOSTRAR PASOS CON PARÁMETROS DEL PASO ==========
                    renderizar_pasos_receta(receta)
                else:
                    ESTADO_RECETA['nombre'] = "(ninguna)"
                    tiempo_row.set_visibility(False)
                    ingredientes_expansion.set_visibility(False)
                    pasos_expansion.set_visibility(False)

            select_receta.on_value_change(on_cambio_receta)

            def refrescar_ui():
                estado_actual = robot.estado
                
                # Obtener progreso y estados (necesarios para la barra de progreso)
                prog_actual = float(getattr(robot, 'progreso', 0.0) or 0.0)
                prog_anterior = ESTADO_BARRA.get('ultimo_progreso', 0.0)
                estado_anterior = ESTADO_BARRA.get('ultimo_estado', EstadoRobot.ESPERA)

                # DETECCIÓN SIMPLE Y DIRECTA
                # El robot nos dice explícitamente cuando completó una receta
                if robot.receta_completada and not ESTADO_COMPLETADO['mostrar']:
                    ESTADO_COMPLETADO['mostrar'] = True
                    ESTADO_COMPLETADO['receta_nombre'] = robot.nombre_receta_completada
                    ESTADO_COMPLETADO['receta_label'] = ULTIMA_RECETA_SELECCIONADA['label']
                    
                    completado_receta.text = robot.nombre_receta_completada or "Receta"
                    completado_card.set_visibility(True)
                    
                    paso_card.set_visibility(False)
                    paso_auto_card.set_visibility(False)
                    
                    # Forzar barra a 100%
                    barra_progreso.value = 1.0
                    progreso_label.text = '100%'
                    barra_progreso.props('color=green')
                    
                    # IMPORTANTE: Detener ejecución aquí para evitar que el código continúe
                    return
                
                # Si hay una receta completada pendiente, mantener las restricciones
                if ESTADO_COMPLETADO['mostrar']:
                    set_cards_bloqueadas(True)

                    barra_progreso.value = 1.0
                    progreso_label.text = '100%'
                    barra_progreso.props('color=green')

                    ESTADO_RECETA['nombre'] = ESTADO_COMPLETADO['receta_nombre']

                    if ESTADO_COMPLETADO['receta_label']:
                        select_receta.value = ESTADO_COMPLETADO['receta_label']
                        ULTIMA_RECETA_SELECCIONADA['label'] = ESTADO_COMPLETADO['receta_label']

                    if ESTADO_COMPLETADO['receta_nombre']:
                        completado_receta.text = ESTADO_COMPLETADO['receta_nombre']
                    
                    completado_card.set_visibility(True)
                    
                    # CRÍTICO: Ocultar cards de pasos TAMBIÉN AQUÍ
                    paso_card.set_visibility(False)
                    paso_auto_card.set_visibility(False)

                    estado_label.text = 'EN ESPERA'
                    estado_label.classes(
                        'text-blue-400',
                        remove='text-gray-400 text-green-400 text-yellow-400 text-purple-400 text-red-400 animate-pulse'
                    )

                    boton_iniciar.set_enabled(False)
                    boton_pausar.set_enabled(False)
                    boton_cancelar.set_enabled(False)

                    return

                coccion_activa = estado_actual in (
                    EstadoRobot.COCINANDO,
                    EstadoRobot.PAUSADO,
                    EstadoRobot.ESPERANDO_CONFIRMACION,
                )

                set_cards_bloqueadas(coccion_activa)

                estados_config = {
                    EstadoRobot.APAGADO: ('APAGADO', 'text-gray-400'),
                    EstadoRobot.ESPERA: ('EN ESPERA', 'text-blue-400'),
                    EstadoRobot.COCINANDO: ('COCINANDO', 'text-green-400 animate-pulse'),
                    EstadoRobot.PAUSADO: ('PAUSADO', 'text-yellow-400'),
                    EstadoRobot.ESPERANDO_CONFIRMACION: ('ESPERANDO CONFIRMACIÓN', 'text-purple-400 animate-pulse'),
                    EstadoRobot.ERROR: ('ERROR', 'text-red-400'),
                }

                texto, clases = estados_config.get(estado_actual, ('DESCONOCIDO', 'text-gray-400'))
                estado_label.text = texto
                estado_label.classes(
                    clases,
                    remove='text-gray-400 text-blue-400 text-green-400 text-yellow-400 text-purple-400 text-red-400 animate-pulse'
                )

                # Progreso
                # Solo marcar como completada si hay una receta activa
                if not ESTADO_BARRA.get('completada', False) and robot.receta_actual is not None:
                    if prog_actual >= 99.9:
                        ESTADO_BARRA['completada'] = True
                    elif (
                        estado_anterior == EstadoRobot.COCINANDO
                        and estado_actual in (EstadoRobot.ESPERA, EstadoRobot.PAUSADO)
                        and prog_anterior > 0.0
                        and prog_actual == 0.0
                    ):
                        ESTADO_BARRA['completada'] = True

                ESTADO_BARRA['ultimo_progreso'] = prog_actual
                ESTADO_BARRA['ultimo_estado'] = estado_actual

                if ESTADO_BARRA.get('completada', False):
                    barra_progreso.value = 1.0
                    progreso_label.text = '100%'
                    barra_progreso.props('color=green')
                else:
                    barra_progreso.value = prog_actual / 100.0
                    progreso_label.text = f'{prog_actual:.0f}%'
                    barra_progreso.props('color=indigo')

                # Habilitar/deshabilitar controles según estado del robot
                robot_apagado = estado_actual == EstadoRobot.APAGADO
                banner_apagado.set_visibility(robot_apagado)
                select_receta.set_enabled(not robot_apagado)
                boton_actualizar.set_enabled(not robot_apagado)
                boton_nueva.set_enabled(not robot_apagado)
                toggle_modo.set_enabled(not robot_apagado)
                boton_iniciar.set_enabled(not robot_apagado)
                boton_pausar.set_enabled(not robot_apagado)
                boton_cancelar.set_enabled(not robot_apagado)

                # Paso actual
                receta = robot.receta_actual
                if receta:
                    # Solo actualizar nombre si hay cocción activa
                    if estado_actual in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, EstadoRobot.ESPERANDO_CONFIRMACION):
                        ESTADO_RECETA['nombre'] = receta.nombre
                        
                        # Solo actualizar paso si estamos en cocción activa Y no hay receta completada
                        if not ESTADO_COMPLETADO['mostrar']:
                            pasos = receta.pasos
                            if pasos:
                                idx = robot.indice_paso_actual
                                if 0 <= idx < len(pasos):
                                    paso = pasos[idx]
                                    paso_label.text = f'Paso {idx+1}/{len(pasos)}: {paso.proceso.nombre}'

                                    if paso.proceso.es_manual():
                                        # Paso MANUAL
                                        # CAMBIO: Usar paso.instrucciones con fallback a proceso.instrucciones
                                        instrucciones_texto = paso.instrucciones or paso.proceso.instrucciones or "Sin instrucciones"
                                        instrucciones_label.text = instrucciones_texto
                                        paso_card.set_visibility(True)
                                        paso_auto_card.set_visibility(False)
                                    else:
                                        # Paso AUTOMÁTICO
                                        paso_card.set_visibility(False)
                                        actualizar_paso_automatico()

                                    if estado_actual == EstadoRobot.ESPERANDO_CONFIRMACION:
                                        boton_confirmar.set_visibility(True)
                                    else:
                                        boton_confirmar.set_visibility(False)
                                else:
                                    paso_card.set_visibility(False)
                                    paso_auto_card.set_visibility(False)
                                    paso_label.text = 'Paso Actual'
                                    boton_confirmar.set_visibility(False)
                            else:
                                paso_card.set_visibility(False)
                                paso_auto_card.set_visibility(False)
                                paso_label.text = 'Paso Actual'
                                boton_confirmar.set_visibility(False)
                        else:
                            # Receta completada: ocultar cards de paso
                            paso_card.set_visibility(False)
                            paso_auto_card.set_visibility(False)
                            boton_confirmar.set_visibility(False)
                    else:
                        # Si no estamos en cocción activa, resetear paso
                        paso_card.set_visibility(False)
                        paso_auto_card.set_visibility(False)
                        paso_label.text = 'Paso Actual'
                        boton_confirmar.set_visibility(False)
                else:
                    paso_card.set_visibility(False)
                    paso_auto_card.set_visibility(False)
                    paso_label.text = 'Paso Actual'
                    boton_confirmar.set_visibility(False)

                # ===== ACTUALIZAR ESTADO MANUAL =====
                if robot.manual_activo:
                    from utils.utils_tiempo import segundos_a_mmss
                    
                    # Temperatura
                    temp_slider.value = robot.manual_temperatura
                    temp_display.text = f"{robot.manual_temperatura}°C"
                    temp_gauge.value = robot.manual_temperatura / 120.0
                    
                    # Velocidad
                    vel_slider.value = robot.manual_velocidad
                    vel_display.text = str(robot.manual_velocidad)
                    vel_gauge.value = robot.manual_velocidad / 10.0
                    
                    # Tiempo
                    tiempo_restante = robot.manual_tiempo_restante
                    tiempo_str = segundos_a_mmss(tiempo_restante)
                    tiempo_display.text = tiempo_str
                    tiempo_gauge.value = tiempo_restante / 5400.0
                    
                    # Actualizar estado_manual
                    estado_manual['temperatura'] = robot.manual_temperatura
                    estado_manual['velocidad'] = robot.manual_velocidad
                    estado_manual['tiempo_segundos'] = tiempo_restante
                    
                elif ESTADO_BARRA.get('manual_estaba_activo', False):
                    # El manual acaba de terminar - mostrar 00:00 una vez más
                    tiempo_display.text = "00:00"
                    tiempo_gauge.value = 0.0
                    estado_manual['tiempo_segundos'] = 0
                else:
                    # Limpiar la flag de notificación cuando se cancela manualmente
                    if 'manual_completado' in NOTIFICACIONES_MOSTRADAS:
                        NOTIFICACIONES_MOSTRADAS.remove('manual_completado')

            # ============ RESTAURAR ESTADO MANUAL AL CARGAR ============
            def restaurar_estado_manual():
                """
                Restaura el estado del modo manual al cargar la página.
                Esto asegura persistencia si el robot está cocinando en manual
                y el usuario navega entre páginas.
                """
                if robot.manual_activo:
                    # Robot está en modo manual activo
                    modo['valor'] = 'Manual'
                    toggle_modo.value = 'Manual'
                    
                    # Mostrar card de controles
                    card_controles_manual.set_visibility(True)
                    
                    # Bloquear card de receta
                    select_receta.set_enabled(False)
                    boton_actualizar.set_enabled(False)
                    boton_nueva.set_enabled(False)
                    card_receta.classes(add='opacity-50 pointer-events-none')
                    mensaje_modo_manual.set_visibility(True)
                    
                    # Ocultar expansiones de receta
                    ingredientes_expansion.set_visibility(False)
                    pasos_expansion.set_visibility(False)
                    
                    # Actualizar valores de los controles con estado actual
                    from utils.utils_tiempo import segundos_a_mmss
                    
                    # Temperatura
                    temp_slider.value = robot.manual_temperatura
                    temp_display.text = f"{robot.manual_temperatura}°C"
                    temp_gauge.value = robot.manual_temperatura / 120.0  # ← GAUGE
                    estado_manual['temperatura'] = robot.manual_temperatura
                    
                    # Velocidad
                    vel_slider.value = robot.manual_velocidad
                    vel_display.text = str(robot.manual_velocidad)
                    vel_gauge.value = robot.manual_velocidad / 10.0  # ← GAUGE
                    estado_manual['velocidad'] = robot.manual_velocidad
                    
                    # Tiempo
                    tiempo_str = segundos_a_mmss(robot.manual_tiempo_restante)
                    tiempo_display.text = tiempo_str
                    tiempo_gauge.value = robot.manual_tiempo_restante / 5400.0  # ← GAUGE
                    estado_manual['tiempo_segundos'] = robot.manual_tiempo_restante
            # Restaurar estado inmediatamente al cargar
            restaurar_estado_manual()
            
            ui.timer(interval=0.5, callback=refrescar_ui)
            ui.timer(interval=0.5, callback=monitor_global_recetas)
            refrescar_recetas()

    # ==================================================================================
    # PÁGINA PROCESOS
    # ==================================================================================

    @ui.page('/procesos')
    def pagina_procesos() -> None:
        aplicar_tema_global()
        ui.page_title('Procesos - Robot de Cocina')
        
        # Estados para controlar la visualización de procesos
        mostrar_todos_base = {'value': False}
        mostrar_todos_usuario = {'value': False}
        
        # Función de refresco para procesos
        def refrescar_procesos_completo():
            refrescar_procesos()
        
        drawer = _crear_navegacion(robot, refrescar_procesos_completo)

        with ui.header().classes('!bg-white dark:!bg-gray-900 shadow-sm'):
            with ui.row().classes('w-full items-center justify-between px-6 py-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.button(icon='menu', on_click=lambda: drawer.toggle()).props('flat dense round')
                    ui.label('Gestión de Procesos').classes('text-2xl font-bold text-gray-800 dark:text-white')
                
                with ui.row().classes('items-center gap-2'):
                    ui.icon('circle', size='xs').classes('text-green-500 dark:text-green-400 animate-pulse')
                    ui.label('Sistema activo').classes('text-sm text-gray-600 dark:text-gray-400')

        with ui.column().classes('p-6 max-w-7xl mx-auto gap-6'):

            def mostrar_detalle_proceso(proceso):
                """Muestra un diálogo con los detalles del proceso (SIN instrucciones)."""
                with ui.dialog() as dlg, ui.card().classes('max-w-xl'):
                    with ui.column().classes('p-6 gap-4'):
                        # Título
                        ui.label(proceso.nombre).classes('text-2xl font-bold text-gray-800 dark:text-white')
                        
                        # Badge de tipo de ejecución
                        if proceso.es_manual():
                            ui.badge('MANUAL', color='purple').classes('text-white')
                        else:
                            ui.badge('AUTOMÁTICO', color='green').classes('text-white')
                        
                        ui.separator()
                        
                        # Información general
                        with ui.column().classes('gap-2'):
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('category', size='sm').classes('text-indigo-600 dark:text-indigo-400')
                                ui.label('Tipo:').classes('font-semibold')
                                ui.label(proceso.tipo.capitalize()).classes('text-gray-600 dark:text-gray-400')
                            
                            with ui.row().classes('items-center gap-2'):
                                ui.icon('source', size='sm').classes('text-indigo-600 dark:text-indigo-400')
                                ui.label('Origen:').classes('font-semibold')
                                origen_texto = 'Fábrica' if proceso.origen == 'base' else 'Usuario'
                                ui.label(origen_texto).classes('text-gray-600 dark:text-gray-400')

                        # Mensaje informativo
                        ui.separator()
                        with ui.card().classes('bg-blue-50 dark:bg-blue-900/20 p-3'):
                            with ui.row().classes('items-start gap-2'):
                                ui.icon('info', size='sm').classes('text-blue-600 dark:text-blue-400')
                                with ui.column().classes('gap-1'):
                                    ui.label('Plantilla de proceso').classes('font-semibold text-blue-800 dark:text-blue-300')
                                    if proceso.es_manual():
                                        ui.label(
                                            'Las instrucciones específicas se definen al añadir este proceso a una receta.'
                                        ).classes('text-sm text-blue-700 dark:text-blue-400')
                                    else:
                                        ui.label(
                                            'Los parámetros (temperatura, tiempo, velocidad) se definen al añadir este proceso a una receta.'
                                        ).classes('text-sm text-blue-700 dark:text-blue-400')
                        
                        # Botones de acción
                        with ui.row().classes('w-full justify-between mt-6'):
                            ui.button('Cerrar', on_click=dlg.close).props('flat')
                            
                            # SOLO permitir borrar procesos de usuario
                            if getattr(proceso, 'origen', 'usuario') == 'usuario':
                                with ui.dialog() as confirm_dialog:
                                    with ui.card().classes('p-6'):
                                        ui.label('¿Eliminar proceso?').classes('text-xl font-bold mb-2')
                                        ui.label(
                                            'Esta acción no se puede deshacer.'
                                        ).classes('text-red-600 mb-4')

                                        with ui.row().classes('gap-2 justify-end'):
                                            ui.button(
                                                'Cancelar',
                                                on_click=confirm_dialog.close
                                            ).props('flat')

                                            ui.button(
                                                'Eliminar',
                                                on_click=lambda: [
                                                    servicios.eliminar_proceso_usuario(proceso.id),
                                                    confirm_dialog.close(),
                                                    dlg.close(),
                                                    refrescar_procesos(),
                                                    ui.notify('Proceso eliminado', type='positive')
                                                ]
                                            ).props('unelevated color=red icon=delete')

                                ui.button(
                                    'Eliminar proceso',
                                    icon='delete',
                                    on_click=confirm_dialog.open,
                                ).props('unelevated color=red')
                
                dlg.open()

            with ui.card().classes('w-full shadow-xl'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center justify-between'):
                        ui.icon('factory', size='lg').classes('text-indigo-600 dark:text-indigo-400')
                        ui.label('Procesos de Fábrica').classes('text-2xl font-bold text-gray-800 dark:text-white')
                    ui.label('Procesos predefinidos del sistema (no editables). Haz clic en una fila para ver detalles.').classes('text-gray-600 dark:text-gray-400')

                    procesos_base_map = {}
                    tabla_base = ui.table(
                        columns=[
                            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left'},
                            {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left'},
                            {'name': 'tipo_ej', 'label': 'Tipo de Ejecución', 'field': 'tipo_ej', 'align': 'left'},
                        ],
                        rows=[],
                        row_key='nombre'
                    ).props('flat').classes('w-full cursor-pointer')
                    
                    tabla_base.on('row-click', lambda e: mostrar_detalle_proceso(procesos_base_map.get(e.args[1]['nombre'])))
                    
                    # Botón para expandir/contraer procesos de fábrica (DEBAJO de la tabla)
                    boton_expandir_base = ui.button(
                        'Mostrar todos los procesos',
                        icon='expand_more',
                        on_click=lambda: toggle_base()
                    ).props('flat color=indigo').classes('mt-2')
                    
                    def toggle_base():
                        mostrar_todos_base['value'] = not mostrar_todos_base['value']
                        refrescar_procesos()
                        if mostrar_todos_base['value']:
                            boton_expandir_base.props('icon=expand_less')
                            boton_expandir_base.text = 'Mostrar menos'
                        else:
                            boton_expandir_base.props('icon=expand_more')
                            boton_expandir_base.text = 'Mostrar todos los procesos'
                        boton_expandir_base.update()

            with ui.card().classes('w-full shadow-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('add_box', size='lg').classes('text-blue-600 dark:text-blue-400')
                        ui.label('Crear Nuevo Proceso').classes('text-2xl font-bold text-gray-800 dark:text-white')

                    # ========== INPUTS DEL FORMULARIO ==========
                    # CAMBIO: Solo 4 inputs (sin temperatura, tiempo, velocidad)
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        input_nombre = ui.input('Nombre').props('outlined dense').classes('col-span-2')
                        input_tipo = ui.input('Tipo (ej: Preparación, Cocción)').props('outlined dense')
                        select_tipo_ej = ui.select(
                            ['Manual', 'Automático'], 
                            label='Tipo de Ejecución', 
                            value=None
                        ).props('outlined dense')

                    # ========== FUNCIÓN CREAR PROCESO ==========
                    def crear_proceso():
                        """Crea un nuevo proceso SIN parámetros de ejecución."""
                        # Validaciones
                        nombre = (input_nombre.value or '').strip()
                        tipo = (input_tipo.value or '').strip() or "Genérico"
                        tipo_ej = select_tipo_ej.value
                        
                        if not nombre:
                            ui.notify('El nombre es obligatorio', type='negative')
                            return
                        
                        if not tipo_ej:
                            ui.notify('Selecciona un tipo de ejecución', type='negative')
                            return
                        
                        # Convertir tipo de ejecución a formato de BD
                        tipo_ej_bd = 'manual' if tipo_ej == 'Manual' else 'automatico'
                        
                        # CAMBIO: Crear proceso sin parámetros numéricos
                        try:
                            servicios.crear_proceso_usuario(
                                nombre=nombre,
                                tipo=tipo,
                                tipo_ejecucion=tipo_ej_bd,
                                instrucciones="",
                            )

                            ui.notify('Proceso creado', type='positive')
                            
                            # Limpiar inputs
                            input_nombre.value = ''
                            input_tipo.value = ''
                            select_tipo_ej.value = None
                            
                            # Refrescar tabla de procesos
                            refrescar_procesos()
                            
                        except Exception as ex:
                            ui.notify(f'Error: {ex}', type='negative')

                    # ========== BOTÓN GUARDAR ==========
                    ui.button('GUARDAR PROCESO', on_click=crear_proceso).props(
                        'unelevated color=blue size=lg icon=save'
                    ).classes('w-full')

            with ui.card().classes('w-full shadow-xl'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center justify-between'):
                        ui.icon('precision_manufacturing', size='lg').classes('text-indigo-600 dark:text-indigo-400')
                        ui.label('Mis Procesos').classes('text-2xl font-bold')
                        
                    ui.label('Procesos creados por ti. Haz clic en una fila para ver detalles.').classes('text-gray-600 dark:text-gray-400')

                    procesos_map = {}
                    tabla_usuario = ui.table(
                        columns=[
                            {'name': 'nombre', 'label': 'Nombre', 'field': 'nombre', 'align': 'left'},
                            {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo', 'align': 'left'},
                            {'name': 'tipo_ej', 'label': 'Tipo de Ejecución', 'field': 'tipo_ej', 'align': 'left'},
                        ],
                        rows=[],
                        row_key='nombre'
                    ).props('flat').classes('w-full cursor-pointer')
                    
                    tabla_usuario.on('row-click', lambda e: mostrar_detalle_proceso(procesos_map.get(e.args[1]['nombre'])))
                    
                    # Botón para expandir/contraer procesos de usuario (DEBAJO de la tabla)
                    boton_expandir_usuario = ui.button(
                        'Mostrar todos los procesos',
                        icon='expand_more',
                        on_click=lambda: toggle_usuario()
                    ).props('flat color=indigo').classes('mt-2')
                    
                    def toggle_usuario():
                        mostrar_todos_usuario['value'] = not mostrar_todos_usuario['value']
                        refrescar_procesos()
                        if mostrar_todos_usuario['value']:
                            boton_expandir_usuario.props('icon=expand_less')
                            boton_expandir_usuario.text = 'Mostrar menos'
                        else:
                            boton_expandir_usuario.props('icon=expand_more')
                            boton_expandir_usuario.text = 'Mostrar todos los procesos'
                        boton_expandir_usuario.update()

            # ========== FUNCIÓN REFRESCAR PROCESOS ==========
            def refrescar_procesos():
                """Carga los procesos y actualiza las tablas SIN datos numéricos."""
                
                # Procesos base
                procs_base = servicios.cargar_procesos_base()
                procesos_base_map.clear()
                
                # Limitar a 10 si no se ha expandido
                procs_base_a_mostrar = procs_base if mostrar_todos_base['value'] else procs_base[:10]
                
                # CAMBIO: Sin columnas numéricas
                tabla_base.rows = [
                    {
                        'nombre': p.nombre,
                        'tipo': p.tipo.capitalize(),
                        'tipo_ej': 'Manual' if p.es_manual() else 'Automático',
                    }
                    for p in procs_base_a_mostrar
                ]
                
                for p in procs_base:
                    procesos_base_map[p.nombre] = p
                
                tabla_base.update()
                
                # Actualizar visibilidad del botón de fábrica
                total_base = len(procs_base)
                if total_base > 10:
                    boton_expandir_base.set_visibility(True)
                else:
                    boton_expandir_base.set_visibility(False)

                # Procesos usuario
                procs_user = servicios.cargar_procesos_usuario()
                
                # Limitar a 10 si no se ha expandido
                procs_user_a_mostrar = procs_user if mostrar_todos_usuario['value'] else procs_user[:10]
                
                # CAMBIO: Sin columnas numéricas
                tabla_usuario.rows = [
                    {
                        'nombre': p.nombre,
                        'tipo': p.tipo.capitalize(),
                        'tipo_ej': 'Manual' if p.es_manual() else 'Automático',
                    }
                    for p in procs_user_a_mostrar
                ]
                
                tabla_usuario.update()

                procesos_map.clear()
                for p in procs_user:
                    procesos_map[p.nombre] = p
                
                # Actualizar visibilidad del botón de usuario
                total_user = len(procs_user)
                if total_user > 10:
                    boton_expandir_usuario.set_visibility(True)
                else:
                    boton_expandir_usuario.set_visibility(False)

            refrescar_procesos()
            ui.timer(interval=0.5, callback=monitor_global_recetas)

    # ==================================================================================
    # PÁGINA RECETAS
    # ==================================================================================

    @ui.page('/recetas')
    def pagina_recetas() -> None:
        aplicar_tema_global()
        ui.page_title('Recetas - Robot de Cocina')
        
        # Función de refresco para recetas
        def refrescar_recetas_completo():
            refrescar_recetas()
        
        drawer = _crear_navegacion(robot, refrescar_recetas_completo)

        with ui.header().classes('!bg-white dark:!bg-gray-900 shadow-sm'):
            with ui.row().classes('w-full items-center justify-between px-6 py-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.button(icon='menu', on_click=lambda: drawer.toggle()).props('flat dense round')
                    ui.label('Gestión de Recetas').classes('text-2xl font-bold text-gray-800 dark:text-white')
                
                with ui.row().classes('items-center gap-2'):
                    ui.icon('circle', size='xs').classes('text-green-500 dark:text-green-400 animate-pulse')
                    ui.label('Sistema activo').classes('text-sm text-gray-600 dark:text-gray-400')

        with ui.column().classes('p-6 max-w-7xl mx-auto gap-6'):

            with ui.card().classes('w-full shadow-xl'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center justify-between'):
                        ui.icon('factory', size='lg').classes('text-indigo-600 dark:text-indigo-400')
                        ui.label('Recetas de Fábrica').classes('text-2xl font-bold text-gray-800 dark:text-white')

                    recetas_base_grid = ui.row().classes('w-full gap-4 flex-wrap')

            with ui.card().classes('w-full shadow-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('add_box', size='lg').classes('text-blue-600 dark:text-blue-400')
                        ui.label('Crear Nueva Receta').classes('text-2xl font-bold')

                    input_nombre_receta = ui.input('Nombre de la receta').props('outlined dense').classes('w-full')
                    
                    input_desc_receta = ui.textarea('Descripción').props('outlined').classes('w-full')

                    with ui.row().classes('items-center justify-between'):
                        ui.icon('shopping_cart', size='md').classes('text-blue-500 dark:text-blue-400')
                        ui.label('Ingredientes').classes('text-xl font-bold')
                    ingredientes_temp = []

                    with ui.row().classes('w-full gap-2 items-end'):
                        ing_nombre = ui.input('Ingrediente').props('outlined dense').classes('flex-1')
                        ing_cant = ui.number('Cantidad', min=1).props('outlined dense').classes('w-24')
                        ing_unidad = ui.input('Unidad').props('outlined dense').classes('w-32')
                        ing_nota = ui.input('Nota (opcional)').props('outlined dense').classes('flex-1')
                        ui.button(icon='add', on_click=lambda: anadir_ing()).props('fab-mini color=green').tooltip('Añadir')

                    tabla_ings = ui.table(
                        columns=[
                            {'name': 'n', 'label': 'Ingrediente', 'field': 'n'},
                            {'name': 'c', 'label': 'Cantidad', 'field': 'c'},
                            {'name': 'u', 'label': 'Unidad', 'field': 'u'},
                            {'name': 'nt', 'label': 'Nota', 'field': 'nt'},
                            {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones'},
                        ],
                        rows=[]
                    ).props('flat dense').classes('w-full')

                    def actualizar_tabla_ings():
                        tabla_ings.rows = [
                            {
                                'n': i['nombre'],
                                'c': i['cantidad'],
                                'u': i['unidad'],
                                'nt': i['nota'],
                                'idx': idx  # <-- Muy importante para el botón de eliminar
                            }
                            for idx, i in enumerate(ingredientes_temp)
                        ]
                        tabla_ings.update()

                    def eliminar_ing(idx):
                        if 0 <= idx < len(ingredientes_temp):
                            ingredientes_temp.pop(idx)
                            actualizar_tabla_ings()
                            ui.notify('Ingrediente eliminado', type='info')

                    tabla_ings.add_slot('body-cell-acciones', r'''
                        <q-td :props="props">
                            <q-btn flat dense round icon="delete" color="red" size="sm"
                                    @click="$parent.$emit('eliminar', props.row.idx)">
                                <q-tooltip>Eliminar</q-tooltip>
                            </q-btn>
                        </q-td>
                    ''')
                    tabla_ings.on('eliminar', lambda e: eliminar_ing(e.args))

                    def anadir_ing():
                        if not ing_nombre.value:
                            ui.notify('Nombre obligatorio', type='warning')
                            return
                        ingredientes_temp.append({
                            'nombre': ing_nombre.value,
                            'cantidad': ing_cant.value,
                            'unidad': ing_unidad.value or '',
                            'nota': ing_nota.value or ''
                        })
                        actualizar_tabla_ings()  # <-- Usamos la función que asigna idx correctamente
                        # Limpiar inputs
                        ing_nombre.value = ''
                        ing_cant.value = None
                        ing_unidad.value = ''
                        ing_nota.value = ''

                    with ui.row().classes('items-center justify-between'):
                        ui.icon('list', size='md').classes('text-blue-600 dark:text-blue-400')
                        ui.label('Pasos').classes('text-xl font-bold')
                    pasos_temp = []
                    procesos_map = {}

                    with ui.row().classes('w-full gap-2 items-end'):
                        select_proc = ui.select([], label='Seleccionar proceso...').props('outlined dense').classes('flex-1')
                        ui.button(icon='add', on_click=lambda: anadir_paso()).props('fab-mini color=green').tooltip('Añadir')

                        # NUEVO: Contenedor para inputs condicionales de parámetros
                        params_container = ui.column().classes('w-full gap-2 mt-2')

                        # NUEVO: Estado para los inputs de parámetros
                        params_state = {
                            'temp': None,
                            'tiempo': None,
                            'vel': None,
                            'instr': None
                        }

                        def actualizar_inputs_parametros(proceso_label):
                            """Muestra u oculta inputs según el tipo de proceso seleccionado."""
                            params_container.clear()
                            
                            if not proceso_label:
                                return
                            
                            proceso = procesos_map.get(proceso_label)
                            if not proceso:
                                return
                            
                            with params_container:
                                if proceso.es_manual():
                                    # Proceso MANUAL: solo pedir instrucciones
                                    ui.label('Instrucciones para este paso:').classes('text-sm font-bold text-gray-700 dark:text-gray-300')
                                    params_state['instr'] = ui.textarea(
                                        'Escribe las instrucciones específicas para este paso'
                                    ).props('outlined dense').classes('w-full')
                                    
                                    # Resetear numéricos
                                    params_state['temp'] = None
                                    params_state['tiempo'] = None
                                    params_state['vel'] = None
                                else:
                                    # Proceso AUTOMÁTICO: pedir temp, tiempo, velocidad
                                    ui.label('Parámetros de ejecución:').classes('text-sm font-bold text-gray-700 dark:text-gray-300')
                                    
                                    with ui.row().classes('w-full gap-2 items-end'):
                                        params_state['temp'] = ui.number(
                                            'Temperatura (0-120°C)',
                                            min=0,
                                            max=120,
                                        ).props('outlined dense').classes('flex-1')
                                        
                                        params_state['tiempo'] = ui.input(
                                            label='Tiempo (MM:SS)',
                                            placeholder='00:00'
                                        ).props('outlined dense mask="##:##"').classes('flex-1')
                                        
                                        params_state['vel'] = ui.number(
                                            'Velocidad (0-10)',
                                            min=0,
                                            max=10,
                                        ).props('outlined dense').classes('flex-1')
                                    
                                    # Resetear instrucciones
                                    params_state['instr'] = None

                        # Conectar el cambio de proceso a la función
                        select_proc.on_value_change(lambda e: actualizar_inputs_parametros(e.value))

                    tabla_pasos = ui.table(
                        columns=[
                            {'name': 'ord', 'label': '#', 'field': 'ord','align': 'left'},
                            {'name': 'nom', 'label': 'Proceso', 'field': 'nom','align': 'left'},
                            {'name': 'tipo', 'label': 'Tipo', 'field': 'tipo','align': 'left'},
                            {'name': 'params', 'label': 'Parámetros', 'field': 'params', 'align': 'right'},
                            {'name': 'acciones', 'label': 'Acciones', 'field': 'acciones'},
                        ],
                        rows=[]
                    ).props('flat dense').classes('w-full')

                    # Slot con alineación a la derecha
                    tabla_pasos.add_slot('body-cell-params', r'''
                        <q-td :props="props" class="text-right">
                            <div v-if="props.row.params_raw.instr" class="flex items-center gap-2 justify-end">
                                <q-icon name="edit_note" size="xs" class="text-indigo-500 dark:text-indigo-400" />
                                <span class="text-sm text-gray-600 dark:text-gray-400">{{ props.row.params_raw.instr.substring(0, 30) }}...</span>
                            </div>
                            <div v-else-if="props.row.params_raw.tiempo" class="flex items-center gap-4 justify-end">
                                <div class="flex items-center gap-1">
                                    <q-icon name="thermostat" size="xs" class="text-red-500 dark:text-red-400" />
                                    <span class="text-sm text-gray-600 dark:text-gray-400">{{ props.row.params_raw.temp }}°C</span>
                                </div>
                                <div class="flex items-center gap-1">
                                    <q-icon name="timer" size="xs" class="text-orange-500 dark:text-orange-400" />
                                    <span class="text-sm text-gray-600 dark:text-gray-400">{{ props.row.params_raw.tiempo }}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                    <q-icon name="speed" size="xs" class="text-blue-500 dark:text-blue-400" />
                                    <span class="text-sm text-gray-600 dark:text-gray-400">{{ props.row.params_raw.vel }}</span>
                                </div>
                            </div>
                            <span v-else class="text-sm text-gray-600 dark:text-gray-400">-</span>
                        </q-td>
                    ''')

                    def actualizar_tabla_pasos():
                        """Muestra los pasos con sus parámetros."""
                        from utils.utils_tiempo import segundos_a_mmss
                        
                        tabla_pasos.rows = [
                            {
                                'ord': paso_dict['orden'],
                                'nom': paso_dict['proceso'].nombre,
                                'tipo': 'Manual' if paso_dict['proceso'].es_manual() else 'Automático',
                                'params': '-',  # Placeholder
                                'params_raw': {
                                    'instr': paso_dict['instr'] if paso_dict['instr'] else '',
                                    'temp': paso_dict['temp'],
                                    'tiempo': segundos_a_mmss(paso_dict['tiempo']) if paso_dict['tiempo'] else None,
                                    'vel': paso_dict['vel']
                                },
                                'idx': idx
                            }
                            for idx, paso_dict in enumerate(pasos_temp)
                        ]
                        
                        tabla_pasos.update()

                    def eliminar_paso(idx):
                        if 0 <= idx < len(pasos_temp):
                            pasos_temp.pop(idx)
                            # Reajustar el orden de los pasos restantes
                            for i, paso_dict in enumerate(pasos_temp):
                                paso_dict['orden'] = i + 1
                            actualizar_tabla_pasos()
                            ui.notify('Paso eliminado', type='info')

                    tabla_pasos.add_slot('body-cell-acciones', r'''
                        <q-td :props="props">
                            <q-btn flat dense round icon="delete" color="red" size="sm"
                                    @click="$parent.$emit('eliminar', props.row.idx)">
                                <q-tooltip>Eliminar</q-tooltip>
                            </q-btn>
                        </q-td>
                    ''')
                    tabla_pasos.on('eliminar', lambda e: eliminar_paso(e.args))

                    def anadir_paso():
                        """Añade un paso CON sus parámetros de ejecución."""
                        if not select_proc.value:
                            ui.notify('Selecciona un proceso', type='warning')
                            return
                        
                        proc = procesos_map.get(select_proc.value)
                        if not proc:
                            return
                        
                        # CAMBIO: Recoger parámetros según tipo de proceso
                        if proc.es_manual():
                            # Manual: solo instrucciones
                            instr = params_state['instr'].value if params_state['instr'] else None
                            if not instr or not instr.strip():
                                ui.notify('Las instrucciones son obligatorias para pasos manuales', type='warning')
                                return
                            
                            pasos_temp.append({
                                'orden': len(pasos_temp) + 1,
                                'proceso': proc,
                                'temp': None,
                                'tiempo': None,
                                'vel': None,
                                'instr': instr.strip()
                            })
                        else:
                            # Automático: temperatura, tiempo, velocidad
                            try:
                                temp = int(params_state['temp'].value or 0)
                                tiempo_str = params_state['tiempo'].value
                                vel = int(params_state['vel'].value or 0)
                                
                                # Validar tiempo
                                if not tiempo_str or tiempo_str.strip() == '':
                                    ui.notify('El tiempo es obligatorio para pasos automáticos', type='warning')
                                    return
                                
                                from utils.utils_tiempo import mmss_a_segundos
                                tiempo_seg = mmss_a_segundos(tiempo_str)
                                
                                # Validaciones
                                if temp < 0 or temp > 120:
                                    ui.notify('Temperatura debe estar entre 0 y 120°C', type='warning')
                                    return
                                if tiempo_seg < 1:
                                    ui.notify('El tiempo debe ser mayor a 0', type='warning')
                                    return
                                if vel < 0 or vel > 10:
                                    ui.notify('Velocidad debe estar entre 0 y 10', type='warning')
                                    return
                                
                                pasos_temp.append({
                                    'orden': len(pasos_temp) + 1,
                                    'proceso': proc,
                                    'temp': temp,
                                    'tiempo': tiempo_seg,
                                    'vel': vel,
                                    'instr': None
                                })
                            except Exception as ex:
                                ui.notify(f'Error en parámetros: {ex}', type='negative')
                                return
                        
                        actualizar_tabla_pasos()
                        
                        # Limpiar inputs
                        select_proc.value = None
                        params_container.clear()

                    def crear_receta():
                        nombre = (input_nombre_receta.value or '').strip()
                        desc = (input_desc_receta.value or '').strip()

                        # Validaciones robustas
                        if not nombre:
                            ui.notify('El nombre es obligatorio', type='negative')
                            return
                        
                        if not pasos_temp or len(pasos_temp) == 0:
                            ui.notify('Debes añadir al menos un paso a la receta', type='negative')
                            return

                        try:
                            # CAMBIO: Enviar parámetros con cada paso
                            pasos_guardar = []
                            for paso_dict in pasos_temp:
                                proc = paso_dict['proceso']
                                # Si es proceso de usuario, añadir offset de 10000
                                id_proceso = proc.id
                                if getattr(proc, 'origen', 'usuario') == 'usuario':
                                    id_proceso += 10000
                                
                                pasos_guardar.append((
                                    paso_dict['orden'],
                                    id_proceso,  # ← ID con offset si es usuario
                                    paso_dict['temp'],
                                    paso_dict['tiempo'],
                                    paso_dict['vel'],
                                    paso_dict['instr']
                                ))
                            
                            servicios.crear_receta_usuario(
                                nombre=nombre,
                                descripcion=desc,
                                ingredientes=ingredientes_temp,
                                pasos=pasos_guardar
                            )

                        except Exception as ex:
                            # Si hay ERROR al guardar, NO resetear nada para que el usuario mantenga sus datos
                            ui.notify(f'Error al guardar: {ex}', type='negative')
                            return  # Salir sin resetear los campos
                        
                        # SOLO si llegamos aquí (sin errores), resetear todo el formulario
                        ui.notify('Receta creada correctamente', type='positive')
                        input_nombre_receta.value = ''
                        input_desc_receta.value = ''
                        ingredientes_temp.clear()
                        pasos_temp.clear()
                        tabla_ings.rows = []
                        tabla_pasos.rows = []
                        tabla_ings.update()
                        tabla_pasos.update()
                        refrescar_recetas()

                    ui.button('LIMPIAR FORMULARIO', on_click=lambda: [
                        setattr(input_nombre_receta, 'value', ''),
                        setattr(input_desc_receta, 'value', ''),
                        ingredientes_temp.clear(),
                        pasos_temp.clear(),
                        actualizar_tabla_ings(),
                        actualizar_tabla_pasos(),
                        ui.notify('Formulario limpiado', type='info')
                    ]).props('outline color=orange icon=clear_all').classes('w-full')

                    ui.button('GUARDAR RECETA', on_click=crear_receta).props(
                        'unelevated color=blue size=lg icon=save'
                    ).classes('w-full')

            with ui.card().classes('w-full shadow-xl'):
                with ui.column().classes('w-full p-6 gap-4'):
                    with ui.row().classes('items-center gap-2'):
                        ui.icon('menu_book', size='lg').classes('text-indigo-600 dark:text-indigo-400')
                        ui.label('Mis Recetas').classes('text-2xl font-bold')

                    recetas_user_grid = ui.row().classes('w-full gap-4 flex-wrap')

            def mostrar_detalle_receta(receta):
                """Muestra el detalle de una receta con parámetros del PASO."""
                with ui.dialog() as dlg, ui.card().classes('max-w-2xl overflow-x-hidden').props('lang=es'):
                    with ui.column().classes('p-6 gap-4'):
                        # Título y descripción
                        ui.label(receta.nombre).classes('text-3xl font-bold whitespace-normal break-words overflow-wrap-anywhere hyphens-auto')
                        ui.label(receta.descripcion).classes('text-gray-600 dark:text-gray-400 whitespace-normal break-words overflow-wrap-anywhere hyphens-auto')

                        # ========== CALCULAR TIEMPO ESTIMADO ==========
                        # CAMBIO: Usar paso.tiempo_segundos en lugar de proceso.tiempo_segundos
                        tiempo_total_segundos = 0
                        pasos_manuales = 0
                        for paso in receta.pasos:
                            if paso.proceso.es_manual():
                                pasos_manuales += 1
                            else:
                                # IMPORTANTE: Usar paso.tiempo_segundos
                                tiempo_total_segundos += paso.tiempo_segundos or 0
                        
                        # Formatear tiempo
                        if tiempo_total_segundos > 0:
                            horas = tiempo_total_segundos // 3600
                            minutos = (tiempo_total_segundos % 3600) // 60
                            segundos = tiempo_total_segundos % 60
                            
                            tiempo_str = ""
                            if horas > 0:
                                tiempo_str = f"{horas}h {minutos}m"
                            elif minutos > 0:
                                tiempo_str = f"{minutos}m {segundos}s" if segundos > 0 else f"{minutos}m"
                            else:
                                tiempo_str = f"{segundos}s"
                            
                            nota_manual = f" (+ {pasos_manuales} paso{'s' if pasos_manuales != 1 else ''} manual{'es' if pasos_manuales != 1 else ''})" if pasos_manuales > 0 else ""
                            
                            with ui.row().classes('items-center gap-2 bg-indigo-50 dark:bg-gray-700 p-3 rounded-lg'):
                                ui.icon('schedule', size='sm').classes('text-indigo-600 dark:text-indigo-400')
                                ui.label(f'Tiempo estimado: {tiempo_str}{nota_manual}').classes('text-sm font-medium text-gray-700 dark:text-gray-300')

                        # ========== INGREDIENTES ==========
                        if receta.ingredientes:
                            with ui.row().classes('items-center justify-between'):
                                ui.icon('shopping_cart', size='md').classes('text-blue-500 dark:text-blue-400')
                                ui.label('Ingredientes:').classes('text-xl font-bold')
                            for ing in receta.ingredientes:
                                nota = f" ({ing['nota']})" if ing.get('nota') else ""
                                ui.label(f"• {ing['nombre']}: {ing['cantidad']} {ing['unidad']}{nota}").classes('ml-4 whitespace-normal break-words overflow-wrap-anywhere hyphens-auto')

                        # ========== PASOS DE LA RECETA ==========
                        # CAMBIO: Mostrar parámetros del PASO, no del proceso
                        if receta.pasos:
                            with ui.row().classes('items-center justify-between'): 
                                ui.icon('list', size='md').classes('text-blue-600 dark:text-blue-400')
                                ui.label('Pasos:').classes('text-xl font-bold')
                            
                            from utils.utils_tiempo import segundos_a_mmss
                            
                            for paso in receta.pasos:
                                # Determinar icono según tipo
                                tipo_emoji = '(Manual)' if paso.proceso.es_manual() else '(Automático)'
                                
                                # Mostrar nombre del paso
                                ui.label(f"{paso.orden}. {tipo_emoji} {paso.proceso.nombre}").classes('ml-4 font-medium')
                                
                                if paso.proceso.es_manual():
                                    # PASO MANUAL: Mostrar instrucciones del PASO
                                    # Usar paso.instrucciones con fallback a proceso.instrucciones
                                    instr = paso.instrucciones or paso.proceso.instrucciones or "Sin instrucciones"
                                    with ui.row().classes('items-center gap-2'):
                                        ui.icon('edit_note', size='sm').classes('ml-8 text-indigo-600 dark:text-indigo-400')
                                        ui.label(f"{instr}").classes('text-sm text-gray-600 dark:text-gray-400 italic whitespace-normal break-words overflow-wrap-anywhere hyphens-auto')                              
                                else:
                                    # PASO AUTOMÁTICO: Mostrar parámetros del PASO
                                    # CAMBIO: Usar paso.temperatura, paso.tiempo_segundos, paso.velocidad
                                    temp = paso.temperatura if paso.temperatura is not None else 0
                                    tiempo = paso.tiempo_segundos if paso.tiempo_segundos is not None else 0
                                    vel = paso.velocidad if paso.velocidad is not None else 0
                                    
                                    with ui.row().classes('ml-4 items-center gap-6 px-4 py-1 rounded-lg'):
                                        # Temperatura
                                        with ui.row().classes('items-center gap-2'):
                                            ui.icon('thermostat', size='sm').classes('text-red-500 dark:text-red-400')
                                            ui.label(f'{temp}°C').classes('text-sm text-gray-600 dark:text-gray-400')

                                            ui.label('·')
                                        
                                        # Tiempo
                                            ui.icon('timer', size='sm').classes('text-orange-500 dark:text-orange-400')
                                            ui.label(segundos_a_mmss(tiempo)).classes('text-sm text-gray-600 dark:text-gray-400')

                                            ui.label('·')
                                        
                                        # Velocidad
                                            ui.icon('speed', size='sm').classes('text-blue-500 dark:text-blue-400')
                                            ui.label(f'{vel}').classes('text-sm text-gray-600 dark:text-gray-400')

                        # ========== BOTONES ==========
                        with ui.row().classes('w-full justify-between mt-6'):
                            ui.button('Cerrar', on_click=dlg.close).props('flat')

                            # SOLO permitir borrar recetas de usuario
                            if receta.es_editable():
                                with ui.dialog() as confirm_dialog:
                                    with ui.card().classes('p-6'):
                                        ui.label('¿Eliminar receta?').classes('text-xl font-bold mb-2')
                                        ui.label(
                                            'Esta acción no se puede deshacer.'
                                        ).classes('text-red-600 mb-4')

                                        with ui.row().classes('gap-2 justify-end'):
                                            ui.button(
                                                'Cancelar',
                                                on_click=confirm_dialog.close
                                            ).props('flat')

                                            ui.button(
                                                'Eliminar',
                                                on_click=lambda: [
                                                    servicios.eliminar_receta_usuario(receta.id),
                                                    confirm_dialog.close(),
                                                    dlg.close(),
                                                    refrescar_recetas(),
                                                    ui.notify('Receta eliminada', type='positive')
                                                ]
                                            ).props('unelevated color=red icon=delete')

                                ui.button(
                                    'Eliminar receta',
                                    icon='delete',
                                    on_click=confirm_dialog.open,
                                ).props('unelevated color=red')

                dlg.open()

            def refrescar_recetas():
                procesos_map.clear()
                procs_base = servicios.cargar_procesos_base()
                procs_usr = servicios.cargar_procesos_usuario()
                opciones = []

                for p in procs_base:
                    label = f"[Base] {p.nombre} {'(Manual)' if p.es_manual() else '(Automático)'}"
                    procesos_map[label] = p
                    opciones.append(label)

                for p in procs_usr:
                    label = f"[Usuario] {p.nombre} {'(Manual)' if p.es_manual() else '(Automático)'}"
                    procesos_map[label] = p
                    opciones.append(label)

                select_proc.options = opciones
                select_proc.update()

                recetas_base_grid.clear()
                recs_base = servicios.cargar_recetas_base()
                for rec in recs_base:
                    with recetas_base_grid:
                        with ui.card().classes(
                            'w-64 h-56 overflow-hidden cursor-pointer '
                            '!bg-white dark:!bg-gray-800 '
                            '!border !border-gray-200 dark:!border-gray-700 '
                            'hover:shadow-2xl transition-shadow '
                        ).on('click', lambda r=rec: mostrar_detalle_receta(r)):

                            with ui.column().classes('p-4 gap-2'):
                                ui.icon('restaurant', size='xl').classes('text-indigo-600 dark:text-indigo-400')
                                ui.label(rec.nombre).classes(
                                    'font-bold text-lg line-clamp-2 break-words'
                                )
                                ui.label(rec.descripcion or '').classes(
                                    'text-sm text-gray-500 line-clamp-2 break-words'
                                )
                                ui.badge(f'{len(rec.pasos)} pasos', color='indigo')

                recetas_user_grid.clear()
                recs_usr = servicios.cargar_recetas_usuario()
                for rec in recs_usr:
                    with recetas_user_grid:
                        with ui.card().classes(
                            'w-64 h-56 overflow-hidden cursor-pointer '
                            '!bg-white dark:!bg-gray-800 '
                            '!border !border-gray-200 dark:!border-gray-700 '
                            'hover:shadow-2xl transition-shadow '
                        ).on('click', lambda r=rec: mostrar_detalle_receta(r)):

                            with ui.column().classes('p-4 gap-2'):
                                ui.icon('restaurant', size='xl').classes('text-indigo-600 dark:text-indigo-400')
                                ui.label(rec.nombre).classes(
                                    'font-bold text-lg line-clamp-2 break-words'
                                )
                                ui.label(rec.descripcion or 'Sin descripción').classes(
                                    'text-sm text-gray-500 line-clamp-2 break-words'
                                )
                                ui.badge(f'{len(rec.pasos)} pasos', color='indigo')

            refrescar_recetas()
            ui.timer(interval=0.5, callback=monitor_global_recetas)