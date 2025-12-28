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

    def numero_pasos(self) -> int:
        return len(self._pasos)

    @abstractmethod
    def es_editable(self) -> bool:
        """Indica si la receta puede ser modificada o eliminada."""
        pass

    @abstractmethod
    def icono_origen(self) -> str:
        """Devuelve el icono que representa el origen de la receta."""
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self._id}, nombre={self._nombre!r}, "
            f"origen={self._origen!r}, pasos={len(self._pasos)})"
        )


class RecetaBase(Receta):
    """Receta de fábrica (no editable)."""
    
    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        descripcion: str,
        ingredientes: List[Dict[str, Any]],
        pasos: List[PasoReceta],
    ) -> None:
        super().__init__(id_, nombre, descripcion, ingredientes, pasos, origen="base")
    
    def es_editable(self) -> bool:
        """Las recetas de fábrica no se pueden editar."""
        return False
    
    def icono_origen(self) -> str:
        """Icono de fábrica."""
        return "factory"


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
        super().__init__(id_, nombre, descripcion, ingredientes, pasos, origen="usuario")
    
    def es_editable(self) -> bool:
        """Las recetas de usuario sí se pueden editar."""
        return True
    
    def icono_origen(self) -> str:
        """Icono de usuario."""
        return "person"


# =========================
# Estados del robot
# =========================

class EstadoRobot:
    APAGADO = "apagado"
    ESPERA = "en_espera"
    COCINANDO = "cocinando"
    PAUSADO = "pausado"
    ESPERANDO_CONFIRMACION = "esperando_confirmacion"  # Esperando que usuario confirme paso manual
    ERROR = "error"


# =========================
# Robot de cocina
# =========================

class RobotCocina:
    """
    Emula el comportamiento de un robot de cocina.

    - Encendido / apagado
    - Selección de receta
    - Hilo de cocción con progreso
    - PAUSAR / REANUDAR
    - CANCELAR (detener_coccion)
    - Confirmación de pasos manuales
    """

    def __init__(
        self,
        callback_actualizacion: Optional[Callable[["RobotCocina"], None]] = None,
    ) -> None:
        self._estado = EstadoRobot.APAGADO
        self._receta_actual: Optional[Receta] = None
        self._progreso: float = 0.0

        self._hilo_coccion: Optional[threading.Thread] = None
        self._parar: bool = False
        self._pausado: bool = False
        self._confirmado: bool = False  # Para pasos manuales

        # Para poder reanudar desde donde se pausó
        self._indice_paso_actual: int = 0   # índice 0..N-1 en self._receta_actual.pasos
        self._segundo_en_paso: int = 0      # segundo actual dentro del paso

        self._lock = threading.Lock()
        self._callback_actualizacion = callback_actualizacion

    # ----- Propiedades públicas -----

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def receta_actual(self) -> Optional[Receta]:
        return self._receta_actual

    @property
    def progreso(self) -> float:
        """Progreso en porcentaje (0.0 a 100.0)."""
        return self._progreso

    @property
    def indice_paso_actual(self) -> int:
        """
        Índice (0-based) del paso actual dentro de receta_actual.pasos.
        Solo tiene sentido cuando hay receta seleccionada.
        """
        return self._indice_paso_actual

    # ----- Utilidades internas de estado -----

    def _reset_progreso_y_posicion(self) -> None:
        self._progreso = 0.0
        self._indice_paso_actual = 0
        self._segundo_en_paso = 0

    # ----- Energía -----

    def encender(self) -> None:
        with self._lock:
            self._estado = EstadoRobot.ESPERA
            self._reset_progreso_y_posicion()
            self._parar = False
            self._pausado = False
            self._confirmado = False
            self._notificar_cambio()

    def apagar(self) -> None:
        with self._lock:
            self._parar = True
            self._pausado = False
            self._confirmado = False
            self._receta_actual = None
            self._estado = EstadoRobot.APAGADO
            self._reset_progreso_y_posicion()
            self._notificar_cambio()

    # ----- Selección de receta -----

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

    # ----- PAUSAR / REANUDAR / CANCELAR -----

    def pausar(self) -> None:
        """
        Marca el robot como pausado. El hilo de cocción lo detectará
        y se detendrá guardando la posición actual.
        """
        with self._lock:
            if self._estado == EstadoRobot.COCINANDO:
                self._pausado = True
                # El estado visible cambiará a PAUSADO cuando el hilo lo procese.

    def detener_coccion(self) -> None:
        """
        Cancela completamente la cocción actual.
        Resetea el progreso y la posición de la receta.
        """
        with self._lock:
            if self._estado in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, 
                               EstadoRobot.ESPERA, EstadoRobot.ESPERANDO_CONFIRMACION):
                self._parar = True
                self._pausado = False
                self._confirmado = False
                self._reset_progreso_y_posicion()
                self._estado = EstadoRobot.ESPERA
                self._notificar_cambio()

    # ----- Confirmación de paso manual -----

    def confirmar_paso_manual(self) -> None:
        """
        El usuario confirma que ha completado el paso manual.
        El hilo de cocción continuará.
        """
        with self._lock:
            if self._estado == EstadoRobot.ESPERANDO_CONFIRMACION:
                self._confirmado = True

    # ----- Iniciar / reanudar cocción -----

    def iniciar_coccion(self) -> None:
        """
        - Si el robot está en ESPERA: inicia la receta desde 0.
        - Si el robot está en PAUSADO o ESPERANDO_CONFIRMACION: reanuda desde el punto donde se pausó.
        """
        with self._lock:
            if self._estado == EstadoRobot.APAGADO:
                raise RobotApagadoError("No se puede cocinar con el robot apagado.")
            if self._receta_actual is None:
                raise RecetaNoSeleccionadaError("No hay ninguna receta seleccionada.")

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

            # Nuevo hilo de cocción
            self._hilo_coccion = threading.Thread(
                target=self._ejecutar_receta_en_hilo,
                daemon=True,
            )
            self._estado = EstadoRobot.COCINANDO
            self._notificar_cambio()
            self._hilo_coccion.start()

    # ----- Hilo de cocción -----

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
                    self._notificar_cambio()

        except ProcesoInterrumpidoError:
            with self._lock:
                if self._estado != EstadoRobot.APAGADO:
                    self._estado = EstadoRobot.ESPERA
                    self._reset_progreso_y_posicion()
                    self._notificar_cambio()
        except Exception:
            with self._lock:
                self._estado = EstadoRobot.ERROR
                self._notificar_cambio()

    # ----- Notificar cambios -----

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
            f"paso={self._indice_paso_actual}, segundo={self._segundo_en_paso})"
        )