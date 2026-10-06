# LABORATORIO
"""
Pruebas del reproductor de alertas: cola (deque), marcas de tiempo,
modo silencioso y, sobre todo, que nunca bloquea el ciclo de monitoreo.
"""

# LABORATORIO
import time
import unittest
from unittest.mock import patch

import alertas
import config
from alertas import reproductor, sonidos


# LABORATORIO
class RelojFalso:
    def __init__(self):
        self.ahora = time.time()

    def time(self):
        return self.ahora

    def avanzar(self, segundos):
        self.ahora += segundos


# LABORATORIO
class ReproductorConReloj(unittest.TestCase):

    def setUp(self):
        self.reloj = RelojFalso()
        parche_reloj = patch.object(reproductor, "time", self.reloj)
        parche_reloj.start()
        self.addCleanup(parche_reloj.stop)

        parche_sonido = patch.object(sonidos, "emitir")
        self.emitir = parche_sonido.start()
        self.addCleanup(parche_sonido.stop)

        alertas.silenciar(False)
        alertas.reiniciar()
        self.addCleanup(alertas.silenciar, config.MODO_SILENCIOSO)

    def test_ignora_los_eventos_sin_alerta_sonora(self):
        self.assertFalse(alertas.encolar("proceso_nuevo"))
        self.assertEqual(alertas.pendientes(), [])

    def test_no_repite_una_alerta_que_ya_espera(self):
        self.assertTrue(alertas.encolar("cpu_alta"))
        self.assertFalse(alertas.encolar("cpu_alta"))
        self.assertEqual(alertas.pendientes(), ["cpu_alta"])

    def test_la_primera_alerta_suena_de_inmediato(self):
        alertas.encolar("cpu_alta")

        self.assertEqual(alertas.actualizar(), "cpu_alta")
        self.emitir.assert_called_once_with("cpu_alta")
        self.assertEqual(alertas.pendientes(), [])

    def test_la_segunda_espera_a_que_termine_la_primera(self):
        alertas.encolar("cpu_alta")
        alertas.encolar("ram_alta")
        alertas.actualizar()

        # Mientras suena la primera, actualizar() no inicia la segunda.
        self.reloj.avanzar(sonidos.duracion("cpu_alta"))
        alertas.actualizar()
        self.assertEqual(self.emitir.call_count, 1)

        # Pasada la pausa entre alertas, entra la segunda.
        self.reloj.avanzar(config.PAUSA_ENTRE_ALERTAS_S)
        self.assertEqual(alertas.actualizar(), "ram_alta")
        self.assertEqual(self.emitir.call_count, 2)

    def test_las_alertas_suenan_en_el_orden_en_que_llegaron(self):
        orden = ["red_desconectada", "cpu_alta", "ram_alta"]

        for evento in orden:
            alertas.encolar(evento)

        sonadas = []

        for _ in orden:
            alertas.actualizar()
            sonadas.append(alertas.reproduciendo())
            self.reloj.avanzar(sonidos.duracion(sonadas[-1]))
            self.reloj.avanzar(config.PAUSA_ENTRE_ALERTAS_S)

        self.assertEqual(sonadas, orden)

    def test_una_alerta_caducada_se_descarta(self):
        alertas.encolar("cpu_alta")
        self.reloj.avanzar(config.ALERTA_CADUCA_S + config.PERIODO_RAPIDO)

        self.assertIsNone(alertas.actualizar())
        self.emitir.assert_not_called()
        self.assertEqual(alertas.pendientes(), [])

    def test_la_cola_tiene_un_maximo_y_pierde_la_mas_antigua(self):
        todas = list(config.ALERTAS_SONORAS)

        for evento in todas:
            alertas.encolar(evento)

        esperadas = todas[-config.COLA_ALERTAS_MAX:]
        self.assertEqual(alertas.pendientes(), esperadas)

    def test_modo_silencioso_avanza_la_cola_sin_emitir(self):
        alertas.silenciar(True)
        alertas.encolar("cpu_alta")

        self.assertEqual(alertas.actualizar(), "cpu_alta")
        self.emitir.assert_not_called()
        self.assertEqual(alertas.pendientes(), [])

    def test_alternar_silencio_invierte_el_modo(self):
        antes = alertas.silenciado()

        self.assertEqual(alertas.alternar_silencio(), not antes)
        self.assertEqual(alertas.silenciado(), not antes)

    def test_cuando_termina_ya_no_hay_alerta_sonando(self):
        alertas.encolar("cpu_alta")
        alertas.actualizar()

        self.reloj.avanzar(sonidos.duracion("cpu_alta"))
        self.assertIsNone(alertas.reproduciendo())


# LABORATORIO
class NoBloquea(unittest.TestCase):
    """Con el reloj real: mientras suena una alerta el ciclo sigue girando."""

    def setUp(self):
        parche = patch.object(sonidos, "emitir")
        parche.start()
        self.addCleanup(parche.stop)

        alertas.silenciar(False)
        alertas.reiniciar()

    def test_actualizar_vuelve_antes_de_que_termine_la_alerta(self):
        evento = "red_desconectada"
        alertas.encolar(evento)

        inicio = time.perf_counter()
        alertas.actualizar()
        tardo = time.perf_counter() - inicio

        self.assertLess(tardo, sonidos.duracion(evento))

    def test_el_ciclo_sigue_girando_mientras_suena(self):
        evento = "red_desconectada"
        alertas.encolar(evento)
        vueltas = 0
        inicio = time.perf_counter()

        # Mismo ritmo que el dashboard: una vuelta cada REFRESCO_MS.
        while alertas.actualizar() == evento:
            vueltas += 1
            time.sleep(config.REFRESCO_MS / config.MS_POR_SEGUNDO)

        transcurrido = time.perf_counter() - inicio
        self.assertGreater(vueltas, 0)
        self.assertGreaterEqual(transcurrido, sonidos.duracion(evento))


# LABORATORIO
if __name__ == "__main__":
    unittest.main()
