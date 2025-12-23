import re


def mmss_a_segundos(valor: str) -> int:
    """
    Convierte 'MM:SS' a segundos.
    Acepta 00:00 hasta 99:59.
    Lanza ValueError si el formato es inválido.
    """
    if not isinstance(valor, str):
        raise ValueError("Formato de tiempo inválido")

    patron = r'^(\d{1,2}):([0-5]\d)$'
    match = re.match(patron, valor.strip())

    if not match:
        raise ValueError("El tiempo debe tener formato MM:SS (ej. 02:30)")

    minutos = int(match.group(1))
    segundos = int(match.group(2))

    total = minutos * 60 + segundos

    if total <= 0:
        raise ValueError("El tiempo debe ser mayor que 00:00")

    if minutos > 99:
        raise ValueError("El tiempo máximo es 99:59")

    return total


def segundos_a_mmss(segundos: int) -> str:
    """
    Convierte segundos a 'MM:SS'.
    """
    if segundos is None or segundos <= 0:
        return "00:00"

    minutos = segundos // 60
    resto = segundos % 60

    if minutos > 99:
        minutos = 99
        resto = 59

    return f"{minutos:02d}:{resto:02d}"
