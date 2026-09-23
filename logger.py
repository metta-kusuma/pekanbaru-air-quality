from datetime import datetime, timedelta
import os
import pandas as pd
import requests

# Mengambil 2 API Key berbeda dari Environment Variables
OPENWEATHER_API_KEY = os.environ.get("API_KEY")
AIRVISUAL_API_KEY = os.environ.get("AIRVISUAL_API_KEY")

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

  # 1. TARIK DATA KUALITAS UDARA (AirVisual API)
  if AIRVISUAL_API_KEY:
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
            "China_AQI": pollution.get("aqicn"),
            "Main_China_Pollutant": pollution.get("maincn"),
        }

        # Polutan Rinci
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
          air_record[f"{p_name}_AQI_US"] = p_data.get("aqius")

        df_air = pd.DataFrame([air_record])
        if os.path.exists(AIR_CSV):
          df_air.to_csv(AIR_CSV, mode="a", header=False, index=False)
        else:
          df_air.to_csv(AIR_CSV, mode="w", header=True, index=False)
        print("-> Sukses mencatat Air Quality (IQAir).")
      else:
        print("Gagal AirVisual API:", data_av)
    except Exception as e:
      print("Error AirVisual:", e)
  else:
    print("Warning: AIRVISUAL_API_KEY belum terpasang di Environment Variable.")

  # 2. TARIK DATA CUACA TERKINI (OpenWeather API)
  if OPENWEATHER_API_KEY:
    openweather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
      res_ow = requests.get(openweather_url, timeout=10)
      data_ow = res_ow.json()

      if res_ow.status_code == 200:
        main_ow = data_ow.get("main", {})
        weather_desc = data_ow.get("weather", [{}])[0]

        weather_record = {
            "Timestamp": timestamp_wib,
            "City": CITY,
            "Weather_Main": weather_desc.get("main"),
            "Weather_Desc": weather_desc.get("description"),
            "Temp_C": main_ow.get("temp"),
            "Feels_Like_C": main_ow.get("feels_like"),
            "Humidity_Pct": main_ow.get("humidity"),
            "Pressure_hPa": main_ow.get("pressure"),
            "Wind_Speed_ms": data_ow.get("wind", {}).get("speed"),
            "Clouds_Pct": data_ow.get("clouds", {}).get("all"),
            "Visibility_m": data_ow.get("visibility"),
        }

        df_weather = pd.DataFrame([weather_record])
        if os.path.exists(WEATHER_CSV):
          df_weather.to_csv(WEATHER_CSV, mode="a", header=False, index=False)
        else:
          df_weather.to_csv(WEATHER_CSV, mode="w", header=True, index=False)
        print("-> Sukses mencatat Weather (OpenWeather).")
      else:
        print("Gagal OpenWeather API:", data_ow)
    except Exception as e:
      print("Error OpenWeather:", e)
  else:
    print("Warning: OPENWEATHER_API_KEY/API_KEY belum terpasang.")


if __name__ == "__main__":
  fetch_and_log()
