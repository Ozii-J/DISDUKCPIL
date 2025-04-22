import pandas as pd
import os
import hashlib
import json
import time
from PIL import Image

# ============= FUNGSI UTILITAS =============

def load_config():
    """Load user configuration or create default if not exists"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_config.json")
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        # Default configuration with guest user
        default_config = {
            "users": {
                "guest": {
                    "role": "guest",
                    "name": "Pengguna"
                }
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
        return default_config

def get_logo_path():
    """Get the path to the Madiun logo file, checking multiple formats"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for JPG format first (as provided)
    jpg_path = os.path.join(current_dir, "madiun_logo.jpg")
    if os.path.exists(jpg_path):
        return jpg_path
    
    # Then check for PNG format as fallback
    png_path = os.path.join(current_dir, "madiun_logo.png")
    if os.path.exists(png_path):
        return png_path
    
    # Return None if no logo file is found
    return None

# ============= KELAS VISUALISASI DATA =============

class MadiunDataVisualizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
    
    def add_akta_filters(self, df):
        """Filter khusus untuk lembar AKTA"""
        # Detect format of the AKTA sheet based on column names
        is_gender_format = any('LK (MEMILIKI)' in str(col).upper() for col in df.columns)
        is_age_format = any('(0-5 TAHUN)' in str(col).upper() for col in df.columns)
        
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        if is_age_format:
            # First semester format (AKTA 0 SD 17 DESA)
            # Filter Kategori Usia
            usia_options = ['KESELURUHAN', '0-5 TAHUN', '0-17 TAHUN']
            status_options = ['MEMILIKI', 'BELUM MEMILIKI']
            
            # Kolom yang akan digunakan berdasarkan usia parameter
            def get_filtered_df(selected_kecamatan, selected_usia, selected_status, selected_desa=None):
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
                
                # Apply desa filter if provided and a specific kecamatan is selected
                if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                    filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                    
                cols_to_use = [col for col in df.columns if isinstance(col, str) and selected_usia.lower() in col.lower()]
                status_cols = [col for col in cols_to_use if any(status.upper() in col.upper() for status in selected_status)]
                return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
            
            return {
                'type': 'age_format',
                'kecamatan_list': ['ALL'] + kecamatan_list,
                'get_desa_list': get_desa_list,
                'usia_options': usia_options,
                'status_options': status_options,
                'get_filtered_df': get_filtered_df
            }
            
        elif is_gender_format:
            # Second semester format (AKTA with gender breakdown)
            # Filter Jenis Kelamin
            gender_options = ['LK', 'PR', 'JML']
            status_options = ['MEMILIKI', 'BELUM MEMILIKI']
            
            def get_filtered_df(selected_kecamatan, selected_gender, selected_status, selected_desa=None):
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
                
                # Apply desa filter if provided and a specific kecamatan is selected
                if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                    filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                    
                # Build column selections based on both status and gender
                status_cols = []
                for gender in selected_gender:
                    for status in selected_status:
                        col_name = f"{gender} ({status})"
                        if col_name in df.columns:
                            status_cols.append(col_name)
                
                return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
            
            return {
                'type': 'gender_format',
                'kecamatan_list': ['ALL'] + kecamatan_list,
                'get_desa_list': get_desa_list,
                'gender_options': gender_options,
                'status_options': status_options,
                'get_filtered_df': get_filtered_df
            }
        
        else:
            # Fallback for unknown format
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            
            def get_filtered_df(selected_kecamatan, selected_desa=None):
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
                
                # Apply desa filter if provided and a specific kecamatan is selected
                if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                    filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                    
                return filtered_df[['KECAMATAN', 'DESA'] + list(numeric_cols)]
            
            return {
                'type': 'unknown_format',
                'kecamatan_list': ['ALL'] + kecamatan_list,
                'get_desa_list': get_desa_list,
                'get_filtered_df': get_filtered_df
            }

    def add_ktp_filters(self, df):
        """Filter khusus untuk lembar KTP"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        gender_options = ['LK', 'PR']
        ktp_categories = ['WAJIB KTP', 'PEREKAMAN KTP-EL', 'PENCETAKAN KTP-EL']
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_gender, selected_category, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            gender_cols = [col for col in df.columns if any(gender in col for gender in selected_gender) 
                          and selected_category in col]
            return filtered_df[['KECAMATAN', 'DESA'] + gender_cols]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'gender_options': gender_options,
            'ktp_categories': ktp_categories,
            'get_filtered_df': get_filtered_df
        }

    def add_agama_filters(self, df):
        """Filter khusus untuk lembar AGAMA"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        agama_list = ['ISLAM', 'KRISTEN', 'KATHOLIK', 'HINDU', 'BUDHA', 'KONGHUCHU', 
                      'KEPERCAYAAN TERHADAP TUHAN YME']
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_agama, data_type, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            if data_type == 'JUMLAH':
                agama_cols = [f'JUMLAH ({agama})' for agama in selected_agama]
            else:
                agama_cols = []
                for agama in selected_agama:
                    agama_cols.extend([f'LK ({agama})', f'PR ({agama})'])
            
            return filtered_df[['KECAMATAN', 'DESA'] + agama_cols]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'agama_list': agama_list,
            'get_filtered_df': get_filtered_df
        }

    def add_kia_filters(self, df):
        """Filter khusus untuk lembar KIA"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        status_options = ['MEMILIKI KIA', 'BELUM MEMILIKI KIA']
        gender_options = ['LK', 'PR']
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_status, selected_gender, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            status_cols = []
            for status in selected_status:
                status_cols.extend([f'{gender} ({status})' for gender in selected_gender])
            
            return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'status_options': status_options,
            'gender_options': gender_options,
            'get_filtered_df': get_filtered_df
        }

    def add_kartu_keluarga_filters(self, df):
        """Filter khusus untuk lembar Kartu Keluarga"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        data_options = ['JML KEP. KELUARGA', 'JUMLAH PENDUDUK']
        gender_options = ['LK', 'PR', 'JUMLAH']
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_data, selected_gender, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            columns_to_use = []
            for gender in selected_gender:
                column_name = f"{gender} ({selected_data})"
                if column_name in df.columns:
                    columns_to_use.append(column_name)
            
            return filtered_df[['KECAMATAN', 'DESA'] + columns_to_use]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'data_options': data_options,
            'gender_options': gender_options,
            'get_filtered_df': get_filtered_df
        }

    def add_penduduk_filters(self, df):
        """Filter khusus untuk lembar Penduduk"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        gender_options = ['LAKI-LAKI', 'PEREMPUAN', 'TOTAL']
        
        # Filter Kelompok Usia (jika ada)
        usia_groups = [col for col in df.columns if 'USIA' in col] if any('USIA' in col for col in df.columns) else []
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_gender, selected_usia, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            gender_cols = [col for col in df.columns if any(gender in col.upper() for gender in selected_gender)]
            usia_cols = selected_usia if selected_usia else []
            
            selected_cols = gender_cols + usia_cols
            
            return filtered_df[['KECAMATAN', 'DESA'] + selected_cols]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'gender_options': gender_options,
            'usia_groups': usia_groups,
            'get_filtered_df': get_filtered_df
        }
        
    def add_kelompok_umur_filters(self, df):
        """Filter khusus untuk lembar Kelompok Umur"""
        # Get kecamatan list and add ALL option if kecamatan exists
        kecamatan_list = list(df['KECAMATAN'].unique()) if 'KECAMATAN' in df.columns else []
        
        # Deteksi kolom kelompok umur
        umur_cols = []
        for col in df.columns:
            if col not in ['KECAMATAN', 'DESA']:
                # Deteksi pola kolom umur (misalnya "0-4", "5-9", "10-14", dll.)
                if isinstance(col, str) and ('-' in col or 'TAHUN' in col.upper() or 'THN' in col.upper()):
                    umur_cols.append(col)
        
        # Jika terlalu banyak kelompok umur, buat kategori
        umur_categories = {}
        if len(umur_cols) > 10:
            # Kelompokkan berdasarkan rentang
            umur_categories = {
                'Balita (0-4 tahun)': [col for col in umur_cols if '0-4' in col or '0 - 4' in col],
                'Anak-anak (5-14 tahun)': [col for col in umur_cols if any(x in col for x in ['5-9', '5 - 9', '10-14', '10 - 14'])],
                'Remaja (15-24 tahun)': [col for col in umur_cols if any(x in col for x in ['15-19', '15 - 19', '20-24', '20 - 24'])],
                'Dewasa Muda (25-34 tahun)': [col for col in umur_cols if any(x in col for x in ['25-29', '25 - 29', '30-34', '30 - 34'])],
                'Dewasa (35-54 tahun)': [col for col in umur_cols if any(x in col for x in ['35-39', '35 - 39', '40-44', '40 - 44', '45-49', '45 - 49', '50-54', '50 - 54'])],
                'Lansia (55+ tahun)': [col for col in umur_cols if any(x in col for x in ['55-59', '55 - 59', '60-64', '60 - 64', '65-69', '65 - 69', '70-74', '70 - 74', '75+', '75 +'])]
            }
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            if 'DESA' in df.columns:
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    return list(df['DESA'].unique())
                else:
                    return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
            return []
        
        def get_filtered_df(selected_kecamatan, selected_umur, selected_display, selected_desa=None):
            if 'KECAMATAN' in df.columns:
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            else:
                filtered_df = df.copy()
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if 'DESA' in df.columns and selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            # Jika pilihan tampilan adalah persentase, hitung persentase
            if selected_display == 'Persentase' and selected_umur:
                # Hitung total untuk setiap baris
                filtered_df = filtered_df.copy()
                row_totals = filtered_df[selected_umur].sum(axis=1)
                
                # Hitung persentase untuk kolom yang dipilih
                for col in selected_umur:
                    filtered_df[f'{col} (%)'] = (filtered_df[col] / row_totals * 100).round(2)
                
                # Gunakan kolom persentase
                selected_cols = [f'{col} (%)' for col in selected_umur]
                
                # Kembalikan dataframe dengan kolom yang dipilih
                base_cols = []
                if 'KECAMATAN' in df.columns:
                    base_cols.append('KECAMATAN')
                if 'DESA' in df.columns:
                    base_cols.append('DESA')
                return filtered_df[base_cols + selected_cols]
            else:
                # Kembalikan dataframe dengan jumlah absolut
                base_cols = []
                if 'KECAMATAN' in df.columns:
                    base_cols.append('KECAMATAN')
                if 'DESA' in df.columns:
                    base_cols.append('DESA')
                return filtered_df[base_cols + selected_umur]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list if kecamatan_list else [],
            'get_desa_list': get_desa_list,
            'umur_cols': umur_cols,
            'umur_categories': umur_categories,
            'get_filtered_df': get_filtered_df
        }

    def add_pendidikan_filters(self, df):
        """Filter khusus untuk lembar Pendidikan"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        pendidikan_list = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        def get_filtered_df(selected_kecamatan, selected_pendidikan, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            return filtered_df[['KECAMATAN', 'DESA'] + selected_pendidikan]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'pendidikan_list': pendidikan_list,
            'get_filtered_df': get_filtered_df
        }

    def add_pekerjaan_filters(self, df):
        """Filter khusus untuk lembar Pekerjaan"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        pekerjaan_list = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        # Kelompokkan pekerjaan jika terlalu banyak
        pekerjaan_groups = {}
        if len(pekerjaan_list) > 10:
            # Buat grouping berdasarkan kata kunci umum
            pekerjaan_groups = {
                'PERTANIAN': [col for col in pekerjaan_list if any(k in col.upper() for k in ['TANI', 'NELAYAN', 'TERNAK'])],
                'PENDIDIKAN': [col for col in pekerjaan_list if any(k in col.upper() for k in ['GURU', 'DOSEN', 'PENDIDIK'])],
                'KESEHATAN': [col for col in pekerjaan_list if any(k in col.upper() for k in ['DOKTER', 'PERAWAT', 'BIDAN'])],
                'PERDAGANGAN': [col for col in pekerjaan_list if any(k in col.upper() for k in ['DAGANG', 'JUAL', 'WIRASWASTA'])],
                'INDUSTRI': [col for col in pekerjaan_list if any(k in col.upper() for k in ['BURUH', 'KARYAWAN', 'PEGAWAI'])],
                'LAINNYA': [col for col in pekerjaan_list if not any(k in col.upper() for k in ['TANI', 'NELAYAN', 'TERNAK', 'GURU', 'DOSEN', 'PENDIDIK', 'DOKTER', 'PERAWAT', 'BIDAN', 'DAGANG', 'JUAL', 'WIRASWASTA', 'BURUH', 'KARYAWAN', 'PEGAWAI'])]
            }
        
        def get_filtered_df(selected_kecamatan, selected_pekerjaan, selected_desa=None):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                filtered_df = df.copy()
            else:
                filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
            
            # Apply desa filter if provided and a specific kecamatan is selected
            if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                
            return filtered_df[['KECAMATAN', 'DESA'] + selected_pekerjaan]
        
        return {
            'kecamatan_list': ['ALL'] + kecamatan_list,
            'get_desa_list': get_desa_list,
            'pekerjaan_list': pekerjaan_list,
            'pekerjaan_groups': pekerjaan_groups,
            'get_filtered_df': get_filtered_df
        }

    def add_perkawinan_filters(self, df):
        """Filter khusus untuk lembar Status Perkawinan atau KK KAWIN"""
        # Get kecamatan list and add ALL option
        kecamatan_list = list(df['KECAMATAN'].unique())
        
        # Function to get desa list based on selected kecamatan
        def get_desa_list(selected_kecamatan):
            # Check if ALL is selected or a specific kecamatan
            if selected_kecamatan[0] == 'ALL':
                return list(df['DESA'].unique())
            else:
                return list(df[df['KECAMATAN'] == selected_kecamatan[0]]['DESA'].unique())
        
        # Common status categories across both formats
        status_categories = ['BELUM KAWIN', 'KAWIN', 'CERAI HIDUP', 'CERAI MATI']
        
        # First identify if columns contain gender breakdown (LK, PR, JML)
        has_gender_breakdown = any(str(col).startswith('LK') or str(col).startswith('PR') or str(col).startswith('JML') 
                                for col in df.columns)
        
        if has_gender_breakdown:
            # This is the KK KAWIN or PERKAWINAN format with gender breakdown
            gender_options = ['LK', 'PR', 'JML']
            
            def get_filtered_df(selected_kecamatan, selected_status, selected_gender, selected_desa=None):
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
                
                # Apply desa filter if provided and a specific kecamatan is selected
                if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                    filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                    
                # Build column selections based on both status and gender
                status_cols = []
                for gender in selected_gender:
                    for status in selected_status:
                        col_name = f"{gender} ({status})"
                        if col_name in df.columns:
                            status_cols.append(col_name)
                
                return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
            
            return {
                'type': 'gender_breakdown',
                'kecamatan_list': ['ALL'] + kecamatan_list,
                'get_desa_list': get_desa_list,
                'status_categories': status_categories,
                'gender_options': gender_options,
                'get_filtered_df': get_filtered_df
            }
        else:
            # Old PERKAWINAN format without gender breakdown
            # Get all numeric columns as options
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            status_list = [col for col in numeric_cols if col not in ['KECAMATAN', 'DESA']]
            
            def get_filtered_df(selected_kecamatan, selected_status, selected_desa=None):
                # Check if ALL is selected or a specific kecamatan
                if selected_kecamatan[0] == 'ALL':
                    filtered_df = df.copy()
                else:
                    filtered_df = df[df['KECAMATAN'] == selected_kecamatan[0]]
                
                # Apply desa filter if provided and a specific kecamatan is selected
                if selected_kecamatan[0] != 'ALL' and selected_desa and len(selected_desa) > 0:
                    filtered_df = filtered_df[filtered_df['DESA'].isin(selected_desa)]
                    
                return filtered_df[['KECAMATAN', 'DESA'] + selected_status]
            
            return {
                'type': 'no_gender_breakdown',
                'kecamatan_list': ['ALL'] + kecamatan_list,
                'get_desa_list': get_desa_list,
                'status_list': status_list,
                'get_filtered_df': get_filtered_df
            }

# Function to check available files
def get_available_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    available_files = []
    
    # Check for hardcoded files with both naming patterns
    file1_paths = [
        os.path.join(current_dir, "STAT_SMT_I_2024.xlsx"),
        os.path.join(current_dir, "STAT_SMT_1_2024.xlsx")
    ]
    
    file2_paths = [
        os.path.join(current_dir, "STAT_SMT_2_2024.xlsx"),
        os.path.join(current_dir, "STAT_SMT_II_2024.xlsx")
    ]
    
    # Check first semester file
    for file_path in file1_paths:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            available_files.append(filename)
            break
    
    # Check second semester file
    for file_path in file2_paths:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            available_files.append(filename)
            break
    
    return available_files