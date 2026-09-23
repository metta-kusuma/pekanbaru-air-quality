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


def get_aqi_category(ow_aqi_index):
  """Mengubah Indeks OpenWeather (1-5) menjadi Label Status Bahasa Indonesia."""
  categories = {
      1: "Baik (Good)",
      2: "Sedang (Fair)",
      3: "Cukup Buruk / Moderat (Moderate)",
      4: "Tidak Sehat (Poor)",
      5: "Sangat Tidak Sehat (Very Poor)",
  }
  return categories.get(ow_aqi_index, "Tidak Diketahui")


def calculate_us_aqi_pm25(pm25_conc):
  """Menghitung Estimasi Total US AQI (0 - 500) berdasarkan Konsentrasi PM2.5 (ug/m3)

  Sesuai Breakpoint Standar US EPA.
  """
  if pm25_conc is None:
    return None

  c = float(pm25_conc)

  # Breakpoints: (C_low, C_high, I_low, I_high)
  breakpoints = [
      (0.0, 12.0, 0, 50),  # Baik
      (12.1, 35.4, 51, 100),  # Sedang
      (35.5, 55.4, 101, 150),  # Tidak Sehat untuk Kelompok Sensitif
      (55.5, 150.4, 151, 200),  # Tidak Sehat
      (150.5, 250.4, 201, 300),  # Sangat Tidak Sehat
      (250.5, 500.4, 301, 500),  # Berbahaya
  ]

  for c_low, c_high, i_low, i_high in breakpoints:
    if c_low <= c <= c_high:
      aqi = ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
      return round(aqi)

  if c > 500.4:
    return 500
  return 0


def get_us_aqi_status(us_aqi):
  """Memberikan label kategori teks berdasarkan Total US AQI."""
  if us_aqi is None:
    return "Tidak Diketahui"
  if us_aqi <= 50:
    return "Baik (Good)"
  elif us_aqi <= 100:
    return "Sedang (Moderate)"
  elif us_aqi <= 150:
    return "Tidak Sehat bagi Kelompok Sensitif"
  elif us_aqi <= 200:
    return "Tidak Sehat (Unhealthy)"
  elif us_aqi <= 300:
    return "Sangat Tidak Sehat (Very Unhealthy)"
  else:
    return "Berbahaya (Hazardous)"


def fetch_and_log():
  wib_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")

  if not API_KEY:
    print("Error: API_KEY tidak ditemukan di Environment Variables!")
    return

  # 1. TARIK DATA KUALITAS UDARA (OpenWeather Air Pollution API)
  air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"

  try:
    res_air = requests.get(air_url, timeout=10)
    data_air = res_air.json()

    if res_air.status_code == 200 and "list" in data_air:
      item = data_air["list"][0]
      main_aqi = item.get("main", {}).get("aqi")
      comp = item.get("components", {})

      pm25 = comp.get("pm2_5")

      # Kuantifikasi & Labelisasi Tambahan
      ow_status = get_aqi_category(main_aqi)
      us_aqi_total = calculate_us_aqi_pm25(pm25)
      us_status = get_us_aqi_status(us_aqi_total)

      air_record = {
          "Timestamp": timestamp_wib,
          "City": CITY,
          "Latitude": LAT,
          "Longitude": LON,
          "Total_US_AQI": us_aqi_total,  # Contoh: 112 (Angka Total AQI 0-500)
          "Air_Quality_Status": us_status,  # Contoh: "Tidak Sehat bagi Kelompok Sensitif"
          "OW_AQI_Index": main_aqi,  # Indeks OpenWeather 1-5
          "OW_AQI_Category": ow_status,  # Status Indeks OpenWeather
          "PM25_Conc": pm25,  # ug/m3
          "PM10_Conc": comp.get("pm10"),  # ug/m3
          "CO_Conc": comp.get("co"),  # ug/m3
          "NO2_Conc": comp.get("no2"),  # ug/m3
          "O3_Conc": comp.get("o3"),  # ug/m3
          "SO2_Conc": comp.get("so2"),  # ug/m3
          "NH3_Conc": comp.get("nh3"),  # ug/m3
          "NO_Conc": comp.get("no"),  # ug/m3
      }

      df_air = pd.DataFrame([air_record])
      if os.path.exists(AIR_CSV):
        df_air.to_csv(AIR_CSV, mode="a", header=False, index=False)
      else:
        df_air.to_csv(AIR_CSV, mode="w", header=True, index=False)

      print(
          f"[{timestamp_wib}] Sukses mencatat AQI: {us_aqi_total} ({us_status})"
      )
    else:
      print("Gagal mengambil Air Pollution API:", data_air)

  except Exception as e:
    print("Error Air Pollution:", e)

  # 2. TARIK DATA CUACA TERKINI (OpenWeather Current Weather API)
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
          "Weather_Main": weather_desc.get("main"),
          "Weather_Desc": weather_desc.get("description"),
          "Temp_C": main_w.get("temp"),
          "Feels_Like_C": main_w.get("feels_like"),
          "Humidity_Pct": main_w.get("humidity"),
          "Pressure_hPa": main_w.get("pressure"),
          "Wind_Speed_ms": wind_w.get("speed"),
          "Wind_Deg": wind_w.get("deg"),
          "Clouds_Pct": clouds_w.get("all"),
          "Visibility_m": data_weather.get("visibility"),
      }

      df_weather = pd.DataFrame([weather_record])
      if os.path.exists(WEATHER_CSV):
        df_weather.to_csv(WEATHER_CSV, mode="a", header=False, index=False)
      else:
        df_weather.to_csv(WEATHER_CSV, mode="w", header=True, index=False)

      print(
          f"[{timestamp_wib}] Sukses mencatat Weather:"
          f" {weather_desc.get('main')}, {main_w.get('temp')}°C"
      )
    else:
      print("Gagal mengambil Weather API:", data_weather)

  except Exception as e:
    print("Error Weather:", e)


if __name__ == "__main__":
  fetch_and_log()
