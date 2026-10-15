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
    # 1. Rodolfo Piña Soria (Semáforo)
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Este/NE", "lat": 20.541310, "lon": -100.693311},
    {"zona": "Rodolfo Piña Soria (Semáforo) - Hacia Oeste/SO", "lat": 20.541310, "lon": -100.693311},

    # 2. Rodolfo Piña Soria (ETA)
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Este/NE", "lat": 20.542033, "lon": -100.691589},
    {"zona": "Rodolfo Piña Soria (ETA) - Hacia Oeste/SO", "lat": 20.542033, "lon": -100.691589},

    # 3. Antonio Plaza (Gas. Mobil)
    {"zona": "Antonio Plaza (Gas. Mobil)", "lat": 20.541935, "lon": -100.692770},

    # 4. Vicente Guerrero / Antonio Plaza
    {"zona": "Vicente Guerrero / Antonio Plaza", "lat": 20.543529, "lon": -100.692272},

    # 5. Pípila / Venustiano Carranza
    {"zona": "Pipila / Venustiano Carranza", "lat": 20.545164, "lon": -100.691833},

    # 6. Pípila (Mercado)
    {"zona": "Pipila (Mercado)", "lat": 20.546697, "lon": -100.690982},

    # 7. Antonio Plaza (Mercado)
    {"zona": "Antonio Plaza (Mercado)", "lat": 20.546480, "lon": -100.690602},

    # 8. Jesús Cabrera Muñoz Ledo (Semáforo)
    {"zona": "Jesus Cabrera Muñoz Ledo (Semáforo) - Hacia Norte", "lat": 20.545480, "lon": -100.692821},
    {"zona": "Jesus Cabrera Muñoz Ledo (Semáforo) - Hacia Sur", "lat": 20.545480, "lon": -100.692821},

    # 9. Jesús Cabrera Muñoz Ledo (Nutrióloga)
    {"zona": "Jesus Cabrera Muñoz Ledo (Nutriologa) - Hacia Norte", "lat": 20.546340, "lon": -100.693041},
    {"zona": "Jesus Cabrera Muñoz Ledo (Nutriologa) - Hacia Sur", "lat": 20.546340, "lon": -100.693041},

    # 10. Octaviano Muñoz Ledo con esq. Nicolás San Luis de Montañez
    {"zona": "Octaviano Muñoz Ledo esq. Nicolas San Luis - Hacia Este/Centro", "lat": 20.549326, "lon": -100.692837},
    {"zona": "Octaviano Muñoz Ledo esq. Nicolas San Luis - Hacia Poniente/Salida", "lat": 20.549326, "lon": -100.692837},

    # 11. Nicolás San Luis de Montañez esq. Octaviano Muñoz Ledo
    {"zona": "Nicolas San Luis de Montañez esq. Octaviano - Hacia Norte", "lat": 20.549086, "lon": -100.693303},
    {"zona": "Nicolas San Luis de Montañez esq. Octaviano - Hacia Sur", "lat": 20.549086, "lon": -100.693303},

    # 12. Vicente A. Ruiz (Aurrerá)
    {"zona": "Vicente A. Ruiz. (Aurrerá)", "lat": 20.548228, "lon": -100.690233},

    # 13. Octaviano Muñoz Ledo (Los Charcos)
    {"zona": "Octaviano Muñoz Ledo (Los Charcos)", "lat": 20.548410, "lon": -100.689976},

    # 14. Melchor Ocampo (Sanatorio Macías)
    {"zona": "Melchor Ocampo (Sanatorio Macías)", "lat": 20.546492, "lon": -100.689083},

    # 15. Guadalupe Victoria (Tienda 3B)
    {"zona": "Guadalupe Victoria (Tienda 3B)", "lat": 20.546374, "lon": -100.689581},

    # 16. Guadalupe Victoria (Elektra)
    {"zona": "Guadalupe Victoria (Elektra)", "lat": 20.545829, "lon": -100.688402},

    # 17. Mariano Matamoros (Jardín Hidalgo)
    {"zona": "Mariano Matamoros (Jardín Hidalgo)", "lat": 20.545411, "lon": -100.688246},

    # 18. Mariano Matamoros (Impladeag)
    {"zona": "Mariano Matamoros (Impladeag)", "lat": 20.543175, "lon": -100.689379},

    # 19. Ignacio Allende (Parroquia)
    {"zona": "Ignacio Allende (Parroquia)", "lat": 20.545289, "lon": -100.687442},

    # 20. Ignacio Allende (Hospital San Juan)
    {"zona": "Ignacio Allende (Hospital San Juan)", "lat": 20.5448306, "lon": -100.6861881},

    # 21. Juan Aldama (Comunilab)
    {"zona": "Juan Aldama (Comunilab)", "lat": 20.5468316, "lon": -100.6869879},

    # 22. Juan Aldama (Puente Colorado Sur)
    {"zona": "Juan Aldama (Puente Colorado Sur)", "lat": 20.547828, "lon": -100.686353},

    # 23. Juan Aldama, Puente Colorado (Norte)
    {"zona": "Juan Aldama, Puente Colorado (Norte) - Hacia Sur/Centro", "lat": 20.548262, "lon": -100.686137},
    {"zona": "Juan Aldama, Puente Colorado (Norte) - Hacia Norte/Panamericana", "lat": 20.548262, "lon": -100.686137},

    # 24. Narciso Mendoza (Puente Colorado Este)
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Oriente", "lat": 20.547935, "lon": -100.685976},
    {"zona": "Narciso Mendoza (Puente Colorado Este) - Hacia Poniente", "lat": 20.547935, "lon": -100.685976},

    # 25. Narciso Mendoza (Tramo Ocampo a Aldama) - Centrado en tramo urbano
    {"zona": "Narciso Mendoza (Ocampo a Aldama)", "lat": 20.547600, "lon": -100.687800},

    # 26. Morelos (Aproximación al semáforo hacia el Oeste / Centro)
    {"zona": "Morelos Semáforo (Hacia Poniente/Centro)", "lat": 20.543140, "lon": -100.677980},

    # 27. Del Charro (Semáforo Sur)
    {"zona": "Del Charro (Semáforo Sur) - Hacia Norte", "lat": 20.543015, "lon": -100.678676},
    {"zona": "Del Charro (Semáforo Sur) - Hacia Sur", "lat": 20.543015, "lon": -100.678676},

    # 28. Del Charro (Semáforo Norte)
    {"zona": "Del Charro (Semáforo Norte) - Hacia Sur", "lat": 20.543619, "lon": -100.678565},
    {"zona": "Del Charro (Semáforo Norte) - Hacia Norte", "lat": 20.543619, "lon": -100.678565},

    # 29. Lib. Sur (VÍA)
    {"zona": "Lib. Sur (VÍA) - Hacia Oriente/Querétaro", "lat": 20.540724, "lon": -100.673911},
    {"zona": "Lib. Sur (VÍA) - Hacia Poniente/Celaya", "lat": 20.540724, "lon": -100.673911},
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

def consultar_datos_trafico(lat, lon):
    """Consulta la API de TomTom con zoom 18 para capturar segmentos urbanos específicos."""
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/18/json?point={lat},{lon}&key={TOMTOM_API_KEY}"

    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json().get("flowSegmentData", {})
            current_speed = data.get("currentSpeed", 0)
            free_flow_speed = data.get("freeFlowSpeed", 0)
            current_travel_time = data.get("currentTravelTime", 0)
            free_flow_travel_time = data.get("freeFlowTravelTime", 0)

            # Cálculo de retraso en segundos respecto al flujo libre
            retraso_seg = max(0, current_travel_time - free_flow_travel_time)

            # Cálculo de porcentaje de congestión
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
    fecha_str = ahora.strftime("%Y-%m-%d")
    dia_str = DIAS_SEMANA[ahora.weekday()]
    hora_str = ahora.strftime("%H:%M")

    filas_nuevas = []
    for punto in PUNTOS_MONITOREO:
        datos = consultar_datos_trafico(punto["lat"], punto["lon"])
        
        # Estructura: Fecha, Día, Hora, Zona, Velocidad Real, Velocidad Libre, % Congestión, Retraso
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
    print(f"[{hora_str}] {len(filas_nuevas)} registros guardados exitosamente con métricas ampliadas.")

def main():
    print("Iniciando conexión a Google Sheets...")
    sheet = conectar_google_sheets()
    
    total_ciclos = 4
    intervalo_segundos = 900  # 15 minutos exactos

    for i in range(total_ciclos):
        print(f"\n--- Ejecutando toma {i + 1} de {total_ciclos} ---")
        registrar_ciclo(sheet)
        
        if i < total_ciclos - 1:
            print("Esperando 15 minutos para la siguiente toma...")
            time.sleep(intervalo_segundos)

    print("\nBloque de 1 hora completado con éxito.")

if __name__ == "__main__":
    main()
