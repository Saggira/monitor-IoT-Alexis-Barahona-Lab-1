# LABORATORIO
"""
Pruebas del sensor de conexion y de los eventos de red:
red_desconectada, red_conectada y red_sigue_desconectada.
"""

# LABORATORIO
import time
import unittest
from collections import namedtuple
from unittest.mock import patch

import config
import eventos
from eventos import detectores
from sensores import conexion


# LABORATORIO
class RelojFalso:
    """Reloj controlado por la prueba: el tiempo solo avanza si ella quiere."""

    def __init__(self):
        self.ahora = time.time()

    def time(self):
        return self.ahora

    def avanzar(self, segundos):
        self.ahora += segundos


# LABORATORIO
def _lectura(conectado):
    return {"valor": float(conectado), "extra": {"conectado": conectado}}


# LABORATORIO
def _nombres(lista):
    return [nombre for nombre, _ in lista]


# LABORATORIO
class DetectorConexion(unittest.TestCase):

    def setUp(self):
        self.reloj = RelojFalso()
        parche = patch.object(detectores, "time", self.reloj)
        parche.start()
        self.addCleanup(parche.stop)

        detectores._estado["conexion"] = True
        detectores._estado["red_desde"] = None
        detectores._estado["red_aviso"] = None
        detectores._estado["alarma"].pop("falla_conexion", None)

    def test_con_red_estable_no_hay_eventos(self):
        for _ in range(config.VENTANA):
            self.reloj.avanzar(config.PERIODO_RAPIDO)
            self.assertEqual(eventos.detectar("conexion", _lectura(True)), [])

    def test_la_caida_genera_red_desconectada_una_sola_vez(self):
        primera = eventos.detectar("conexion", _lectura(False))
        self.assertEqual(_nombres(primera), ["red_desconectada"])

        self.reloj.avanzar(config.PERIODO_RAPIDO)
        segunda = eventos.detectar("conexion", _lectura(False))
        self.assertEqual(segunda, [])

    def test_no_hay_recordatorio_antes_del_intervalo(self):
        eventos.detectar("conexion", _lectura(False))

        self.reloj.avanzar(config.RECORDATORIO_RED_S - config.PERIODO_RAPIDO)
        self.assertEqual(eventos.detectar("conexion", _lectura(False)), [])

    def test_el_recordatorio_llega_al_cumplirse_el_intervalo(self):
        eventos.detectar("conexion", _lectura(False))

        self.reloj.avanzar(config.RECORDATORIO_RED_S)
        recordatorio = eventos.detectar("conexion", _lectura(False))

        self.assertEqual(_nombres(recordatorio), ["red_sigue_desconectada"])
        self.assertEqual(recordatorio[0][1]["segundos"],
                         round(config.RECORDATORIO_RED_S))

    def test_el_recordatorio_se_repite_cada_intervalo(self):
        eventos.detectar("conexion", _lectura(False))
        avisos = []

        for _ in range(config.VENTANA):
            self.reloj.avanzar(config.RECORDATORIO_RED_S)
            avisos += _nombres(eventos.detectar("conexion", _lectura(False)))

        self.assertEqual(avisos, ["red_sigue_desconectada"] * config.VENTANA)

    def test_la_recuperacion_informa_cuanto_duro_la_caida(self):
        eventos.detectar("conexion", _lectura(False))

        self.reloj.avanzar(config.RECORDATORIO_RED_S)
        recuperada = eventos.detectar("conexion", _lectura(True))

        self.assertEqual(_nombres(recuperada), ["red_conectada"])
        self.assertEqual(recuperada[0][1]["segundos"],
                         round(config.RECORDATORIO_RED_S))

    def test_despues_de_recuperar_no_hay_mas_recordatorios(self):
        eventos.detectar("conexion", _lectura(False))
        self.reloj.avanzar(config.RECORDATORIO_RED_S)
        eventos.detectar("conexion", _lectura(True))

        self.reloj.avanzar(config.RECORDATORIO_RED_S)
        self.assertEqual(eventos.detectar("conexion", _lectura(True)), [])

    def test_una_segunda_caida_vuelve_a_avisar(self):
        eventos.detectar("conexion", _lectura(False))
        eventos.detectar("conexion", _lectura(True))

        nueva = eventos.detectar("conexion", _lectura(False))
        self.assertEqual(_nombres(nueva), ["red_desconectada"])


# LABORATORIO
Direccion = namedtuple("Direccion", "address")


# LABORATORIO
class SondaFalsa:
    """Socket UDP simulado: connect() falla o devuelve la IP indicada."""

    def __init__(self, direccion, puerto=config.SONDA_PUERTO):
        self.direccion = direccion
        self.puerto = puerto

    def __call__(self, *argumentos):
        return self

    def connect(self, destino):
        if self.direccion is None:
            raise OSError("Network is unreachable")

    def getsockname(self):
        return (self.direccion, self.puerto)

    def close(self):
        pass


# LABORATORIO
class SensorConexion(unittest.TestCase):

    def _leer(self, direccion):
        interfaces = {"Wi-Fi": [Direccion("192.168.1.20")]}

        with patch.object(conexion.socket, "socket", SondaFalsa(direccion)), \
             patch.object(conexion.psutil, "net_if_addrs",
                          return_value=interfaces):
            return conexion.leer()

    def test_con_ruta_hacia_el_exterior_esta_conectado(self):
        lectura = self._leer("192.168.1.20")

        self.assertTrue(lectura["extra"]["conectado"])
        self.assertEqual(lectura["extra"]["interfaz"], "Wi-Fi")
        self.assertEqual(lectura["extra"]["texto"], conexion.TEXTO_CONECTADA)
        self.assertEqual(lectura["porcentaje"], config.PORCENTAJE_CONECTADO)

    def test_sin_ruta_esta_desconectado(self):
        lectura = self._leer(None)

        self.assertFalse(lectura["extra"]["conectado"])
        self.assertEqual(lectura["extra"]["texto"],
                         conexion.TEXTO_DESCONECTADA)
        self.assertEqual(lectura["porcentaje"],
                         config.PORCENTAJE_DESCONECTADO)

    def test_las_direcciones_sin_red_real_cuentan_como_desconectado(self):
        for direccion in ("127.0.0.1", "169.254.10.20", "0.0.0.0"):
            with self.subTest(direccion=direccion):
                self.assertFalse(
                    self._leer(direccion)["extra"]["conectado"]
                )

    def test_la_lectura_cumple_la_estructura_estandar_de_los_sensores(self):
        for conectado in ("192.168.1.20", None):
            lectura = self._leer(conectado)

            for clave in ("valor", "unidad", "porcentaje", "detalle", "extra"):
                self.assertIn(clave, lectura)


# LABORATORIO
if __name__ == "__main__":
    unittest.main()
