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

    # Bounding Box Perluas (Setara Range Approach Radar Jakarta / CGK & HLP)
    # Format AirLabs: lat_min,lng_min,lat_max,lng_max
    # lamin: -6.85 (Bogor/Sukabumi), lomin: 105.80 (Selat Sunda/Serang)
    # lamax: -5.50 (Laut Jawa), lomax: 107.50 (Karawang/Purwakarta)
    bbox = "-6.85,105.80,-5.50,107.50"
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
                    # Ambil data metrik penerbangan dasar & navigasi
                    alt_m = f.get('alt') if f.get('alt') is not None else 0
                    alt_ft = round(alt_m * 3.28084, 1) if alt_m else 0  # Konversi ke Feet
                    speed_kmh = f.get('speed') if f.get('speed') is not None else 0
                    speed_kts = round(speed_kmh / 1.852, 1) if speed_kmh else 0  # Konversi ke Knots
                    v_speed_ms = f.get('v_speed') if f.get('v_speed') is not None else 0
                    v_speed_fpm = round(v_speed_ms * 196.85, 1) if v_speed_ms else 0  # Konversi ke Feet/Min

                    # Penentuan Kategori Fase Terbang Berdasarkan Vertical Speed
                    if v_speed_ms > 1.5:
                        flight_phase = "Climbing (Takeoff)"
                    elif v_speed_ms < -1.5:
                        flight_phase = "Descending (Landing/Approach)"
                    elif f.get('is_ground') == 1:
                        flight_phase = "On Taxiway/Runway"
                    else:
                        flight_phase = "Cruising"

                    flight_data.append({
                        # 1. Waktu & Identifikasi
                        'Timestamp_WIB': now_wib,
                        'Flight_IATA': f.get('flight_iata') or 'N/A',
                        'Flight_ICAO': f.get('flight_icao') or 'N/A',
                        'Flight_Number': f.get('flight_number') or 'N/A',
                        
                        # 2. Maskapai & Registrasi Fisik
                        'Airline_IATA': f.get('airline_iata') or 'N/A',
                        'Airline_ICAO': f.get('airline_icao') or 'N/A',
                        'Aircraft_Code': f.get('aircraft_code') or 'N/A',
                        'Registration_Number': f.get('reg_number') or 'N/A',
                        'Transponder_Hex': f.get('hex') or 'N/A',
                        'Airline_Country_Flag': f.get('flag') or 'N/A',
                        
                        # 3. Rute & Bandara
                        'Origin_IATA': f.get('dep_iata') or 'N/A',
                        'Origin_ICAO': f.get('dep_icao') or 'N/A',
                        'Origin_Terminal': f.get('dep_terminal') or 'N/A',
                        'Destination_IATA': f.get('arr_iata') or 'N/A',
                        'Destination_ICAO': f.get('arr_icao') or 'N/A',
                        'Destination_Terminal': f.get('arr_terminal') or 'N/A',
                        
                        # 4. Telemetri Posisi & Koordinat
                        'Latitude': f.get('lat') if f.get('lat') is not None else -6.1256,
                        'Longitude': f.get('lng') if f.get('lng') is not None else 106.6558,
                        'Heading_Deg': f.get('dir') if f.get('dir') is not None else 0,
                        
                        # 5. Ketinggian & Kecepatan Multi-Satuan
                        'Altitude_Meters': alt_m,
                        'Altitude_Feet': alt_ft,
                        'Ground_Speed_KMH': speed_kmh,
                        'Ground_Speed_Knots': speed_kts,
                        'Vertical_Speed_MS': v_speed_ms,
                        'Vertical_Speed_FPM': v_speed_fpm,
                        
                        # 6. Status Operasional & Estimasi Terlambat
                        'Flight_Phase': flight_phase,
                        'Is_Ground': f.get('is_ground') if f.get('is_ground') is not None else 0,
                        'Delayed_Minutes': f.get('delayed') if f.get('delayed') is not None else 0,
                        'ETA_Timestamp': f.get('eta') or 'N/A',
                        'Updated_Unix_Time': f.get('updated') or 0,
                        'Status': f.get('status') or 'en-route'
                    })
            else:
                # Log status jika ruang udara sedang kosong
                flight_data.append({
                    'Timestamp_WIB': now_wib,
                    'Flight_IATA': 'NONE', 'Flight_ICAO': 'NONE', 'Flight_Number': 'NONE',
                    'Airline_IATA': 'N/A', 'Airline_ICAO': 'N/A', 'Aircraft_Code': 'N/A',
                    'Registration_Number': 'N/A', 'Transponder_Hex': 'N/A', 'Airline_Country_Flag': 'N/A',
                    'Origin_IATA': 'N/A', 'Origin_ICAO': 'N/A', 'Origin_Terminal': 'N/A',
                    'Destination_IATA': 'N/A', 'Destination_ICAO': 'N/A', 'Destination_Terminal': 'N/A',
                    'Latitude': -6.1256, 'Longitude': 106.6558, 'Heading_Deg': 0,
                    'Altitude_Meters': 0, 'Altitude_Feet': 0,
                    'Ground_Speed_KMH': 0, 'Ground_Speed_Knots': 0,
                    'Vertical_Speed_MS': 0, 'Vertical_Speed_FPM': 0,
                    'Flight_Phase': 'No Flights', 'Is_Ground': 0, 'Delayed_Minutes': 0,
                    'ETA_Timestamp': 'N/A', 'Updated_Unix_Time': 0, 'Status': 'no_flights'
                })

            df_new = pd.DataFrame(flight_data)

            if os.path.exists(csv_file):
                df_new.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_new.to_csv(csv_file, mode='w', header=True, index=False)

            total_recorded = len(flights) if isinstance(flights, list) else 0
            print(f"[{now_wib}] AirLabs Success: Berhasil mencatat {total_recorded} penerbangan di wilayah radar Approach Jakarta.")

        else:
            print(f"AirLabs API Error: HTTP Status Code {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error fetching AirLabs flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
