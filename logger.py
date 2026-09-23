from datetime import datetime, timedelta
import os
import pandas as pd
import requests

# Mengambil API Key dari GitHub Secrets / Environment Variables
AIRVISUAL_API_KEY = os.environ.get("AIRVISUAL_API_KEY")  # Key AirVisual
OPENWEATHER_API_KEY = os.environ.get("API_KEY")  # Key OpenWeather

CITY = "Pekanbaru"
STATE = "Riau"
COUNTRY = "Indonesia"
LAT = "0.5071"
LON = "101.4478"

CSV_FILE = "pekanbaru_air_quality_log.csv"


def fetch_and_log():
  # 1. Tarik Data dari AirVisual (Kualitas Udara + Cuaca Dasar)
  airvisual_url = f"https://api.airvisual.com/v2/city?city={CITY}&state={STATE}&country={COUNTRY}&key={AIRVISUAL_API_KEY}"

  # 2. Tarik Data dari OpenWeather (Detail Cuaca Tambahan)
  openweather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"

  # Waktu WIB (UTC + 7)
  wib_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")

  record = {"Timestamp": timestamp_wib, "City": CITY}

  # --- PROSES AIRVISUAL ---
  try:
    res_av = requests.get(airvisual_url, timeout=10)
    data_av = res_av.json()

    if data_av.get("status") == "success":
      d = data_av["data"]
      current = d.get("current", {})
      pollution = current.get("pollution", {})
      weather_av = current.get("weather", {})

      record.update({
          "US_AQI": pollution.get("aqius"),
          "Main_US_Pollutant": pollution.get("mainus"),
          "China_AQI": pollution.get("aqicn"),
          "Main_China_Pollutant": pollution.get("maincn"),
          "AV_Temperature_C": weather_av.get("tp"),
          "AV_Humidity_Pct": weather_av.get("hu"),
          "AV_Wind_Speed_ms": weather_av.get("ws"),
      })

      # Rincian Polutan
      pollutants_map = {
          "p2": "PM25",
          "p1": "PM10",
          "o3": "O3",
          "n2": "NO2",
          "s2": "SO2",
          "co": "CO",
      }
      for p_key, p_name in pollutants_map.items():
        p_data = pollution.get(p_key, {})
        record[f"{p_name}_Conc"] = p_data.get("conc")
        record[f"{p_name}_AQI_US"] = p_data.get("aqius")

  except Exception as e:
    print("Gagal mengambil data AirVisual:", e)

  # --- PROSES OPENWEATHER (Cuaca Tambahan) ---
  try:
    res_ow = requests.get(openweather_url, timeout=10)
    data_ow = res_ow.json()

    if res_ow.status_code == 200:
      main_ow = data_ow.get("main", {})
      weather_desc = data_ow.get("weather", [{}])[0]
      wind_ow = data_ow.get("wind", {})
      clouds_ow = data_ow.get("clouds", {})

      record.update({
          "OW_Weather_Main": weather_desc.get("main"),  # Misal: Rain, Clear, Clouds
          "OW_Weather_Desc": weather_desc.get("description"),  # Misal: light rain
          "OW_Temp_C": main_ow.get("temp"),
          "OW_Feels_Like_C": main_ow.get("feels_like"),
          "OW_Humidity_Pct": main_ow.get("humidity"),
          "OW_Pressure_hPa": main_ow.get("pressure"),
          "OW_Wind_Speed_ms": wind_ow.get("speed"),
          "OW_Clouds_Pct": clouds_ow.get("all"),
          "OW_Visibility_m": data_ow.get("visibility"),  # Jarak pandang (penting untuk kabut asap)
      })
  except Exception as e:
    print("Gagal mengambil data OpenWeather:", e)

  # --- SIMPAN KE CSV ---
  df_new = pd.DataFrame([record])
  if os.path.exists(CSV_FILE):
    df_new.to_csv(CSV_FILE, mode="a", header=False, index=False)
  else:
    df_new.to_csv(CSV_FILE, mode="w", header=True, index=False)

  print(f"Sukses mencatat gabungan data AQI & Cuaca pada {timestamp_wib}")


if __name__ == "__main__":
  fetch_and_log()
