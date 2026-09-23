from datetime import datetime, timedelta
import os
import pandas as pd
import requests

AIRVISUAL_API_KEY = os.environ.get("API_KEY")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

CITY = "Pekanbaru"
STATE = "Riau"
COUNTRY = "Indonesia"
LAT = "0.5071"
LON = "101.4478"

AIR_CSV = "pekanbaru_air_quality_log.csv"
WEATHER_CSV = "pekanbaru_weather_log.csv"


def fetch_and_log():
  wib_time = datetime.utcnow() + timedelta(hours=7)
  timestamp_wib = wib_time.strftime("%Y-%m-%d %H:%M:%S")

  # 1. TARIK DATA KUALITAS UDARA (AirVisual)
  airvisual_url = f"https://api.airvisual.com/v2/city?city={CITY}&state={STATE}&country={COUNTRY}&key={AIRVISUAL_API_KEY}"
  try:
    res_av = requests.get(airvisual_url, timeout=10)
    data_av = res_av.json()
    if data_av.get("status") == "success":
      d = data_av["data"]
      pollution = d.get("current", {}).get("pollution", {})

      air_record = {
          "Timestamp": timestamp_wib,
          "City": CITY,
          "US_AQI": pollution.get("aqius"),
          "Main_Pollutant": pollution.get("mainus"),
      }

      pollutants = {
          "p2": "PM25",
          "p1": "PM10",
          "o3": "O3",
          "n2": "NO2",
          "s2": "SO2",
          "co": "CO",
      }
      for p_key, p_name in pollutants.items():
        p_data = pollution.get(p_key, {})
        air_record[f"{p_name}_Conc"] = p_data.get("conc")
        air_record[f"{p_name}_AQI"] = p_data.get("aqius")

      df_air = pd.DataFrame([air_record])
      if os.path.exists(AIR_CSV):
        df_air.to_csv(AIR_CSV, mode="a", header=False, index=False)
      else:
        df_air.to_csv(AIR_CSV, mode="w", header=True, index=False)
      print("Sukses mencatat Air Quality.")
  except Exception as e:
    print("Error Air Quality:", e)

  # 2. TARIK DATA CUACA TERKINI (OpenWeather)
  ow_key = OPENWEATHER_API_KEY if OPENWEATHER_API_KEY else AIRVISUAL_API_KEY
  openweather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={ow_key}&units=metric"
  try:
    res_ow = requests.get(openweather_url, timeout=10)
    data_ow = res_ow.json()
    if res_ow.status_code == 200:
      main_ow = data_ow.get("main", {})
      weather_desc = data_ow.get("weather", [{}])[0]
      wind_ow = data_ow.get("wind", {})

      weather_record = {
          "Timestamp": timestamp_wib,
          "City": CITY,
          "Weather_Main": weather_desc.get("main"),
          "Weather_Desc": weather_desc.get("description"),
          "Temp_C": main_ow.get("temp"),
          "Feels_Like_C": main_ow.get("feels_like"),
          "Humidity_Pct": main_ow.get("humidity"),
          "Pressure_hPa": main_ow.get("pressure"),
          "Wind_Speed_ms": wind_ow.get("speed"),
          "Clouds_Pct": data_ow.get("clouds", {}).get("all"),
          "Visibility_m": data_ow.get("visibility"),
      }

      df_weather = pd.DataFrame([weather_record])
      if os.path.exists(WEATHER_CSV):
        df_weather.to_csv(WEATHER_CSV, mode="a", header=False, index=False)
      else:
        df_weather.to_csv(WEATHER_CSV, mode="w", header=True, index=False)
      print("Sukses mencatat Weather.")
  except Exception as e:
    print("Error Weather:", e)


if __name__ == "__main__":
  fetch_and_log()
