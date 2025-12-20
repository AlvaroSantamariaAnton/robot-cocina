# eliminar_todo.py
import os
import pathlib

proyecto = pathlib.Path(__file__).parent

print("Buscando y eliminando TODOS los robot.db...")
count = 0
for db in proyecto.rglob("robot.db"):
    print(f"Eliminando: {db}")
    os.remove(db)
    count += 1

print(f"\n✓ {count} archivo(s) eliminado(s)")