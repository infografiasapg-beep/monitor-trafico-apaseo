import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Lee las credenciales desde los secretos de GitHub
TOMTOM_API_KEY = os.environ.get("TOMTOM_API_KEY")
GCP_SA_JSON = os.environ.get("GCP_SA_KEY")
SPREADSHEET_NAME = "Trafico Apaseo"  # Nombre exacto de tu hoja en Google Sheets

# Zona horaria local de Apaseo el Grande (Tiempo del Centro de México)
ZONA_HORARIA = ZoneInfo("America/Mexico_City")

PUNTOS_MONITOREO = [
    {"zona": "Entronque Carretera Panamericana / Libramiento", "lat": 20.5482, "lon": -100.6865},
    {"zona": "Acceso Autopista Celaya-Querétaro", "lat": 20.5365, "lon": -100.6720},
    {"zona": "Zona Centro (Calle Ignacio Allende)", "lat": 20.5428, "lon": -100.6833},
    {"zona": "Prolongación Hidalgo / Zona Comercial", "lat": 20.5451, "lon": -100.6902}
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GCP_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1

def consultar_trafico_tomtom(lat, lon):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={TOMTOM_API_KEY}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("flowSegmentData", {})
            current_speed = data.get("currentSpeed", 0)
            free_flow_speed = data.get("freeFlowSpeed", 0)
            if free_flow_speed > 0:
                congestion = max(0, ((free_flow_speed - current_speed) / free_flow_speed) * 100)
            else:
                congestion = 0.0
            return round(congestion, 1)
    except Exception as e:
        print(f"Error consultando TomTom: {e}")
    return 0.0

def ejecutar():
    # Obtiene la hora local de México
    ahora = datetime.now(ZONA_HORARIA)
    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA[ahora.weekday()]
    hora_str = ahora.strftime("%H:%M")

    sheet = conectar_google_sheets()
    filas_nuevas = []

    for punto in PUNTOS_MONITOREO:
        pct_congestion = consultar_trafico_tomtom(punto["lat"], punto["lon"])
        fila = [fecha_str, dia_str, hora_str, f"{pct_congestion}%", punto["zona"]]
        filas_nuevas.append(fila)
        print(f"[{hora_str}] {punto['zona']}: {pct_congestion}%")

    sheet.append_rows(filas_nuevas)
    print(f"Datos registrados con éxito a las {hora_str} (Hora México).")

if __name__ == "__main__":
    ejecutar()
