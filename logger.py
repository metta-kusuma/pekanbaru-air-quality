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
            
            # Penyesuaian waktu ke WIB (UTC + 7)
            wib_time = datetime.utcnow() + timedelta(hours=7)
            timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Susun data dasar (lokasi, indeks umum, dan cuaca)
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
            
            # Menarik rincian lengkap seluruh polutan (PM2.5, PM10, O3, NO2, SO2, CO)
            pollutants_map = {
                "p2": "PM25",
                "p1": "PM10",
                "o3": "O3",
                "n2": "NO2",
                "s2": "SO2",
                "co": "CO"
            }
            
            for p_key, p_name in pollutants_map.items():
                p_data = pollution.get(p_key, {})
                record[f"{p_name}_Conc"] = p_data.get("conc")
                record[f"{p_name}_AQI_US"] = p_data.get("aqius")
                record[f"{p_name}_AQI_China"] = p_data.get("aqicn")
            
            df_new = pd.DataFrame([record])
            
            # Simpan ke CSV (Append jika sudah ada, buat baru jika belum)
            if os.path.exists(CSV_FILE):
                df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
            else:
                df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
                
            print(f"Sukses mencatat seluruh parameter lengkap AQI Pekanbaru (WIB) pada {record['Timestamp']}")
        else:
            print("Gagal mengambil data dari API:", data)
            
    except Exception as e:
        print("Terjadi kesalahan:", e)

if __name__ == "__main__":
    fetch_and_log()
