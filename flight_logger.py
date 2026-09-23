import os
import requests
import pandas as pd
from datetime import datetime
import pytz

def fetch_and_save_flights():
    # Mengambil API Key dari Secrets GitHub / Environment
    api_key = os.getenv("AIRLABS_API_KEY")
    
    if not api_key:
        print("Error: AIRLABS_API_KEY tidak ditemukan di environment variables.")
        return

    # Bounding Box Terfokus Udara Bandara Soekarno-Hatta (CGK) & Halim (HLP)
    # Latitude: -6.35 s/d -6.00 | Longitude: 106.55 s/d 106.90
    bbox = "-6.35,106.55,-6.00,106.90"
    
    url = f"https://airlabs.co/api/v9/flights?bbox={bbox}&api_key={api_key}"
    
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    csv_file = "jakarta_flights_log.csv"

    try:
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            
            # Memastikan struktur JSON merespons dengan key 'response'
            if 'error' in result:
                print(f"AirLabs API Warning/Error: {result['error'].get('message', 'Unknown API Error')}")
                return

            flights = result.get('response', [])
            flight_data = []

            if isinstance(flights, list) and len(flights) > 0:
                for f in flights:
                    # Ambil nilai secara aman dengan fallback jika bernilai None/null
                    flight_iata = f.get('flight_iata') or 'N/A'
                    flight_icao = f.get('flight_icao') or 'N/A'
                    hex_code = f.get('hex') or 'N/A'
                    flag = f.get('flag') or 'N/A'
                    dep_iata = f.get('dep_iata') or 'N/A'
                    arr_iata = f.get('arr_iata') or 'N/A'
                    alt = f.get('alt') if f.get('alt') is not None else 0
                    speed = f.get('speed') if f.get('speed') is not None else 0
                    heading = f.get('dir') if f.get('dir') is not None else 0
                    lat = f.get('lat') if f.get('lat') is not None else -6.1256
                    lng = f.get('lng') if f.get('lng') is not None else 106.6558
                    status = f.get('status') or 'en-route'

                    flight_data.append({
                        'Timestamp': now_wib,
                        'Flight_IATA': flight_iata,
                        'Flight_ICAO': flight_icao,
                        'Hex_Code': hex_code,
                        'Flag': flag,
                        'Origin_IATA': dep_iata,
                        'Destination_IATA': arr_iata,
                        'Altitude_m': alt,
                        'Speed_kmh': speed,
                        'Heading': heading,
                        'Latitude': lat,
                        'Longitude': lng,
                        'Status': status
                    })
            else:
                # Log status jika sedang tidak ada pesawat yang terdeteksi
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
                    'Latitude': -6.1256,
                    'Longitude': 106.6558,
                    'Status': 'no_flights'
                })

            df_new = pd.DataFrame(flight_data)

            # Append data ke file CSV
            if os.path.exists(csv_file):
                df_new.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_new.to_csv(csv_file, mode='w', header=True, index=False)

            total_recorded = len(flights) if isinstance(flights, list) else 0
            print(f"[{now_wib}] AirLabs Success: Berhasil mencatat {total_recorded} penerbangan di Jakarta (CGK/HLP).")

        else:
            print(f"AirLabs API Error: HTTP Status Code {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error fetching AirLabs flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
