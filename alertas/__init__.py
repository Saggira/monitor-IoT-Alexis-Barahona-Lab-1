# LABORATORIO
"""
Paquete alertas
Reaccion sonora a los eventos del nodo. Se divide en dos modulos:
    sonidos.py       construye y emite el sonido de cada alerta
    reproductor.py   cola de alertas pendientes con marcas de tiempo
Ninguno de los dos conoce los sensores ni los detectores: reciben el
nombre de un evento y deciden si suena y cuando
"""
# LABORATORIO
from .sonidos import preparar, motor, etiqueta
from .reproductor import (encolar, actualizar, reproduciendo, pendientes,
                          silenciar, silenciado, alternar_silencio,
                          reiniciar)
