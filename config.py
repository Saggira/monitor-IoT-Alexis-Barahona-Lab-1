"""
config.py
Parametros de configuracion del nodo de telemetria.
Todo lo que puede cambiar entre una instalacion y otra vive aqui.
Ningun otro archivo del proyecto debe contener un numero literal.

Alexis Barahona (8-1029-1162) - 1GS134

Unidad 2 - Programacion en Python para sistemas IoT
Facultad de Ingenieria de Sistemas Computacionales - UTP
"""

import os

NODO = "Laptop_Alexis"
UBICACION = "Actividad en clase 3 - Desarrollo de Software VIII"

PERIODO_RAPIDO = 1.0 # cpu, memoria, red
PERIODO_LENTO = 5.0 # disco, procesos, bateria
PERIODO_REPORTE = 30.0 # resumen periodico hacia la bitacora
REFRESCO_MS = 200 # cada cuanto refresca el dashboard 

CPU_ALTO = 70.0
CPU_BAJO = 50.0
CPU_NUCLEO_SATURADO = 90.0 
RAM_ALTA = 85.0
RAM_BAJA = 75.0
DISCO_LLENO = 90.0 
DISCO_ALIVIADO = 85.0
RED_PICO_KBS = 500.0 
RED_CALMA_KBS = 200.0
BATERIA_BAJA = 20.0
BATERIA_RECUPERADA = 30.0
PROCESO_PESADO = 50.0 
SALTO_ANOMALO = 40.0

VENTANA = 10 
MAX_EVENTOS_LOG = 200 
ARCHIVO_BITACORA = "bitacora.json"

UNIDAD_DISCO = "C:\\" if os.name == "nt" else "/"
TOP_PROCESOS = 8

PROCESOS_IGNORADOS = ("kworker", "kthread", "ksoftirqd", "migration",
 "rcu_", "irq/", "svchost")


SONDA_IP = "8.8.8.8"
SONDA_PUERTO = 80
PREFIJOS_SIN_RED = ("0.", "127.", "169.254.") 
RECORDATORIO_RED_S = 15.0 
PORCENTAJE_CONECTADO = 100.0  
PORCENTAJE_DESCONECTADO = 0.0


MODO_SILENCIOSO = False  
COLA_ALERTAS_MAX = 8  
ALERTA_CADUCA_S = 10.0  
PAUSA_ENTRE_ALERTAS_S = 0.3 

MUESTREO_HZ = 22050
CANALES = 1
BYTES_MUESTRA = 2
AMPLITUD_MAX = 32767
VOLUMEN = 0.5  
FADE_MS = 8  
MS_POR_SEGUNDO = 1000.0
PREFIJO_ARCHIVO_SONIDO = "lab_alerta_"
CAMPANA = "\a"  
PLATAFORMA_MAC = "darwin"  # sys.platform de macOS
COMANDO_AUDIO_MAC = "afplay"  # reproductor de audio incluido en macOS


ALERTAS_SONORAS = {
    "cpu_alta": {
        "etiqueta": "CPU alta",
        "notas": ((600, 100, 40), (800, 100, 40), (1000, 100, 40),
                  (1300, 300, 0)),
    },
    "cpu_normal": {
        "etiqueta": "CPU normal",
        "notas": ((800, 100, 40), (600, 200, 0)),
    },
    "ram_alta": {
        "etiqueta": "Memoria alta",
        "notas": ((330, 350, 120), (220, 550, 0)),
    },
    "ram_normal": {
        "etiqueta": "Memoria normal",
        "notas": ((330, 150, 0),),
    },
    "red_pico": {
        "etiqueta": "Pico de trafico",
        "notas": ((1200, 45, 45), (1200, 45, 45), (1200, 45, 45),
                  (1200, 45, 45), (1200, 45, 0)),
    },
    "red_calma": {
        "etiqueta": "Trafico normal",
        "notas": ((1200, 60, 0),),
    },
    "red_desconectada": {
        "etiqueta": "Red desconectada",
        "notas": ((1000, 250, 0), (500, 250, 0), (1000, 250, 0),
                  (500, 250, 0), (1000, 250, 0), (500, 250, 0)),
    },
    "red_conectada": {
        "etiqueta": "Red conectada",
        "notas": ((500, 150, 30), (1000, 300, 0)),
    },
    "red_sigue_desconectada": {
        "etiqueta": "Sigue sin red",
        "notas": ((500, 150, 200), (500, 150, 0)),
    },
}

# LABORATORIO
COLUMNAS_TARJETAS = 4
GEOMETRIA_VENTANA = "1360x760"
FUENTE_SONIDO = ("Segoe UI", 10, "bold")
MARGEN_SONIDO = 14

# LABORATORIO
PRUEBA_DECIMALES = 2  
PRUEBA_SEGUNDOS_CAIDA = 42  
