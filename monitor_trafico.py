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

# Lista completa de puntos de monitoreo extraídos de tu tabla
PUNTOS_MONITOREO = [
    {"zona": "Antonio Plaza (Norte a Sur)", "lat": 20.542009, "lon": -100.69275},
    {"zona": "Guadalupe Victoria - Elektra (Oeste a Este)", "lat": 20.545793, "lon": -100.688365},
    {"zona": "Jesús Cabrera M. - Escuela Nuevo Mundo (Hacia Sur)", "lat": 20.5462143, "lon": -100.6930116},
    {"zona": "Jesús Cabrera M. - Semaforo Oxxo", "lat": 20.545245, "lon": -100.692707},
    {"zona": "Jesús Cabrera M. - Gasolinera Repsol", "lat": 20.544307, "lon": -100.692544},
    {"zona": "Juan Aldama - Puente Colorado (Sur a Norte)", "lat": 20.54766, "lon": -100.68638},
    {"zona": "Mariano Matamoros - Presidencia (Sur a Norte)", "lat": 20.545107, "lon": -100.68841},
    {"zona": "Melchor Ocampo - Sanatorio Macías (Norte a Sur)", "lat": 20.546439, "lon": -100.689101},
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Oriente / Salida)", "lat": 20.543142, "lon": -100.67808},
    {"zona": "Morelos - Semáforo Lienzo Charro (Hacia Poniente / Centro)", "lat": 20.54325, "lon": -100.67875},
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Oriente / Puente Colorado)", "lat": 20.548134, "lon": -100.686754},
    {"zona": "Narciso Mendoza - Libros Rocío (Hacia Poniente / Ocampo)", "lat": 20.54818, "lon": -100.6872},
    {"zona": "Narciso Mendoza - Semáforo (Hacia Oriente)", "lat": 20.547989, "lon": -100.685942},
    {"zona": "Narciso Mendoza - Semáforo (Hacia Poniente)", "lat": 20.54798, "lon": -100.68535},
    {"zona": "Octaviano Muñoz Ledo - Los Charcos (Este a Oeste)", "lat": 20.548394, "lon": -100.689885},
    {"zona": "Pípila - Mercado (Sur a Norte)", "lat": 20.546691, "lon": -100.690979},
    {"zona": "Piña Soria - Auto Zone (Hacia Este / Salida Qro)", "lat": 20.541670, "lon": -100.692220},
    {"zona": "Piña Soria - Auto Zone (Hacia Oeste / Centro)", "lat": 20.54167, "lon": -100.69266},
    {"zona": "Venustiano Carranza - Central (Este a Oeste)", "lat": 20.545699, "lon": -100.692539},
    {"zona": "Vicente Ruiz - Aurrerá (Sur a Norte)", "lat": 20.54821, "lon": -100.690237},
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def esta_en_horario_monitoreo(ahora):
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
                print(f"[Aviso] {nombre_zona} ({lat}, {lon}) no devolvió segmento de tráfico.", flush=True)
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
            print(f"[Error TomTom] {nombre_zona} respondió HTTP {resp.status_code}", flush=True)
    except Exception as e:
        print(f"[Excepción] Error consultando {nombre_zona} ({lat}, {lon}): {e}", flush=True)

    return {
        "vel_real": 0,
        "vel_libre": 0,
        "congestion": 0.0,
        "retraso": 0
    }

def registrar_ciclo(sheet):
    ahora = datetime.now(ZONA_HORARIA)
    
    if not esta_en_horario_monitoreo(ahora):
        print(f"[{ahora.strftime('%H:%M')}] Fuera de la ventana de monitoreo (05:30 a 22:00).", flush=True)
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
    print(f"[{hora_str}] {len(filas_nuevas)} registros guardados correctamente.", flush=True)
    return True

def main():
    ahora_inicial = datetime.now(ZONA_HORARIA)
    if not esta_en_horario_monitoreo(ahora_inicial):
        print(f"Hora actual ({ahora_inicial.strftime('%H:%M')}) fuera de horario. Esperando siguiente ciclo.", flush=True)
        return

    print("Conectando con Google Sheets...", flush=True)
    sheet = conectar_google_sheets()
    
    total_ciclos = 4
    intervalo_segundos = 900  # 15 minutos

    for i in range(total_ciclos):
        print(f"\n--- Ejecutando toma {i + 1} de {total_ciclos} ---", flush=True)
        continuar = registrar_ciclo(sheet)
        
        if not continuar:
            break
        
        if i < total_ciclos - 1:
            print("Esperando 15 minutos para la siguiente toma...", flush=True)
            time.sleep(intervalo_segundos)

    print("\nCiclo por hora finalizado con éxito.", flush=True)

if __name__ == "__main__":
    main()
