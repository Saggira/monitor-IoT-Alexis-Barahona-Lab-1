# LABORATORIO
"""
alertas/reproductor.py
Cola de alertas sonoras con marcas de tiempo.

Este modulo nunca espera: no hay time.sleep() ni hilos. Funciona igual
que el resto del nucleo, con marcas de tiempo:
    - encolar(evento) solo anota la alerta en un deque y vuelve.
    - actualizar() se llama en cada vuelta del ciclo de monitoreo. Si la
      alerta anterior ya termino (su marca de fin quedo atras), saca la
      siguiente de la cola y la inicia. Si no, vuelve sin hacer nada.
Mientras suena una alerta el ciclo sigue leyendo sensores, detectando
eventos y refrescando el dashboard.
"""

# LABORATORIO
import time
from collections import deque

import config
from . import sonidos

# LABORATORIO
_cola = deque(maxlen=config.COLA_ALERTAS_MAX)


# LABORATORIO
_estado = {
    "actual": None,
    "fin": time.time(),
    "libre": time.time(),
    "silencio": config.MODO_SILENCIOSO,
}


# LABORATORIO
def encolar(evento):
    """Anota la alerta del evento. Devuelve True si quedo en la cola.
    Ignora los eventos sin sonido y las alertas ya pendientes."""
    if not sonidos.existe(evento):
        return False

    if any(pendiente == evento for pendiente, _ in _cola):
        return False

    _cola.append((evento, time.time()))
    return True


# LABORATORIO
def reproduciendo():
    """Alerta que esta sonando en este instante, o None."""
    if time.time() < _estado["fin"]:
        return _estado["actual"]

    return None


# LABORATORIO
def actualizar():
    """Una vuelta del reproductor. No bloquea.
    Devuelve la alerta que esta sonando, o None."""
    ahora = time.time()

    if ahora < _estado["libre"]:
        return reproduciendo()

    while _cola:
        evento, marca = _cola.popleft()

        if ahora - marca > config.ALERTA_CADUCA_S:
            continue

        _estado["actual"] = evento
        _estado["fin"] = ahora + sonidos.duracion(evento)
        _estado["libre"] = _estado["fin"] + config.PAUSA_ENTRE_ALERTAS_S

        if not _estado["silencio"]:
            sonidos.emitir(evento)

        break

    return reproduciendo()


# LABORATORIO
def pendientes():
    """Nombres de las alertas que esperan su turno."""
    return [evento for evento, _ in _cola]


# LABORATORIO
def silenciar(valor=True):
    """Activa o desactiva el modo silencioso."""
    _estado["silencio"] = bool(valor)

    if _estado["silencio"]:
        sonidos.detener()


# LABORATORIO
def silenciado():
    return _estado["silencio"]


# LABORATORIO
def alternar_silencio():
    """Invierte el modo silencioso y devuelve el nuevo estado."""
    silenciar(not _estado["silencio"])
    return _estado["silencio"]


# LABORATORIO
def reiniciar():
    """Vacia la cola y deja el reproductor libre. Lo usan las pruebas."""
    _cola.clear()
    ahora = time.time()
    _estado.update({"actual": None, "fin": ahora, "libre": ahora})
