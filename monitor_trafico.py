import os
import json
import time
from datetime import datetime
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

# Lista completa de puntos de monitoreo calibrados
PUNTOS_MONITOREO = [
    # 1. Rodolfo Piña Soria (Semáforo) - Doble sentido
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Este/NE", "lat": 20.541310, "lon": -100.693311, "heading": 65},
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Oeste/SO", "lat": 20.541310, "lon": -100.693311, "heading": 245},

    # 2. Rodolfo Piña Soria (ETA) - Doble sentido
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Este/NE", "lat": 20.542033, "lon": -100.691589, "heading": 65},
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Oeste/SO", "lat": 20.542033, "lon": -100.691589, "heading": 245},

    # 3. Antonio Plaza (Gas. Mobil) - Sentido Norte
    {"zona": "Antonio Plaza (Gas. Mobil)", "lat": 20.541935, "lon": -100.692770, "heading": 25},

    # 4. Vicente Guerrero / Antonio Plaza - Sentido Norte
    {"zona": "Vicente Guerrero / Antonio Plaza", "lat": 20.543529, "lon": -100.692272, "heading": 25},

    # 5. Pípila / Venustiano Carranza - Sentido Norte
    {"zona": "Pipila / Venustiano Carranza", "lat": 20.545164, "lon": -100.691833, "heading": 25},

    # 6. Pípila (Mercado) - Sentido Norte
    {"zona": "Pipila (Mercado)", "lat": 20.546697, "lon": -100.690982, "heading": 25},

    # 7. Antonio Plaza (Mercado) - Sentido Sur
    {"zona": "Antonio Plaza (Mercado)", "lat": 20.546480, "lon": -100.690602, "heading": 205},

    # 8. Jesús Cabrera Muñoz Ledo (Semáforo) - Doble sentido
    {"zona": "Jesus Cabrera Muñoz Ledo (Semáforo) - Hacia Norte", "lat": 20.545480, "lon": -100.692821, "heading": 350},
    {"zona": "Jesus Cabrera Muñoz Ledo (Semáforo) - Hacia Sur", "lat": 20.545480, "lon": -100.692821, "heading": 170},

    # 9. Jesús Cabrera Muñoz Ledo (Nutrióloga) - Doble sentido
    {"zona": "Jesus Cabrera Muñoz Ledo (Nutriologa) - Hacia Norte", "lat": 20.546340, "lon": -100.693041, "heading": 350},
    {"zona": "Jesus Cabrera Muñoz Ledo (Nutriologa) - Hacia Sur", "lat": 20.546340, "lon": -100.693041, "heading": 170},

    # 10. Octaviano Muñoz Ledo con esq. Nicolás San Luis de Montañez - Doble sentido
    {"zona": "Octaviano Muñoz Ledo esq. Nicolas San Luis - Hacia Este/Centro", "lat": 20.549326, "lon": -100.692837, "heading": 115},
    {"zona": "Octaviano Muñoz Ledo esq. Nicolas San Luis - Hacia Poniente/Salida", "lat": 20.549326, "lon": -100.692837, "heading": 295},

    # 11. Nicolás San Luis de Montañez esq. Octaviano Muñoz Ledo - Doble sentido
    {"zona": "Nicolas San Luis de Montañez es
