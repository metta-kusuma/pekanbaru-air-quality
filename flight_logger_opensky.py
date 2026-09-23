import os
import requests
import pandas as pd
from datetime import datetime
import pytz

def get_airline_name(callsign):
    """Menebak nama maskapai berdasarkan 3 huruf pertama kode Callsign ICAO"""
    if not callsign or callsign == 'N/A':
        return 'Unknown'
    
    prefix = callsign[:3].upper()
    airlines = {
        'GIA': 'Garuda Indonesia',
        'LKN': 'Lion Air',
        'BTK': 'Batik Air',
        'CTV': 'Citilink',
        'AWQ': 'Indonesia AirAsia',
        'SJY': 'Sriwijaya Air',
        'GFA': 'Gulf Air',
        'SIA': 'Singapore Airlines',
        'MAS': 'Malaysia Airlines',
        'UAE': 'Emirates',
        'QFA': 'Qantas',
        'CPA': 'Cathay Pacific'
    }
    return airlines.get(prefix, 'Other Airline')

def fetch_and_save_flights():
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    
    if not username or not password:
        print("Error: OPENSKY_USERNAME atau OPENSKY_PASSWORD tidak ditemukan di environment variables.")
        return

    # Bounding Box Jakarta & Sekitarnya (CGK & HLP)
    # lamin, lomin, lamax, lomax
    params = {
        'lamin': -6.35,
        'lomin': 106.55,
        'lamax': -6.00,
        'lomax': 106.90
    }
    
    url = "https://opensky-network.org/api/states/all"
    
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    csv_file = "jakarta_flights_log_opensky.csv"

    try:
        response = requests.get(url, params=params, auth=(username, password), timeout=20)
        
        if response.status_code == 200:
            result = response.json()
            states = result.get('states', [])
            flight_data = []

            if states:
                for s in states:
                    # Menampung seluruh 17 elemen mentah OpenSky (s[0] s/d s[16])
                    transponder_hex = s[0] or 'N/A'                          # s[0]: icao24
                    callsign = s[1].strip() if s[1] else 'N/A'              # s[1]: callsign
                    origin_country = s[2] or 'N/A'                        # s[2]: origin_country
                    time_position = s[3] or 0                                 # s[3]: time_position
                    last_contact = s[4] or 0                                  # s[4]: last_contact
                    longitude = s[5] if s[5] is not None else 106.6558       # s[5]: longitude
                    latitude = s[6] if s[6] is not None else -6.1256         # s[6]: latitude
                    baro_altitude_m = s[7] if s[7] is not None else 0         # s[7]: baro_altitude
                    is_ground = 1 if s[8] else 0                              # s[8]: on_ground
                    velocity_ms = s[9] if s[9] is not None else 0             # s[9]: velocity
                    heading_deg = s[10] if s[10] is not None else 0           # s[10]: true_track
                    vertical_rate_ms = s[11] if s[11] is not None else 0      # s[11]: vertical_rate
                    sensors = str(s[12]) if s[12] is not None else 'N/A'      # s[12]: sensors
                    geo_altitude_m = s[13] if s[13] is not None else 0        # s[13]: geo_altitude
                    squawk = s[14] or 'N/A'                                   # s[14]: squawk
                    spi = 1 if s[15] else 0                                   # s[15]: spi
                    position_source = s[16] if s[16] is not None else 0       # s[16]: position_source

                    # Konversi Satuan untuk kemudahan analisis
                    alt_feet = round(baro_altitude_m * 3.28084, 1)
                    geo_alt_feet = round(geo_altitude_m * 3.28084, 1)
                    speed_kmh = round(velocity_ms * 3.6, 1)
                    speed_knots = round(velocity_ms * 1.94384, 1)
                    v_speed_fpm = round(vertical_rate_ms * 196.85, 1)

                    # Penentuan Kategori Fase Terbang
                    if vertical_rate_ms > 1.5:
                        flight_phase = "Climbing (Takeoff)"
                    elif vertical_rate_ms < -1.5:
                        flight_phase = "Descending (Landing/Approach)"
                    elif is_ground == 1:
                        flight_phase = "On Taxiway/Runway"
                    else:
                        flight_phase = "Cruising"

                    flight_data.append({
                        'Timestamp_WIB': now_wib,
                        'Callsign': callsign,
                        'Airline_Inferred': get_airline_name(callsign),
                        'Transponder_Hex': transponder_hex,
                        'Country_Origin': origin_country,
                        'Squawk_Code': squawk,
                        'Latitude': latitude,
                        'Longitude': longitude,
                        'Baro_Altitude_Meters': baro_altitude_m,
                        'Baro_Altitude_Feet': alt_feet,
                        'Geo_Altitude_Meters': geo_altitude_m,
                        'Geo_Altitude_Feet': geo_alt_feet,
                        'Speed_KMH': speed_kmh,
                        'Speed_Knots': speed_knots,
                        'Vertical_Speed_MS': vertical_rate_ms,
                        'Vertical_Speed_FPM': v_speed_fpm,
                        'Heading_Deg': heading_deg,
                        'Flight_Phase': flight_phase,
                        'Is_Ground': is_ground,
                        'SPI_Transponder': spi,
                        'Position_Source_ID': position_source,
                        'Time_Position_Unix': time_position,
                        'Last_Contact_Unix': last_contact,
                        'Sensors_Data': sensors,
                        'Source': 'OpenSky Network'
                    })
            else:
                flight_data.append({
                    'Timestamp_WIB': now_wib,
                    'Callsign': 'NONE',
                    'Airline_Inferred': 'N/A',
                    'Transponder_Hex': 'N/A',
                    'Country_Origin': 'N/A',
                    'Squawk_Code': 'N/A',
                    'Latitude': -6.1256,
                    'Longitude': 106.6558,
                    'Baro_Altitude_Meters': 0,
                    'Baro_Altitude_Feet': 0,
                    'Geo_Altitude_Meters': 0,
                    'Geo_Altitude_Feet': 0,
                    'Speed_KMH': 0,
                    'Speed_Knots': 0,
                    'Vertical_Speed_MS': 0,
                    'Vertical_Speed_FPM': 0,
                    'Heading_Deg': 0,
                    'Flight_Phase': 'No Flights',
                    'Is_Ground': 0,
                    'SPI_Transponder': 0,
                    'Position_Source_ID': 0,
                    'Time_Position_Unix': 0,
                    'Last_Contact_Unix': 0,
                    'Sensors_Data': 'N/A',
                    'Source': 'OpenSky Network'
                })

            df_new = pd.DataFrame(flight_data)

            if os.path.exists(csv_file):
                df_new.to_csv(csv_file, mode='a', header=False, index=False)
            else:
                df_new.to_csv(csv_file, mode='w', header=True, index=False)

            total_recorded = len(states) if states else 0
            print(f"[{now_wib}] OpenSky Success: Berhasil mencatat {total_recorded} penerbangan (100% Atribut) di Jakarta.")

        else:
            print(f"OpenSky API Error: HTTP Status Code {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error fetching OpenSky flight data: {e}")

if __name__ == "__main__":
    fetch_and_save_flights()
