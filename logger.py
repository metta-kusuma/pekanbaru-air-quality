from datetime import datetime, timedelta
import os
import pandas as pd
import requests

# Mengambil OpenWeather API Key dari Environment Variable / GitHub Secrets
API_KEY = os.environ.get("API_KEY")

CITY = "Pekanbaru"
LAT = "0.5071"
LON = "101.4478"

AIR_CSV = "pekanbaru_air_quality_log.csv"
WEATHER_CSV = "pekanbaru_weather_log.csv"


def fetch_and_log():
  # Waktu WIB (UTC + 7)
  wib_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")

  if not API_KEY:
    print("Error: API_KEY tidak ditemukan di Environment Variables!")
    return

  # -------------------------------------------------------------
  # 1. TARIK DATA KUALITAS UDARA (OpenWeather Air Pollution API)
  # -------------------------------------------------------------
  air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"

  try:
    res_air = requests.get(air_url, timeout=10)
    data_air = res_air.json()

    if res_air.status_code == 200 and "list" in data_air:
      item = data_air["list"][0]
      main_aqi = item.get("main", {}).get("aqi")  # Indeks 1 (Baik) - 5 (Sangat Buruk)
      comp = item.get("components", {})  # Konsentrasi polutan dalam ug/m3

      air_record = {
          "Timestamp": timestamp_wib,
          "City": CITY,
          "Latitude": LAT,
          "Longitude": LON,
          "OW_AQI_Index": main_aqi,  # Scale: 1 = Good, 2 = Fair, 3 = Moderate, 4 = Poor, 5 = Very Poor
          "PM25_Conc": comp.get("pm2_5"),  # Konsentrasi PM2.5 (ug/m3)
          "PM10_Conc": comp.get("pm10"),  # Konsentrasi PM10 (ug/m3)
          "CO_Conc": comp.get("co"),  # Konsentrasi Carbon Monoxide (ug/m3)
          "NO2_Conc": comp.get("no2"),  # Konsentrasi Nitrogen Dioxide (ug/m3)
          "O3_Conc": comp.get("o3"),  # Konsentrasi Ozone (ug/m3)
          "SO2_Conc": comp.get("so2"),  # Konsentrasi Sulfur Dioxide (ug/m3)
          "NH3_Conc": comp.get("nh3"),  # Konsentrasi Ammonia (ug/m3)
          "NO_Conc": comp.get("no"),  # Konsentrasi Nitrogen Monoxide (ug/m3)
      }

      df_air = pd.DataFrame([air_record])
      if os.path.exists(AIR_CSV):
        df_air.to_csv(AIR_CSV, mode="a", header=False, index=False)
      else:
        df_air.to_csv(AIR_CSV, mode="w", header=True, index=False)

      print(
          f"[{timestamp_wib}] Sukses mencatat Air Quality OpenWeather"
          f" (PM2.5: {comp.get('pm2_5')} ug/m3)."
      )
    else:
      print("Gagal mengambil Air Pollution API:", data_air)

  except Exception as e:
    print("Error Air Pollution:", e)

  # -------------------------------------------------------------
  # 2. TARIK DATA CUACA TERKINI (OpenWeather Current Weather API)
  # -------------------------------------------------------------
  weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

  try:
    res_weather = requests.get(weather_url, timeout=10)
    data_weather = res_weather.json()

    if res_weather.status_code == 200:
      main_w = data_weather.get("main", {})
      weather_desc = data_weather.get("weather", [{}])[0]
      wind_w = data_weather.get("wind", {})
      clouds_w = data_weather.get("clouds", {})

      weather_record = {
          "Timestamp": timestamp_wib,
          "City": CITY,
          "Weather_Main": weather_desc.get("main"),  # Misal: Rain, Clouds, Clear
          "Weather_Desc": weather_desc.get(
              "description"
          ),  # Misal: overcast clouds, light rain
          "Temp_C": main_w.get("temp"),  # Suhu (Celcius)
          "Feels_Like_C": main_w.get("feels_like"),  # Sensasi Suhu (Celcius)
          "Humidity_Pct": main_w.get("humidity"),  # Kelembapan (%)
          "Pressure_hPa": main_w.get("pressure"),  # Tekanan Udara (hPa)
          "Wind_Speed_ms": wind_w.get("speed"),  # Kecepatan Angin (m/s)
          "Wind_Deg": wind_w.get("deg"),  # Arah Angin (Derajat)
          "Clouds_Pct": clouds_w.get("all"),  # Tutupan Awan (%)
          "Visibility_m": data_weather.get(
              "visibility"
          ),  # Jarak Pandang (Meter) - Sangat berguna untuk kabut asap!
      }

      df_weather = pd.DataFrame([weather_record])
      if os.path.exists(WEATHER_CSV):
        df_weather.to_csv(WEATHER_CSV, mode="a", header=False, index=False)
      else:
        df_weather.to_csv(WEATHER_CSV, mode="w", header=True, index=False)

      print(
          f"[{timestamp_wib}] Sukses mencatat Current Weather OpenWeather"
          f" ({weather_desc.get('main')}, {main_w.get('temp')}°C)."
      )
    else:
      print("Gagal mengambil Weather API:", data_weather)

  except Exception as e:
    print("Error Weather:", e)


if __name__ == "__main__":
  fetch_and_log()
