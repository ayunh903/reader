
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
    # Fungsi proses_files_gradio dapat diimpor atau ditambahkan di sini (dipotong karena panjang)
    return pd.DataFrame(), None  # Placeholder sementara
