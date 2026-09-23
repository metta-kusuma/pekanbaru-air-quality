import os
import requests
import pandas as pd

# === 1. MENGAMBIL API KEY AMAN DARI GITHUB SECRETS ===
# Jangan khawatir, sistem GitHub Actions akan otomatis mengisi ini nanti
API_KEY = os.getenv("AIRLABS_API_KEY") 

def validasi_dan_ambil_json(url, params):
    """Fungsi pembantu untuk menghindari error koneksi dan menangkap respons asli"""
    try:
        response = requests.get(url, params=params, timeout=20)
        if response.status_code != 200:
            print(f"  [Error Server] HTTP Status: {response.status_code}")
            return None
        return response.json()
    except Exception as e:
        print(f"  [Error Koneksi]: {e}")
        return None

# FUNGSI 1: Mengambil Data Jadwal Penerbangan Pekanbaru (URL SUDAH DIPERBAIKI)
def ambil_data_jadwal(bandara="PKU"):
    url = "https://airlabs.co"
    frames = []
    
    for tipe in ["dep_iata", "arr_iata"]:
        params = {"api_key": API_KEY, tipe: bandara}
        data = validasi_dan_ambil_json(url, params)
        
        if data and "response" in data and data["response"]:
            frames.append(pd.DataFrame(data["response"]))
            
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame()

# FUNGSI 2: Mengambil Metadata Maskapai (URL SUDAH DIPERBAIKI)
def ambil_metadata_maskapai():
    url = "https://airlabs.co"
    params = {"api_key": API_KEY}
    data = validasi_dan_ambil_json(url, params)
    
    if data and "response" in data and data["response"]:
        return pd.DataFrame(data["response"])
    return pd.DataFrame()

# === EKSEKUSI PROSES ===
if not API_KEY:
    print("[Gagal] AIRLABS_API_KEY tidak ditemukan di GitHub Secrets!")
    exit(1)

print("1. Menarik data jadwal aktif Pekanbaru...")
df_jadwal = ambil_data_jadwal("PKU")

print("\n2. Menarik data referensi maskapai global...")
df_maskapai = ambil_metadata_maskapai()

# === VALIDASI AKHIR DAN PENYIMPANAN ===
if not df_jadwal.empty:
    print(f"\n[Sukses] Berhasil menarik {len(df_jadwal)} data jadwal penerbangan!")
    
    if not df_maskapai.empty:
        # Memastikan kolom 'airline_iata' ada di kedua dataframe sebelum di-merge
        if 'airline_iata' in df_jadwal.columns and 'airline_iata' in df_maskapai.columns:
            df_analisis = pd.merge(df_jadwal, df_maskapai[['airline_iata', 'name']], on='airline_iata', how='left')
            print(" -> Data jadwal sukses digabungkan dengan nama maskapai.")
        else:
            df_analisis = df_jadwal
    else:
        df_analisis = df_jadwal
        print(" -> Data maskapai kosong. Menggunakan data jadwal murni.")
        
    # Catatan: print(display()) dihapus karena lingkungan GitHub Actions tidak mendukung fungsi display() Colab
    nama_file = "dataset_analisis_penerbangan_pku.csv"
    
    # Logika Incremental (Gabungkan data lama jika sudah ada agar data terus bertambah)
    if os.path.exists(nama_file):
        df_lama = pd.read_csv(nama_file)
        # Menghapus duplikat berdasarkan nomor penerbangan dan waktu keberangkatan
        df_total = pd.concat([df_lama, df_analisis]).drop_duplicates(subset=["flight_num", "dep_time"], keep="last")
        df_total.to_csv(nama_file, index=False)
        print(f"Dataset diperbarui! Total keseluruhan data saat ini: {len(df_total)} baris.")
    else:
        df_analisis.to_csv(nama_file, index=False)
        print(f"File baru berhasil dibuat dengan {len(df_analisis)} baris.")
else:
    print("\n[Gagal] Tidak ada data yang berhasil ditarik. Silakan periksa limit API Anda.")
