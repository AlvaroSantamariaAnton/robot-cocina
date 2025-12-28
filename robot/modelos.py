import threading
import time
from typing import List, Optional, Callable, Dict, Any
from utils.utils_tiempo import segundos_a_mmss
from abc import ABC, abstractmethod


# =========================
# Excepciones específicas
# =========================

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


# =========================
# Mixin para origen
# =========================

class ConOrigen:
    """
    Mixin para entidades que tienen origen (base/usuario).
    Proporciona funcionalidad común relacionada con el origen.
    """
    def __init__(self, *args, origen: str = "base", **kwargs):
        super().__init__(*args, **kwargs)
        self._origen = origen
    
    @property
    def origen(self) -> str:
        return self._origen
    
    def es_de_fabrica(self) -> bool:
        """Devuelve True si la entidad es de fábrica (base)."""
        return self._origen == "base"
    
    def es_de_usuario(self) -> bool:
        """Devuelve True si la entidad fue creada por el usuario."""
        return self._origen == "usuario"

# =========================
# Modelos de dominio
# =========================

class ProcesoCocina(ABC, ConOrigen):
    """
    Clase base abstracta para procesos de cocina.
    
    Esta clase se mapea con la tabla de procesos (base o usuario) en la BD.
    Ahora solo contiene metadatos del proceso, SIN parámetros de ejecución.
    """

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        tipo: str,
        tipo_ejecucion: str,
        instrucciones: Optional[str],
        origen: str = "base",
    ) -> None:
        super().__init__(origen=origen)  # ← Llama al mixin
        self._id = id_
        self._nombre = nombre
        self._tipo = tipo
        self._tipo_ejecucion = tipo_ejecucion
        self._instrucciones = instrucciones or ""

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def tipo(self) -> str:
        return self._tipo

    @property
    def tipo_ejecucion(self) -> str:
        return self._tipo_ejecucion

    @property
    def instrucciones(self) -> str:
        return self._instrucciones

    @abstractmethod
    def es_manual(self) -> bool:
        """Devuelve True si el proceso requiere intervención manual."""
        pass

    @abstractmethod
    def descripcion_resumida(self) -> str:
        """Descripción resumida del proceso (solo nombre y tipo)."""
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id}, nombre={self._nombre!r}, tipo={self._tipo!r}, "
            f"tipo_ejecucion={self._tipo_ejecucion!r}, origen={self._origen!r})"
        )


class ProcesoManual(ProcesoCocina):
    """Proceso que requiere intervención manual del usuario."""
    
    def es_manual(self) -> bool:
        """Devuelve True ya que es un proceso manual."""
        return True

    def descripcion_resumida(self) -> str:
        """Descripción resumida del proceso manual."""
        return f"{self._nombre} - [MANUAL]"


class ProcesoAutomatico(ProcesoCocina):
    """Proceso automático ejecutado por el robot."""
    
    def es_manual(self) -> bool:
        """Devuelve False ya que es un proceso automático."""
        return False

    def descripcion_resumida(self) -> str:
        """Descripción resumida del proceso automático."""
        return f"{self._nombre} - [AUTOMÁTICO]"


class PasoReceta:
    """
    Un paso concreto dentro de una receta.
    
    Ahora incluye los parámetros de ejecución específicos de este paso:
    - Para pasos automáticos: temperatura, tiempo_segundos, velocidad
    - Para pasos manuales: instrucciones (texto libre)
    """

    def __init__(
        self, 
        orden: int, 
        proceso: ProcesoCocina,
        temperatura: Optional[int] = None,
        tiempo_segundos: Optional[int] = None,
        velocidad: Optional[int] = None,
        instrucciones: Optional[str] = None,
    ) -> None:
        self._orden = orden
        self._proceso = proceso
        self._temperatura = temperatura
        self._tiempo_segundos = tiempo_segundos
        self._velocidad = velocidad
        self._instrucciones = instrucciones

    @property
    def orden(self) -> int:
        return self._orden

    @property
    def proceso(self) -> ProcesoCocina:
        return self._proceso

    @property
    def temperatura(self) -> Optional[int]:
        return self._temperatura

    @property
    def tiempo_segundos(self) -> Optional[int]:
        return self._tiempo_segundos

    @property
    def velocidad(self) -> Optional[int]:
        return self._velocidad

    @property
    def instrucciones(self) -> Optional[str]:
        """
        Instrucciones específicas de este paso.
        Para pasos manuales, esto contiene el texto que se muestra al usuario.
        """
        return self._instrucciones

    def __repr__(self) -> str:
        return (
            f"PasoReceta(orden={self._orden}, proceso={self._proceso!r}, "
            f"temp={self._temperatura}, tiempo={self._tiempo_segundos}, "
            f"vel={self._velocidad})"
        )


class Receta(ConOrigen, ABC):
    """Clase base abstracta para recetas de cocina."""

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        descripcion: str,
        ingredientes: List[Dict[str, Any]],
        pasos: List[PasoReceta],
        origen: str = "base",
    ) -> None:
        super().__init__(origen=origen)  # ← Llama al mixin
        self._id = id_
        self._nombre = nombre
        self._descripcion = descripcion
        self._ingredientes = ingredientes
        self._pasos = sorted(pasos, key=lambda p: p.orden)

    @property
    def id(self) -> Optional[int]:
        return self._id

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def ingredientes(self) -> List[Dict[str, Any]]:
        return list(self._ingredientes)

    @property
    def pasos(self) -> List[PasoReceta]:
        return list(self._pasos)

    @abstractmethod
    def es_editable(self) -> bool:
        """Devuelve True si la receta puede ser editada o eliminada."""
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id}, nombre={self._nombre!r}, "
            f"pasos={len(self._pasos)}, origen={self._origen!r})"
        )


class RecetaBase(Receta):
    """Receta de fábrica (inmutable)."""

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        descripcion: str,
        ingredientes: List[Dict[str, Any]],
        pasos: List[PasoReceta],
    ) -> None:
        super().__init__(
            id_=id_,
            nombre=nombre,
            descripcion=descripcion,
            ingredientes=ingredientes,
            pasos=pasos,
            origen="base",
        )

    def es_editable(self) -> bool:
        """Las recetas base NO son editables."""
        return False


class RecetaUsuario(Receta):
    """Receta creada por el usuario (editable)."""

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        descripcion: str,
        ingredientes: List[Dict[str, Any]],
        pasos: List[PasoReceta],
    ) -> None:
        super().__init__(
            id_=id_,
            nombre=nombre,
            descripcion=descripcion,
            ingredientes=ingredientes,
            pasos=pasos,
            origen="usuario",
        )

    def es_editable(self) -> bool:
        """Las recetas de usuario SON editables."""
        return True


# =========================
# Estados del Robot
# =========================

class EstadoRobot:
    """Enum simulado de estados del robot."""
    APAGADO = "APAGADO"
    ESPERA = "ESPERA"
    COCINANDO = "COCINANDO"
    PAUSADO = "PAUSADO"
    ESPERANDO_CONFIRMACION = "ESPERANDO_CONFIRMACION"
    ERROR = "ERROR"


# =========================
# Estrategia de Ejecución (Polimorfismo)
# =========================

class EstrategiaEjecucion(ABC):
    """
    Clase base abstracta para estrategias de ejecución.
    Implementa el patrón Strategy para manejar ejecución de recetas vs manual.
    """
    
    @abstractmethod
    def ejecutar(self, robot: 'RobotCocina') -> None:
        """Ejecuta la estrategia en el robot dado."""
        pass
    
    @abstractmethod
    def puede_pausar(self) -> bool:
        """Indica si esta estrategia puede ser pausada."""
        pass
    
    @abstractmethod
    def descripcion(self) -> str:
        """Descripción de lo que está ejecutando."""
        pass


class EjecucionReceta(EstrategiaEjecucion):
    """Estrategia para ejecutar recetas."""
    
    def __init__(self, receta: Receta):
        self._receta = receta
    
    def ejecutar(self, robot: 'RobotCocina') -> None:
        """Ejecuta la receta en el robot."""
        robot._ejecutar_receta_en_hilo()
    
    def puede_pausar(self) -> bool:
        return True
    
    def descripcion(self) -> str:
        return f"Receta: {self._receta.nombre}"


class EjecucionManual(EstrategiaEjecucion):
    """Estrategia para ejecución manual."""
    
    def __init__(self, temperatura: int, velocidad: int, tiempo: int):
        self._temperatura = temperatura
        self._velocidad = velocidad
        self._tiempo = tiempo
    
    def ejecutar(self, robot: 'RobotCocina') -> None:
        """Ejecuta la cocción manual en el robot."""
        robot._ejecutar_manual_en_hilo()
    
    def puede_pausar(self) -> bool:
        return True
    
    def descripcion(self) -> str:
        return f"Manual: {self._temperatura}°C, Vel {self._velocidad}, {segundos_a_mmss(self._tiempo)}"


# =========================
# Robot de Cocina
# =========================

class RobotCocina:
    """
    Controla el estado del robot y la ejecución de recetas o cocción manual.
    
    CAMBIOS PRINCIPALES:
    - Añade soporte para modo manual con temporizador
    - Política de preempción: solo una ejecución activa a la vez
    - Ajustes en caliente durante cocción manual
    """

    # Constantes de validación para modo manual
    TEMP_MIN = 0
    TEMP_MAX = 120
    VEL_MIN = 0
    VEL_MAX = 10
    TIEMPO_MIN = 1  # segundos
    TIEMPO_MAX = 5400  # 90 minutos

    def __init__(self) -> None:
        # Estado general
        self._estado = EstadoRobot.APAGADO
        self._lock = threading.Lock()
        self._callback_actualizacion: Optional[Callable] = None

        # Ejecución de recetas (existente)
        self._receta_actual: Optional[Receta] = None
        self._progreso = 0.0
        self._indice_paso_actual = 0
        self._segundo_en_paso = 0
        self._hilo_coccion: Optional[threading.Thread] = None
        self._parar = False
        self._pausado = False
        self._confirmado = False

        # Ejecución manual (NUEVO)
        self._manual_activo = False
        self._manual_temperatura = 0
        self._manual_velocidad = 0
        self._manual_tiempo_restante = 0
        self._manual_tiempo_total = 0
        self._hilo_manual: Optional[threading.Thread] = None
        self._manual_parar = False
        self._manual_pausado = False
        
        # Estrategia de ejecución actual
        self._estrategia_actual: Optional[EstrategiaEjecucion] = None

    # ===== PROPIEDADES PÚBLICAS (existentes) =====

    @property
    def estado(self) -> str:
        with self._lock:
            return self._estado

    @property
    def receta_actual(self) -> Optional[Receta]:
        with self._lock:
            return self._receta_actual

    @property
    def progreso(self) -> float:
        with self._lock:
            return self._progreso

    @property
    def paso_actual(self) -> Optional[PasoReceta]:
        with self._lock:
            if self._receta_actual and 0 <= self._indice_paso_actual < len(self._receta_actual.pasos):
                return self._receta_actual.pasos[self._indice_paso_actual]
            return None

    @property
    def indice_paso_actual(self) -> int:
        with self._lock:
            return self._indice_paso_actual

    @property
    def segundo_en_paso(self) -> int:
        with self._lock:
            return self._segundo_en_paso

    # ===== PROPIEDADES PARA MODO MANUAL (NUEVO) =====

    @property
    def manual_activo(self) -> bool:
        """Indica si el modo manual está ejecutándose."""
        with self._lock:
            return self._manual_activo

    @property
    def manual_temperatura(self) -> int:
        """Temperatura actual en modo manual."""
        with self._lock:
            return self._manual_temperatura

    @property
    def manual_velocidad(self) -> int:
        """Velocidad actual en modo manual."""
        with self._lock:
            return self._manual_velocidad

    @property
    def manual_tiempo_restante(self) -> int:
        """Tiempo restante en segundos en modo manual."""
        with self._lock:
            return self._manual_tiempo_restante

    @property
    def manual_tiempo_total(self) -> int:
        """Tiempo total configurado para la cocción manual."""
        with self._lock:
            return self._manual_tiempo_total

    @property
    def manual_progreso(self) -> float:
        """Progreso de la cocción manual (0-100)."""
        with self._lock:
            if self._manual_tiempo_total > 0:
                return ((self._manual_tiempo_total - self._manual_tiempo_restante) / 
                        self._manual_tiempo_total) * 100.0
            return 0.0

    # ===== MÉTODOS DE CONFIGURACIÓN =====

    def registrar_callback_actualizacion(self, callback: Callable) -> None:
        """
        Registra una función que será llamada cuando cambie el estado.
        """
        with self._lock:
            self._callback_actualizacion = callback

    def _reset_progreso_y_posicion(self) -> None:
        """Resetea el progreso y la posición en la receta."""
        self._progreso = 0.0
        self._indice_paso_actual = 0
        self._segundo_en_paso = 0

    def _reset_estado_manual(self) -> None:
        """Resetea el estado del modo manual."""
        self._manual_activo = False
        self._manual_temperatura = 0
        self._manual_velocidad = 0
        self._manual_tiempo_restante = 0
        self._manual_tiempo_total = 0
        self._manual_parar = False
        self._manual_pausado = False

    # ===== VALIDACIÓN DE PARÁMETROS MANUALES =====

    def _validar_parametros_manuales(
        self, 
        temperatura: int, 
        velocidad: int, 
        tiempo: int
    ) -> None:
        """
        Valida los parámetros para cocción manual.
        Lanza ModoManualError si alguno es inválido.
        """
        if not (self.TEMP_MIN <= temperatura <= self.TEMP_MAX):
            raise ModoManualError(
                f"Temperatura debe estar entre {self.TEMP_MIN}°C y {self.TEMP_MAX}°C"
            )
        if not (self.VEL_MIN <= velocidad <= self.VEL_MAX):
            raise ModoManualError(
                f"Velocidad debe estar entre {self.VEL_MIN} y {self.VEL_MAX}"
            )
        if not (self.TIEMPO_MIN <= tiempo <= self.TIEMPO_MAX):
            raise ModoManualError(
                f"Tiempo debe estar entre {self.TIEMPO_MIN}s y {self.TIEMPO_MAX}s (90 min)"
            )

    # ===== CONTROL DE ENCENDIDO/APAGADO =====

    def encender(self) -> None:
        """Enciende el robot."""
        with self._lock:
            if self._estado == EstadoRobot.APAGADO:
                self._estado = EstadoRobot.ESPERA
                self._notificar_cambio()

    def apagar(self) -> None:
        """
        Apaga el robot. Detiene cualquier proceso en curso.
        """
        with self._lock:
            # Detener receta si está activa
            if self._hilo_coccion and self._hilo_coccion.is_alive():
                self._parar = True
            
            # Detener manual si está activo
            if self._hilo_manual and self._hilo_manual.is_alive():
                self._manual_parar = True
            
            self._receta_actual = None
            self._estado = EstadoRobot.APAGADO
            self._reset_progreso_y_posicion()
            self._reset_estado_manual()
            self._estrategia_actual = None
            self._notificar_cambio()

    # ===== SELECCIÓN DE RECETA =====

    def seleccionar_receta(self, receta: Receta) -> None:
        """
        Selecciona la receta a ejecutar.
        No inicia la cocción.
        """
        with self._lock:
            self._receta_actual = receta
            if self._estado != EstadoRobot.APAGADO:
                self._estado = EstadoRobot.ESPERA
            self._reset_progreso_y_posicion()
            self._parar = False
            self._pausado = False
            self._confirmado = False
            self._notificar_cambio()

    # ===== INICIAR COCCIÓN MANUAL (NUEVO) =====

    def iniciar_manual(
        self, 
        temperatura: int, 
        velocidad: int, 
        tiempo: int,
        forzar: bool = False
    ) -> None:
        """
        Inicia una cocción manual con los parámetros especificados.
        
        Args:
            temperatura: Temperatura en °C (0-120)
            velocidad: Velocidad (0-10)
            tiempo: Tiempo en segundos (1-5400)
            forzar: Si True, cancela cualquier ejecución activa sin preguntar
        
        Raises:
            RobotApagadoError: Si el robot está apagado
            ModoManualError: Si los parámetros son inválidos
            ConflictoEjecucionError: Si hay una ejecución activa y forzar=False
        """
        with self._lock:
            if self._estado == EstadoRobot.APAGADO:
                raise RobotApagadoError("No se puede cocinar con el robot apagado.")
            
            # Validar parámetros
            self._validar_parametros_manuales(temperatura, velocidad, tiempo)
            
            # Verificar conflicto con receta activa
            if not forzar and self._estrategia_actual is not None:
                if isinstance(self._estrategia_actual, EjecucionReceta):
                    raise ConflictoEjecucionError(
                        "Hay una receta en ejecución. Debe cancelarla primero."
                    )
                elif isinstance(self._estrategia_actual, EjecucionManual) and self._manual_activo:
                    raise ConflictoEjecucionError(
                        "Ya hay una cocción manual activa. Debe cancelarla primero."
                    )
            
            # Si llegamos aquí y hay algo activo, lo cancelamos (forzar=True)
            if self._hilo_coccion and self._hilo_coccion.is_alive():
                self._parar = True
                # Liberar lock temporalmente para permitir que el hilo termine
                self._lock.release()
                try:
                    self._hilo_coccion.join(timeout=3.0)
                finally:
                    self._lock.acquire()
            
            if self._hilo_manual and self._hilo_manual.is_alive():
                self._manual_parar = True
                # Liberar lock temporalmente para permitir que el hilo termine
                self._lock.release()
                try:
                    self._hilo_manual.join(timeout=3.0)
                finally:
                    self._lock.acquire()
            
            # Resetear estados de ejecuciones previas
            self._reset_progreso_y_posicion()
            self._parar = False
            self._pausado = False
            
            # Configurar parámetros manuales
            self._manual_temperatura = temperatura
            self._manual_velocidad = velocidad
            self._manual_tiempo_restante = tiempo
            self._manual_tiempo_total = tiempo
            self._manual_activo = True
            self._manual_parar = False
            self._manual_pausado = False
            
            # Establecer estrategia y estado
            self._estrategia_actual = EjecucionManual(temperatura, velocidad, tiempo)
            self._estado = EstadoRobot.COCINANDO
            
            # Iniciar hilo de ejecución manual
            self._hilo_manual = threading.Thread(
                target=self._ejecutar_manual_en_hilo,
                daemon=True,
            )
            self._notificar_cambio()
            self._hilo_manual.start()

    # ===== AJUSTAR PARÁMETROS EN CALIENTE (NUEVO) =====

    def ajustar_manual(
        self,
        temperatura: Optional[int] = None,
        velocidad: Optional[int] = None,
        tiempo: Optional[int] = None
    ) -> None:
        """
        Ajusta los parámetros de cocción manual mientras está en ejecución.
        Solo ajusta los parámetros proporcionados (no None).
        
        Args:
            temperatura: Nueva temperatura (opcional)
            velocidad: Nueva velocidad (opcional)
            tiempo: Nuevo tiempo restante (opcional)
        
        Raises:
            ModoManualError: Si modo manual no está activo o parámetros inválidos
        """
        with self._lock:
            if not self._manual_activo:
                raise ModoManualError("El modo manual no está activo.")
            
            # Validar parámetros individuales
            if temperatura is not None:
                if not (self.TEMP_MIN <= temperatura <= self.TEMP_MAX):
                    raise ModoManualError(
                        f"Temperatura debe estar entre {self.TEMP_MIN}°C y {self.TEMP_MAX}°C"
                    )
                self._manual_temperatura = temperatura
            
            if velocidad is not None:
                if not (self.VEL_MIN <= velocidad <= self.VEL_MAX):
                    raise ModoManualError(
                        f"Velocidad debe estar entre {self.VEL_MIN} y {self.VEL_MAX}"
                    )
                self._manual_velocidad = velocidad
            
            if tiempo is not None:
                if not (self.TIEMPO_MIN <= tiempo <= self.TIEMPO_MAX):
                    raise ModoManualError(
                        f"Tiempo debe estar entre {self.TIEMPO_MIN}s y {self.TIEMPO_MAX}s"
                    )
                self._manual_tiempo_restante = tiempo
                # Actualizar tiempo total si es mayor
                if tiempo > self._manual_tiempo_total:
                    self._manual_tiempo_total = tiempo
            
            self._notificar_cambio()

    # ===== PAUSAR / REANUDAR / CANCELAR =====

    def pausar(self) -> None:
        """
        Marca el robot como pausado. El hilo de cocción lo detectará
        y se detendrá guardando la posición actual.
        """
        with self._lock:
            if self._estado == EstadoRobot.COCINANDO:
                if self._manual_activo:
                    self._manual_pausado = True
                else:
                    self._pausado = True
                # El estado visible cambiará a PAUSADO cuando el hilo lo procese.

    def detener_coccion(self) -> None:
        """
        Cancela completamente la cocción actual (receta o manual).
        Resetea el progreso y la posición.
        """
        with self._lock:
            if self._estado in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, 
                               EstadoRobot.ESPERA, EstadoRobot.ESPERANDO_CONFIRMACION):
                # Cancelar receta
                self._parar = True
                self._pausado = False
                self._confirmado = False
                self._reset_progreso_y_posicion()
                
                # Cancelar manual
                self._manual_parar = True
                self._manual_pausado = False
                self._reset_estado_manual()
                
                self._estrategia_actual = None
                self._estado = EstadoRobot.ESPERA
                self._notificar_cambio()

    # ===== CONFIRMACIÓN DE PASO MANUAL =====

    def confirmar_paso_manual(self) -> None:
        """
        El usuario confirma que ha completado el paso manual.
        El hilo de cocción continuará.
        """
        with self._lock:
            if self._estado == EstadoRobot.ESPERANDO_CONFIRMACION:
                self._confirmado = True

    # ===== INICIAR / REANUDAR COCCIÓN DE RECETAS =====

    def iniciar_coccion(self, forzar: bool = False) -> None:
        """
        - Si el robot está en ESPERA: inicia la receta desde 0.
        - Si el robot está en PAUSADO o ESPERANDO_CONFIRMACION: reanuda desde el punto donde se pausó.
        
        Args:
            forzar: Si True, cancela cualquier cocción manual activa sin preguntar
        
        Raises:
            ConflictoEjecucionError: Si hay cocción manual activa y forzar=False
        """
        with self._lock:
            if self._estado == EstadoRobot.APAGADO:
                raise RobotApagadoError("No se puede cocinar con el robot apagado.")
            if self._receta_actual is None:
                raise RecetaNoSeleccionadaError("No hay ninguna receta seleccionada.")
            
            # Verificar conflicto con manual activo
            if not forzar and self._manual_activo:
                raise ConflictoEjecucionError(
                    "Hay una cocción manual activa. Debe cancelarla primero."
                )
            
            # Si hay manual activo y forzar=True, lo cancelamos
            if self._hilo_manual and self._hilo_manual.is_alive():
                self._manual_parar = True
                # Liberar lock temporalmente para permitir que el hilo termine
                self._lock.release()
                try:
                    self._hilo_manual.join(timeout=3.0)
                finally:
                    self._lock.acquire()
                self._reset_estado_manual()

            # ¿Reanudar desde pausa o confirmación?
            if self._estado in (EstadoRobot.PAUSADO, EstadoRobot.ESPERANDO_CONFIRMACION):
                # No reseteamos progreso ni posición
                self._pausado = False
                self._parar = False
                self._confirmado = False
            else:
                # Inicio desde cero
                self._reset_progreso_y_posicion()
                self._parar = False
                self._pausado = False
                self._confirmado = False

            # Si ya hay un hilo corriendo, lo marcamos para parar
            if self._hilo_coccion and self._hilo_coccion.is_alive():
                self._parar = True

            # Establecer estrategia
            self._estrategia_actual = EjecucionReceta(self._receta_actual)

            # Nuevo hilo de cocción
            self._hilo_coccion = threading.Thread(
                target=self._ejecutar_receta_en_hilo,
                daemon=True,
            )
            self._estado = EstadoRobot.COCINANDO
            self._notificar_cambio()
            self._hilo_coccion.start()

    # ===== HILO DE COCCIÓN MANUAL (NUEVO) =====

    def _ejecutar_manual_en_hilo(self) -> None:
        """
        Ejecuta la cocción manual: decrementa el temporizador cada segundo
        hasta que llegue a 0 o sea pausado/cancelado.
        """
        try:
            while True:
                time.sleep(1)
                
                with self._lock:
                    # Verificar cancelación o apagado
                    if self._manual_parar or self._estado == EstadoRobot.APAGADO:
                        self._reset_estado_manual()
                        self._estado = EstadoRobot.ESPERA
                        self._estrategia_actual = None
                        self._notificar_cambio()
                        return
                    
                    # Verificar pausa
                    if self._manual_pausado:
                        self._estado = EstadoRobot.PAUSADO
                        self._notificar_cambio()
                        return
                    
                    # Decrementar temporizador
                    if self._manual_tiempo_restante > 0:
                        self._manual_tiempo_restante -= 1
                        self._notificar_cambio()
                    
                    # Verificar finalización
                    if self._manual_tiempo_restante <= 0:
                        self._reset_estado_manual()
                        self._estado = EstadoRobot.ESPERA
                        self._estrategia_actual = None
                        self._notificar_cambio()
                        return
                        
        except Exception:
            with self._lock:
                self._estado = EstadoRobot.ERROR
                self._reset_estado_manual()
                self._estrategia_actual = None
                self._notificar_cambio()

    # ===== HILO DE COCCIÓN DE RECETAS (existente, sin cambios) =====

    def _ejecutar_receta_en_hilo(self) -> None:
        """
        Ejecuta la receta actual de forma incremental, permitiendo pausa y cancelación.
        Guarda en qué paso y segundo va, para poder reanudar.
        
        Los pasos manuales pausan automáticamente y esperan confirmación del usuario.
        
        CAMBIO IMPORTANTE: Ahora usa paso.tiempo_segundos en lugar de proceso.tiempo_segundos
        """
        try:
            with self._lock:
                receta = self._receta_actual
                if receta is None:
                    return
                pasos = receta.pasos
                total_pasos = len(pasos)
                i = self._indice_paso_actual
                t = self._segundo_en_paso

            if total_pasos == 0:
                with self._lock:
                    self._estado = EstadoRobot.ERROR
                    self._progreso = 0.0
                    self._estrategia_actual = None
                    self._notificar_cambio()
                return

            while True:
                with self._lock:
                    if self._parar or self._estado == EstadoRobot.APAGADO:
                        raise ProcesoInterrumpidoError("Proceso cancelado por el usuario.")
                    if i >= total_pasos:
                        break  # receta completada

                    paso = pasos[i]
                    proceso = paso.proceso
                    self._indice_paso_actual = i

                # ===== PASO MANUAL =====
                if proceso.es_manual():
                    with self._lock:
                        self._estado = EstadoRobot.ESPERANDO_CONFIRMACION
                        self._confirmado = False
                        self._notificar_cambio()

                    # Esperar confirmación del usuario
                    while True:
                        time.sleep(0.5)
                        with self._lock:
                            if self._parar or self._estado == EstadoRobot.APAGADO:
                                raise ProcesoInterrumpidoError("Proceso cancelado por el usuario.")
                            if self._confirmado:
                                break

                    # Usuario confirmó, avanzar al siguiente paso
                    with self._lock:
                        i += 1
                        t = 0
                        self._indice_paso_actual = i
                        self._segundo_en_paso = 0
                        # Calcular progreso
                        self._progreso = (i / total_pasos) * 100.0
                        self._estado = EstadoRobot.COCINANDO
                        self._notificar_cambio()
                    continue

                # ===== PASO AUTOMÁTICO =====
                # CAMBIO: Ahora leemos de paso.tiempo_segundos
                duracion = max(1, paso.tiempo_segundos or 1)

                # Ejecutar los "segundos" de este paso
                while t < duracion:
                    time.sleep(1)

                    with self._lock:
                        if self._parar or self._estado == EstadoRobot.APAGADO:
                            raise ProcesoInterrumpidoError("Proceso cancelado por el usuario.")
                        if self._pausado:
                            # Guardar posición actual y pasar a PAUSADO
                            self._indice_paso_actual = i
                            self._segundo_en_paso = t
                            self._estado = EstadoRobot.PAUSADO
                            self._notificar_cambio()
                            return

                        # Avanzar progreso global
                        self._progreso = (
                            (i + (t + 1) / duracion) / total_pasos
                        ) * 100.0
                        self._notificar_cambio()

                    t += 1

                # Paso completado, avanzar al siguiente
                with self._lock:
                    i += 1
                    t = 0
                    self._indice_paso_actual = i
                    self._segundo_en_paso = 0

            # Receta completada
            with self._lock:
                if self._estado != EstadoRobot.APAGADO:
                    self._progreso = 100.0
                    self._estado = EstadoRobot.ESPERA
                    self._reset_progreso_y_posicion()
                    self._estrategia_actual = None
                    self._notificar_cambio()

        except ProcesoInterrumpidoError:
            with self._lock:
                if self._estado != EstadoRobot.APAGADO:
                    self._estado = EstadoRobot.ESPERA
                    self._reset_progreso_y_posicion()
                    self._estrategia_actual = None
                    self._notificar_cambio()
        except Exception:
            with self._lock:
                self._estado = EstadoRobot.ERROR
                self._estrategia_actual = None
                self._notificar_cambio()

    # ===== NOTIFICAR CAMBIOS =====

    def _notificar_cambio(self) -> None:
        if self._callback_actualizacion is not None:
            try:
                self._callback_actualizacion(self)
            except Exception:
                # No dejamos que un fallo en la UI rompa el robot
                pass

    def __repr__(self) -> str:
        return (
            f"RobotCocina(estado={self._estado!r}, "
            f"receta_actual={self._receta_actual!r}, progreso={self._progreso:.1f}, "
            f"paso={self._indice_paso_actual}, segundo={self._segundo_en_paso}, "
            f"manual_activo={self._manual_activo})"
        )