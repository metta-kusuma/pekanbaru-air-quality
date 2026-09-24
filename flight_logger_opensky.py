import os
import requests
import pandas as pd
from datetime import datetime
import pytz
import time
from FlightRadarAPI import FlightRadar24API

def get_airline_name(callsign):
    """Menebak nama maskapai berdasarkan kode Callsign ICAO / Registrasi Fisik"""
    if not callsign or callsign == 'N/A' or callsign == 'NONE':
        return 'Unknown'
    
    callsign = callsign.strip().upper()
    prefix = callsign[:3]
    
    if callsign.startswith(('PK', 'T7', 'P7', 'VH', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', '9V')):
        if callsign.startswith('9V'):
            return 'Singapore Registered Aircraft / GA'
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
# 1. OPENSKY DATA FETCHING (JAKARTA, SINGAPURA, BALI, KALIMANTAN - 500 KM+)
# -------------------------------------------------------------------
def fetch_opensky_flights(now_wib):
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    
    if not username or not password:
        print("Error: OPENSKY_USERNAME atau OPENSKY_PASSWORD tidak ditemukan di environment variables.")
        return

    # Bounding Box Raksasa mencakup seluruh wilayah Asia Tenggara Maritim
    params = {'lamin': -13.25, 'lamax': 7.50, 'lomin': 98.50, 'lomax': 119.70}
    url = "https://opensky-network.org/api/states/all"

    try:
        response = requests.get(url, params=params, auth=(username, password), timeout=20)
        if response.status_code == 200:
            result = response.json()
            states = result.get('states', [])
            
            f_jkt, f_sin, f_dps, f_kal = [], [], [], []

            if states:
                for s in states:
                    latitude = s[6] if s[6] is not None else 0
                    longitude = s[5] if s[5] is not None else 0
                    
                    # Filter radius 500 km per bandara pusat
                    is_jakarta = (-10.63 <= latitude <= -1.60 and 102.00 <= longitude <= 111.16)
                    is_singapore = (-3.14 <= latitude <= 5.86 and 99.49 <= longitude <= 108.49)
                    is_bali = (-13.25 <= latitude <= -4.25 and 110.67 <= longitude <= 119.70)
                    is_kalimantan = (-5.75 <= latitude <= 7.50 and 108.50 <= longitude <= 119.70)

                    if not is_jakarta and not is_singapore and not is_bali and not is_kalimantan:
                        continue

                    row = build_opensky_row(s, now_wib)

                    if is_jakarta: f_jkt.append(row)
                    if is_singapore: f_sin.append(row)
                    if is_bali: f_dps.append(row)
                    if is_kalimantan: f_kal.append(row)

            # Fallback jika data kosong
            fallback = lambda lat, lon: [{'Timestamp_WIB': now_wib, 'Callsign': 'NONE', 'Airline_Inferred': 'N/A', 'Transponder_Hex': 'N/A', 'Country_Origin': 'N/A', 'Squawk_Code': 'N/A', 'Latitude': lat, 'Longitude': lon, 'Baro_Altitude_Meters': 0, 'Baro_Altitude_Feet': 0, 'Geo_Altitude_Meters': 0, 'Geo_Altitude_Feet': 0, 'Speed_KMH': 0, 'Speed_Knots': 0, 'Vertical_Speed_MS': 0, 'Vertical_Speed_FPM': 0, 'Heading_Deg': 0, 'Flight_Phase': 'No Flights', 'Is_Ground': 0, 'SPI_Transponder': 0, 'Position_Source_ID': 0, 'Time_Position_Unix': 0, 'Last_Contact_Unix': 0, 'Sensors_Data': 'N/A', 'Source': 'OpenSky Network'}]

            if not f_jkt: f_jkt = fallback(-6.1256, 106.6558)
            if not f_sin: f_sin = fallback(1.3644, 103.9915)
            if not f_dps: f_dps = fallback(-8.7482, 115.1672)
            if not f_kal: f_kal = fallback(-1.2682, 116.8942)

            pd.DataFrame(f_jkt).to_csv('jakarta_flights_log_opensky.csv', mode='a' if os.path.exists('jakarta_flights_log_opensky.csv') else 'w', header=not os.path.exists('jakarta_flights_log_opensky.csv'), index=False)
            pd.DataFrame(f_sin).to_csv('singapore_flights_log_opensky.csv', mode='a' if os.path.exists('singapore_flights_log_opensky.csv') else 'w', header=not os.path.exists('singapore_flights_log_opensky.csv'), index=False)
            pd.DataFrame(f_dps).to_csv('bali_flights_log_opensky.csv', mode='a' if os.path.exists('bali_flights_log_opensky.csv') else 'w', header=not os.path.exists('bali_flights_log_opensky.csv'), index=False)
            pd.DataFrame(f_kal).to_csv('kalimantan_flights_log_opensky.csv', mode='a' if os.path.exists('kalimantan_flights_log_opensky.csv') else 'w', header=not os.path.exists('kalimantan_flights_log_opensky.csv'), index=False)
            
            print(f"[{now_wib}] OpenSky Success (500km Range): Jakarta ({len(f_jkt)}), Singapore ({len(f_sin)}), Bali ({len(f_dps)}), Kalimantan ({len(f_kal)}).")

        else:
            print(f"OpenSky API Error: Status Code {response.status_code}")

    except Exception as e:
        print(f"Error fetching OpenSky data: {e}")

def build_opensky_row(s, now_wib):
    transponder_hex = s[0] or 'N/A'
    callsign = s[1].strip() if s[1] else 'N/A'
    origin_country = s[2] or 'N/A'
    time_position = s[3] or 0
    last_contact = s[4] or 0
    longitude = s[5] if s[5] is not None else 0
    latitude = s[6] if s[6] is not None else 0
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

    return {
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
    }

# -------------------------------------------------------------------
# 2. FLIGHTRADAR24 DATA FETCHING (4 BANDARA - RADIUS 500 KM - TEPAT 36 KOLOM)
# -------------------------------------------------------------------
def fetch_fr24_flights(now_wib):
    regions = {
        'Jakarta': {'lat': -6.1256, 'lon': 106.6558, 'csv': 'jakarta_flights_log_fr24.csv'},
        'Singapore': {'lat': 1.3644, 'lon': 103.9915, 'csv': 'singapore_flights_log_fr24.csv'},
        'Bali': {'lat': -8.7482, 'lon': 115.1672, 'csv': 'bali_flights_log_fr24.csv'},
        'Kalimantan': {'lat': -1.2682, 'lon': 116.8942, 'csv': 'kalimantan_flights_log_fr24.csv'}  # Balikpapan / IKN Center
    }

    try:
        fr_api = FlightRadar24API()
    except Exception as e:
        print(f"Error initializing FlightRadar24API: {e}")
        return

    for region_name, config in regions.items():
        csv_file = config['csv']
        flight_data = []

        try:
            bounds = fr_api.get_bounds_by_point(latitude=config['lat'], longitude=config['lon'], radius=500000)
            flights = fr_api.get_flights(bounds=bounds)

            if isinstance(flights, list) and len(flights) > 0:
                for f in flights:
                    callsign_clean = getattr(f, 'callsign', None) or getattr(f, 'number', None) or 'N/A'
                    airline_name = get_airline_name(callsign_clean)

                    alt_ft = getattr(f, 'altitude', 0) or 0
                    alt_m = round(alt_ft / 3.28084, 1) if alt_ft else 0
                    speed_kts = getattr(f, 'ground_speed', 0) or 0
                    speed_kmh = round(speed_kts * 1.852, 1) if speed_kts else 0
                    v_speed_fpm = getattr(f, 'vertical_speed', 0) or 0
                    v_speed_ms = round(v_speed_fpm / 196.85, 2) if v_speed_fpm else 0
                    is_ground = 1 if getattr(f, 'on_ground', False) else 0

                    if v_speed_ms > 1.5:
                        flight_phase = "Climbing (Takeoff)"
                    elif v_speed_ms < -1.5:
                        flight_phase = "Descending (Landing/Approach)"
                    elif is_ground == 1:
                        flight_phase = "On Taxiway/Runway"
                    else:
                        flight_phase = "Cruising"

                    flight_data.append({
                        'Timestamp_WIB': now_wib,
                        'Callsign': getattr(f, 'callsign', None) or 'N/A',
                        'Flight_Number': getattr(f, 'number', None) or 'N/A',
                        'Flight_ID': getattr(f, 'id', None) or 'N/A',
                        'Airline_Name': airline_name,
                        'Airline_ICAO': getattr(f, 'airline_icao', None) or 'N/A',
                        'Airline_IATA': 'N/A',
                        'Aircraft_Model': getattr(f, 'aircraft_code', None) or 'N/A',
                        'Aircraft_Type': 'N/A',
                        'Registration_Number': getattr(f, 'registration', None) or 'N/A',
                        'Aircraft_Image_URL': 'N/A',
                        'Origin_IATA': getattr(f, 'origin_airport_iata', None) or 'N/A',
                        'Origin_ICAO': 'N/A',
                        'Origin_Airport_Name': 'N/A',
                        'Origin_City': 'N/A',
                        'Destination_IATA': getattr(f, 'destination_airport_iata', None) or 'N/A',
                        'Destination_ICAO': 'N/A',
                        'Destination_Airport_Name': 'N/A',
                        'Destination_City': 'N/A',
                        'Latitude': getattr(f, 'latitude', config['lat']),
                        'Longitude': getattr(f, 'longitude', config['lon']),
                        'Heading_Deg': getattr(f, 'heading', 0),
                        'Squawk_Code': getattr(f, 'squawk', 'N/A') or 'N/A',
                        'Altitude_Meters': alt_m,
                        'Altitude_Feet': alt_ft,
                        'Ground_Speed_KMH': speed_kmh,
                        'Ground_Speed_Knots': speed_kts,
                        'Vertical_Speed_MS': v_speed_ms,
                        'Vertical_Speed_FPM': v_speed_fpm,
                        'Flight_Phase': flight_phase,
                        'Is_Ground': is_ground,
                        'Status_Text': 'N/A',
                        'Scheduled_Departure': 'N/A',
                        'Actual_Departure': 'N/A',
                        'Estimated_Arrival': 'N/A',
                        'Source': 'FlightRadar24'
                    })

            if not flight_data:
                flight_data.append({
                    'Timestamp_WIB': now_wib, 'Callsign': 'NONE', 'Flight_Number': 'NONE', 'Flight_ID': 'N/A',
                    'Airline_Name': 'N/A', 'Airline_ICAO': 'N/A', 'Airline_IATA': 'N/A',
                    'Aircraft_Model': 'N/A', 'Aircraft_Type': 'N/A', 'Registration_Number': 'N/A', 'Aircraft_Image_URL': 'N/A',
                    'Origin_IATA': 'N/A', 'Origin_ICAO': 'N/A', 'Origin_Airport_Name': 'N/A', 'Origin_City': 'N/A',
                    'Destination_IATA': 'N/A', 'Destination_ICAO': 'N/A', 'Destination_Airport_Name': 'N/A', 'Destination_City': 'N/A',
                    'Latitude': config['lat'], 'Longitude': config['lon'], 'Heading_Deg': 0, 'Squawk_Code': 'N/A',
                    'Altitude_Meters': 0, 'Altitude_Feet': 0, 'Ground_Speed_KMH': 0, 'Ground_Speed_Knots': 0,
                    'Vertical_Speed_MS': 0, 'Vertical_Speed_FPM': 0, 'Flight_Phase': 'No Flights / API Error', 'Is_Ground': 0,
                    'Status_Text': 'N/A', 'Scheduled_Departure': 'N/A', 'Actual_Departure': 'N/A', 'Estimated_Arrival': 'N/A',
                    'Source': 'FlightRadar24'
                })

            df_new = pd.DataFrame(flight_data)
            df_new = df_new.fillna('N/A')
            df_new.to_csv(csv_file, mode='a' if os.path.exists(csv_file) else 'w', header=not os.path.exists(csv_file), index=False)
            print(f"[{now_wib}] FlightRadar24 ({region_name} - 500km Range) Success: Berhasil mencatat {len(flight_data)} penerbangan ke {csv_file}.")
            time.sleep(1)

        except Exception as region_error:
            print(f"Error fetching FlightRadar24 data for {region_name}: {region_error}")
            continue

# -------------------------------------------------------------------
# MAIN EXECUTION
# -------------------------------------------------------------------
if __name__ == "__main__":
    wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(wib).strftime('%Y-%m-%d %H:%M:%S')
    
    fetch_opensky_flights(now_wib)
    fetch_fr24_flights(now_wib)
