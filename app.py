from nicegui import ui

from robot.modelos import RobotCocina
from robot import servicios
from ui.vistas import registrar_vistas


# ====================================
# Inicialización de la base de datos
# ====================================

# Crea la BD y los datos de fábrica si no existen.
servicios.inicializar_bd_si_es_necesario()

# ===============================
# Crear instancia del robot
# ===============================

robot = RobotCocina()

# =================================
# Registrar vistas de la interfaz
# =================================

registrar_vistas(robot)

# ===============================
# Lanzar la aplicación NiceGUI
# ===============================

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='Robot de cocina')
