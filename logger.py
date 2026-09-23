from datetime import datetime, timedelta
import os
import pandas as pd
import requests

# Ambil API Keys dari GitHub Secrets
OPENWEATHER_API_KEY = os.environ.get("API_KEY")
AQICN_API_KEY = os.environ.get("AQICN_API_KEY")

CITY = "Pekanbaru"
LAT = "0.5071"
LON = "101.4478"

AIR_CSV = "pekanbaru_air_quality_log.csv"
WEATHER_CSV = "pekanbaru_weather_log.csv"
FORECAST_CSV = "pekanbaru_weather_forecast_log.csv"


def calculate_us_aqi_pm25(pm25_conc):
  """Kalkulasi Total US AQI dari konsentrasi PM2.5 (standar US EPA)."""
  if pm25_conc is None:
    return None
  c = float(pm25_conc)
  breakpoints = [
      (0.0, 12.0, 0, 50),
      (12.1, 35.4, 51, 100),
      (35.5, 55.4, 101, 150),
      (55.5, 150.4, 151, 200),
      (150.5, 250.4, 201, 300),
      (250.5, 500.4, 301, 500),
  ]
  for c_low, c_high, i_low, i_high in breakpoints:
    if c_low <= c <= c_high:
      return round(((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low)
  return 500 if c > 500.4 else 0


def get_us_aqi_status(us_aqi):
  """Label Kategori Status Kualitas Udara."""
  if us_aqi is None:
    return "Tidak Diketahui"
  if us_aqi <= 50:
    return "Baik"
  if us_aqi <= 100:
    return "Sedang"
  if us_aqi <= 150:
    return "Tidak Sehat bagi Kelompok Sensitif"
  if us_aqi <= 200:
    return "Tidak Sehat"
  if us_aqi <= 300:
    return "Sangat Tidak Sehat"
  return "Berbahaya (Hazardous)"


def fetch_and_log():
  wib_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")

  # ==========================================================
  # 1. KUALITAS UDARA (OpenWeather Air Pollution + AQICN)
  # ==========================================================
  air_record = {
      "Timestamp": timestamp_wib,
      "City": CITY,
      "Latitude": LAT,
      "Longitude": LON,
  }

  # A. OpenWeather Air Pollution
  if OPENWEATHER_API_KEY:
    ow_air_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}"
    try:
      res_ow = requests.get(ow_air_url, timeout=10)
      if res_ow.status_code == 200:
        item = res_ow.json()["list"][0]
        comp = item.get("components", {})
        pm25 = comp.get("pm2_5")
        us_aqi_calc = calculate_us_aqi_pm25(pm25)

        air_record.update({
            "OW_US_AQI_Calc": us_aqi_calc,
            "OW_AQI_Status": get_us_aqi_status(us_aqi_calc),
            "OW_AQI_Index": item.get("main", {}).get("aqi"),
            "PM25_Conc": pm25,
            "PM10_Conc": comp.get("pm10"),
            "CO_Conc": comp.get("co"),
            "NO2_Conc": comp.get("no2"),
            "O3_Conc": comp.get("o3"),
            "SO2_Conc": comp.get("so2"),
            "NH3_Conc": comp.get("nh3"),
            "NO_Conc": comp.get("no"),
        })
    except Exception as e:
      print("Error OpenWeather Air Pollution:", e)

  # B. AQICN / WAQI Station
  if AQICN_API_KEY:
    aqicn_url = (
        f"https://api.waqi.info/feed/geo:{LAT};{LON}/?token={AQICN_API_KEY}"
    )
    try:
      res_aqicn = requests.get(aqicn_url, timeout=10)
      data_aqicn = res_aqicn.json()
      if data_aqicn.get("status") == "ok":
        d = data_aqicn["data"]
        station_aqi = d.get("aqi")
        air_record.update({
            "AQICN_Station_AQI": station_aqi,
            "AQICN_Station_Status": get_us_aqi_status(station_aqi),
            "AQICN_Station_Name": d.get("city", {}).get("name"),
            "AQICN_Dominant_Pollutant": d.get("dominentpol"),
        })
    except Exception as e:
      print("Error AQICN:", e)

  # Simpan Air Quality CSV
  df_air = pd.DataFrame([air_record])
  if os.path.exists(AIR_CSV):
    df_air.to_csv(AIR_CSV, mode="a", header=False, index=False)
  else:
    df_air.to_csv(AIR_CSV, mode="w", header=True, index=False)
  print(f"[{timestamp_wib}] Sukses mencatat dataset Kualitas Udara.")

  # ==========================================================
  # 2. CUACA TERKINI (OpenWeather Current Weather API)
  # ==========================================================
  if OPENWEATHER_API_KEY:
    ow_weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
      res_w = requests.get(ow_weather_url, timeout=10)
      if res_w.status_code == 200:
        data_w = res_w.json()
        main_w = data_w.get("main", {})
        weather_desc = data_w.get("weather", [{}])[0]

        weather_record = {
            "Timestamp": timestamp_wib,
            "City": CITY,
            "Weather_Main": weather_desc.get("main"),
            "Weather_Desc": weather_desc.get("description"),
            "Temp_C": main_w.get("temp"),
            "Feels_Like_C": main_w.get("feels_like"),
            "Humidity_Pct": main_w.get("humidity"),
            "Pressure_hPa": main_w.get("pressure"),
            "Wind_Speed_ms": data_w.get("wind", {}).get("speed"),
            "Clouds_Pct": data_w.get("clouds", {}).get("all"),
            "Visibility_m": data_w.get("visibility"),
        }

        df_weather = pd.DataFrame([weather_record])
        if os.path.exists(WEATHER_CSV):
          df_weather.to_csv(WEATHER_CSV, mode="a", header=False, index=False)
        else:
          df_weather.to_csv(WEATHER_CSV, mode="w", header=True, index=False)
        print(f"[{timestamp_wib}] Sukses mencatat dataset Cuaca Terkini.")
    except Exception as e:
      print("Error OpenWeather Current Weather:", e)

    # ==========================================================
    # 3. PREDIKSI CUACA (OpenWeather Forecast 5-Day / 3-Hour API)
    # ==========================================================
    ow_forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
      res_f = requests.get(ow_forecast_url, timeout=10)
      if res_f.status_code == 200:
        data_f = res_f.json()
        forecast_list = data_f.get("list", [])

        forecast_rows = []
        for item in forecast_list:
          # Konversi UTC target forecast ke WIB
          dt_txt_utc = item.get("dt_txt")
          dt_utc = datetime.strptime(dt_txt_utc, "%Y-%m-%d %H:%M:%S")
          dt_wib = (dt_utc + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")

          main_f = item.get("main", {})
          w_f = item.get("weather", [{}])[0]

          forecast_rows.append({
              "Fetched_Timestamp": timestamp_wib,  # Waktu data ditarik
              "Forecast_Target_WIB": dt_wib,  # Waktu target prediksi (WIB)
              "City": CITY,
              "Weather_Main": w_f.get("main"),
              "Weather_Desc": w_f.get("description"),
              "Temp_C": main_f.get("temp"),
              "Feels_Like_C": main_f.get("feels_like"),
              "Humidity_Pct": main_f.get("humidity"),
              "Pressure_hPa": main_f.get("pressure"),
              "Wind_Speed_ms": item.get("wind", {}).get("speed"),
              "Pop_Rain_Prob": item.get(
                  "pop"
              ),  # Probabilitas Hujan (0.0 - 1.0)
              "Clouds_Pct": item.get("clouds", {}).get("all"),
              "Visibility_m": item.get("visibility"),
          })

        df_forecast = pd.DataFrame(forecast_rows)
        if os.path.exists(FORECAST_CSV):
          df_forecast.to_csv(FORECAST_CSV, mode="a", header=False, index=False)
        else:
          df_forecast.to_csv(FORECAST_CSV, mode="w", header=True, index=False)
        print(f"[{timestamp_wib}] Sukses mencatat dataset Perkiraan Cuaca.")
    except Exception as e:
      print("Error OpenWeather Forecast:", e)


if __name__ == "__main__":
  fetch_and_log()
