import os
import requests
import pandas as pd
from datetime import datetime
import pytz
from FlightRadarAPI import FlightRadar24API

def get_airline_name(callsign):
    """Menebak nama maskapai berdasarkan kode Callsign ICAO / Registrasi Fisik"""
    if not callsign or callsign == 'N/A' or callsign == 'NONE':
        return 'Unknown'
    
    callsign = callsign.strip().upper()
    prefix = callsign[:3]
    
    if callsign.startswith(('PK', 'T7', 'P7', 'VH', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9')):
        return 'Private / Business Jet / General Aviation'
    
    airlines = {
        'GIA': 'Garuda Indonesia', 'LNI': 'Lion Air', 'LKN': 'Lion Air (Alt)', 'BTK': 'Batik Air',
        'CTV': 'Citilink', 'AWQ': 'Indonesia AirAsia', 'SJV': 'Sriwijaya Air / Super Air Jet',
        'SJY': 'Sriwijaya Air', 'NAM': 'NAM Air', 'PAS': 'Pelita Air Service', 'TNU': 'TransNusa',
        'PTP': 'PT TransNusa Aviation Mandiri', 'WON': 'Wings Air', 'SUA': 'Susi Air',
        'TNX': 'Trigana Air Service', 'SPRN': 'Super Air Jet (Alt)', 'KCN': 'K-Mile Air / Kencana Air',
        'JDE': 'IndiGo / Eastindo Charter', 'RGM': 'Rimbun Air', 'CTW': 'Citilink (Cargo/Charter)',
        'MKT': 'Mokulele / Smart Aviation', 'TAG': 'Express Transportasi Antarbenua',
        'OEY': 'Other Charter / Executive', 'FHS': 'Flight Inspection / Helicopter',
        'RON': 'Nami Air / Indonesia Air Transport', 'XAR': 'Express Air', 'BHA': 'Aero Nusantara Indonesia',
        'PKN': 'Nusantara Air Charter', 'SMG': 'Semuwa Air', 'PPA': 'Pelita Air',
        'TREK': 'TNI Angkatan Udara', 'ALPHA': 'TNI Angkatan Udara', 'NAVY': 'TNI Angkatan Udara',
        'POL': 'Kepolisian Republik Indonesia', 'RGI': 'My Indo Airlines', 'BTP': 'Asia Cargo Airlines',
        'TNO': 'Tri-MG Intra Asia Airlines', 'CSN': 'China Southern Airlines', 'TGW': 'Scoot',
        'ANA': 'All Nippon Airways (ANA)', 'CCA': 'Air China', 'PAL': 'Philippine Airlines',
        'CEB': 'Cebu Pacific', 'CXA': 'XiamenAir', 'JAL': 'Japan Airlines (JAL)',
        'CDG': 'Shandong Airlines / China Eastern', 'CES': 'China Eastern Airlines',
        'HVN': 'Vietnam Airlines', 'KAL': 'Korean Air', 'KMI': 'K-Mile Air',
        'MXD': 'Batik Air Malaysia (Malindo)', 'ETD': 'Etihad Airways', 'SVA': 'Saudia (Saudi Arabian)',
        'THY': 'Turkish Airlines', 'QTR': 'Qatar Airways', 'JST': 'Jetstar Airways',
        'MYU': 'My Indo Airlines', 'QQE': 'Qatar Executive / Charter', 'UAE': 'Emirates',
        'SUD': 'Saudi Arabian Airlines', 'SWR': 'Swiss International Air Lines', 'GFA': 'Gulf Air',
        'OMA': 'Oman Air', 'RJA': 'Royal Jordanian', 'KAC': 'Kuwait Airways', 'SIA': 'Singapore Airlines',
        'SLK': 'SilkAir', 'MAS': 'Malaysia Airlines', 'AXM': 'AirAsia (Malaysia)', 'MYX': 'MYAirline',
        'THA': 'Thai Airways International', 'AIQ': 'Thai AirAsia', 'TLM': 'Thai Lion Air',
        'CPA': 'Cathay Pacific', 'HDA': 'Cathay Dragon / HK Express', 'HKP': 'Hong Kong Express Airways',
        'CRK': 'Hong Kong Airlines', 'VJC': 'VietJet Air', 'RBA': 'Royal Brunei Airlines',
        'MMR': 'Myanmar Airways International', 'TZP': 'Zipair Tokyo', 'AAR': 'Asiana Airlines',
        'JJA': 'Jeju Air', 'CHB': 'China Cargo Airlines', 'CAL': 'China Airlines (Taiwan)',
        'EVA': 'EVA Air', 'SJX': 'Starlux Airlines', 'AIC': 'Air India', 'IGO': 'IndiGo',
        'BPO': 'Biman Bangladesh Airlines', 'ALK': 'SriLankan Airlines', 'QFA': 'Qantas',
        'VOZ': 'Virgin Australia', 'ANZ': 'Air New Zealand', 'KLM': 'KLM Royal Dutch Airlines',
        'AFR': 'Air France', 'BAW': 'British Airways', 'DLH': 'Lufthansa', 'UAL': 'United Airlines',
        'AAL': 'American Airlines', 'DAL': 'Delta Air Lines', 'FDX': 'FedEx Express', 'UPS': 'UPS Airlines',
        'GTI': 'Atlas Air', 'BOX': 'Aerologic (DHL Cargo)', 'PAC': 'Polar Air Cargo', 'SQC': 'Singapore Airlines Cargo'
    }
    return airlines.get(prefix, 'Other Airline')

# -------------------------------------------------------------------
# 1. OPENSKY DATA FETCHING (ASLI)
# -------------------------------------------------------------------
def fetch_opensky_flights(now_wib):
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    
    if not username or not password:
        print("Error: OPENSKY_USERNAME atau OPENSKY_PASSWORD tidak ditemukan di environment variables.")
        return

    params = {'lamin': -6.85, 'lomin': 105.80, 'lamax': -5.50, 'lomax': 107.50}
    url = "https://opensky-network.org/api/states/all"
    csv_file = "jakarta_flights_log_opensky.csv"

    try:
        response = requests.get(url, params=params, auth=(username, password), timeout=20)
        if response.status_code == 200:
            result = response.json()
            states = result.get('states', [])
            flight_data = []

            if states:
                for s in states:
                    transponder_hex = s[0] or 'N/A'
                    callsign = s[1].strip() if s[1] else 'N/A'
                    origin_country = s[2] or 'N/A'
                    time_position = s[3] or 0
                    last_contact = s[4] or 0
                    longitude = s[5] if s[5] is not None else 106.6558
                    latitude = s[6] if s[6] is not None else -6.1256
                    baro_altitude_m = s[7] if s[7] is not None else 0
                    is_ground = 1 if s[8] else 0
                    velocity_ms = s[9] if s[9] is not None else 0
                    heading_deg = s[10] if s[10] is not None else 0
                    vertical_rate_ms = s[11] if s[11] is not None else 0
                    sensors = str(s[12]) if s[12] is not None else 'N/A'
                    geo_altitude_m = s[13] if s[13] is not None else 0
                    squawk = s[14] or 'N/A'
                    spi = 1 if s[15] else 0
                    position_source = s[16] if s[16] is not None else 0

                    alt_feet = round(baro_altitude_m * 3.28084, 1)
                    geo_alt_feet = round(geo_altitude_m * 3.28084, 1)
                    speed_kmh = round(velocity_ms * 3.6, 1)
                    speed_knots = round(velocity_ms * 1.94384, 1)
                    v_speed_fpm = round(vertical_rate_ms * 196.85, 1)

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
                    'Timestamp_WIB': now_wib, 'Callsign': 'NONE', 'Airline_Inferred': 'N/A',
                    'Transponder_Hex': 'N/A', 'Country_Origin': 'N/A', 'Squawk_Code': 'N/A',
                    'Latitude': -6.1256, 'Longitude': 106.6558, 'Baro_Altitude_Meters': 0,
                    'Baro_Altitude_Feet': 0, 'Geo_Altitude_Meters': 0, 'Geo_Altitude_Feet': 0,
                    'Speed_KMH': 0, 'Speed_Knots': 0, 'Vertical_Speed_MS': 0, 'Vertical_Speed_FPM': 0,
                    'Heading_Deg': 0, 'Flight_Phase': 'No Flights', 'Is_Ground': 0,
                    'SPI_Transponder': 0, 'Position_Source_ID': 0, 'Time_Position_Unix': 0,
                    'Last_Contact_Unix': 0, 'Sensors_Data': 'N/A', 'Source': 'OpenSky Network'
                })

            df_new = pd.DataFrame(flight_data)
            df_new.to_csv(csv_file, mode='a' if os.path.exists(csv_file) else 'w', header=not os.path.exists(csv_file), index=False)
            print(f"[{now_wib}] OpenSky Success: Berhasil mencatat {len(states) if states else 0} penerbangan.")

        else:
            print(f"OpenSky API Error: Status Code {response.status_code}")

    except Exception as e:
        print(f"Error fetching OpenSky data: {e}")

# -------------------------------------------------------------------
# 2. FLIGHTRADAR24 DATA FETCHING (EXTENDED FULL DETAILS)
# -------------------------------------------------------------------
def fetch_fr24_flights(now_wib):
    csv_file = "jakarta_flights_log_fr24.csv"
    
    try:
        fr_api = FlightRadar24API()
        bounds = fr_api.get_bounds_by_point(latitude=-6.1256, longitude=106.6558, radius=100000)
        flights = fr_api.get_flights(bounds=bounds)
        flight_data = []

        if isinstance(flights, list) and len(flights) > 0:
            for f in flights:
                # Memanggil detail penerbangan lengkap per pesawat
                try:
                    details = fr_api.get_flight_details(f)
                    if isinstance(details, dict):
                        f.set_flight_details(details)
                except Exception:
                    pass  # Tetap amankan proses jika ada 1 detail penerbangan yang gagal

                alt_ft = f.altitude if f.altitude is not None else 0
                alt_m = round(alt_ft / 3.28084, 1) if alt_ft else 0
                speed_kts = f.ground_speed if f.ground_speed is not None else 0
                speed_kmh = round(speed_kts * 1.852, 1) if speed_kts else 0
                v_speed_fpm = f.vertical_speed if f.vertical_speed is not None else 0
                v_speed_ms = round(v_speed_fpm / 196.85, 2) if v_speed_fpm else 0
                is_ground = 1 if f.on_ground else 0

                if v_speed_ms > 1.5:
                    flight_phase = "Climbing (Takeoff)"
                elif v_speed_ms < -1.5:
                    flight_phase = "Descending (Landing/Approach)"
                elif is_ground == 1:
                    flight_phase = "On Taxiway/Runway"
                else:
                    flight_phase = "Cruising"

                flight_data.append({
                    # 1. Identifikasi & Waktu
                    'Timestamp_WIB': now_wib,
                    'Callsign': getattr(f, 'callsign', None) or 'N/A',
                    'Flight_Number': getattr(f, 'number', None) or 'N/A',
                    'Flight_ID': getattr(f, 'id', None) or 'N/A',
                    
                    # 2. Maskapai & Fisik Pesawat
                    'Airline_Name': getattr(f, 'airline_name', None) or 'N/A',
                    'Airline_ICAO': getattr(f, 'airline_icao', None) or 'N/A',
                    'Airline_IATA': getattr(f, 'airline_iata', None) or 'N/A',
                    'Aircraft_Model': getattr(f, 'aircraft_code', None) or 'N/A',
                    'Aircraft_Type': getattr(f, 'aircraft_model', None) or 'N/A',
                    'Registration_Number': getattr(f, 'registration', None) or 'N/A',
                    'Aircraft_Image_URL': getattr(f, 'aircraft_image_thumbnail_url', None) or 'N/A',
                    
                    # 3. Rute & Detail Bandara
                    'Origin_IATA': getattr(f, 'origin_airport_iata', None) or 'N/A',
                    'Origin_ICAO': getattr(f, 'origin_airport_icao', None) or 'N/A',
                    'Origin_Airport_Name': getattr(f, 'origin_airport_name', None) or 'N/A',
                    'Origin_City': getattr(f, 'origin_airport_city', None) or 'N/A',
                    'Destination_IATA': getattr(f, 'destination_airport_iata', None) or 'N/A',
                    'Destination_ICAO': getattr(f, 'destination_airport_icao', None) or 'N/A',
                    'Destination_Airport_Name': getattr(f, 'destination_airport_name', None) or 'N/A',
                    'Destination_City': getattr(f, 'destination_airport_city', None) or 'N/A',
                    
                    # 4. Telemetri Posisi & Navigasi
                    'Latitude': getattr(f, 'latitude', None) if getattr(f, 'latitude', None) is not None else -6.1256,
                    'Longitude': getattr(f, 'longitude', None) if getattr(f, 'longitude', None) is not None else 106.6558,
                    'Heading_Deg': getattr(f, 'heading', None) if getattr(f, 'heading', None) is not None else 0,
                    'Squawk_Code': getattr(f, 'squawk', None) or 'N/A',
                    
                    # 5. Ketinggian & Kecepatan
                    'Altitude_Meters': alt_m,
                    'Altitude_Feet': alt_ft,
                    'Ground_Speed_KMH': speed_kmh,
                    'Ground_Speed_Knots': speed_kts,
                    'Vertical_Speed_MS': v_speed_ms,
                    'Vertical_Speed_FPM': v_speed_fpm,
                    
                    # 6. Status Operasional & Jadwal Presisi
                    'Flight_Phase': flight_phase,
                    'Is_Ground': is_ground,
                    'Status_Text': getattr(f, 'status_text', None) or 'N/A',
                    'Scheduled_Departure': getattr(f, 'time_scheduled_departure', None) or 'N/A',
                    'Actual_Departure': getattr(f, 'time_real_departure', None) or 'N/A',
                    'Estimated_Arrival': getattr(f, 'time_estimated_arrival', None) or 'N/A',
                    
                    'Source': 'FlightRadar24'
                })
        else:
            flight_data.append({
                'Timestamp_WIB': now_wib, 'Callsign': 'NONE', 'Flight_Number': 'NONE', 'Flight_ID': 'N/A',
                'Airline_Name': 'N/A', 'Airline_ICAO': 'N/A', 'Airline_IATA': 'N/A',
                'Aircraft_Model': 'N/A', 'Aircraft_Type': 'N/A', 'Registration_Number': 'N/A', 'Aircraft_Image_URL': 'N/A',
                'Origin_IATA': 'N/A', 'Origin_ICAO': 'N/A', 'Origin_Airport_Name': 'N/A', 'Origin_City': 'N/A',
                'Destination_IATA': 'N/A', 'Destination_ICAO': 'N/A', 'Destination_Airport_Name': 'N/A', 'Destination_City': 'N/A',
                'Latitude': -6.1256, 'Longitude': 106.6558, 'Heading_Deg': 0, 'Squawk_Code': 'N/A',
                'Altitude_Meters': 0, 'Altitude_Feet': 0, 'Ground_Speed_KMH': 0, 'Ground_Speed_Knots': 0,
                'Vertical_Speed_MS': 0, 'Vertical_Speed_FPM': 0, 'Flight_Phase': 'No Flights', 'Is_Ground': 0,
                'Status_Text': 'N/A', 'Scheduled_Departure': 'N/A', 'Actual_Departure': 'N/A', 'Estimated_Arrival': 'N/A',
                'Source': 'FlightRadar24'
            })

        df_new = pd.DataFrame(flight_data)
        df_new.to_csv(csv_file, mode='a' if os.path.exists(csv_file) else 'w', header=not os.path.exists(csv_file), index=False)
        print(f"[{now_wib}] FlightRadar24 Success: Berhasil mencatat {len(flights) if flights else 0} penerbangan (Full Details).")

    except Exception as e:
        print(f"Error fetching FlightRadar24 data: {e}")

# -------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------
if __name__ == "__main__":
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    
    fetch_opensky_flights(now_wib)
    fetch_fr24_flights(now_wib)
