# LABORATORIO
"""
Pruebas de la reaccion a los eventos: el despachador registra el evento
en la bitacora y ademas encola su alerta sonora. Incluye una prueba del
ciclo completo del nucleo con la red cayendo y volviendo.
"""

# LABORATORIO
import time
import unittest
from unittest.mock import patch

import alertas
import almacenamiento as registro
import config
import eventos
import nucleo
from alertas import sonidos
from eventos import detectores


# LABORATORIO
class ManejadoresDeRed(unittest.TestCase):

    def setUp(self):
        registro.limpiar_eventos()
        alertas.reiniciar()

    def test_los_tres_eventos_de_red_estan_registrados(self):
        for evento in ("red_desconectada", "red_conectada",
                       "red_sigue_desconectada"):
            with self.subTest(evento=evento):
                self.assertIn(evento, eventos.eventos_conocidos())

    def test_red_desconectada_es_una_alerta(self):
        anotado = eventos.atender("red_desconectada", {"segundos": 0})

        self.assertEqual(anotado["nivel"], "ALERTA")
        self.assertEqual(anotado["origen"], "red_desconectada")

    def test_red_conectada_informa_la_duracion_de_la_caida(self):
        anotado = eventos.atender("red_conectada", {"segundos": config.PRUEBA_SEGUNDOS_CAIDA})

        self.assertEqual(anotado["nivel"], "INFO")
        self.assertIn(str(config.PRUEBA_SEGUNDOS_CAIDA), anotado["mensaje"])

    def test_el_recordatorio_informa_cuanto_lleva_sin_red(self):
        anotado = eventos.atender("red_sigue_desconectada", {"segundos": config.PRUEBA_SEGUNDOS_CAIDA})

        self.assertEqual(anotado["nivel"], "ALERTA")
        self.assertIn(str(config.PRUEBA_SEGUNDOS_CAIDA), anotado["mensaje"])

    def test_atender_un_evento_encola_su_alerta_sonora(self):
        eventos.atender("red_desconectada", {"segundos": 0})

        self.assertEqual(alertas.pendientes(), ["red_desconectada"])

    def test_un_evento_sin_sonido_no_encola_nada(self):
        eventos.atender("proceso_nuevo", {"nombre": "prueba"})

        self.assertEqual(alertas.pendientes(), [])

    def test_un_evento_desconocido_no_rompe_ni_suena(self):
        eventos.atender("evento_inexistente", {})

        self.assertEqual(alertas.pendientes(), [])


# LABORATORIO
class CicloCompleto(unittest.TestCase):
    """nucleo.ciclo() con una lectura de conexion simulada."""

    def setUp(self):
        registro.limpiar_eventos()
        alertas.silenciar(False)
        alertas.reiniciar()
        self.addCleanup(alertas.silenciar, config.MODO_SILENCIOSO)

        parche = patch.object(sonidos, "emitir")
        self.emitir = parche.start()
        self.addCleanup(parche.stop)

        detectores._estado["conexion"] = True
        detectores._estado["red_desde"] = None
        detectores._estado["red_aviso"] = None

        self.conectado = True
        parche = patch("sensores.leer", side_effect=self._leer)
        parche.start()
        self.addCleanup(parche.stop)

        nucleo._activos = ["conexion"]
        self.addCleanup(nucleo._activos.clear)

    def _leer(self, clave):
        return {
            "valor": float(self.conectado),
            "unidad": "estado",
            "porcentaje": config.PORCENTAJE_CONECTADO,
            "detalle": "",
            "extra": {"conectado": self.conectado},
        }

    def _vuelta(self):
        """Una vuelta del ciclo en la que toca leer el grupo rapido."""
        ahora = time.time()

        for clave in nucleo._marcas:
            nucleo._marcas[clave] = ahora

        nucleo._marcas["rapido"] = ahora - config.PERIODO_RAPIDO
        return nucleo.ciclo()

    def test_la_caida_de_red_genera_el_evento_y_suena_su_alerta(self):
        self.assertEqual(self._vuelta()["eventos"], [])

        self.conectado = False
        resultado = self._vuelta()

        self.assertEqual([e["origen"] for e in resultado["eventos"]],
                         ["red_desconectada"])
        self.assertEqual(alertas.reproduciendo(), "red_desconectada")
        self.emitir.assert_called_once_with("red_desconectada")

    def test_el_ciclo_sigue_detectando_mientras_suena_la_alerta(self):
        self.conectado = False
        self._vuelta()
        self.assertEqual(alertas.reproduciendo(), "red_desconectada")

        # La alerta sigue sonando, pero el ciclo ya devuelve lecturas
        # nuevas y detecta la recuperacion sin esperar a que termine.
        self.conectado = True
        resultado = self._vuelta()

        self.assertEqual([e["origen"] for e in resultado["eventos"]],
                         ["red_conectada"])
        self.assertEqual(alertas.reproduciendo(), "red_desconectada")
        self.assertEqual(alertas.pendientes(), ["red_conectada"])


# LABORATORIO
if __name__ == "__main__":
    unittest.main()
