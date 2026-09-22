import os
import requests
import pandas as pd
from datetime import datetime

# Mengambil API Key dari GitHub Secrets
API_KEY = os.environ.get("API_KEY")
CITY = "Pekanbaru"
STATE = "Riau"
COUNTRY = "Indonesia"
CSV_FILE = "pekanbaru_air_quality_log.csv"

def fetch_and_log():
    url = f"https://api.airvisual.com/v2/city?city={CITY}&state={STATE}&country={COUNTRY}&key={API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "success":
            current = data["data"]["current"]
            pollution = current["pollution"]
            weather = current["weather"]
            
            record = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "City": CITY,
                "US_AQI": pollution.get("aqius"),
                "Main_Pollutant": pollution.get("mainus"),
                "Temperature_C": weather.get("tp"),
                "Humidity_Pct": weather.get("hu")
            }
            
            df_new = pd.DataFrame([record])
            
            # Jika file CSV sudah ada, tambahkan baris baru tanpa header
            if os.path.exists(CSV_FILE):
                df_new.to_csv(CSV_FILE, mode='a', header=False, index=False)
            else:
                df_new.to_csv(CSV_FILE, mode='w', header=True, index=False)
                
            print(f"Sukses mencatat data AQI Pekanbaru pada {record['Timestamp']}")
        else:
            print("Gagal mengambil data dari API:", data)
            
    except Exception as e:
        print("Terjadi kesalahan:", e)

if __name__ == "__main__":
    fetch_and_log()
