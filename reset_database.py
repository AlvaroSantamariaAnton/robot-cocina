#!/usr/bin/env python3
"""
Script para eliminar la base de datos existente y forzar su recreación
con la nueva estructura (ingredientes estructurados, tipos de ejecución, etc.)

USO:
    python reset_database.py
"""

import os
import sys

# Ruta al directorio data
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, 'data')
db_path = os.path.join(data_dir, 'robot.db')

def main():
    print("=" * 60)
    print("RESETEO DE BASE DE DATOS")
    print("=" * 60)
    
    if os.path.exists(db_path):
        print(f"\n✓ Base de datos encontrada en: {db_path}")
        respuesta = input("\n⚠️  ¿Deseas ELIMINAR la base de datos actual? (s/N): ")
        
        if respuesta.lower() in ('s', 'si', 'sí', 'yes', 'y'):
            try:
                os.remove(db_path)
                print(f"\n✓ Base de datos eliminada correctamente")
            except Exception as e:
                print(f"\n✗ Error al eliminar la base de datos: {e}")
                sys.exit(1)
        else:
            print("\n✓ Operación cancelada. No se ha eliminado nada.")
            sys.exit(0)
    else:
        print(f"\n✓ No existe base de datos en: {db_path}")
        print("  (Será creada automáticamente al iniciar la aplicación)")
    
    print("\n" + "=" * 60)
    print("INICIANDO RECREACIÓN")
    print("=" * 60)
    
    # Importar e inicializar
    try:
        sys.path.insert(0, script_dir)
        from data.init_db import inicializar_bd
        
        print("\n✓ Creando nueva base de datos...")
        inicializar_bd()
        print(f"✓ Base de datos creada exitosamente en: {db_path}")
        
        # Mostrar estadísticas
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM procesos_base")
        n_procesos_base = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM recetas_base")
        n_recetas_base = cur.fetchone()[0]
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"✓ Procesos de fábrica: {n_procesos_base}")
        print(f"✓ Recetas de fábrica: {n_recetas_base}")
        print("\n✓ ¡Todo listo! Puedes iniciar la aplicación con: python app.py")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error al crear la base de datos: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
