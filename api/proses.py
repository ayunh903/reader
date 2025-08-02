from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import json, os
from datetime import datetime
from io import BytesIO
from collections import Counter

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# === Logika pembersihan dan pengganti nama (hanya sebagian untuk ringkas, bisa dilengkapi) ===
replacement_nama_fasilitas = {
    "AEON Credit Services Indonesia": "AEON Credit",
    "Adira Dinamika Multi Finance": "Adira",
    "Akulaku Finance Indonesia": "Akulaku",
    "Atome Finance Indonesia": "Atome Finance",
    "Bank Neo Commerce": "Akulaku",
    "Bank Jago": "Bank Jago",
    "Bank BTPN Syariah,": "BTPNS",
    "Bina Artha Ventura": "BAV"
}

def bersihkan_nama_fasilitas(nama_fasilitas: str) -> str:
    if not nama_fasilitas:
        return ""
    lower_fasilitas = nama_fasilitas.lower()
    if "d/h" in lower_fasilitas:
        nama_bersih = nama_fasilitas[:lower_fasilitas.find("d/h")].strip()
    elif "d.h" in lower_fasilitas:
        nama_bersih = nama_fasilitas[:lower_fasilitas.find("d.h")].strip()
    else:
        nama_bersih = nama_fasilitas.strip()
    for pattern in ["PT ", "PT.", "PD.", "(Persero)", "(Perseroda)", "Perseroda", "(UUS)", " Tbk"]:
        nama_bersih = nama_bersih.replace(pattern, "")
        nama_bersih = nama_bersih.replace("Bank Perekonomian Rakyat Syariah", "BPRS")
    nama_bersih = nama_bersih.replace("Bank Perekonomian Rakyat", "BPR")
    nama_bersih = nama_bersih.replace("Koperasi Simpan Pinjam", "KSP")
    nama_bersih = nama_bersih.strip()
    for nama_asli, alias in replacement_nama_fasilitas.items():
        if nama_asli.lower() == nama_bersih.lower():
            return alias
    return nama_bersih

def gabungkan_fasilitas_dengan_jumlah(fasilitas_list):
    counter = Counter(fasilitas_list)
    return '; '.join([f"{nama} ({jumlah})" if jumlah > 1 else nama for nama, jumlah in counter.items()])

@app.post("/proses")
async def proses(files: list[UploadFile] = File(...)):
    hasil_semua = []
    excluded_fasilitas = {"BTPNS", "Bank Jago", "BAV"}

    for f in files:
        filename = f.filename
        content = await f.read()
        try:
            data = json.loads(content.decode("latin-1"))
        except:
            continue

        fasilitas = data.get('individual', {}).get('fasilitas', {}).get('kreditPembiayan', [])
        data_pokok = data.get('individual', {}).get('dataPokokDebitur', [])
        nama_debitur = ', '.join(set(debitur.get('namaDebitur', '') for debitur in data_pokok if debitur.get('namaDebitur')))

        total_plafon = 0
        total_baki_debet = 0
        jumlah_fasilitas_aktif = 0
        kol_1_list, kol_25_list, wo_list, lovi_list = [], [], [], []
        baki_debet_kol25wo = 0

        for item in fasilitas:
            kondisi_ket = (item.get('kondisiKet') or '').lower()
            nama_fasilitas = item.get('ljkKet') or ''
            nama_fasilitas_lower = nama_fasilitas.lower()
            is_aktif = kondisi_ket in ['fasilitas aktif', 'diblokir sementara']

            if kondisi_ket == "lunas" and "pt lolc ventura indonesia" not in nama_fasilitas_lower:
                continue

            jumlah_hari_tunggakan = int(item.get('jumlahHariTunggakan', 0))
            kualitas = item.get('kualitas', '')
            kol_value = f"{kualitas}/{jumlah_hari_tunggakan}" if jumlah_hari_tunggakan != 0 else kualitas
            tanggal_kondisi = item.get('tanggalKondisi', '')
            baki_debet = int(item.get('bakiDebet', 0))

            if kondisi_ket in ['dihapusbukukan', 'hapus tagih'] or is_aktif:
                if baki_debet == 0:
                    baki_debet = sum([
                        int(item.get('tunggakanPokok', 0)),
                        int(item.get('tunggakanBunga', 0)),
                        int(item.get('denda', 0))
                    ])
                    if baki_debet == 0:
                        kondisi_ket = 'lunas'
                        is_aktif = False

            plafon_awal = int(item.get('plafonAwal', 0))
            nama_fasilitas_bersih = bersihkan_nama_fasilitas(nama_fasilitas)
            baki_debet_format = "{:,.0f}".format(baki_debet).replace(",", ".")

            if is_aktif and kualitas == '1' and jumlah_hari_tunggakan <= 30:
                fasilitas_teks = nama_fasilitas_bersih
            elif is_aktif:
                fasilitas_teks = f"{nama_fasilitas_bersih} Kol {kol_value} {baki_debet_format}"
            elif kondisi_ket in ['dihapusbukukan', 'hapus tagih']:
                try:
                    tahun_wo = int(str(tanggal_kondisi)[:4])
                except:
                    tahun_wo = ""
                fasilitas_teks = f"{nama_fasilitas_bersih} WO {tahun_wo} {baki_debet_format}"
            else:
                fasilitas_teks = nama_fasilitas_bersih

            if kondisi_ket == 'lunas':
                fasilitas_lovi = "Lunas"
            elif is_aktif:
                fasilitas_lovi = f"Kol {kol_value}"
            elif kondisi_ket in ['dihapusbukukan', 'hapus tagih']:
                fasilitas_lovi = f"WO {tahun_wo} {baki_debet_format}"
            else:
                fasilitas_lovi = nama_fasilitas_bersih

            if "pt lolc ventura indonesia" not in nama_fasilitas_lower:
                if is_aktif:
                    total_plafon += plafon_awal
                    total_baki_debet += baki_debet
                    jumlah_fasilitas_aktif += 1
                    if kualitas == '1' and jumlah_hari_tunggakan <= 30:
                        if jumlah_hari_tunggakan == 0:
                            kol_1_list.append(nama_fasilitas_bersih)
                        else:
                            kol_1_list.append(f"{nama_fasilitas_bersih} Kol {kualitas}/{jumlah_hari_tunggakan}")
                    else:
                        kol_25_list.append(fasilitas_teks)
                        if nama_fasilitas_bersih not in excluded_fasilitas:
                            baki_debet_kol25wo += baki_debet
                elif kondisi_ket in ['dihapusbukukan', 'hapus tagih']:
                    wo_list.append(fasilitas_teks)
                    if nama_fasilitas_bersih not in excluded_fasilitas:
                        baki_debet_kol25wo += baki_debet
            else:
                if is_aktif or kondisi_ket in ["lunas", "dihapusbukukan"]:
                    tanggal_akad_akhir = item.get("tanggalAkadAkhir", "")
                    if tanggal_akad_akhir:
                        if not lovi_list:
                            lovi_list.append({
                                "keterangan": fasilitas_lovi,
                                "tanggal": tanggal_akad_akhir
                            })
                        else:
                            if tanggal_akad_akhir > lovi_list[0]["tanggal"]:
                                lovi_list[0] = {
                                    "keterangan": fasilitas_lovi,
                                    "tanggal": tanggal_akad_akhir
                                }

        if (
            jumlah_fasilitas_aktif >= 0 and
            not kol_25_list and
            not wo_list and
            not lovi_list
        ):
            rekomendasi = "OK"
        elif any("lunas" in lovi.get('keterangan', '').lower() or "kol 1" in lovi.get('keterangan', '').lower() for lovi in lovi_list):
            rekomendasi = "OK"
        elif (
            jumlah_fasilitas_aktif >= 0 and
            baki_debet_kol25wo <= 250_000 and
            not lovi_list
        ):
            rekomendasi = "OK"
        else:
            rekomendasi = "NOT OK"

        nik = os.path.splitext(filename)[0]
        if nik.upper().startswith("NIK_"):
            nik = nik[4:]

        hasil_semua.append({
            'NIK': "'" + nik,
            'Nama Debitur': nama_debitur,
            'Rekomendasi': rekomendasi,
            'Jumlah Fasilitas': jumlah_fasilitas_aktif,
            'Total Plafon Awal': total_plafon if jumlah_fasilitas_aktif > 0 else "",
            'Total Baki Debet': total_baki_debet if jumlah_fasilitas_aktif > 0 else "",
            'Kol 1': gabungkan_fasilitas_dengan_jumlah(kol_1_list),
            'Kol 2-5': '; '.join(kol_25_list),
            'WO/dihapusbukukan': '; '.join(wo_list),
            'LOVI': '; '.join([l.get('keterangan', '') for l in lovi_list])
        })

    if not hasil_semua:
        return {"error": "Tidak ada data yang diproses."}

    df = pd.DataFrame(hasil_semua)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    import base64
    encoded = base64.b64encode(output.read()).decode("utf-8")

    return {
        "preview": df.to_dict(orient="records"),
        "file": encoded,
        "filename": f"File SLIK {datetime.today().strftime('%d-%m-%Y_%H%M%S')}.xlsx"
    }
