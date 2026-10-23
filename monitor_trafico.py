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

    # 3. Jesús Cabrera M. (Escuela Nuevo Mundo) - Doble Sentido
    {"zona": "Jesús Cabrera M. - Escuela Nuevo Mundo (Hacia Norte)", "lat": 20.546324, "lon": -100.693058},
    {"zona": "Jesús Cabrera M. - Escuela Nuevo Mundo (Hacia Sur)", "lat": 20.546324, "lon": -100.693058},

    # 4. Jesús Cabrera M. (Semáforo Oxxo) - Doble Sentido
    {"zona": "Jesús Cabrera M. - Semáforo Oxxo (Hacia Norte / Salida)", "lat": 20.545503, "lon": -100.692827},
    {"zona": "Jesús Cabrera M. - Semáforo Oxxo (Hacia Sur / Centro)", "lat": 20.545503, "lon": -100.692827},

    # 5. Juan Aldama (Puente Colorado) - Coordenada ajustada
    {"zona": "Juan Aldama - Puente Colorado (Sur a Norte)", "lat": 20.547467, "lon": -100.686468},

    # 6. Mariano Matamoros (Presidencia)
    {"zona": "Mariano Matamoros - Presidencia (Sur a Norte)", "lat": 20.545107, "lon": -100.688410},

    # 7. Melchor Ocampo (Sanatorio Macías)
    {"zona": "Melchor Ocampo - Sanatorio Macías (Norte a Sur)", "lat": 20.546439, "lon": -100.689101},

    # 8. Morelos (Semáforo Lienzo Charro) - Doble Sentido
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Oriente / Salida)", "lat": 20.543142, "lon": -100.678080},
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Poniente / Centro)", "lat": 20.543142, "lon": -100.678080},

    # 9. Narciso Mendoza (Libros Rocío) - Doble Sentido
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Oriente / Puente Colorado)", "lat": 20.548127, "lon": -100.686624},
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Poniente / Ocampo)", "lat": 20.548127, "lon": -100.686624},

    # 10. Narciso Mendoza (Semáforo Este a Oeste) - Doble Sentido
    {"zona": "Narciso Mendoza - Semáforo (Hacia Oriente)", "lat": 20.547922, "lon": -100.685871},
    {"zona": "Narciso Mendoza - Semáforo (Hacia Poniente)", "lat": 20.547922, "lon": -100.685871},

    # 11. Octaviano Muñoz Ledo (Los Charcos)
    {"zona": "Octaviano Muñoz Ledo - Los Charcos (Este a Oeste)", "lat": 20.548394, "lon": -100.689885},

    # 12. Pípila (Mercado)
    {"zona": "Pípila - Mercado (Sur a Norte)", "lat": 20.546627, "lon": -100.691033},

    # 13. Piña Soria (Auto Zone) - Doble Sentido
    {"zona": "Piña Soria - Auto Zone (Hacia Este / Salida Qro)", "lat": 20.541780, "lon": -100.692170},
    {"zona": "Piña Soria - Auto Zone (Hacia Oeste / Centro)", "lat": 20.541780, "lon": -100.692170},

    # 14. Venustiano Carranza (Central)
    {"zona": "Venustiano Carranza - Central (Este a Oeste)", "lat": 20.545699, "lon": -100.692539},

    # 15. Vicente Ruiz (Aurrerá)
    {"zona": "Vicente Ruiz - Aurrerá (Sur a Norte)", "lat": 20.548210, "lon": -100.690237},
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def esta_en_horario_monitoreo(ahora):
    """Verifica si la hora actual local está dentro del rango 05:30 a 22:00."""
    return HORA_INICIO <= ahora.time() <= HORA_FIN

def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GCP_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1

def consultar_datos_trafico(lat, lon, nombre_zona):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/18/json?point={lat},{lon}&key={TOMTOM_API_KEY}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            flow_data = resp.json().get("flowSegmentData")
            if not flow_data:
                print(f"[Aviso] {nombre_zona} ({lat}, {lon}) no devolvió segmento de tráfico.")
                return {"vel_real": 0, "vel_libre": 0, "congestion": 0.0, "retraso": 0}

            current_speed = flow_data.get("currentSpeed", 0)
            free_flow_speed = flow_data.get("freeFlowSpeed", 0)
            current_travel_time = flow_data.get("currentTravelTime", 0)
            free_flow_travel_time = flow_data.get("freeFlowTravelTime", 0)

            retraso_seg = max(0, current_travel_time - free_flow_travel_time)

            if free_flow_speed > 0:
                congestion = max(0, ((free_flow_speed - current_speed) / free_flow_speed) * 100)
            else:
                congestion = 0.0

            return {
                "vel_real": current_speed,
                "vel_libre": free_flow_speed,
                "congestion": round(congestion, 1),
                "retraso": retraso_seg
            }
        else:
            print(f"[Error TomTom] {nombre_zona} respondió HTTP {resp.status_code}")
    except Exception as e:
        print(f"[Excepción] Error consultando {nombre_zona} ({lat}, {lon}): {e}")

    return {
        "vel_real": 0,
        "vel_libre": 0,
        "congestion": 0.0,
        "retraso": 0
    }

def registrar_ciclo(sheet):
    ahora = datetime.now(ZONA_HORARIA)
    
    if not esta_en_horario_monitoreo(ahora):
        print(f"[{ahora.strftime('%H:%M')}] Fuera de la ventana de monitoreo (05:30 a 22:00).")
        return False

    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA[ahora.weekday()]
    hora_str = ahora.strftime("%H:%M")

    filas_nuevas = []
    for punto in PUNTOS_MONITOREO:
        datos = consultar_datos_trafico(punto["lat"], punto["lon"], punto["zona"])
        
        fila = [
            fecha_str,
            dia_str,
            hora_str,
            punto["zona"],
            datos["vel_real"],
            datos["vel_libre"],
            f"{datos['congestion']}%",
            datos["retraso"]
        ]
        filas_nuevas.append(fila)
        time.sleep(0.1)

    sheet.append_rows(filas_nuevas)
    print(f"[{hora_str}] {len(filas_nuevas)} registros guardados correctamente.")
    return True

def main():
    ahora_inicial = datetime.now(ZONA_HORARIA)
    if not esta_en_horario_monitoreo(ahora_inicial):
        print(f"Hora actual ({ahora_inicial.strftime('%H:%M')}) fuera de horario. Esperando siguiente ciclo.")
        return

    print("Conectando con Google Sheets...")
    sheet = conectar_google_sheets()
    
    total_ciclos = 4
    intervalo_segundos = 900  # 15 minutos

    for i in range(total_ciclos):
        print(f"\n--- Ejecutando toma {i + 1} de {total_ciclos} ---")
        continuar = registrar_ciclo(sheet)
        
        if not continuar:
            break
        
        if i < total_ciclos - 1:
            print("Esperando 15 minutos para la siguiente toma...")
            time.sleep(intervalo_segundos)

    print("\nCiclo por hora finalizado con éxito.")

if __name__ == "__main__":
    main()
