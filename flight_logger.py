import os
import requests
import pandas as pd
from datetime import datetime
import pytz

def fetch_and_save_flights():
    api_key = os.getenv("AIRLABS_API_KEY")
    
    if not api_key:
        print("Error: AIRLABS_API_KEY tidak ditemukan di environment variables.")
        return

    # Bounding Box Udara Bandara CGK & HLP
    bbox = "-6.35,106.55,-6.00,106.90"
    url = f"https://airlabs.co/api/v9/flights?bbox={bbox}&api_key={api_key}"
    
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    csv_file = "jakarta_flights_log.csv"

    try:
        response = requests.get(url, timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            
            if 'error' in result:
                print(f"AirLabs API Warning/Error: {result['error'].get('message', 'Unknown API Error')}")
                return

            flights = result.get('response', [])
            flight_data = []

            if isinstance(flights, list) and len(flights) > 0:
                for f in flights:
                    flight_data.append({
                        'Timestamp': now_wib,
                        'Flight_IATA': f.get('flight_iata') or 'N/A',
                        'Flight_ICAO': f.get('flight_icao') or 'N/A',
                        'Airline_IATA': f.get('airline_iata') or 'N/A',
                        'Airline_ICAO': f.get('airline_icao') or 'N/A',
                        'Aircraft_Code': f.get('aircraft_code') or 'N/A',
                        'Registration': f.get('reg_number') or 'N/A',
                        'Hex_Code': f.get('hex') or 'N/A',
                        'Flag': f.get('flag') or 'N/A',
                        'Origin_IATA': f.get('dep_iata') or 'N/A',
                        'Destination_IATA': f.get('arr_iata') or 'N/A',
                        'Altitude_m': f.get('alt') if f.get('alt') is not None else 0,
                        'Speed_kmh': f.get('speed') if f.get('speed') is not None else 0,
                        'Vertical_Speed_ms': f.get('v_speed') if f.get('v_speed') is not None else 0,
                        'Heading': f.get('dir') if f.get('dir') is not None else 0,
                        'Is_Ground': f.get('is_ground') if f.get('is_ground') is not None else 0,
                        'Delayed_Minutes': f.get('delayed') if f.get('delayed') is not None else 0,
                        'Latitude': f.get('lat') if f.get('lat') is not None else -6.1256,
                        'Longitude': f.get('lng') if f.get('lng') is not None else 106.6558,
                        'Status': f.get('status') or 'en-route'
                    })
            else:
                # Log status jika sedang tidak ada pesawat yang terdeteksi
                flight_data.append({
                    'Timestamp': now_wib,
                    'Flight_IATA': 'NONE',
                    'Flight_ICAO': 'NONE',
                    'Airline_IATA': 'N/A',
                    'Airline_ICAO': 'N/A',
                    'Aircraft_Code': 'N/A',
                    'Registration': 'N/A',
                    'Hex_Code': 'N/A',
                    'Flag': 'N/A',
                    'Origin_IATA': 'N/A',
                    'Destination_IATA': 'N/A',
                    'Altitude_m': 0,
                    'Speed_kmh': 0,
                    'Vertical_Speed_ms': 0,
                    'Heading': 0,
                    'Is_Ground': 0,
                    'Delayed_Minutes': 0,
                    'Latitude': -6.1256,
                    'Longitude': 106.6558,
                    'Status': 'no_flights'
                })

            df_new = pd.DataFrame(flight_data)

            if os.path.exists(csv_file):
                df_new.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_new.to_csv(csv_file, mode='w', header=True, index=False)

            total_recorded = len(flights) if isinstance(flights, list) else 0
            print(f"[{now_wib}] AirLabs Success: Berhasil mencatat {total_recorded} penerbangan lengkap di Jakarta (CGK/HLP).")

        else:
            print(f"AirLabs API Error: HTTP Status Code {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error fetching AirLabs flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
