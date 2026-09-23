import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# Mengambil API Key dari GitHub Secrets
API_KEY = os.environ.get("API_KEY")
CITY = "Pekanbaru"
STATE = "Riau"
COUNTRY = "Indonesia"
CSV_FILE = "pekanbaru_air_quality_log.csv"

def fetch_and_log():
    url = f"https://api.airvisual.com/v2/city?city={CITY}&state={STATE}&country={COUNTRY}&key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") == "success":
            d = data["data"]
            loc = d.get("location", {}).get("coordinates", [None, None])
            current = d["current"]
            pollution = current["pollution"]
            weather = current["weather"]
            
            # Menyesuaikan waktu ke WIB (UTC + 7) agar pas dengan waktu lokal Pekanbaru
            wib_time = datetime.utcnow() + timedelta(hours=7)
            timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")
            
            record = {
                "Timestamp": timestamp_wib,
                "City": d.get("city", CITY),
                "State": d.get("state", STATE),
                "Country": d.get("country", COUNTRY),
                "Latitude": loc[1] if len(loc) > 1 else None,
                "Longitude": loc[0] if len(loc) > 0 else None,
                "US_AQI": pollution.get("aqius"),
                "Main_US_Pollutant": pollution.get("mainus"),
                "China_AQI": pollution.get("aqicn"),
                "Main_China_Pollutant": pollution.get("maincn"),
                "Temperature_C": weather.get("tp"),
                "Pressure_hPa": weather.get("pr"),
                "Humidity_Pct": weather.get("hu"),
                "Wind_Speed_ms": weather.get("ws"),
                "Wind_Direction_deg": weather.get("wd"),
                "HeatIndex_C": weather.get("heatIndex")
            }
            
            df_new = pd.DataFrame([record])
            
            # Jika file CSV sudah ada, tambahkan baris baru tanpa header
            if os.path.exists(CSV_FILE):
                df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
            else:
                df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
                
            print(f"Sukses mencatat data AQI Pekanbaru (WIB) pada {record['Timestamp']}")
        else:
            print("Gagal mengambil data dari API:", data)
            
    except Exception as e:
        print("Terjadi kesalahan:", e)

if __name__ == "__main__":
    fetch_and_log()
