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
    {"zona": "Nicolas San Luis de Montañez esq. Octaviano - Hacia Norte", "lat": 20.549086, "lon": -100.693303, "heading": 25},
    {"zona": "Nicolas San Luis de Montañez esq. Octaviano - Hacia Sur", "lat": 20.549086, "lon": -100.693303, "heading": 205},

    # 12. Vicente A. Ruiz (Aurrerá) - Sentido Poniente
    {"zona": "Vicente A. Ruiz. (Aurrerá)", "lat": 20.548228, "lon": -100.690233, "heading": 295},

    # 13. Octaviano Muñoz Ledo (Los Charcos) - Sentido Oriente
    {"zona": "Octaviano Muñoz Ledo (Los Charcos)", "lat": 20.548410, "lon": -100.689976, "heading": 115},

    # 14. Melchor Ocampo (Sanatorio Macías) - Sentido Oriente/Sur
    {"zona": "Melchor Ocampo (Sanatorio Macías)", "lat": 20.546492, "lon": -100.689083, "heading": 115},

    # 15. Guadalupe Victoria (Tienda 3B) - Sentido Poniente
    {"zona": "Guadalupe Victoria (Tienda 3B)", "lat": 20.546374, "lon": -100.689581, "heading": 295},

    # 16. Guadalupe Victoria (Elektra) - Sentido Poniente
    {"zona": "Guadalupe Victoria (Elektra)", "lat": 20.545829, "lon": -100.688402, "heading": 295},

    # 17. Mariano Matamoros (Jardín Hidalgo) - Sentido Sur
    {"zona": "Mariano Matamoros (Jardín Hidalgo)", "lat": 20.545411, "lon": -100.688246, "heading": 205},

    # 18. Mariano Matamoros (Impladeag) - Sentido Sur
    {"zona": "Mariano Matamoros (Impladeag)", "lat": 20.543175, "lon": -100.689379, "heading": 205},

    # 19. Ignacio Allende (Parroquia) - Sentido Norte
    {"zona": "Ignacio Allende (Parroquia)", "lat": 20.545289, "lon": -100.687442, "heading": 25},

    # 20. Ignacio Allende (Hospital San Juan) - Sentido Norte
    {"zona": "Ignacio Allende (Hospital San Juan)", "lat": 20.5448306, "lon": -100.6861881, "heading": 25},

    # 21. Juan Aldama (Comunilab) - Sentido Norte
    {"zona": "Juan Aldama (Comunilab)", "lat": 20.5468316, "lon": -100.6869879, "heading": 25},

    # 22. Juan Aldama (Puente Colorado Sur) - Sentido Norte hacia entronque
    {"zona": "Juan Aldama (Puente Colorado Sur)", "lat": 20.547828, "lon": -100.686353, "heading": 25},

    # 23. Juan Aldama, Puente Colorado (Norte) - Doble sentido
    {"zona": "Juan Aldama, Puente Colorado (Norte) - Hacia Sur/Centro", "lat": 20.548262, "lon": -100.686137, "heading": 205},
    {"zona": "Juan Aldama, Puente Colorado (Norte) - Hacia Norte/Panamericana", "lat": 20.548262, "lon": -100.686137, "heading": 25},

    # 24. Narciso Mendoza (Puente Colorado Este) - Doble sentido
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Oriente", "lat": 20.547935, "lon": -100.685976, "heading": 115},
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Poniente", "lat": 20.547935, "lon": -100.685976, "heading": 295},

    # 25. Narciso Mendoza (Puente Colorado Oeste) - Doble sentido
    {"zona": "Narciso Mendoza (Puente Colorado Oeste) - Hacia Poniente", "lat": 20.548115, "lon": -100.686503, "heading": 295},
    {"zona": "Narciso Mendoza (Puente Colorado Oeste) - Hacia Oriente", "lat": 20.548115, "lon": -100.686503, "heading": 115},

    # 26. Morelos Semáforo (Este) - Doble sentido
    {"zona": "Morelos Semáforo (Este) - Hacia Poniente/Centro", "lat": 20.543178, "lon": -100.678348, "heading": 270},
    {"zona": "Morelos Semáforo (Este) - Hacia Oriente/Salida", "lat": 20.543178, "lon": -100.678348, "heading": 90},

    # 27. Del Charro (Semáforo Sur) - Doble sentido
    {"zona": "Del Charro (Semáforo Sur) - Hacia Norte", "lat": 20.543015, "lon": -100.678676, "heading": 0},
    {"zona": "Del Charro (Semáforo Sur) - Hacia Sur", "lat": 20.543015, "lon": -100.678676, "heading": 180},

    # 28. Del Charro (Semáforo Norte) - Doble sentido
    {"zona": "Del Charro (Semáforo Norte) - Hacia Sur", "lat": 20.543619, "lon": -100.678565, "heading": 180},
    {"zona": "Del Charro (Semáforo Norte) - Hacia Norte", "lat": 20.543619, "lon": -100.678565, "heading": 0},

    # 29. Lib. Sur (VÍA) - Doble sentido
    {"zona": "Lib. Sur (VÍA) - Hacia Oriente/Querétaro", "lat": 20.540724, "lon": -100.673911, "heading": 120},
    {"zona": "Lib. Sur (VÍA) - Hacia Poniente/Celaya", "lat": 20.540724, "lon": -100.673911, "heading": 300},
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

def consultar_trafico_tomtom(lat, lon, heading=None):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point={lat},{lon}&key={TOMTOM_API_KEY}"
    if heading is not None:
        url += f"&heading={heading}"

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
        print(f"Error consultando TomTom ({lat}, {lon}): {e}")
    return 0.0

def registrar_ciclo(sheet):
    ahora = datetime.now(ZONA_HORARIA)
    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA[ahora.weekday()]
    hora_str = ahora.strftime("%H:%M")

    filas_nuevas = []
    for punto in PUNTOS_MONITOREO:
        rumbo = punto.get("heading")
        pct_congestion = consultar_trafico_tomtom(punto["lat"], punto["lon"], heading=rumbo)
        fila = [fecha_str, dia_str, hora_str, f"{pct_congestion}%", punto["zona"]]
        filas_nuevas.append(fila)

    sheet.append_rows(filas_nuevas)
    print(f"[{hora_str}] {len(filas_nuevas)} registros guardados exitosamente.")

def main():
    print("Iniciando conexión a Google Sheets...")
    sheet = conectar_google_sheets()
    
    # Ejecuta exactamente 4 ciclos separados por 15 minutos (900 seg) cada hora
    total_ciclos = 4
    intervalo_segundos = 900  # 15 minutos

    for i in range(total_ciclos):
        print(f"\n--- Ejecutando toma {i + 1} de {total_ciclos} ---")
        registrar_ciclo(sheet)
        
        # Solo espera si aún quedan tomas pendientes en este ciclo
        if i < total_ciclos - 1:
            print(f"Esperando 15 minutos exactos para la siguiente toma...")
            time.sleep(intervalo_segundos)

    print("\nCiclo por hora completado con éxito.")

if __name__ == "__main__":
    main()
