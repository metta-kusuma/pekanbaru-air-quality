import pandas as pd
from flight_logger_opensky import get_airline_name

csv_path = 'jakarta_flights_log_opensky.csv'

try:
    print("Membaca file CSV...")
    df = pd.read_csv(csv_path)
    
    print("Memperbarui nama maskapai berdasarkan Callsign...")
    df['Airline_Inferred'] = df['Callsign'].apply(get_airline_name)
    
    print("Menyimpan perubahan langsung ke file asli...")
    df.to_csv(csv_path, index=False)
    print("SELESAI! Seluruh data 'Other Airline' lama berhasil diperbarui.")
except Exception as e:
    print("Error:", e)
