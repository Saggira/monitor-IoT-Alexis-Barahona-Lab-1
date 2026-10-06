"""
eventos/detectores.py
Convierten lecturas numericas en eventos.
Los cuatro tipos de evento del curso estan representados aqui:
 1. Por umbral con histeresis .... cpu_alta, ram_alta, disco_lleno,
 red_pico, bateria_baja
 2. Por flanco ................... nucleo_saturado, swap_activo,
 cargador_conectado, proceso_nuevo
 3. Por tiempo ................... lo genera el nucleo, no este modulo
 4. Por falla o ausencia ......... sensor_ausente, lectura_invalida,
 salto_anomalo
Cada detector devuelve una LISTA de pares (nombre_evento, dato).
Una misma lectura puede producir varios eventos a la vez.
"""

import time  # LABORATORIO

import config
import almacenamiento as registro

_estado = {
    "alarma": {}, 
    "nucleos": [],  
    "swap": False,
    "cargador": None,
    "pids": set(),
    "nombres": set(),
    "previo": {},  
    "conexion": True,  # LABORATORIO: se supone conectado hasta que se demuestre lo contrario
    "red_desde": None,  # LABORATORIO: marca de tiempo en que se perdio la red
    "red_aviso": None,  # LABORATORIO: marca de tiempo del ultimo aviso
}


def _histeresis(clave, valor, alto, bajo, ev_sube, ev_baja):
    """Umbral con dos limites. Devuelve la lista de eventos generados.
    Con un solo umbral, una lectura oscilando entre 69.9 y 70.1 generaria
    decenas de eventos. Con dos, hay que bajar de `bajo` para que el
    sistema acepte que la condicion termino.
    """
    activa = _estado["alarma"].get(clave, False)

    if not activa and valor >= alto:
        _estado["alarma"][clave] = True
        return [(ev_sube, {"valor": round(valor, 1), "umbral": alto})]

    if activa and valor <= bajo:
        _estado["alarma"][clave] = False
        return [(ev_baja, {"valor": round(valor, 1), "umbral": bajo})]

    return []


def _salto(clave, valor):
    """Anomalia: variacion brusca entre dos muestras consecutivas."""
    previo = _estado["previo"].get(clave)
    _estado["previo"][clave] = valor

    if previo is None:
        return []

    diferencia = abs(valor - previo)

    if diferencia >= config.SALTO_ANOMALO:
        return [
            (
                "salto_anomalo",
                {
                    "metrica": clave,
                    "de": round(previo, 1),
                    "a": round(valor, 1),
                    "salto": round(diferencia, 1),
                },
            )
        ]

    return []



def _cpu(lectura):
    eventos = []
    valor = lectura["valor"]

    if not 0.0 <= valor <= 100.0:
        return [("lectura_invalida", {"metrica": "cpu", "valor": valor})]

    eventos += _salto("cpu", valor)

    promedio = registro.media("cpu")

    if promedio is not None:
        eventos += _histeresis(
            "cpu",
            promedio,
            config.CPU_ALTO,
            config.CPU_BAJO,
            "cpu_alta",
            "cpu_normal",
        )

    nucleos = lectura["extra"]["nucleos"]
    anterior = _estado["nucleos"]

    if len(anterior) != len(nucleos):
        anterior = [False] * len(nucleos)

    actual = []

    for i, uso in enumerate(nucleos):
        saturado = uso >= config.CPU_NUCLEO_SATURADO

        if saturado and not anterior[i]:
            eventos.append(("nucleo_saturado", {"nucleo": i, "valor": uso}))

        elif not saturado and anterior[i]:
            eventos.append(("nucleo_libre", {"nucleo": i, "valor": uso}))

        actual.append(saturado)

    _estado["nucleos"] = actual

    return eventos


def _memoria(lectura):
    eventos = []
    promedio = registro.media("memoria")

    if promedio is not None:
        eventos += _histeresis(
            "memoria",
            promedio,
            config.RAM_ALTA,
            config.RAM_BAJA,
            "ram_alta",
            "ram_normal",
        )

    usa_swap = lectura["extra"]["usa_swap"]

    if usa_swap != _estado["swap"]:
        _estado["swap"] = usa_swap
        nombre = "swap_activo" if usa_swap else "swap_inactivo"
        eventos.append((nombre, {"valor": lectura["extra"]["swap_pct"]}))

    return eventos


def _disco(lectura):
    return _histeresis(
        "disco",
        lectura["valor"],
        config.DISCO_LLENO,
        config.DISCO_ALIVIADO,
        "disco_lleno",
        "disco_aliviado",
    )


def _red(lectura):
    return _histeresis(
        "red",
        lectura["valor"],
        config.RED_PICO_KBS,
        config.RED_CALMA_KBS,
        "red_pico",
        "red_calma",
    )


def _procesos(lectura):
    """Flanco sobre conjuntos: lo que entra y lo que sale.
    Restar dos conjuntos resuelve en una linea lo que con listas y
    bucles anidados tomaria veinte.
    """
    eventos = []

    nombres = {
        n
        for n in lectura["extra"]["nombres"]
        if not n.startswith(config.PROCESOS_IGNORADOS)
    }

    anteriores = _estado["nombres"]

    if anteriores:  # la primera vuelta no compara
        for nuevo in nombres - anteriores:
            eventos.append(("proceso_nuevo", {"nombre": nuevo}))

        for cerrado in anteriores - nombres:
            eventos.append(("proceso_cerrado", {"nombre": cerrado}))

    _estado["nombres"] = nombres

    for p in lectura["extra"]["top"]:
        if p["cpu"] >= config.PROCESO_PESADO:
            eventos.append(("proceso_pesado", p))
        break  # basta con avisar del mayor

    return eventos


def _bateria(lectura):
    eventos = []

    carga = lectura["valor"]
    activa = _estado["alarma"].get("bateria", False)

    if not activa and carga <= config.BATERIA_BAJA:
        _estado["alarma"]["bateria"] = True
        eventos.append(
            (
                "bateria_baja",
                {
                    "valor": carga,
                    "umbral": config.BATERIA_BAJA,
                },
            )
        )

    elif activa and carga >= config.BATERIA_RECUPERADA:
        _estado["alarma"]["bateria"] = False
        eventos.append(
            (
                "bateria_recuperada",
                {
                    "valor": carga,
                    "umbral": config.BATERIA_RECUPERADA,
                },
            )
        )

    conectado = lectura["extra"]["conectado"]

    if _estado["cargador"] is None:
        _estado["cargador"] = conectado  # primera lectura: no hay flanco

    elif conectado != _estado["cargador"]:
        _estado["cargador"] = conectado
        nombre = (
            "cargador_conectado"
            if conectado
            else "cargador_desconectado"
        )
        eventos.append((nombre, {"valor": lectura["valor"]}))

    return eventos


# LABORATORIO
def _conexion(lectura):
    """Perdida y recuperacion de la red, con recordatorio por tiempo.
    Flanco de bajada: red_desconectada (una sola vez).
    Mientras siga caida: red_sigue_desconectada cada RECORDATORIO_RED_S.
    Flanco de subida: red_conectada, con lo que duro la caida.
    """
    eventos = []
    conectado = lectura["extra"]["conectado"]
    ahora = time.time()

    if not conectado and _estado["conexion"]:
        _estado["conexion"] = False
        _estado["red_desde"] = ahora
        _estado["red_aviso"] = ahora
        caida = ahora - _estado["red_desde"]
        eventos.append(("red_desconectada", {"segundos": round(caida)}))

    elif conectado and not _estado["conexion"]:
        _estado["conexion"] = True
        caida = ahora - _estado["red_desde"]
        eventos.append(("red_conectada", {"segundos": round(caida)}))

    elif (not conectado
          and ahora - _estado["red_aviso"] >= config.RECORDATORIO_RED_S):
        _estado["red_aviso"] = ahora
        caida = ahora - _estado["red_desde"]
        eventos.append(("red_sigue_desconectada", {"segundos": round(caida)}))

    return eventos


DETECTORES = {
    "cpu": _cpu,
    "memoria": _memoria,
    "disco": _disco,
    "red": _red,
    "procesos": _procesos,
    "bateria": _bateria,
    "conexion": _conexion,  # LABORATORIO
}


def detectar(clave, lectura):
    """Punto de entrada del modulo.
    Recibe la clave de la metrica y su lectura; devuelve la lista de
    eventos que esa lectura provoco. Si la lectura es None, el sensor
    no respondio y eso tambien es un evento.
    """
    if lectura is None:
        ya_fallaba = _estado["alarma"].get(f"falla_{clave}", False)

        if not ya_fallaba:
            _estado["alarma"][f"falla_{clave}"] = True
            return [("sensor_ausente", {"metrica": clave})]

        return []

    if _estado["alarma"].get(f"falla_{clave}", False):
        _estado["alarma"][f"falla_{clave}"] = False

    funcion = DETECTORES.get(clave)

    if funcion is None:
        return []

    return funcion(lectura)