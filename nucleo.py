"""
nucleo.py
Motor de monitoreo. Aqui esta el bucle orientado a eventos.
Diseño clave: el ciclo no usa time.sleep() para esperar. Cada metrica
guarda su propia marca de tiempo y se lee cuando le toca. Asi un solo
ciclo atiende tareas con periodos distintos sin bloquearse, que es el
patron recomendado de la Unidad 2.
La funcion ciclo() no bloquea: se puede llamar cada 200 ms desde un
dashboard grafico o desde un bucle de consola. Ella decide sola que
hay que leer en ese instante.
"""

import time
import alertas 
import config
import sensores
import eventos
import almacenamiento as registro

GRUPO_RAPIDO = ["cpu", "memoria", "red", "conexion"]  # LABORATORIO
GRUPO_LENTO = ["disco", "procesos", "bateria"]

_marcas = {"rapido": 0.0, "lento": 0.0, "reporte": 0.0}


_ultimas = {}
_activos = []


def iniciar():
    """Detecta que sensores existen en este equipo y prepara el ciclo."""
    global _activos

    _activos = sensores.disponibles()
    alertas.preparar()  # LABORATORIO
    ahora = time.time()

    for clave in _marcas:
        _marcas[clave] = ahora

    
    for clave in _activos:
        _ultimas[clave] = sensores.leer(clave)

    ausentes = [c for c in sensores.LECTORES if c not in _activos]

    for clave in ausentes:
        eventos.atender("sensor_ausente", {"metrica": clave})

    registro.registrar_evento(
        "INFO",
        "sistema",
        f"Nodo {config.NODO} iniciado | sensores activos: "
        f"{', '.join(_activos)}"
    )

    return _activos


def _leer_grupo(claves):
    """Lee un grupo de metricas y despacha los eventos que provoquen."""
    nuevos = []

    for clave in claves:
        if clave not in _activos:
            continue

        lectura = sensores.leer(clave)
        _ultimas[clave] = lectura

        if lectura is not None:
            registro.agregar(clave, lectura["valor"])

        for nombre, dato in eventos.detectar(clave, lectura):
            nuevos.append(eventos.atender(nombre, dato))

    return nuevos


def ciclo():
    """Una vuelta del bucle de monitoreo. No bloquea.
    Devuelve un diccionario con las ultimas lecturas y con los eventos
    generados en esta vuelta.
    """
    ahora = time.time()
    nuevos = []

    if ahora - _marcas["rapido"] >= config.PERIODO_RAPIDO:
        nuevos += _leer_grupo(GRUPO_RAPIDO)
        _marcas["rapido"] = ahora

    if ahora - _marcas["lento"] >= config.PERIODO_LENTO:
        nuevos += _leer_grupo(GRUPO_LENTO)
        _marcas["lento"] = ahora

    if ahora - _marcas["reporte"] >= config.PERIODO_REPORTE:
        nuevos.append(generar_reporte())
        _marcas["reporte"] = ahora

    alertas.actualizar()  # LABORATORIO

    return {"lecturas": dict(_ultimas), "eventos": nuevos}


def generar_reporte():
    """Resume el periodo, lo guarda en la bitacora y vacia el historial."""
    datos = registro.resumen()
    registro.guardar_bitacora(datos)
    registro.limpiar_periodo()

    return eventos.atender(
        "reporte",
        {"metricas": len(datos["metricas"])}
    )


def lecturas():
    """Ultimas lecturas conocidas, sin forzar una nueva medicion."""
    return dict(_ultimas)


def activos():
    return list(_activos)


if __name__ == "__main__":
    iniciar()

    for _ in range(10):
        resultado = ciclo()
        for e in resultado["eventos"]:
            print(f"{e['hora']} [{e['nivel']}] {e['mensaje']}")
        time.sleep(0.5)
