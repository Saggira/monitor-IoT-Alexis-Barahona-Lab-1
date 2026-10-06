# LABORATORIO
"""
sensores/conexion.py
Estado de la conexion de red.

sensores/red.py mide cuanto trafico pasa, pero no dice si el equipo esta
conectado: con la red caida el trafico simplemente vale 0, igual que con
la red en calma. Este sensor responde otra pregunta: hay ruta hacia el
exterior?

Se resuelve abriendo un socket UDP y llamando a connect(). En UDP eso no
envia ningun paquete: solo consulta la tabla de rutas del sistema. Es
instantaneo, no depende de internet ni de ningun servidor, y falla en el
acto cuando se apaga el Wi-Fi o se desconecta el cable.
"""

# LABORATORIO
import socket

import psutil

import config

# LABORATORIO
ETIQUETA = "Conexion"
UNIDAD = "estado"
TEXTO_CONECTADA = "CONECTADA"
TEXTO_DESCONECTADA = "SIN RED"


# LABORATORIO
def disponible():
    """El sistema operativo siempre puede consultar sus rutas."""
    return True


# LABORATORIO
def _direccion_local():
    """IP con la que el equipo saldria al exterior, o None si no hay ruta."""
    sonda = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sonda.connect((config.SONDA_IP, config.SONDA_PUERTO))
        direccion, _puerto = sonda.getsockname()
    except OSError:
        return None
    finally:
        sonda.close()

    if direccion.startswith(config.PREFIJOS_SIN_RED):
        return None

    return direccion


# LABORATORIO
def _interfaz(direccion):
    """Nombre del adaptador que tiene esa IP (Wi-Fi, Ethernet...)."""
    try:
        for nombre, direcciones in psutil.net_if_addrs().items():
            for d in direcciones:
                if d.address == direccion:
                    return nombre
    except Exception:
        pass

    return None


# LABORATORIO
def leer():
    direccion = _direccion_local()
    conectado = direccion is not None
    interfaz = _interfaz(direccion) if conectado else None

    if conectado:
        detalle = f"salida por {interfaz or '?'} | {direccion}"
    else:
        detalle = "sin ruta hacia el exterior"

    return {
        "valor": float(conectado),
        "unidad": UNIDAD,
        "porcentaje": (config.PORCENTAJE_CONECTADO if conectado
                       else config.PORCENTAJE_DESCONECTADO),
        "detalle": detalle,
        "extra": {
            "conectado": conectado,
            "direccion": direccion,
            "interfaz": interfaz,
            "texto": TEXTO_CONECTADA if conectado else TEXTO_DESCONECTADA,
        },
    }
