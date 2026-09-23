import os
import requests
import pandas as pd
from datetime import datetime
import pytz

def fetch_and_save_flights():
    # Mengambil API Key dari Secrets GitHub
    api_key = os.getenv("AIRLABS_API_KEY")
    
    if not api_key:
        print("Error: AIRLABS_API_KEY tidak ditemukan di environment variables.")
        return

    # Bounding Box Pekanbaru (lat_min, lon_min, lat_max, lon_max)
    # Latitude: 0.35 s/d 0.65 | Longitude: 101.30 s/d 101.60
    bbox = "0.35,101.30,0.65,101.60"
    
    url = f"https://airlabs.co/api/v9/flights?bbox={bbox}&api_key={api_key}"
    
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    csv_file = "pekanbaru_flights_log.csv"

    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            flights = result.get('response', [])
            flight_data = []

            if flights:
                for f in flights:
                    flight_data.append({
                        'Timestamp': now_wib,
                        'Flight_IATA': f.get('flight_iata', 'N/A'),
                        'Flight_ICAO': f.get('flight_icao', 'N/A'),
                        'Hex_Code': f.get('hex', 'N/A'),
                        'Flag': f.get('flag', 'N/A'),
                        'Origin_IATA': f.get('dep_iata', 'N/A'),
                        'Destination_IATA': f.get('arr_iata', 'N/A'),
                        'Altitude_m': f.get('alt', 0),
                        'Speed_kmh': f.get('speed', 0),
                        'Heading': f.get('dir', 0),
                        'Latitude': f.get('lat', 0.5071),
                        'Longitude': f.get('lng', 101.4478),
                        'Status': f.get('status', 'en-route')
                    })
            else:
                # Log status jika sedang tidak ada pesawat yang melintas
                flight_data.append({
                    'Timestamp': now_wib,
                    'Flight_IATA': 'NONE',
                    'Flight_ICAO': 'NONE',
                    'Hex_Code': 'N/A',
                    'Flag': 'N/A',
                    'Origin_IATA': 'N/A',
                    'Destination_IATA': 'N/A',
                    'Altitude_m': 0,
                    'Speed_kmh': 0,
                    'Heading': 0,
                    'Latitude': 0.5071,
                    'Longitude': 101.4478,
                    'Status': 'no_flights'
                })

            df_new = pd.DataFrame(flight_data)

            # Append data ke file CSV
            if os.path.exists(csv_file):
                df_new.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_new.to_csv(csv_file, mode='w', header=True, index=False)

            print(f"[{now_wib}] AirLabs Success: Berhasil mencatat {len(flights)} data penerbangan di Pekanbaru.")

        else:
            print(f"AirLabs API Error: HTTP Status Code {response.status_code}")

    except Exception as e:
        print(f"Error fetching AirLabs flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
