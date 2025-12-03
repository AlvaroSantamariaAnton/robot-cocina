import threading
import time
from typing import List, Optional, Callable


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
# Modelos de dominio
# =========================

class ProcesoCocina:
    """
    Representa un proceso genérico de cocina dentro del robot.

    Esta clase se mapea con la tabla de procesos (base o usuario) en la BD.
    """

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        tipo: str,
        temperatura: int,
        tiempo_segundos: int,
        velocidad: int,
        origen: str = "base",
    ) -> None:
        self._id = id_
        self._nombre = nombre
        self._tipo = tipo
        self._temperatura = temperatura
        self._tiempo_segundos = tiempo_segundos
        self._velocidad = velocidad
        self._origen = origen

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
    def temperatura(self) -> int:
        return self._temperatura

    @property
    def tiempo_segundos(self) -> int:
        return self._tiempo_segundos

    @property
    def velocidad(self) -> int:
        return self._velocidad

    @property
    def origen(self) -> str:
        return self._origen

    def descripcion_resumida(self) -> str:
        """Devuelve una descripción corta tipo: 'Picar verduras - 5s - vel 3'."""
        partes = [self._nombre]
        if self._temperatura:
            partes.append(f"{self._temperatura}ºC")
        if self._tiempo_segundos:
            partes.append(f"{self._tiempo_segundos}s")
        if self._velocidad:
            partes.append(f"vel {self._velocidad}")
        return " - ".join(partes)

    def __repr__(self) -> str:
        return (
            f"ProcesoCocina(id={self._id}, nombre={self._nombre!r}, tipo={self._tipo!r}, "
            f"temp={self._temperatura}, tiempo={self._tiempo_segundos}, "
            f"velocidad={self._velocidad}, origen={self._origen!r})"
        )


class PasoReceta:
    """Un paso concreto dentro de una receta (orden + proceso)."""

    def __init__(self, orden: int, proceso: ProcesoCocina) -> None:
        self._orden = orden
        self._proceso = proceso

    @property
    def orden(self) -> int:
        return self._orden

    @property
    def proceso(self) -> ProcesoCocina:
        return self._proceso

    def __repr__(self) -> str:
        return f"PasoReceta(orden={self._orden}, proceso={self._proceso!r})"


class Receta:
    """Receta formada por varios pasos de cocina."""

    def __init__(
        self,
        id_: Optional[int],
        nombre: str,
        descripcion: str,
        pasos: List[PasoReceta],
        origen: str = "base",
    ) -> None:
        self._id = id_
        self._nombre = nombre
        self._descripcion = descripcion
        # Aseguramos que los pasos están ordenados
        self._pasos = sorted(pasos, key=lambda p: p.orden)
        self._origen = origen

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
    def pasos(self) -> List[PasoReceta]:
        # Devolvemos copia para no permitir modificaciones externas directas
        return list(self._pasos)

    @property
    def origen(self) -> str:
        return self._origen

    def numero_pasos(self) -> int:
        return len(self._pasos)

    def __repr__(self) -> str:
        return (
            f"Receta(id={self._id}, nombre={self._nombre!r}, origen={self._origen!r}, "
            f"pasos={len(self._pasos)})"
        )


# =========================
# Estados del robot
# =========================

class EstadoRobot:
    APAGADO = "apagado"
    ESPERA = "en_espera"
    COCINANDO = "cocinando"
    PAUSADO = "pausado"
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
            self._notificar_cambio()

    def apagar(self) -> None:
        with self._lock:
            self._parar = True
            self._pausado = False
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
            if self._estado in (EstadoRobot.COCINANDO, EstadoRobot.PAUSADO, EstadoRobot.ESPERA):
                self._parar = True
                self._pausado = False
                self._reset_progreso_y_posicion()
                self._estado = EstadoRobot.ESPERA
                self._notificar_cambio()

    # ----- Iniciar / reanudar cocción -----

    def iniciar_coccion(self) -> None:
        """
        - Si el robot está en ESPERA: inicia la receta desde 0.
        - Si el robot está en PAUSADO: reanuda desde el punto donde se pausó.
        """
        with self._lock:
            if self._estado == EstadoRobot.APAGADO:
                raise RobotApagadoError("No se puede cocinar con el robot apagado.")
            if self._receta_actual is None:
                raise RecetaNoSeleccionadaError("No hay ninguna receta seleccionada.")

            # ¿Reanudar desde pausa?
            if self._estado == EstadoRobot.PAUSADO:
                # No reseteamos progreso ni posición
                self._pausado = False
                self._parar = False
            else:
                # Inicio desde cero
                self._reset_progreso_y_posicion()
                self._parar = False
                self._pausado = False

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
                    duracion = max(1, paso.proceso.tiempo_segundos)

                    # Por si la receta ha cambiado externamente
                    self._indice_paso_actual = i

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
                self._progreso = 100.0
                self._estado = EstadoRobot.ESPERA
                # Reseteamos posición para que la próxima vez empiece desde cero
                self._reset_progreso_y_posicion()
                self._notificar_cambio()

        except ProcesoInterrumpidoError:
            with self._lock:
                # Si se cancela, dejamos estado en ESPERA y progreso en 0
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
