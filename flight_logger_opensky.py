import os
import requests
import pandas as pd
from datetime import datetime
import pytz

def get_airline_name(callsign):
    """Menebak nama maskapai berdasarkan kode Callsign ICAO / Registrasi Fisik"""
    if not callsign or callsign == 'N/A' or callsign == 'NONE':
        return 'Unknown'
    
    callsign = callsign.strip().upper()
    prefix = callsign[:3]
    
    # Deteksi Pesawat Privat / Charter Registrasi Khusus (misal: PK-OFI, T7-MEL, T7-CPA, P7-301)
    if callsign.startswith(('PK', 'T7', 'P7', 'VH', 'N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9')):
        return 'Private / Business Jet / General Aviation'
    
    airlines = {
        # --- MASKAPAI DOMESTIK INDONESIA ---
        'GIA': 'Garuda Indonesia',
        'LNI': 'Lion Air',                   # LNI1713, LNI685, LNI020, LNI292, LNI656, LNI241
        'LKN': 'Lion Air (Alt)',
        'BTK': 'Batik Air',
        'CTV': 'Citilink',
        'AWQ': 'Indonesia AirAsia',
        'SJV': 'Sriwijaya Air / Super Air Jet', # SJV701, SJV850, SJV796, SJV254, SJV639, SJV604, SJV601, SJV820, SJV908, SJV921, SJV956, SJV924, SJV933, SJV316, SJV919, SJV321
        'SJY': 'Sriwijaya Air',
        'NAM': 'NAM Air',
        'PAS': 'Pelita Air Service',          # PAS350, PAS806, PAS320, PAS213, PAS200, PAS329
        'TNU': 'TransNusa',                   # TNU156, TNU386, TNU675, TNU633, TNU861, TNU5104
        'PTP': 'PT TransNusa Aviation Mandiri',
        'WON': 'Wings Air',
        'SUA': 'Susi Air',
        'TNX': 'Trigana Air Service',
        'SPRN': 'Super Air Jet (Alt)',        # SPRN2
        'KCN': 'K-Mile Air / Kencana Air',    # KCN191
        'JDE': 'IndiGo / Eastindo Charter',   # JDE702, JDE101, JDE311
        'RGM': 'Rimbun Air',                  # RGM369, RGM020
        'CTW': 'Citilink (Cargo/Charter)',    # CTW436
        'MKT': 'Mokulele / Smart Aviation',   # MKT104
        'TAG': 'Express Transportasi Antarbenua', # TAG08
        'OEY': 'Other Charter / Executive',   # OEY328
        'FHS': 'Flight Inspection / Helicopter', # FHS101
        'RON': 'Nami Air / Indonesia Air Transport',
        'XAR': 'Express Air',
        'BHA': 'Aero Nusantara Indonesia',
        'PKN': 'Nusantara Air Charter',
        'SMG': 'Semuwa Air',
        'PPA': 'Pelita Air',
        
        # --- MILITER & KEPOLISIAN INDONESIA ---
        'TREK': 'TNI Angkatan Udara',          # TREK309
        'ALPHA': 'TNI Angkatan Udara',
        'NAVY': 'TNI Angkatan Laut',
        'POL': 'Kepolisian Republik Indonesia',
        'RGI': 'My Indo Airlines',
        'BTP': 'Asia Cargo Airlines',
        'TNO': 'Tri-MG Intra Asia Airlines',
        
        # --- MASKAPAI INTERNASIONAL (Dari Log CSV Anda) ---
        'CSN': 'China Southern Airlines',      # CSN8353, CSN8055, CSN8354, CSN387, CSN388
        'TGW': 'Scoot',                        # TGW273, TGW28
        'ANA': 'All Nippon Airways (ANA)',     # ANA835, ANA871, ANA836
        'CCA': 'Air China',                    # CCA977, CCA978
        'PAL': 'Philippine Airlines',          # PAL535, PAL536
        'CEB': 'Cebu Pacific',                 # CEB759, CEB760
        'CXA': 'XiamenAir',                    # CXA8674, CXA838, CXA855, CXA8673, CXA8694, CXA856
        'JAL': 'Japan Airlines (JAL)',         # JAL729, JAL720
        'CDG': 'Shandong Airlines / China Eastern', # CDG2153, CDG2154
        'CES': 'China Eastern Airlines',       # CES5070
        'HVN': 'Vietnam Airlines',             # HVN635, HVN634
        'KAL': 'Korean Air',                   # KAL437, KAL438
        'KMI': 'K-Mile Air',                   # KMI801, KMI804
        'MXD': 'Batik Air Malaysia (Malindo)', # MXD396, MXD191, MXD397, MXD398
        'ETD': 'Etihad Airways',               # ETD473, ETD479
        'SVA': 'Saudia (Saudi Arabian)',       # SVA826, SVA827
        'THY': 'Turkish Airlines',             # THY169
        'QTR': 'Qatar Airways',                # QTR955, QTR958
        'JST': 'Jetstar Airways',              # JST76
        'MYU': 'My Indo Airlines',             # MYU924, MYU9900
        'QQE': 'Qatar Executive / Charter',    # QQE525
        
        # --- MASKAPAI GLOBAL LAINNYA ---
        'UAE': 'Emirates',
        'SUD': 'Saudi Arabian Airlines',
        'SWR': 'Swiss International Air Lines',
        'GFA': 'Gulf Air',
        'OMA': 'Oman Air',
        'RJA': 'Royal Jordanian',
        'KAC': 'Kuwait Airways',
        'SIA': 'Singapore Airlines',
        'SLK': 'SilkAir',
        'MAS': 'Malaysia Airlines',
        'AXM': 'AirAsia (Malaysia)',
        'MYX': 'MYAirline',
        'THA': 'Thai Airways International',
        'AIQ': 'Thai AirAsia',
        'TLM': 'Thai Lion Air',
        'CPA': 'Cathay Pacific',
        'HDA': 'Cathay Dragon / HK Express',
        'HKP': 'Hong Kong Express Airways',
        'CRK': 'Hong Kong Airlines',
        'VJC': 'VietJet Air',
        'RBA': 'Royal Brunei Airlines',
        'MMR': 'Myanmar Airways International',
        'TZP': 'Zipair Tokyo',
        'AAR': 'Asiana Airlines',
        'JJA': 'Jeju Air',
        'CHB': 'China Cargo Airlines',
        'CAL': 'China Airlines (Taiwan)',
        'EVA': 'EVA Air',
        'SJX': 'Starlux Airlines',
        'AIC': 'Air India',
        'IGO': 'IndiGo',
        'BPO': 'Biman Bangladesh Airlines',
        'ALK': 'SriLankan Airlines',
        'QFA': 'Qantas',
        'VOZ': 'Virgin Australia',
        'ANZ': 'Air New Zealand',
        'KLM': 'KLM Royal Dutch Airlines',
        'AFR': 'Air France',
        'BAW': 'British Airways',
        'DLH': 'Lufthansa',
        'UAL': 'United Airlines',
        'AAL': 'American Airlines',
        'DAL': 'Delta Air Lines',
        'FDX': 'FedEx Express',
        'UPS': 'UPS Airlines',
        'GTI': 'Atlas Air',
        'BOX': 'Aerologic (DHL Cargo)',
        'PAC': 'Polar Air Cargo',
        'SQC': 'Singapore Airlines Cargo'
    }
    
    return airlines.get(prefix, 'Other Airline')

def fetch_and_save_flights():
    username = os.getenv("OPENSKY_USERNAME")
    password = os.getenv("OPENSKY_PASSWORD")
    
    if not username or not password:
        print("Error: OPENSKY_USERNAME atau OPENSKY_PASSWORD tidak ditemukan di environment variables.")
        return

    # Bounding Box Setara Range Approach Radar Jakarta (CGK & HLP)
    # Radius ~80-100 km dari Soekarno-Hatta
    params = {
        'lamin': -6.85,  # Batas Selatan: Bogor, Sukabumi Utara
        'lomin': 105.80, # Batas Barat: Serang, Cilegon, Selat Sunda
        'lamax': -5.50,  # Batas Utara: Laut Jawa (Area Holding North)
        'lomax': 107.50  # Batas Timur: Karawang, Purwakarta
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
