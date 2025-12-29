# 🤖 Robot de Cocina Inteligente

## 📋 Descripción

Sistema completo de control y gestión para un robot de cocina inteligente, desarrollado en Python con interfaz gráfica web moderna. El proyecto permite gestionar recetas, procesos de cocción tanto automáticos como manuales, y controlar en tiempo real el estado del robot a través de una interfaz intuitiva basada en NiceGUI.

### Características Principales

- **🎛️ Control en Tiempo Real**: Monitoreo y control del robot con actualización instantánea de estado
- **📖 Gestión de Recetas**: Biblioteca de recetas predefinidas y capacidad de crear recetas personalizadas
- **⚙️ Procesos Personalizables**: Define procesos automáticos y manuales según tus necesidades
- **🔄 Dos Modos de Operación**: 
  - **Modo Guiado**: Ejecuta recetas paso a paso con confirmación manual cuando sea necesario
  - **Modo Manual**: Control directo de temperatura, velocidad y tiempo
- **💾 Persistencia de Datos**: Base de datos SQLite para almacenar recetas y procesos de usuario
- **🎨 Interfaz Moderna**: UI responsive con tema claro/oscuro y diseño Material Design
- **🔄 Ejecución Concurrente**: Utiliza hilos para operaciones no bloqueantes
- **📊 Visualización en Tiempo Real**: Barras de progreso, gauges y notificaciones visuales

---

## 📁 Estructura del Proyecto

```
robot-cocina/
│
├── data/                       # Capa de datos y persistencia
│   ├── __init__.py            # Exposición de funciones de BD
│   ├── init_db.py             # Inicialización y gestión de BD SQLite
│   └── robot.db               # Base de datos (generada automáticamente)
│
├── robot/                      # Lógica de negocio del robot
│   ├── modelos.py             # Modelos de dominio (Robot, Receta, Proceso)
│   └── servicios.py           # Servicios CRUD y lógica de aplicación
│
├── ui/                         # Interfaz de usuario
│   └── vistas.py              # Vistas y componentes NiceGUI
│
├── utils/                      # Utilidades compartidas
│   └── utils_tiempo.py        # Conversión de formatos de tiempo
│
├── app.py                      # Punto de entrada de la aplicación
├── .gitignore                 # Archivos excluidos de control de versiones
└── README.md                  # Este archivo
```

### Descripción de Módulos

#### 📦 `data/`
Gestiona toda la persistencia de datos mediante SQLite:
- **`init_db.py`**: Crea tablas, carga datos de fábrica, gestiona conexiones
- **`robot.db`**: Base de datos con recetas base, recetas de usuario, procesos

#### 🤖 `robot/`
Contiene la lógica de negocio y modelos del dominio:
- **`modelos.py`**: 
  - Clases abstractas y concretas para procesos y recetas
  - Implementación del robot con máquina de estados
  - Patrón Strategy para diferentes modos de ejecución
  - Gestión de hilos para cocción asíncrona
- **`servicios.py`**: 
  - Funciones CRUD para procesos y recetas
  - Conversión entre filas de BD y objetos del dominio
  - Validación y gestión de datos

#### 🎨 `ui/`
Interfaz gráfica web construida con NiceGUI:
- **`vistas.py`**: 
  - Panel de control principal
  - Vista de gestión de recetas
  - Vista de gestión de procesos
  - Componentes reutilizables y navegación

#### 🔧 `utils/`
Utilidades compartidas:
- **`utils_tiempo.py`**: Conversión entre formatos MM:SS ↔ segundos

---

## 🔧 Requisitos

### Requisitos del Sistema
- **Python**: 3.8 o superior
- **Sistema Operativo**: Windows, macOS, Linux

### Dependencias Principales
```
nicegui>=2.0.0    # Framework de interfaz gráfica web
```

### Instalación de Dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install nicegui
```

---

## 🚀 Cómo Usar la Aplicación

### 1. Instalación

```bash
# Clonar el repositorio (si aplica)
git clone https://github.com/AlvaroSantamariaAnton/robot-cocina.git
cd robot-cocina

# Instalar dependencias
pip install nicegui
```

### 2. Ejecución

```bash
# Ejecutar la aplicación
python app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8080`

### 3. Uso Básico

#### Panel de Control

1. **Encender el Robot**: Activa el switch "O/I" en la tarjeta de estado
2. **Seleccionar Modo**:
   - **Guiado**: Para ejecutar recetas paso a paso
   - **Manual**: Para control directo de parámetros

#### Modo Guiado

1. Selecciona una receta del menú desplegable
2. Visualiza ingredientes y pasos
3. Presiona "Iniciar Cocción"
4. Confirma pasos manuales cuando se solicite
5. Monitorea el progreso en tiempo real

#### Modo Manual

1. Cambia el selector de modo a "Manual"
2. Ajusta temperatura (0-120°C)
3. Configura velocidad (0-10)
4. Establece tiempo (MM:SS)
5. Presiona "Iniciar" para comenzar

#### Gestión de Recetas

1. Navega a "Recetas" en el menú lateral
2. **Crear Nueva Receta**:
   - Haz clic en "Nueva Receta"
   - Completa nombre, descripción e ingredientes
   - Añade pasos con procesos y parámetros o instrucciones
   - Guarda la receta
3. **Eliminar Receta**: Solo recetas de usuario pueden eliminarse

#### Gestión de Procesos

1. Navega a "Procesos" en el menú lateral
2. **Crear Nuevo Proceso**:
   - Haz clic en "Nuevo Proceso"
   - Define nombre, tipo (Mezclar, Cocinar, etc.)
   - Selecciona tipo de ejecución (Automático/Manual)
   - Guarda el proceso
3. **Eliminar Proceso**: Solo procesos de usuario pueden eliminarse

---

## 🏗️ Arquitectura y Diseño

### Patrones de Diseño Implementados

#### 1. **Model-View-Controller (MVC)**
- **Model** (`robot/modelos.py`): Lógica de negocio y entidades del dominio
- **View** (`ui/vistas.py`): Interfaz de usuario con NiceGUI
- **Controller** (`robot/servicios.py` + callbacks): Coordinación entre modelo y vista

#### 2. **Strategy Pattern**
```python
class EstrategiaCocina(ABC):
    @abstractmethod
    def ejecutar(self, robot: 'RobotCocina') -> None:
        pass

class EjecucionReceta(EstrategiaCocina):
    # Implementación para ejecutar recetas

class EjecucionManual(EstrategiaCocina):
    # Implementación para modo manual
```

#### 3. **State Pattern**
El robot implementa una máquina de estados:
- `APAGADO`: Robot inactivo
- `ESPERA`: Encendido pero sin actividad
- `COCINANDO`: Ejecutando proceso/receta
- `PAUSADO`: Cocción pausada
- `ESPERANDO_CONFIRMACION`: Esperando acción del usuario
- `ERROR`: Estado de error

#### 4. **Observer Pattern**
```python
def registrar_callback_actualizacion(self, callback: Callable[['RobotCocina'], None]) -> None:
    self._callback_actualizacion = callback
```
La UI se actualiza automáticamente cuando cambia el estado del robot.

#### 5. **Template Method**
Las clases abstractas `ProcesoCocina` y `Receta` definen la estructura base que las subclases deben implementar.

#### 6. **Mixin Pattern**
```python
class ConOrigen:
    """Mixin que proporciona funcionalidad de origen (base/usuario)"""
```

### Base de Datos

#### Estructura de Tablas

**Procesos:**
- `procesos_base`: Procesos predefinidos de fábrica
- `procesos_usuario`: Procesos creados por el usuario

**Recetas:**
- `recetas_base`: Recetas predefinidas
- `recetas_usuario`: Recetas del usuario
- `pasos_receta_base`: Pasos de recetas predefinidas
- `pasos_receta_usuario`: Pasos de recetas del usuario

---

## 🎯 Justificación de Principios de Programación

### 1. ⚠️ Gestión Adecuada de Excepciones

#### Implementación

El proyecto define **excepciones personalizadas** específicas del dominio en `modelos.py`:

```python
class RobotApagadoError(Exception):
    """Se lanza cuando se intenta cocinar con el robot apagado."""
    pass

class RecetaNoSeleccionadaError(Exception):
    """Se lanza cuando no hay receta seleccionada y se intenta cocinar."""
    pass

class ProcesoInterrumpidoError(Exception):
    """Se lanza cuando un proceso es detenido antes de finalizar."""
    pass

class ModoManualError(Exception):
    """Se lanza cuando hay errores específicos del modo manual."""
    pass

class ConflictoEjecucionError(Exception):
    """Se lanza cuando se intenta iniciar una ejecución mientras otra está activa."""
    pass
```

#### Justificación

**✅ Ventajas:**

1. **Claridad Semántica**: Las excepciones personalizadas comunican claramente qué tipo de error ocurrió
   - `RobotApagadoError` indica inmediatamente que el problema es que el robot está apagado
   - Mejor que un genérico `ValueError` o `RuntimeError`

2. **Control de Flujo Específico**: Permite manejar diferentes errores de formas distintas
   ```python
   try:
       robot.cocinar()
   except RobotApagadoError:
       ui.notify("Por favor, enciende el robot primero", type='warning')
   except RecetaNoSeleccionadaError:
       ui.notify("Selecciona una receta antes de cocinar", type='info')
   except ConflictoEjecucionError:
       ui.notify("Ya hay una cocción en curso", type='warning')
   ```

3. **Seguridad y Robustez**: Previene estados inválidos del sistema
   - No se puede cocinar con el robot apagado
   - No se pueden ejecutar dos cocciones simultáneamente
   - Los errores son capturados y manejados apropiadamente

4. **Debugging Facilitado**: Stack traces más informativos que ayudan a identificar problemas rápidamente

5. **Documentación Implícita**: Los nombres de las excepciones documentan qué puede salir mal

**🔍 Ejemplos en el código:**

En `servicios.py`, se usan try-finally para garantizar el cierre de conexiones:
```python
def cargar_procesos_base() -> List[ProcesoCocina]:
    conn = conectar()
    try:
        cur = conn.cursor()
        # ... operaciones con BD
        return [_fila_a_proceso_base(f) for f in filas]
    finally:
        conn.close()  # SIEMPRE se cierra, incluso si hay error
```

En `modelos.py`, las excepciones personalizadas previenen estados inválidos:
```python
def cocinar(self) -> None:
    if self._estado == EstadoRobot.APAGADO:
        raise RobotApagadoError("No se puede cocinar con el robot apagado.")
    
    if self._receta_actual is None:
        raise RecetaNoSeleccionadaError("No hay receta seleccionada.")
```

---

### 2. 🔀 Uso de Hilos o Procesos Paralelos

#### Implementación

El proyecto utiliza **threading** de Python para ejecutar procesos de cocción de forma asíncrona:

```python
import threading

# En la clase RobotCocina
def cocinar(self) -> None:
    # ...
    self._hilo_coccion = threading.Thread(
        target=self._ejecutar_receta_en_hilo,
        daemon=True,
    )
    self._estado = EstadoRobot.COCINANDO
    self._hilo_coccion.start()

def _ejecutar_receta_en_hilo(self) -> None:
    """Ejecuta la receta en un hilo separado."""
    try:
        while True:
            time.sleep(1)  # Simula 1 segundo de cocción
            # ... actualizar progreso, verificar pausas, etc.
    except ProcesoInterrumpidoError:
        # Manejar cancelación
        pass
```

También se usa un **lock** para sincronización thread-safe:
```python
self._lock = threading.Lock()

with self._lock:
    # Operaciones críticas que modifican el estado
    self._progreso = nuevo_progreso
    self._estado = nuevo_estado
    self._notificar_cambio()
```

#### Justificación

**✅ Ventajas:**

1. **UI No Bloqueante**: La interfaz permanece responsive mientras el robot cocina
   - Sin hilos: La aplicación se congelaría durante la cocción
   - Con hilos: El usuario puede pausar, cancelar o navegar por la interfaz mientras cocina

2. **Simulación Realista**: El hilo simula el paso del tiempo real de cocción
   - Cada segundo de cocción se simula con `time.sleep(1)`
   - El progreso se actualiza incrementalmente
   - El usuario ve la evolución en tiempo real

3. **Control Fino**: Permite pausar/reanudar/cancelar en cualquier momento
   ```python
   def pausar_coccion(self) -> None:
       with self._lock:
           self._pausado = True
   
   def reanudar_coccion(self) -> None:
       with self._lock:
           self._pausado = False
           # Se reanuda desde donde se pausó
   ```

4. **Seguridad con Locks**: Previene condiciones de carrera (race conditions)
   - Múltiples partes del código pueden intentar modificar el estado simultáneamente
   - El lock garantiza que solo un hilo modifique el estado a la vez
   - Previene estados inconsistentes

5. **Daemon Threads**: Los hilos marcados como daemon se terminan automáticamente cuando la aplicación se cierra
   - No deja procesos huérfanos
   - Limpieza automática de recursos

**🔍 Ejemplo de flujo paralelo:**

```
Hilo Principal (UI)          Hilo de Cocción
      |                            |
      |--[Usuario presiona "Cocinar"]
      |                            |
      |--[Crea hilo daemon]-->     |
      |                            |--[Inicia cocción]
      |                            |
      |--[Usuario navega UI]       |--[time.sleep(1)]
      |                            |--[Actualiza progreso]
      |                            |--[Notifica cambio]
      |--[UI se actualiza]<--------|
      |                            |
      |--[Usuario pausa]           |
      |--[Establece flag _pausado] |
      |                            |--[Detecta pausa]
      |                            |--[Guarda posición]
      |                            |--[Hilo termina]
```

**⚠️ Sincronización:**

El lock es crítico para evitar problemas como:
- **Lost Update**: Dos hilos actualizan el progreso simultáneamente
- **Dirty Read**: La UI lee un estado mientras está siendo modificado
- **Inconsistent State**: El progreso y el estado no coinciden

Ejemplo de uso correcto del lock:
```python
# INCORRECTO (sin lock):
self._progreso = 50.0
self._estado = EstadoRobot.COCINANDO
# ⚠️ Otro hilo podría leer aquí y ver estado inconsistente

# CORRECTO (con lock):
with self._lock:
    self._progreso = 50.0
    self._estado = EstadoRobot.COCINANDO
    # ✅ Ambos cambios son atómicos
```

---

### 3. 🎭 Uso de Abstracción

#### Implementación

El proyecto utiliza **clases abstractas** (ABC - Abstract Base Classes) para definir interfaces y comportamientos comunes:

```python
from abc import ABC, abstractmethod

class ProcesoCocina(ABC, ConOrigen):
    """Clase base abstracta para procesos de cocina."""
    
    @abstractmethod
    def es_manual(self) -> bool:
        """Devuelve True si el proceso requiere intervención manual."""
        pass
    
    @abstractmethod
    def descripcion_resumida(self) -> str:
        """Descripción resumida del proceso."""
        pass

class Receta(ConOrigen, ABC):
    """Clase base abstracta para recetas de cocina."""
    
    @abstractmethod
    def obtener_duracion_total(self) -> int:
        """Calcula la duración total en segundos."""
        pass
    
    @abstractmethod
    def puede_eliminarse(self) -> bool:
        """Determina si la receta puede ser eliminada."""
        pass

class EstrategiaCocina(ABC):
    """Estrategia abstracta para diferentes modos de cocción."""
    
    @abstractmethod
    def ejecutar(self, robot: 'RobotCocina') -> None:
        """Ejecuta la estrategia de cocción."""
        pass
```

#### Justificación

**✅ Ventajas:**

1. **Contrato Explícito**: Define qué métodos DEBEN implementar las subclases
   - Si una subclase no implementa un método abstracto, Python lanza un error
   - Imposible crear instancias de clases abstractas
   - Garantiza que todas las implementaciones cumplan la interfaz

2. **Polimorfismo Garantizado**: Todas las subclases son intercambiables
   ```python
   # Puedo tratar cualquier proceso genéricamente:
   def mostrar_proceso(proceso: ProcesoCocina):
       print(proceso.descripcion_resumida())  # Funciona para Manual y Automático
       if proceso.es_manual():
           print("Requiere intervención del usuario")
   ```

3. **Extensibilidad**: Fácil añadir nuevos tipos sin modificar código existente
   - Nuevo tipo de proceso: Solo crear nueva subclase que implemente los métodos abstractos
   - Nuevo modo de cocción: Solo crear nueva `EstrategiaCocina`
   - Principio Abierto/Cerrado (SOLID): Abierto a extensión, cerrado a modificación

4. **Documentación Viva**: La clase abstracta documenta la interfaz esperada
   - Cualquier desarrollador sabe qué métodos debe implementar
   - IDE's proporcionan autocompletado y verificación de tipos
   - Reduce errores de programación

5. **Separación de Niveles**: Código de alto nivel trabaja con abstracciones, no detalles
   ```python
   # Alto nivel (no le importa si es Manual o Automático):
   for paso in receta.pasos:
       if paso.proceso.es_manual():
           esperar_confirmacion_usuario()
       else:
           ejecutar_automaticamente(paso)
   ```

**🔍 Ejemplo de flujo con abstracción:**

```python
# servicios.py - Instanciación polimórfica
def _fila_a_proceso_base(fila: Tuple) -> ProcesoCocina:
    # Polimorfismo: Devuelve ProcesoCocina (abstracción)
    # pero instancia la subclase correcta
    if tipo_ejecucion == "manual":
        return ProcesoManual(...)  # Subclase concreta
    else:
        return ProcesoAutomatico(...)  # Subclase concreta

# vistas.py - Uso polimórfico
procesos = servicios.cargar_procesos_base()  # List[ProcesoCocina]
for proceso in procesos:
    # Funciona sin importar si es Manual o Automático:
    label = proceso.descripcion_resumida()  # ← Método abstracto
    tipo = "Manual" if proceso.es_manual() else "Automático"  # ← Método abstracto
```

**⚡ Beneficio real:**

Sin abstracción:
```python
# ❌ Código frágil que necesita conocer todos los tipos:
if isinstance(proceso, ProcesoManual):
    label = f"{proceso.nombre} - [MANUAL]"
elif isinstance(proceso, ProcesoAutomatico):
    label = f"{proceso.nombre} - [AUTOMÁTICO]"
elif isinstance(proceso, ProcesoNuevoTipo):  # ← Hay que modificar AQUÍ
    label = f"{proceso.nombre} - [NUEVO]"
```

Con abstracción:
```python
# ✅ Código robusto que funciona con cualquier tipo:
label = proceso.descripcion_resumida()  # ← Funciona con CUALQUIER subclase
```

---

### 4. 🦎 Uso de Polimorfismo

#### Implementación

El polimorfismo permite que diferentes clases respondan al mismo mensaje de formas distintas. Ejemplos clave:

**1. Procesos (Manual vs Automático):**
```python
class ProcesoManual(ProcesoCocina):
    def es_manual(self) -> bool:
        return True
    
    def descripcion_resumida(self) -> str:
        return f"{self._nombre} - [MANUAL]"

class ProcesoAutomatico(ProcesoCocina):
    def es_manual(self) -> bool:
        return False
    
    def descripcion_resumida(self) -> str:
        return f"{self._nombre} - [AUTOMÁTICO]"
```

**2. Recetas (Base vs Usuario):**
```python
class RecetaBase(Receta):
    def puede_eliminarse(self) -> bool:
        return False  # Recetas de fábrica no se pueden eliminar
    
    def es_editable(self) -> bool:
        return False

class RecetaUsuario(Receta):
    def puede_eliminarse(self) -> bool:
        return True  # Recetas de usuario sí se pueden eliminar
    
    def es_editable(self) -> bool:
        return True
```

**3. Estrategias de Cocción:**
```python
class EjecucionReceta(EstrategiaCocina):
    def ejecutar(self, robot: 'RobotCocina') -> None:
        # Ejecuta receta paso a paso con pasos manuales/automáticos
        pass

class EjecucionManual(EstrategiaCocina):
    def ejecutar(self, robot: 'RobotCocina') -> None:
        # Ejecuta modo manual con cuenta regresiva
        pass
```

#### Justificación

**✅ Ventajas:**

1. **Mismo Interfaz, Diferentes Comportamientos**: El código cliente no necesita saber qué tipo específico está usando
   ```python
   # Funciona con CUALQUIER ProcesoCocina:
   def mostrar_info(proceso: ProcesoCocina):
       print(proceso.descripcion_resumida())  # Diferente output según el tipo
       
       # Pero el código es el mismo!
   ```

2. **Lógica de Negocio Simplificada**: Las decisiones se delegan a los objetos
   ```python
   # ❌ Sin polimorfismo (muchos if/else):
   if tipo_proceso == "manual":
       return f"{nombre} - [MANUAL]"
   elif tipo_proceso == "automatico":
       return f"{nombre} - [AUTOMÁTICO]"
   # ¿Y si añadimos semi-automático? → Modificar todos los if/else
   
   # ✅ Con polimorfismo:
   return proceso.descripcion_resumida()  # ← Delega al objeto
   ```

3. **Extensibilidad sin Modificación**: Añadir nuevos tipos no requiere cambiar código existente
   - Nuevo tipo de proceso: Crear `ProcesoSemiAutomatico(ProcesoCocina)`
   - Todo el código existente funcionará automáticamente
   - Principio Abierto/Cerrado de SOLID

4. **UI Adaptativa**: La interfaz se adapta automáticamente según el tipo
   ```python
   # vistas.py
   for paso in receta.pasos:
       if paso.proceso.es_manual():  # ← Polimorfismo
           # Mostrar botón "Confirmar"
           mostrar_confirmacion()
       else:
           # Mostrar barra de progreso
           mostrar_progreso()
   ```

5. **Validaciones Específicas**: Cada tipo implementa sus propias reglas
   ```python
   # RecetaBase no permite eliminación:
   if receta.puede_eliminarse():  # ← False para RecetaBase
       boton_eliminar.set_enabled(True)
   else:
       boton_eliminar.set_enabled(False)
   ```

**🔍 Ejemplo real del código:**

En `servicios.py`, la función `_fila_a_proceso_base` demuestra polimorfismo en acción:

```python
def _fila_a_proceso_base(fila: Tuple) -> ProcesoCocina:
    """
    Convierte una fila de BD a un objeto ProcesoCocina.
    Polimorfismo: Retorna el tipo apropiado según tipo_ejecucion.
    """
    id_, nombre, tipo, tipo_ejecucion, instrucciones = fila
    
    # Decide QUÉ subclase instanciar en tiempo de ejecución:
    if tipo_ejecucion == "manual":
        return ProcesoManual(...)  # ← Polimorfismo
    else:
        return ProcesoAutomatico(...)  # ← Polimorfismo
    
    # El código que llama a esta función recibe un ProcesoCocina
    # y no necesita saber si es Manual o Automático
```

Luego, en `vistas.py`:
```python
procesos = servicios.cargar_procesos_base()  # Lista polimórfica

for proceso in procesos:
    # El mismo código funciona para Manual y Automático:
    nombre = proceso.nombre  # ← Igual para ambos
    descripcion = proceso.descripcion_resumida()  # ← Diferente implementación
    
    if proceso.es_manual():  # ← Polimorfismo en acción
        icono = 'pan_tool'
    else:
        icono = 'settings'
```

**🎯 Caso de uso real: Habilitar/Deshabilitar botón eliminar:**

```python
# vistas.py - Gestión de recetas
for receta in todas_las_recetas:
    with ui.card():
        ui.label(receta.nombre)
        
        # Polimorfismo: RecetaBase.puede_eliminarse() → False
        #              RecetaUsuario.puede_eliminarse() → True
        boton_eliminar = ui.button('Eliminar')
        boton_eliminar.set_enabled(receta.puede_eliminarse())
        
        # ¡No hay if/else! El objeto decide por sí mismo.
```

**🚀 Beneficio de escalabilidad:**

Si mañana queremos añadir `ProcesoSemiAutomatico`:

1. Crear la clase:
```python
class ProcesoSemiAutomatico(ProcesoCocina):
    def es_manual(self) -> bool:
        return False  # O True, según la lógica
    
    def descripcion_resumida(self) -> str:
        return f"{self._nombre} - [SEMI-AUTO]"
```

2. Actualizar `_fila_a_proceso_base`:
```python
if tipo_ejecucion == "manual":
    return ProcesoManual(...)
elif tipo_ejecucion == "semi":
    return ProcesoSemiAutomatico(...)  # ← Solo cambio aquí
else:
    return ProcesoAutomatico(...)
```

3. **TODO EL RESTO DEL CÓDIGO FUNCIONA SIN CAMBIOS** ✨

---

### 5. 🧬 Uso de Herencia

#### Implementación

El proyecto utiliza herencia para compartir código común y especializar comportamientos:

**Jerarquía de Procesos:**
```
            ProcesoCocina (ABC)
                   ↑
        ┌──────────┴──────────┐
        │                     │
  ProcesoManual        ProcesoAutomatico
```

**Jerarquía de Recetas:**
```
              Receta (ABC)
                   ↑
        ┌──────────┴──────────┐
        │                     │
   RecetaBase           RecetaUsuario
```

**Ejemplo de código:**
```python
class ProcesoCocina(ABC, ConOrigen):
    """Clase base que define la estructura común."""
    
    def __init__(self, id_, nombre, tipo, tipo_ejecucion, instrucciones, origen):
        super().__init__(origen=origen)  # ← Herencia múltiple con Mixin
        self._id = id_
        self._nombre = nombre
        # ... campos comunes
    
    @property
    def id(self):
        return self._id  # ← Método común heredado por todas las subclases
    
    @abstractmethod
    def es_manual(self) -> bool:
        pass  # ← Método que DEBE implementar cada subclase

class ProcesoManual(ProcesoCocina):
    """Especialización para procesos manuales."""
    
    def es_manual(self) -> bool:
        return True  # ← Implementación específica
    
    # Hereda automáticamente:
    # - __init__
    # - @property id, nombre, tipo, etc.
    # - __repr__
    # - Todos los métodos de ConOrigen
```

#### Justificación

**✅ Ventajas:**

1. **Reutilización de Código**: Evita duplicación mediante código compartido
   ```python
   # Sin herencia (DUPLICACIÓN):
   class ProcesoManual:
       def __init__(self, id_, nombre, tipo, ...):
           self._id = id_
           self._nombre = nombre
           # ... 50 líneas de código común
   
   class ProcesoAutomatico:
       def __init__(self, id_, nombre, tipo, ...):
           self._id = id_  # ← DUPLICADO
           self._nombre = nombre  # ← DUPLICADO
           # ... 50 líneas DUPLICADAS
   
   # Con herencia (DRY - Don't Repeat Yourself):
   class ProcesoCocina:
       # ... código común UNA VEZ
   
   class ProcesoManual(ProcesoCocina):
       # Solo código específico
   
   class ProcesoAutomatico(ProcesoCocina):
       # Solo código específico
   ```

2. **Jerarquía de Tipos Clara**: Relaciones "es-un" bien definidas
   - `ProcesoManual` **es un** `ProcesoCocina`
   - `RecetaUsuario` **es una** `Receta`
   - Type hints funcionan: `List[ProcesoCocina]` incluye manuales y automáticos

3. **Mantenimiento Simplificado**: Cambios en la clase base se propagan automáticamente
   ```python
   # Si añadimos un nuevo campo en ProcesoCocina:
   class ProcesoCocina(ABC):
       def __init__(self, ..., categoria: str = "general"):
           self._categoria = categoria
       
       @property
       def categoria(self):
           return self._categoria
   
   # ✅ ProcesoManual y ProcesoAutomatico lo heredan AUTOMÁTICAMENTE
   # No hay que modificar ninguna subclase
   ```

4. **Herencia Múltiple con Mixins**: Combina comportamientos ortogonales
   ```python
   class ProcesoCocina(ABC, ConOrigen):
       #                    ↑ Mixin para funcionalidad de origen
       pass
   
   # Todas las subclases obtienen:
   # - es_de_fabrica()
   # - es_de_usuario()
   # - @property origen
   ```

5. **Polimorfismo Natural**: La herencia habilita polimorfismo
   ```python
   # Puedo usar List[ProcesoCocina] con mezcla de tipos:
   procesos: List[ProcesoCocina] = [
       ProcesoManual(...),
       ProcesoAutomatico(...),
       ProcesoManual(...),
   ]
   
   # Todos se tratan uniformemente:
   for p in procesos:
       print(p.nombre)  # ← Funciona para todos
   ```

**🔍 Ejemplo de herencia en acción:**

```python
# modelos.py

# Clase base (padre):
class Receta(ConOrigen, ABC):
    def __init__(self, id_, nombre, descripcion, ingredientes, pasos, origen):
        super().__init__(origen=origen)
        self._id = id_
        self._nombre = nombre
        self._descripcion = descripcion
        self._ingredientes = ingredientes
        self._pasos = pasos
    
    # Métodos comunes heredados por TODAS las recetas:
    @property
    def id(self):
        return self._id
    
    @property
    def nombre(self):
        return self._nombre
    
    def obtener_duracion_total(self) -> int:
        """Calcula duración sumando todos los pasos."""
        total = 0
        for paso in self._pasos:
            if paso.tiempo_segundos:
                total += paso.tiempo_segundos
        return total
    
    # Método abstracto (debe implementarse en subclases):
    @abstractmethod
    def puede_eliminarse(self) -> bool:
        pass

# Subclase 1 (hija):
class RecetaBase(Receta):
    def puede_eliminarse(self) -> bool:
        return False  # Recetas de fábrica son inmutables
    
    # Hereda: id, nombre, descripcion, obtener_duracion_total(), etc.

# Subclase 2 (hija):
class RecetaUsuario(Receta):
    def puede_eliminarse(self) -> bool:
        return True  # Recetas de usuario pueden eliminarse
    
    # Hereda: id, nombre, descripcion, obtener_duracion_total(), etc.
```

**📊 Beneficios medibles:**

| Aspecto | Sin Herencia | Con Herencia |
|---------|--------------|--------------|
| Líneas de código | ~500 (duplicado) | ~300 (reutilizado) |
| Bugs por duplicación | Alto | Bajo |
| Facilidad de cambios | Difícil (cambiar en N lugares) | Fácil (cambiar 1 vez) |
| Consistencia | Baja (puede diverger) | Alta (compartida) |

**🎯 Caso de uso real: Añadir validación:**

Supongamos que queremos validar que el nombre de una receta no esté vacío:

```python
# Sin herencia:
class RecetaBase:
    @property
    def nombre(self):
        if not self._nombre:  # ← Validación
            return "(Sin nombre)"
        return self._nombre

class RecetaUsuario:
    @property
    def nombre(self):
        if not self._nombre:  # ← DUPLICADO (puede olvidarse!)
            return "(Sin nombre)"
        return self._nombre

# Con herencia:
class Receta(ABC):
    @property
    def nombre(self):
        if not self._nombre:  # ← UNA VEZ
            return "(Sin nombre)"
        return self._nombre

# RecetaBase y RecetaUsuario heredan automáticamente ✅
```

---

### 6. 🔒 Uso de Encapsulamiento

#### Implementación

El proyecto aplica encapsulamiento ocultando detalles internos y exponiendo solo lo necesario mediante propiedades:

```python
class RobotCocina:
    def __init__(self):
        # Atributos privados (prefijo _):
        self._estado: EstadoRobot = EstadoRobot.APAGADO
        self._receta_actual: Optional[Receta] = None
        self._progreso: float = 0.0
        self._hilo_coccion: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._pausado = False
        self._parar = False
    
    # Propiedades de solo lectura (getters sin setters):
    @property
    def estado(self) -> EstadoRobot:
        return self._estado
    
    @property
    def progreso(self) -> float:
        return self._progreso
    
    @property
    def receta_actual(self) -> Optional[Receta]:
        return self._receta_actual
    
    # Métodos públicos (interfaz controlada):
    def seleccionar_receta(self, receta: Receta) -> None:
        if self._estado == EstadoRobot.APAGADO:
            raise RobotApagadoError(...)
        with self._lock:  # ← Control de acceso concurrente
            self._receta_actual = receta
    
    # Métodos privados (detalles de implementación):
    def _ejecutar_receta_en_hilo(self) -> None:
        # ... lógica interna
        pass
    
    def _notificar_cambio(self) -> None:
        # ... callback a la UI
        pass
```

**Ejemplo de propiedades:**
```python
class ProcesoCocina(ABC):
    def __init__(self, id_, nombre, tipo, ...):
        self._id = id_              # ← Privado
        self._nombre = nombre       # ← Privado
        self._tipo = tipo           # ← Privado
    
    # Propiedades de solo lectura:
    @property
    def id(self) -> Optional[int]:
        return self._id  # ✅ Solo lectura, no se puede modificar desde fuera
    
    @property
    def nombre(self) -> str:
        return self._nombre
    
    @property
    def tipo(self) -> str:
        return self._tipo
    
    # No hay setters: Los atributos solo se establecen en __init__
```

#### Justificación

**✅ Ventajas:**

1. **Protección de Estado Interno**: Los atributos privados no pueden modificarse arbitrariamente
   ```python
   # ❌ Sin encapsulamiento:
   robot.estado = EstadoRobot.COCINANDO  # ¡Cambio directo sin validación!
   robot.progreso = 9999  # ¡Valor inválido!
   
   # ✅ Con encapsulamiento:
   robot.cocinar()  # ← Único punto de entrada, con validaciones
   # robot.estado = ...  ← Error! Es read-only
   # robot.progreso = ...  ← Error! Es read-only
   ```

2. **Validación Centralizada**: Todo cambio de estado pasa por métodos controlados
   ```python
   def seleccionar_receta(self, receta: Receta) -> None:
       # Validaciones:
       if self._estado == EstadoRobot.APAGADO:
           raise RobotApagadoError("El robot debe estar encendido")
       
       if self._estado in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO):
           raise ConflictoEjecucionError("Ya hay una cocción activa")
       
       # Solo si pasa las validaciones:
       with self._lock:
           self._receta_actual = receta
   ```

3. **Invariantes Garantizadas**: El estado interno siempre es consistente
   - No se puede cocinar con robot apagado (validado en `cocinar()`)
   - No se puede tener progreso > 100% (controlado en `_ejecutar_receta_en_hilo`)
   - No se pueden ejecutar dos cocciones simultáneas (lock + validaciones)

4. **Cambios Internos Sin Romper API Externa**: Puedo modificar implementación sin afectar código cliente
   ```python
   # Versión 1:
   @property
   def progreso(self) -> float:
       return self._progreso  # ← Simple atributo
   
   # Versión 2 (sin romper código existente):
   @property
   def progreso(self) -> float:
       # Ahora calculo el progreso en tiempo real:
       if self._receta_actual and self._receta_actual.pasos:
           total_pasos = len(self._receta_actual.pasos)
           return (self._indice_paso_actual / total_pasos) * 100
       return 0.0
   
   # ✅ El código que usa robot.progreso SIGUE FUNCIONANDO
   ```

5. **Thread-Safety**: El lock protege operaciones críticas
   ```python
   def pausar_coccion(self) -> None:
       with self._lock:  # ← Solo un hilo a la vez
           if self._estado != EstadoRobot.COCINANDO:
               raise ...
           self._pausado = True
           # Estado consistente garantizado
   ```

6. **Documentación Implícita**: La API pública documenta qué es seguro usar
   - Atributos con `_`: "No tocar, detalles internos"
   - Métodos públicos: "Interfaz estable y segura"
   - Propiedades: "Valores que puedes leer pero no modificar"

**🔍 Ejemplo de encapsulamiento en acción:**

```python
# vistas.py (código de UI)

# ❌ MAL (sin encapsulamiento):
if robot._estado == EstadoRobot.COCINANDO:  # ← Acceso directo
    robot._pausado = True  # ← Modificación directa (PELIGROSO)
    robot._estado = EstadoRobot.PAUSADO  # ← Rompe invariantes

# ✅ BIEN (con encapsulamiento):
if robot.estado == EstadoRobot.COCINANDO:  # ← Propiedad pública
    robot.pausar_coccion()  # ← Método público con validaciones
```

**🛡️ Protección contra errores comunes:**

```python
# Sin encapsulamiento:
robot.progreso = 150  # ❌ ¡Progreso > 100%! (estado inválido)
robot.estado = EstadoRobot.COCINANDO  # ❌ Sin validar si hay receta
robot.receta_actual = None  # ❌ Eliminar receta mientras cocina

# Con encapsulamiento:
# robot.progreso = 150  ← ERROR de Python: no se puede asignar
# robot.estado = ...  ← ERROR: no se puede asignar
# robot.receta_actual = None  ← ERROR: no se puede asignar

# Las únicas formas de cambiar estado son:
robot.encender()  # ← Método público con validaciones
robot.seleccionar_receta(receta)  # ← Método público con validaciones
robot.cocinar()  # ← Método público con validaciones
```

**📊 Comparación de seguridad:**

| Situación | Sin Encapsulamiento | Con Encapsulamiento |
|-----------|---------------------|---------------------|
| Cambio de estado inválido | ⚠️ Posible | ✅ Bloqueado |
| Progreso > 100% | ⚠️ Posible | ✅ Imposible |
| Cocinar sin receta | ⚠️ Posible | ✅ Bloqueado |
| Race conditions | ⚠️ Posibles | ✅ Prevenidas (lock) |
| Debugging | ❌ Difícil (muchos puntos de modificación) | ✅ Fácil (puntos controlados) |

**🎯 Caso de uso real: Modo Manual:**

```python
# Estado del modo manual (encapsulado):
class RobotCocina:
    def __init__(self):
        self._manual_activo = False  # ← Privado
        self._manual_tiempo_restante = 0  # ← Privado
        self._manual_temperatura = 0  # ← Privado
        self._manual_velocidad = 0  # ← Privado
    
    def iniciar_modo_manual(self, temperatura, velocidad, tiempo_segundos):
        # Validaciones:
        if self._estado == EstadoRobot.APAGADO:
            raise RobotApagadoError(...)
        
        if temperatura < 0 or temperatura > 250:
            raise ValueError("Temperatura fuera de rango")
        
        if velocidad < 0 or velocidad > 10:
            raise ValueError("Velocidad fuera de rango")
        
        # Solo si pasa validaciones:
        with self._lock:
            self._manual_temperatura = temperatura
            self._manual_velocidad = velocidad
            self._manual_tiempo_restante = tiempo_segundos
            self._manual_activo = True
            self._iniciar_hilo_manual()
    
    # Propiedades de solo lectura:
    @property
    def manual_tiempo_restante(self) -> int:
        return self._manual_tiempo_restante
    
    @property
    def manual_temperatura(self) -> int:
        return self._manual_temperatura
```

**✨ Beneficio final:**

El encapsulamiento crea una **"API segura"**:
- ✅ Solo se puede cambiar el estado a través de métodos validados
- ✅ Los invariantes (reglas de negocio) SIEMPRE se cumplen
- ✅ El código cliente no puede romper el sistema accidentalmente
- ✅ Los cambios internos no afectan al código cliente
- ✅ Thread-safety garantizada mediante locks
