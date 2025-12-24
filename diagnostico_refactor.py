#!/usr/bin/env python3
"""
Script de diagnóstico mejorado - IGNORA COMENTARIOS

Ejecutar: python diagnostico_refactor_v2.py
"""

import os
import re

# Patrones a buscar (código antiguo que debe actualizarse)
PATRONES_PROBLEMA = [
    # Acceso a parámetros desde proceso (debería ser desde paso)
    (r'(?<!#.{0,100})paso\.proceso\.temperatura(?!\s*or)', 'Posible acceso incorrecto - debería ser paso.temperatura'),
    (r'(?<!#.{0,100})paso\.proceso\.tiempo_segundos(?!\s*or)', 'Posible acceso incorrecto - debería ser paso.tiempo_segundos'),
    (r'(?<!#.{0,100})paso\.proceso\.velocidad(?!\s*or)', 'Posible acceso incorrecto - debería ser paso.velocidad'),
    
    # Inputs antiguos en formulario de proceso (asignaciones)
    (r'^\s*input_temp\s*=\s*ui\.number', 'Input antiguo - eliminar'),
    (r'^\s*input_velocidad\s*=\s*ui\.number.*Velocidad.*0.*10', 'Input antiguo - eliminar'),
    
    # Uso de inputs que ya no existen
    (r'input_temp\.value', 'Input no existe - eliminar'),
    (r'input_velocidad\.value', 'Input no existe - eliminar'),
    
    # Llamadas antiguas a crear_proceso_usuario con parámetros
    (r'temperatura\s*=\s*int\(input_temp', 'Parámetro antiguo en crear_proceso_usuario'),
    (r'velocidad\s*=\s*int\(input_velocidad', 'Parámetro antiguo en crear_proceso_usuario'),
]

def es_comentario(linea):
    """Verifica si una línea es un comentario."""
    stripped = linea.strip()
    return stripped.startswith('#')

def buscar_en_archivo(ruta_archivo):
    """Busca patrones problemáticos en un archivo (ignorando comentarios)."""
    problemas_encontrados = []
    
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
            
            for num_linea, linea in enumerate(lineas, 1):
                # Ignorar comentarios
                if es_comentario(linea):
                    continue
                
                for patron, descripcion in PATRONES_PROBLEMA:
                    if re.search(patron, linea):
                        problemas_encontrados.append({
                            'linea': num_linea,
                            'patron': patron,
                            'descripcion': descripcion,
                            'codigo': linea.strip()[:150]
                        })
    except Exception as e:
        print(f"Error leyendo {ruta_archivo}: {e}")
    
    return problemas_encontrados

def verificar_estructura_especifica():
    """Verificaciones específicas de estructura."""
    print("\n🔍 VERIFICACIONES ESPECÍFICAS")
    print("-" * 80)
    
    problemas = []
    
    # Verificar que servicios.crear_proceso_usuario NO tiene parámetros de ejecución
    try:
        with open('robot/servicios.py', 'r') as f:
            contenido = f.read()
            
            # Buscar la función crear_proceso_usuario
            patron_funcion = r'def crear_proceso_usuario\((.*?)\):'
            match = re.search(patron_funcion, contenido, re.DOTALL)
            
            if match:
                params = match.group(1)
                if 'temperatura' in params or 'tiempo_segundos' in params or 'velocidad' in params:
                    problemas.append("❌ servicios.crear_proceso_usuario() todavía tiene parámetros antiguos")
                else:
                    print("✅ servicios.crear_proceso_usuario() tiene firma correcta")
    except:
        pass
    
    # Verificar que ProcesoCocina NO tiene atributos de ejecución
    try:
        with open('robot/modelos.py', 'r') as f:
            contenido = f.read()
            
            # Buscar la clase ProcesoCocina
            patron_clase = r'class ProcesoCocina:.*?def __init__\((.*?)\):'
            match = re.search(patron_clase, contenido, re.DOTALL)
            
            if match:
                init_params = match.group(1)
                if 'temperatura' in init_params or 'tiempo_segundos' in init_params or 'velocidad' in init_params:
                    problemas.append("❌ ProcesoCocina.__init__() todavía tiene parámetros antiguos")
                else:
                    print("✅ ProcesoCocina tiene estructura correcta")
    except:
        pass
    
    # Verificar que PasoReceta SÍ tiene atributos de ejecución
    try:
        with open('robot/modelos.py', 'r') as f:
            contenido = f.read()
            
            # Buscar la clase PasoReceta
            patron_clase = r'class PasoReceta:.*?def __init__\((.*?)\):'
            match = re.search(patron_clase, contenido, re.DOTALL)
            
            if match:
                init_params = match.group(1)
                tiene_temp = 'temperatura' in init_params
                tiene_tiempo = 'tiempo_segundos' in init_params
                tiene_vel = 'velocidad' in init_params
                tiene_instr = 'instrucciones' in init_params
                
                if tiene_temp and tiene_tiempo and tiene_vel and tiene_instr:
                    print("✅ PasoReceta tiene los parámetros de ejecución")
                else:
                    problemas.append("❌ PasoReceta no tiene todos los parámetros necesarios")
    except:
        pass
    
    return problemas

def main():
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE REFACTOR v2 - Ignorando comentarios")
    print("=" * 80)
    print()
    
    archivos_a_revisar = [
        'ui/vistas.py',
        'robot/modelos.py',
        'robot/servicios.py',
    ]
    
    total_problemas = 0
    
    for archivo in archivos_a_revisar:
        if not os.path.exists(archivo):
            print(f"⚠️  {archivo} no encontrado")
            continue
        
        print(f"\n📄 Revisando: {archivo}")
        print("-" * 80)
        
        problemas = buscar_en_archivo(archivo)
        
        if problemas:
            total_problemas += len(problemas)
            for p in problemas:
                print(f"\n  ⚠️  LÍNEA {p['linea']}: {p['descripcion']}")
                print(f"      Código: {p['codigo']}")
        else:
            print("  ✅ Sin problemas detectados en código")
    
    # Verificaciones específicas
    problemas_estructura = verificar_estructura_especifica()
    total_problemas += len(problemas_estructura)
    
    if problemas_estructura:
        print("\n❌ PROBLEMAS DE ESTRUCTURA:")
        for p in problemas_estructura:
            print(f"  {p}")
    
    print("\n" + "=" * 80)
    if total_problemas > 0:
        print(f"❌ TOTAL: {total_problemas} problema(s) real(es) encontrado(s)")
        print("\nRevisa los archivos y aplica los cambios sugeridos.")
    else:
        print("✅ ¡PERFECTO! El refactor está completo y correcto.")
        print("La aplicación debería funcionar sin problemas.")
    print("=" * 80)

if __name__ == "__main__":
    main()