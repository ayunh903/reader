
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import os
import json
import pandas as pd
from datetime import datetime
from collections import Counter

app = FastAPI()

replacement_nama_fasilitas = {
    "AEON Credit Services Indonesia": "AEON Credit",
    "Adira Dinamika Multi Finance": "Adira",
    "Akulaku Finance Indonesia": "Akulaku",
    "Atome Finance Indonesia": "Atome Finance",
    "Astra Multi Finance": "Astra MF",
    "BFI Finance Indonesia": "BFI",
    "BIMA Multi Finance": "Bima MF",
    "BPD Jawa Barat dan Banten": "BJB",
    "BPD Jawa Barat dan Banten Syariah": "BJB Syariah",
    "BPD Jawa Timur": "Bank Jatim",
    "BPD Sumatera Utara": "Bank Sumut",
    "Bank BCA Syariah": "BCA Syariah",
    "Bank CIMB Niaga": "CIMB Niaga",
    "Bank Central Asia": "BCA",
    "Bank DBS Indonesia": "Bank DBS",
    "Bank Danamon": "Danamon",
    "Bank Danamon Indonesia": "Danamon",
    "Bank Danamon Syariah": "Danamon Syariah",
    "Bank Hibank Indonesia": "Hibank",
    "Bank HSBC Indonesia": "HSBC",
    "Bank KEB Hana Indonesia": "Bank KEB Hana",
    "Bank Mandiri": "Bank Mandiri",
    "Bank Mandiri Taspen": "Bank Mantap",
    "Bank Mayapada Internasional": "Bank Mayapada",
    "Bank Maybank Indonesia": "Maybank",
    "Bank Mega Syariah": "Bank Mega Syariah",
    "Bank Muamalat Indonesia": "Bank Muamalat",
    "Bank Negara Indonesia": "BNI",
    "Bank Neo Commerce": "Akulaku",
    "Bank OCBC NISP": "OCBC NISP",
    "Bank Panin Indonesia": "Panin Bank",
    "Bank Permata": "Bank Permata",
    "Bank QNB Indonesia": "Bank QNB",
    "Bank Rakyat Indonesia": "BRI",
    "Bank Sahabat Sampoerna": "Bank Sampoerna",
    "Bank Saqu Indonesia ( ": "Bank Saqu",
    "Bank Seabank Indonesia": "Seabank",
    "Bank SMBC Indonesia": "Bank SMBC",
    "Bank Syariah Indonesia": "BSI",
    "Bank Tabungan Negara": "BTN",
    "Bank UOB Indonesia": "Bank UOB",
    "Bank Woori Saudara": "BWS",
    "Bank Woori Saudara Indonesia 1906":"BWS",
    "Bussan Auto Finance": "BAF",
    "Cakrawala Citra Mega Multifinance":"CCM Finance",
    "Commerce Finance": "Seabank",
    "Dana Mandiri Sejahtera": "Dana Mandiri",
    "Esta Dana Ventura": "Esta Dana",
    "Federal International Finance": "FIF",
    "Globalindo Multi Finance": "Globalindo MF",
    "Home Credit Indonesia": "Home Credit",
    "Indodana Multi Finance": "Indodana MF",
    "Indomobil Finance Indonesia": "IMFI",
    "Indonesia Airawata Finance (": "Indonesia Airawata Finance",
    "JACCS Mitra Pinasthika Mustika Finance Indonesia": "JACCS",
    "KB Finansia Multi Finance": "Kreditplus",
    "Kredivo Finance Indonesia": "Kredivo",
    "Krom Bank Indonesia": "Krom Bank",
    "Mandala Multifinance": "Mandala MF",
    "Mandiri Utama Finance": "MUF",
    "Maybank Syariah": "Maybank Syariah",
    "Mega Auto Finance": "MAF",
    "Mega Central Finance": "MCF",
    "Mitra Bisnis Keluarga Ventura": "MBK",
    "Multifinance Anak Bangsa": "MF Anak Bangsa",
    "Panin Bank": "Panin Bank",
    "Permodalan Nasional Madani": "PNM",
    "Pratama Interdana Finance": "Pratama Finance",
    "Standard Chartered Bank": "Standard Chartered",
    "Summit Oto Finance": "Summit Oto",
    "Super Bank Indonesia": "Superbank",
    "Wahana Ottomitra Multiartha": "WOM",
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

@app.post("/api/proses")
async def proses_api(files: List[UploadFile] = File(...)):
    try:
        df, _ = proses_files_gradio(files)
        if df.empty:
            return JSONResponse(status_code=400, content={"error": "Tidak ada data yang bisa diproses."})
        return df.to_dict(orient="records")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

def proses_files_gradio(files):
    if not files:
        return pd.DataFrame(), None

    hasil_semua = []

    for f in files:
        original_name = getattr(f, "orig_name", None) or getattr(f, "name", None) or os.path.basename(f.name if hasattr(f, "name") else f)
        path = getattr(f, "name", None) or getattr(f, "path", None) or f

        if not str(original_name).lower().endswith(".txt"):
            continue

        try:
            with open(path, "r", encoding="latin-1") as file:
                data = json.load(file)
        except Exception as e:
            print(f"Gagal membaca file: {original_name} -> {e}")
            continue

        fasilitas = data.get('individual', {}).get('fasilitas', {}).get('kreditPembiayan', [])
        data_pokok = data.get('individual', {}).get('dataPokokDebitur', [])
        nama_debitur = ', '.join(set(debitur.get('namaDebitur', '') for debitur in data_pokok if debitur.get('namaDebitur')))

        total_plafon = 0
        total_baki_debet = 0
        jumlah_fasilitas_aktif = 0
        kol_1_list, kol_25_list, wo_list, lovi_list = [], [], [], []
        baki_debet_kol25wo = 0
        excluded_fasilitas = {"BTPNS", "Bank Jago", "BAV"}

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

        filename = os.path.basename(original_name or path)
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
        return pd.DataFrame(), None

    df = pd.DataFrame(hasil_semua)
    tanggal_hari_ini = datetime.today().strftime('%d-%m-%Y_%H%M%S')
    output_file = f'File SLIK {tanggal_hari_ini}.xlsx'
    df.to_excel(output_file, index=False)

    
