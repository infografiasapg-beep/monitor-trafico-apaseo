import os
import json
import time
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Credenciales desde los secretos de GitHub
TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
GCP_SA_JSON = os.environ.get("GCP_SA_KEY")
SPREADSHEET_NAME = "Trafico Apaseo"

# Huso horario local de Apaseo el Grande
ZONA_HORARIA = ZoneInfo("America/Mexico_City")

# Rango horario de captura: 5:30 am a 10:00 pm (22:00)
HORA_INICIO = dtime(5, 30)
HORA_FIN = dtime(22, 0)

# Lista de 21 registros calibrados y ordenados alfabéticamente
PUNTOS_MONITOREO = [
    # 1. Antonio Plaza
    {"zona": "Antonio Plaza (Norte a Sur)", "lat": 20.542009, "lon": -100.692750},

    # 2. Guadalupe Victoria (Elektra)
    {"zona": "Guadalupe Victoria - Elektra (Oeste a Este)", "lat": 20.545793, "lon": -100.688365},

    # 3. Jesús Cabrera M. (Escuela Nuevo Mundo) - Sentidos desacoplados
    {"zona": "Jesús Cabrera M. - Escuela Nuevo Mundo (Hacia Norte)", "lat": 20.546650, "lon": -100.693080},
    {"zona": "Jesús Cabrera M. - Escuela Nuevo Mundo (Hacia Sur)", "lat": 20.545950, "lon": -100.692950},

    # 4. Jesús Cabrera M. (Semáforo Oxxo) - Sentidos desacoplados
    {"zona": "Jesús Cabrera M. - Semáforo Oxxo (Hacia Norte / Salida)", "lat": 20.545300, "lon": -100.692800},
    {"zona": "Jesús Cabrera M. - Semáforo Oxxo (Hacia Sur / Centro)", "lat": 20.545850, "lon": -100.693000},

    # 5. Juan Aldama (Puente Colorado)
    {"zona": "Juan Aldama - Puente Colorado (Sur a Norte)", "lat": 20.547680, "lon": -100.686440},

    # 6. Mariano Matamoros (Presidencia)
    {"zona": "Mariano Matamoros - Presidencia (Sur a Norte)", "lat": 20.545107, "lon": -100.688410},

    # 7. Melchor Ocampo (Sanatorio Macías)
    {"zona": "Melchor Ocampo - Sanatorio Macías (Norte a Sur)", "lat": 20.546439, "lon": -100.689101},

    # 8. Morelos (Semáforo Lienzo Charro) - Sentidos desacoplados
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Oriente / Salida)", "lat": 20.543142, "lon": -100.678080},
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Poniente / Centro)", "lat": 20.543250, "lon": -100.678750},

    # 9. Narciso Mendoza (Libros Rocío) - Coordenada (20.54802, -100.68644)
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Oriente / Puente Colorado)", "lat": 20.548020, "lon": -100.686440},
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Poniente / Ocampo)", "lat": 20.548180, "lon": -100.687200},

    # 10. Narciso Mendoza (Semáforo Este a Oeste) - Sentidos desacoplados
    {"zona": "Narciso Mendoza - Semáforo (Hacia Oriente)", "lat": 20.547922, "lon": -100.685871},
    {"zona": "Narciso Mendoza - Semáforo (Hacia Poniente)", "lat": 20.547980, "lon": -100.685350},

    # 11. Octaviano Muñoz Ledo (Los Charcos)
    {"zona": "Octaviano Muñoz Ledo - Los Charcos (Este a Oeste)", "lat": 20.548394, "lon": -100.689885},

    # 12. Pípila (Mercado)
    {"zona": "Pípila - Mercado (Sur a Norte)", "lat": 20.546627, "lon": -100.691033},

    # 13. Piña Soria (Auto Zone) - Sentidos desacoplados
    {"zona": "Piña Soria - Auto Zone (Hacia Este / Salida Qro)", "lat": 20.541750, "lon": -100.691800},
    {"zona": "Piña Soria - Auto Zone (Hacia Oeste / Centro)", "lat": 20.541880, "lon": -100.692600},

    # 14. Venustiano Carranza (Central)
    {"zona": "Venustiano Carranza - Central (Este a Oeste)", "lat": 20.545699, "lon": -100.692539},

    # 15. Vicente Ruiz (Aurrerá)
    {"zona": "Vicente Ruiz - Aurrerá (Sur a Norte)", "lat": 20.548210, "lon": -100.690237},
]

DIAS
