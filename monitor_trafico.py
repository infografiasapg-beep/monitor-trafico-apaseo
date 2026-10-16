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

# Rango horario permitido: 5:30 am a 10:00 pm (22:00)
HORA_INICIO = dtime(5, 30)
HORA_FIN = dtime(22, 0)

# Lista completa de puntos de monitoreo ordenada alfabéticamente por calle
PUNTOS_MONITOREO = [
    # --- ANTONIO PLAZA ---
    {"zona": "Antonio Plaza (Gas. Mobil)", "lat": 20.541935, "lon": -100.692770},
    {"zona": "Antonio Plaza (Mercado)", "lat": 20.546480, "lon": -100.690602},

    # --- DEL CHARRO ---
    {"zona": "Del Charro (Semáforo Norte) - Hacia Norte", "lat": 20.543619, "lon": -100.678565},
    {"zona": "Del Charro (Semáforo Norte) - Hacia Sur", "lat": 20.543619, "lon": -100.678565},
    {"zona": "Del Charro (Semáforo Sur) - Hacia Norte", "lat": 20.543015, "lon": -100.678676},
    {"zona": "Del Charro (Semáforo Sur) - Hacia Sur", "lat": 20.543015, "lon": -100.678676},

    # --- GUADALUPE VICTORIA ---
    {"zona": "Guadalupe Victoria (Elektra)", "lat": 20.545829, "lon": -100.688402},
    {"zona": "Guadalupe Victoria (Tienda 3B)", "lat": 20.546374, "lon": -100.689581},

    # --- IGNACIO ALLENDE ---
    {"zona": "Ignacio Allende (Hospital San Juan)", "lat": 20.5448306, "lon": -100.6861881},
    {"zona": "Ignacio Allende (Parroquia)", "lat": 20.545289, "lon": -100.687442},

    # --- JESÚS CABRERA MUÑOZ LEDO ---
    {"zona": "Jesús Cabrera Muñoz Ledo (Nutrióloga) - Hacia Norte", "lat": 20.546340, "lon": -100.693041},
    {"zona": "Jesús Cabrera Muñoz Ledo (Nutrióloga) - Hacia Sur", "lat": 20.546340, "lon": -100.693041},
    {"zona": "Jesús Cabrera Muñoz Ledo (Semáforo) - Hacia Norte", "lat": 20.545480, "lon": -100.692821},
    {"zona": "Jesús Cabrera Muñoz Ledo (Semáforo) - Hacia Sur", "lat": 20.545480, "lon": -100.692821},

    # --- JUAN ALDAMA ---
    {"zona": "Juan Aldama (Comunilab)", "lat": 20.5466675, "lon": -100.6869746},
    {"zona": "Juan Aldama (Puente Colorado Norte) - Hacia Norte/Panamericana", "lat": 20.548262, "lon": -100.686137},
    {"zona": "Juan Aldama (Puente Colorado Norte) - Hacia Sur/Centro", "lat": 20.548262, "lon": -100.686137},
    {"zona": "Juan Aldama (Puente Colorado Sur)", "lat": 20.547828, "lon": -100.686353},

    # --- LIBRAMIENTO SUR ---
    {"zona": "Lib. Sur (VÍA) - Hacia Oriente/Querétaro", "lat": 20.540724, "lon": -100.673911},
    {"zona": "Lib. Sur (VÍA) - Hacia Poniente/Celaya", "lat": 20.540724, "lon": -100.673911},

    # --- MARIANO MATAMOROS ---
    {"zona": "Mariano Matamoros (Impladeag)", "lat": 20.543175, "lon": -100.689379},
    {"zona": "Mariano Matamoros (Jardín Hidalgo)", "lat": 20.545411, "lon": -100.688246},

    # --- MELCHOR OCAMPO ---
    {"zona": "Melchor Ocampo (Sanatorio Macías)", "lat": 20.546492, "lon": -100.689083},

    # --- MORELOS ---
    {"zona": "Morelos (Colegio Vasco)", "lat": 20.5464484, "lon": -100.6856178},
    {"zona": "Morelos Semáforo (Hacia Poniente/Centro)", "lat": 20.543140, "lon": -100.677980},

    # --- NARCISO MENDOZA ---
    {"zona": "Narciso Mendoza (Ocampo a Aldama)", "lat": 20.548180, "lon": -100.687450},
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Oriente", "lat": 20.547935, "lon": -100.685976},
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Poniente", "lat": 20.547935, "lon": -100.685976},

    # --- NICOLÁS SAN LUIS DE MONTAÑEZ ---
    {"zona": "Nicolás San Luis de Montañez esq. Octaviano - Hacia Norte", "lat": 20.549086, "lon": -100.693303},
    {"zona": "Nicolás San Luis de Montañez esq. Octaviano - Hacia Sur", "lat": 20.549086, "lon": -100.693303},

    # --- OCTAVIANO MUÑOZ LEDO ---
    {"zona": "Octaviano Muñoz Ledo (Los Charcos)", "lat": 20.548410, "lon": -100.689976},
    {"zona": "Octaviano Muñoz Ledo esq. Nicolás San Luis - Hacia Este/Centro", "lat": 20.549326, "lon": -100.692837},
    {"zona": "Octaviano Muñoz Ledo esq. Nicolás San Luis - Hacia Poniente/Salida", "lat": 20.549326, "lon": -100.692837},

    # --- PÍPILA ---
    {"zona": "Pípila / Venustiano Carranza", "lat": 20.545164, "lon": -100.691833},
    {"zona": "Pípila (Mercado)", "lat": 20.546697, "lon": -100.690982},

    # --- RODOLFO PIÑA SORIA ---
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Este/NE", "lat": 20.542033, "lon": -100.691589},
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Oeste/SO", "lat": 20.542033, "lon": -100.691589},
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Este/NE", "lat": 20.541310, "lon": -100.693311},
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Oeste/SO", "lat": 20.541310, "lon": -100.693311},

    # --- VICENTE A. RUIZ ---
    {"zona": "Vicente A. Ruiz (Aurrerá)", "lat": 20.548228, "lon": -100.690233},

    # --- VICENTE GUERRERO ---
    {"zona": "Vicente Guerrero / Antonio Plaza", "lat": 20.543529, "lon": -100.692272},
]

DIAS_SEMANA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

def esta_en_horario_monitoreo(ahora):
    """Verifica si la hora actual está entre las 05:30 y las 22:00 en Apaseo el Grande."""
    hora_actual = ahora.time()
    return HORA_INICIO <= hora_actual <= HORA_FIN

def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(GCP_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open(SPREADSHEET_NAME).sheet1

def consultar_datos_trafico(lat, lon):
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/18/json?point={lat},{lon}&key={TOMTOM_API_KEY}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("flowSegmentData", {})
            current_speed = data.get("currentSpeed", 0)
            free_flow_speed = data.get("freeFlowSpeed", 0)
            current_travel_time = data.get("currentTravelTime", 0)
            free_flow_travel_time = data.get("freeFlowTravelTime", 0)

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
    except Exception as e:
        print(f"Error consultando TomTom ({lat}, {lon}): {e}")

    return {
        "vel_real": 0,
        "vel_libre": 0,
        "congestion": 0.0,
        "retraso": 0
    }

def registrar_ciclo(sheet):
    ahora = datetime.now(ZONA_HORARIA)
    
    # Validar si está en la ventana 05:30 - 22:00
    if not esta_en_horario_monitoreo(ahora):
        print(f"[{ahora.strftime('%H:%M')}] Fuera de horario de monitoreo (05:30 a 22:00). Finalizando ciclo.")
        return False

    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA[ahora.weekday()]
    hora_str = ahora.strftime("%H:%M")

    filas_nuevas = []
    for punto in PUNTOS_MONITOREO:
        datos = consultar_datos_trafico(punto["lat"], punto["lon"])
        
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

    sheet.append_rows(filas_nuevas)
    print(f"[{hora_str}] {len(filas_nuevas)} registros guardados exitosamente.")
    return True

def main():
    ahora_inicial = datetime.now(ZONA_HORARIA)
    if not esta_en_horario_monitoreo(ahora_inicial):
        print(f"Hora actual ({ahora_inicial.strftime('%H:%M')}) fuera de la ventana 05:30 a 22:00. No se ejecutará la toma.")
        return

    print("Iniciando conexión a Google Sheets...")
    sheet = conectar_google_sheets()
    
    total_ciclos = 4
    intervalo_segundos = 900  # 15 minutos

    for i in range(total_ciclos):
        print(f"\n--- Ejecutando toma {i + 1} de {total_ciclos} ---")
        continuar = registrar_ciclo(sheet)
        
        # Si se cruza el límite de las 22:00, se detiene
        if not continuar:
            break
        
        if i < total_ciclos - 1:
            print("Esperando 15 minutos para la siguiente toma...")
            time.sleep(intervalo_segundos)

    print("\nBloque completado con éxito.")

if __name__ == "__main__":
    main()
