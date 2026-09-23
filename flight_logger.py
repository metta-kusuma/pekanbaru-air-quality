import os
import pandas as pd
from datetime import datetime
import pytz
from FlightRadar24 import FlightRadar24API

def fetch_and_save_flights():
    fr_api = FlightRadar24API()
  
    bounds = "0.65,0.35,101.30,101.60"
    
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    
    csv_file = "pekanbaru_flights_log.csv"
    
    try:
        flights = fr_api.get_flights(bounds=bounds)
        flight_data = []
        
        if flights:
            for f in flights:
                flight_data.append({
                    'Timestamp': now_wib,
                    'Flight_Callsign': f.callsign if f.callsign else 'N/A',
                    'Airline': f.airline_short if f.airline_short else 'N/A',
                    'Origin': f.origin_airport_iata if f.origin_airport_iata else 'N/A',
                    'Destination': f.destination_airport_iata if f.destination_airport_iata else 'N/A',
                    'Altitude_ft': f.altitude,
                    'Ground_Speed_kts': f.ground_speed,
                    'Latitude': f.latitude,
                    'Longitude': f.longitude
                })
        else:
            # Catat log kosong jika tidak ada pesawat yang melintas
            flight_data.append({
                'Timestamp': now_wib,
                'Flight_Callsign': 'NONE',
                'Airline': 'NONE',
                'Origin': 'N/A',
                'Destination': 'N/A',
                'Altitude_ft': 0,
                'Ground_Speed_kts': 0,
                'Latitude': 0.5071,
                'Longitude': 101.4478
            })
            
        df_new = pd.DataFrame(flight_data)
        
        # Append data ke file CSV secara otomatis
        if os.path.exists(csv_file):
            df_new.to_csv(csv_file, mode='a', header=False, index=False)
        else:
            df_new.to_csv(csv_file, mode='w', header=True, index=False)
            
        print(f"[{now_wib}] Berhasil mencatat {len(flights)} data penerbangan Pekanbaru.")
        
    except Exception as e:
        print(f"Error fetching flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
