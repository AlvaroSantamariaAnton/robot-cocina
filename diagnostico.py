import os
import sqlite3
from data.init_db import DB_PATH, conectar

print("="*60)
print("DIAGNÓSTICO DE BASE DE DATOS")
print("="*60)

# 1. Verificar ruta
print(f"\n1. Ruta de BD configurada: {DB_PATH}")
print(f"   ¿Existe el archivo? {os.path.exists(DB_PATH)}")

# 2. Buscar TODOS los robot.db
print("\n2. Buscando todos los robot.db en el proyecto...")
import pathlib
proyecto = pathlib.Path(__file__).parent
for db in proyecto.rglob("robot.db"):
    print(f"   ✓ Encontrado: {db}")

# 3. Si existe, verificar estructura
if os.path.exists(DB_PATH):
    print(f"\n3. Verificando estructura de: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Verificar tabla recetas_base
    cur.execute("PRAGMA table_info(recetas_base)")
    columnas = cur.fetchall()
    print("\n   Columnas en 'recetas_base':")
    for col in columnas:
        print(f"      - {col[1]} ({col[2]})")
    
    # Verificar si existe columna ingredientes
    nombres_columnas = [col[1] for col in columnas]
    if 'ingredientes' in nombres_columnas:
        print("\n   ✅ Columna 'ingredientes' EXISTE")
    else:
        print("\n   ❌ Columna 'ingredientes' NO EXISTE")
        print("   ⚠️  LA BASE DE DATOS ES ANTIGUA!")
    
    # Verificar tabla procesos_base
    cur.execute("PRAGMA table_info(procesos_base)")
    columnas_proc = cur.fetchall()
    print("\n   Columnas en 'procesos_base':")
    for col in columnas_proc:
        print(f"      - {col[1]} ({col[2]})")
    
    nombres_col_proc = [col[1] for col in columnas_proc]
    if 'tipo_ejecucion' in nombres_col_proc:
        print("\n   ✅ Columna 'tipo_ejecucion' EXISTE")
    else:
        print("\n   ❌ Columna 'tipo_ejecucion' NO EXISTE")
        print("   ⚠️  LA BASE DE DATOS ES ANTIGUA!")
    
    # Contar procesos
    cur.execute("SELECT COUNT(*) FROM procesos_base")
    n_proc = cur.fetchone()[0]
    print(f"\n   Total procesos de fábrica: {n_proc}")
    
    # Contar recetas
    cur.execute("SELECT COUNT(*) FROM recetas_base")
    n_rec = cur.fetchone()[0]
    print(f"   Total recetas de fábrica: {n_rec}")
    
    conn.close()
else:
    print("\n3. ❌ El archivo NO EXISTE")

print("\n" + "="*60)
print("FIN DEL DIAGNÓSTICO")
print("="*60)