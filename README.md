EFDOO_NombreAlumno/
│
├─ app.py                 # Punto de entrada: lanza NiceGUI y el robot
├─ robot/
│   ├─ __init__.py
│   ├─ modelos.py         # Clases de POO: Robot, Receta, Proceso, etc.
│   └─ servicios.py       # Lógica de negocio: control del robot, recetas, etc.
├─ data/
│   ├─ robot.db           # Base de datos SQLite
│   └─ init_db.py         # Script para crear tablas e insertar datos de fábrica
├─ ui/
│   ├─ __init__.py
│   └─ vistas.py          # Páginas NiceGUI: panel, gestión recetas, ajustes...
└─ README.md