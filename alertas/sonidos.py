# LABORATORIO
"""
alertas/sonidos.py
Construccion y emision de los sonidos de alerta.
En macOS se usa afplay (
"""

# LABORATORIO
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from array import array

import config

# LABORATORIO
try:
    import winsound
except ImportError:
    winsound = None

# LABORATORIO
_archivos = {}

# LABORATORIO
_proceso = None


# LABORATORIO
def existe(evento):
    """True si el evento tiene una alerta sonora definida."""
    return evento in config.ALERTAS_SONORAS


# LABORATORIO
def etiqueta(evento):
    """Nombre legible de la alerta, para mostrarlo en pantalla."""
    return config.ALERTAS_SONORAS[evento]["etiqueta"]


# LABORATORIO
def duracion(evento):
    """Duracion total de la alerta en segundos, pausas incluidas."""
    notas = config.ALERTAS_SONORAS[evento]["notas"]
    total_ms = sum(nota_ms + pausa_ms for _, nota_ms, pausa_ms in notas)
    return total_ms / config.MS_POR_SEGUNDO


# LABORATORIO
def _externo():
    """Comando de audio del sistema (macOS), o None si no aplica."""
    if sys.platform == config.PLATAFORMA_MAC:
        return shutil.which(config.COMANDO_AUDIO_MAC)

    return None


# LABORATORIO
def motor():
    """Nombre del mecanismo que se usara para emitir el sonido."""
    if winsound is not None:
        return "winsound"

    if _externo() is not None:
        return config.COMANDO_AUDIO_MAC

    return "campana del sistema"


# LABORATORIO
def _sintetizar(notas):
    """Convierte una secuencia de notas en muestras de audio."""
    muestras = array("h")
    por_ms = config.MUESTREO_HZ / config.MS_POR_SEGUNDO
    suave = int(config.FADE_MS * por_ms)

    for frecuencia, nota_ms, pausa_ms in notas:
        total = int(nota_ms * por_ms)

        for i in range(total):
            envolvente = min(i, total - i, suave) / suave
            onda = math.sin(math.tau * frecuencia * i / config.MUESTREO_HZ)
            muestras.append(
                int(config.AMPLITUD_MAX * config.VOLUMEN * envolvente * onda)
            )

        muestras.frombytes(
            bytes(int(pausa_ms * por_ms) * config.BYTES_MUESTRA)
        )

    return muestras


# LABORATORIO
def _archivo(evento):
    """Ruta del WAV de la alerta. Lo genera si todavia no existe."""
    ruta = _archivos.get(evento)

    if ruta is not None and os.path.exists(ruta):
        return ruta

    ruta = os.path.join(
        tempfile.gettempdir(),
        f"{config.PREFIJO_ARCHIVO_SONIDO}{evento}.wav"
    )

    muestras = _sintetizar(config.ALERTAS_SONORAS[evento]["notas"])

    with wave.open(ruta, "wb") as archivo:
        archivo.setnchannels(config.CANALES)
        archivo.setsampwidth(config.BYTES_MUESTRA)
        archivo.setframerate(config.MUESTREO_HZ)
        archivo.writeframes(muestras.tobytes())

    _archivos[evento] = ruta
    return ruta


# LABORATORIO
def preparar():
    """Genera de antemano todos los WAV, para que la primera alerta no
    tenga que sintetizarse en pleno ciclo de monitoreo."""
    if winsound is None and _externo() is None:
        return

    for evento in config.ALERTAS_SONORAS:
        try:
            _archivo(evento)
        except OSError:
            pass  


# LABORATORIO
def _campana():
    sys.stdout.write(config.CAMPANA)
    sys.stdout.flush()


# LABORATORIO
def emitir(evento):
    """Inicia el sonido y vuelve de inmediato: nunca espera a que termine."""
    global _proceso

    if winsound is not None:
        try:
            winsound.PlaySound(
                _archivo(evento),
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        except (OSError, RuntimeError):
            _campana()
        return

    comando = _externo()

    if comando is None:
        _campana()
        return

    try:
        _proceso = subprocess.Popen(
            [comando, _archivo(evento)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except OSError:
        _campana()


# LABORATORIO
def detener():
    """Corta el sonido que este en curso."""
    if winsound is not None:
        winsound.PlaySound(None, winsound.SND_PURGE)

    if _proceso is not None and _proceso.poll() is None:
        _proceso.terminate()
