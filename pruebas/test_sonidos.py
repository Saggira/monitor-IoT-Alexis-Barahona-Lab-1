# LABORATORIO
"""
Pruebas del catalogo de alertas sonoras: cada evento tiene su sonido,
todos son distintos y los archivos de audio se generan bien.
"""

# LABORATORIO
import os
import unittest
import wave
from unittest.mock import patch

import config
from alertas import sonidos
from eventos.manejadores import MANEJADORES


# LABORATORIO
class CatalogoDeAlertas(unittest.TestCase):

    def test_toda_alerta_sonora_corresponde_a_un_evento_con_manejador(self):
        for evento in config.ALERTAS_SONORAS:
            with self.subTest(evento=evento):
                self.assertIn(evento, MANEJADORES)

    def test_cubre_cpu_memoria_trafico_y_conexion(self):
        for evento in ("cpu_alta", "ram_alta", "red_pico",
                       "red_desconectada", "red_conectada",
                       "red_sigue_desconectada"):
            with self.subTest(evento=evento):
                self.assertTrue(sonidos.existe(evento))

    def test_no_hay_dos_alertas_con_el_mismo_sonido(self):
        patrones = [alerta["notas"]
                    for alerta in config.ALERTAS_SONORAS.values()]

        self.assertEqual(len(set(patrones)), len(patrones))

    def test_cada_alerta_tiene_etiqueta_y_al_menos_una_nota(self):
        for evento, alerta in config.ALERTAS_SONORAS.items():
            with self.subTest(evento=evento):
                self.assertTrue(alerta["etiqueta"])
                self.assertTrue(alerta["notas"])

    def test_duracion_suma_notas_y_pausas(self):
        notas = config.ALERTAS_SONORAS["cpu_alta"]["notas"]
        esperada = sum(n + p for _, n, p in notas) / config.MS_POR_SEGUNDO

        self.assertAlmostEqual(sonidos.duracion("cpu_alta"), esperada)


# LABORATORIO
class ArchivosDeAudio(unittest.TestCase):

    def test_el_wav_generado_dura_lo_que_dice_la_configuracion(self):
        for evento in config.ALERTAS_SONORAS:
            with self.subTest(evento=evento):
                ruta = sonidos._archivo(evento)
                self.addCleanup(os.remove, ruta)

                with wave.open(ruta, "rb") as audio:
                    segundos = audio.getnframes() / audio.getframerate()
                    self.assertEqual(audio.getnchannels(), config.CANALES)
                    self.assertEqual(audio.getsampwidth(),
                                     config.BYTES_MUESTRA)

                self.assertAlmostEqual(segundos, sonidos.duracion(evento),
                                       places=config.PRUEBA_DECIMALES)

    def test_el_volumen_nunca_supera_la_amplitud_maxima(self):
        muestras = sonidos._sintetizar(
            config.ALERTAS_SONORAS["cpu_alta"]["notas"]
        )

        self.assertLessEqual(max(muestras), config.AMPLITUD_MAX)
        self.assertGreaterEqual(min(muestras), -config.AMPLITUD_MAX)


# LABORATORIO
class Emision(unittest.TestCase):

    def test_sin_winsound_se_usa_la_campana_del_sistema(self):
        with patch.object(sonidos, "winsound", None), \
             patch.object(sonidos, "_externo", return_value=None), \
             patch.object(sonidos, "_campana") as campana:
            sonidos.emitir("cpu_alta")

        campana.assert_called_once_with()

    def test_en_mac_se_lanza_el_reproductor_sin_esperar(self):
        with patch.object(sonidos, "winsound", None), \
             patch.object(sonidos, "_externo",
                          return_value=config.COMANDO_AUDIO_MAC), \
             patch.object(sonidos, "_archivo", return_value="alerta.wav"), \
             patch.object(sonidos.subprocess, "Popen") as lanzar:
            sonidos.emitir("cpu_alta")

        lanzar.assert_called_once()
        self.assertEqual(lanzar.call_args.args[0],
                         [config.COMANDO_AUDIO_MAC, "alerta.wav"])

    def test_en_windows_se_reproduce_en_modo_asincrono(self):
        falso = patch.object(sonidos, "winsound").start()
        self.addCleanup(patch.stopall)
        falso.SND_FILENAME = 1 << 0
        falso.SND_ASYNC = 1 << 1

        with patch.object(sonidos, "_archivo", return_value="alerta.wav"):
            sonidos.emitir("cpu_alta")

        banderas = falso.PlaySound.call_args.args[1]
        self.assertTrue(banderas & falso.SND_ASYNC)


# LABORATORIO
if __name__ == "__main__":
    unittest.main()
