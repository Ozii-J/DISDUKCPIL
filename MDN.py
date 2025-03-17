import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
import numpy as np

class MadiunDataVisualizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
    
    def add_akta_filters(self, df):
        """Filter khusus untuk lembar AKTA"""
        st.sidebar.subheader("Filter Data AKTA")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Detect format of the AKTA sheet based on column names
        is_gender_format = any('LK (MEMILIKI)' in str(col).upper() for col in df.columns)
        is_age_format = any('(0-5 TAHUN)' in str(col).upper() for col in df.columns)
        
        # Different filters based on sheet format
        if is_age_format:
            # First semester format (AKTA 0 SD 17 DESA)
            # Filter Kategori Usia
            usia_options = ['KESELURUHAN', '0-5 TAHUN', '0-17 TAHUN']
            selected_usia = st.sidebar.selectbox(
                "Pilih Kategori Usia",
                options=usia_options
            )
            
            # Filter Status Kepemilikan
            status_options = ['MEMILIKI', 'BELUM MEMILIKI']
            selected_status = st.sidebar.multiselect(
                "Pilih Status Kepemilikan",
                options=status_options,
                default=status_options
            )
            
            # Terapkan filter
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
            
            # Kolom yang akan digunakan berdasarkan usia
            cols_to_use = [col for col in df.columns if isinstance(col, str) and selected_usia.lower() in col.lower()]
            status_cols = [col for col in cols_to_use if any(status.upper() in col.upper() for status in selected_status)]
            
            return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
        
        elif is_gender_format:
            # Second semester format (AKTA with gender breakdown)
            # Filter Jenis Kelamin
            gender_options = ['LK', 'PR', 'JML']
            selected_gender = st.sidebar.multiselect(
                "Pilih Jenis Kelamin",
                options=gender_options,
                default=gender_options
            )
            
            # Filter Status Kepemilikan
            status_options = ['MEMILIKI', 'BELUM MEMILIKI']
            selected_status = st.sidebar.multiselect(
                "Pilih Status Kepemilikan",
                options=status_options,
                default=status_options
            )
            
            # Terapkan filter
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
            
            # Kolom yang akan digunakan
            status_cols = []
            for gender in selected_gender:
                for status in selected_status:
                    col_name = f"{gender} ({status})"
                    if col_name in df.columns:
                        status_cols.append(col_name)
            
            return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
        
        else:
            # Fallback for unknown format
            st.warning("Format lembar AKTA tidak dikenali. Menampilkan semua kolom numerik.")
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
            return filtered_df[['KECAMATAN', 'DESA'] + list(numeric_cols)]

    def add_ktp_filters(self, df):
        """Filter khusus untuk lembar KTP"""
        st.sidebar.subheader("Filter Data KTP")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Jenis Kelamin
        gender_options = ['LK', 'PR']
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=gender_options,
            default=gender_options
        )
        
        # Filter Kategori KTP
        ktp_categories = ['WAJIB KTP', 'PEREKAMAN KTP-EL', 'PENCETAKAN KTP-EL']
        selected_category = st.sidebar.selectbox(
            "Pilih Kategori KTP",
            options=ktp_categories
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        # Kolom yang akan digunakan
        gender_cols = [col for col in df.columns if any(gender in col for gender in selected_gender) 
                      and selected_category in col]
        
        return filtered_df[['KECAMATAN', 'DESA'] + gender_cols]

    def add_agama_filters(self, df):
        """Filter khusus untuk lembar AGAMA"""
        st.sidebar.subheader("Filter Data Agama")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Agama
        agama_list = ['ISLAM', 'KRISTEN', 'KATHOLIK', 'HINDU', 'BUDHA', 'KONGHUCHU', 
                      'KEPERCAYAAN TERHADAP TUHAN YME']
        selected_agama = st.sidebar.multiselect(
            "Pilih Agama",
            options=agama_list,
            default=['ISLAM']
        )
        
        # Filter Jenis Data
        data_type = st.sidebar.selectbox(
            "Pilih Jenis Data",
            options=['JUMLAH', 'DETAIL GENDER']
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        # Kolom yang akan digunakan
        if data_type == 'JUMLAH':
            agama_cols = [f'JUMLAH ({agama})' for agama in selected_agama]
        else:
            agama_cols = []
            for agama in selected_agama:
                agama_cols.extend([f'LK ({agama})', f'PR ({agama})'])
        
        return filtered_df[['KECAMATAN', 'DESA'] + agama_cols]

    def add_kia_filters(self, df):
        """Filter khusus untuk lembar KIA"""
        st.sidebar.subheader("Filter Data KIA")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Status KIA
        status_options = ['MEMILIKI KIA', 'BELUM MEMILIKI KIA']
        selected_status = st.sidebar.multiselect(
            "Pilih Status KIA",
            options=status_options,
            default=['MEMILIKI KIA']
        )
        
        # Filter Jenis Kelamin
        gender_options = ['LK', 'PR']
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=gender_options,
            default=gender_options
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        # Kolom yang akan digunakan
        status_cols = []
        for status in selected_status:
            status_cols.extend([f'{gender} ({status})' for gender in selected_gender])
        
        return filtered_df[['KECAMATAN', 'DESA'] + status_cols]

    def add_kartu_keluarga_filters(self, df):
        """Filter khusus untuk lembar Kartu Keluarga"""
        st.sidebar.subheader("Filter Data Kartu Keluarga")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Data yang akan ditampilkan
        data_options = ['JML KEP. KELUARGA', 'JUMLAH PENDUDUK']
        selected_data = st.sidebar.selectbox(
            "Pilih Jenis Data",
            options=data_options,
            index=0
        )
        
        # Filter Jenis Kelamin
        gender_options = ['LK', 'PR', 'JUMLAH']
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=gender_options,
            default=gender_options
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        # Kolom yang akan digunakan
        columns_to_use = []
        for gender in selected_gender:
            column_name = f"{gender} ({selected_data})"
            if column_name in df.columns:
                columns_to_use.append(column_name)
        
        return filtered_df[['KECAMATAN', 'DESA'] + columns_to_use]

    def add_penduduk_filters(self, df):
        """Filter khusus untuk lembar Penduduk"""
        st.sidebar.subheader("Filter Data Penduduk")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Jenis Kelamin
        gender_options = ['LAKI-LAKI', 'PEREMPUAN', 'TOTAL']
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=gender_options,
            default=['TOTAL']
        )
        
        # Filter Kelompok Usia (jika ada)
        if any('USIA' in col for col in df.columns):
            usia_groups = [col for col in df.columns if 'USIA' in col]
            selected_usia = st.sidebar.multiselect(
                "Pilih Kelompok Usia",
                options=usia_groups,
                default=[]
            )
        else:
            selected_usia = []
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        # Kolom yang akan digunakan
        gender_cols = [col for col in df.columns if any(gender in col.upper() for gender in selected_gender)]
        usia_cols = selected_usia if selected_usia else []
        
        selected_cols = gender_cols + usia_cols
        
        return filtered_df[['KECAMATAN', 'DESA'] + selected_cols]
        
    def add_kelompok_umur_filters(self, df):
        """Filter khusus untuk lembar Kelompok Umur"""
        st.sidebar.subheader("Filter Data Kelompok Umur")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Deteksi kolom kelompok umur
        umur_cols = []
        for col in df.columns:
            if col not in ['KECAMATAN', 'DESA']:
                # Deteksi pola kolom umur (misalnya "0-4", "5-9", "10-14", dll.)
                if isinstance(col, str) and ('-' in col or 'TAHUN' in col.upper() or 'THN' in col.upper()):
                    umur_cols.append(col)
        
        # Jika terlalu banyak kelompok umur, buat kategori
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
            
            # Pilih kategori umur
            selected_category = st.sidebar.selectbox(
                "Pilih Kategori Umur",
                options=list(umur_categories.keys())
            )
            
            available_umur_options = umur_categories[selected_category]
        else:
            available_umur_options = umur_cols
        
        # Filter Kelompok Umur
        selected_umur = st.sidebar.multiselect(
            "Pilih Kelompok Umur",
            options=available_umur_options,
            default=available_umur_options[:5] if len(available_umur_options) > 5 else available_umur_options
        )
        
        # Filter Jenis Tampilan
        display_options = ['Jumlah Absolut', 'Persentase']
        selected_display = st.sidebar.radio(
            "Jenis Tampilan",
            options=display_options
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
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
            if 'KECAMATAN' in df.columns and 'DESA' in df.columns:
                return filtered_df[['KECAMATAN', 'DESA'] + selected_cols]
            elif 'KECAMATAN' in df.columns:
                return filtered_df[['KECAMATAN'] + selected_cols]
            else:
                return filtered_df[selected_cols]
        else:
            # Kembalikan dataframe dengan jumlah absolut
            if 'KECAMATAN' in df.columns and 'DESA' in df.columns:
                return filtered_df[['KECAMATAN', 'DESA'] + selected_umur]
            elif 'KECAMATAN' in df.columns:
                return filtered_df[['KECAMATAN'] + selected_umur]
            else:
                return filtered_df[selected_umur]

    def add_pendidikan_filters(self, df):
        """Filter khusus untuk lembar Pendidikan"""
        st.sidebar.subheader("Filter Data Pendidikan")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Jenjang Pendidikan
        pendidikan_list = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
        selected_pendidikan = st.sidebar.multiselect(
            "Pilih Jenjang Pendidikan",
            options=pendidikan_list,
            default=pendidikan_list[:3] if len(pendidikan_list) > 3 else pendidikan_list
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        return filtered_df[['KECAMATAN', 'DESA'] + selected_pendidikan]

    def add_pekerjaan_filters(self, df):
        """Filter khusus untuk lembar Pekerjaan"""
        st.sidebar.subheader("Filter Data Pekerjaan")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Jenis Pekerjaan
        pekerjaan_list = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
        
        # Kelompokkan pekerjaan jika terlalu banyak
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
            
            selected_group = st.sidebar.selectbox(
                "Pilih Kelompok Pekerjaan",
                options=list(pekerjaan_groups.keys())
            )
            
            pekerjaan_options = pekerjaan_groups[selected_group]
        else:
            pekerjaan_options = pekerjaan_list
        
        selected_pekerjaan = st.sidebar.multiselect(
            "Pilih Jenis Pekerjaan",
            options=pekerjaan_options,
            default=pekerjaan_options[:6] if len(pekerjaan_options) > 6 else pekerjaan_options
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        return filtered_df[['KECAMATAN', 'DESA'] + selected_pekerjaan]

    def add_perkawinan_filters(self, df):
        """Filter khusus untuk lembar Status Perkawinan atau KK KAWIN"""
        st.sidebar.subheader("Filter Data Status Perkawinan")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Detect if this is a PERKAWINAN or KK KAWIN sheet by column names
        # Common status categories across both formats
        status_categories = ['BELUM KAWIN', 'KAWIN', 'CERAI HIDUP', 'CERAI MATI']
        
        # First identify if columns contain gender breakdown (LK, PR, JML)
        has_gender_breakdown = any(str(col).startswith('LK') or str(col).startswith('PR') or str(col).startswith('JML') 
                                for col in df.columns)
        
        if has_gender_breakdown:
            # This is the KK KAWIN or PERKAWINAN format with gender breakdown
            # Filter Status Perkawinan
            selected_status = st.sidebar.multiselect(
                "Pilih Status Perkawinan",
                options=status_categories,
                default=status_categories
            )
            
            # Filter Jenis Kelamin
            gender_options = ['LK', 'PR', 'JML']
            selected_gender = st.sidebar.multiselect(
                "Pilih Jenis Kelamin",
                options=gender_options,
                default=gender_options
            )
            
            # Terapkan filter
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
            
            # Build column selections based on both status and gender
            status_cols = []
            for gender in selected_gender:
                for status in selected_status:
                    col_name = f"{gender} ({status})"
                    if col_name in df.columns:
                        status_cols.append(col_name)
            
            return filtered_df[['KECAMATAN', 'DESA'] + status_cols]
        else:
            # Old PERKAWINAN format without gender breakdown
            # Filter Status Perkawinan (use all numeric columns as options)
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            status_list = [col for col in numeric_cols if col not in ['KECAMATAN', 'DESA']]
            selected_status = st.sidebar.multiselect(
                "Pilih Status Perkawinan",
                options=status_list,
                default=status_list
            )
            
            # Terapkan filter
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
            
            return filtered_df[['KECAMATAN', 'DESA'] + selected_status]

    def visualize_filtered_data(self, df, sheet_name):
        """Visualisasi data yang sudah difilter"""
        # Make a copy of the dataframe to avoid modifying the original
        df_copy = df.copy()
        
        # Convert any non-string column names to string to avoid errors
        df_copy.columns = [str(col) for col in df_copy.columns]
        
        # First, preprocess the dataframe to handle potential issues
        # Ensure KECAMATAN and DESA columns exist (for grouping)
        if 'KECAMATAN' not in df_copy.columns:
            st.warning("Kolom KECAMATAN tidak ditemukan. Beberapa fitur mungkin tidak berfungsi.")
            df_copy['KECAMATAN'] = 'Unknown'
        
        if 'DESA' not in df_copy.columns:
            st.warning("Kolom DESA tidak ditemukan. Beberapa fitur mungkin tidak berfungsi.")
            df_copy['DESA'] = 'Unknown'
        
        # Apply appropriate filter based on sheet name
        # Check multiple variants of names to handle different Excel formats
        if any(akta_keyword in sheet_name.upper() for akta_keyword in ['AKTA', 'AKTA 0', 'AKTA 0 SD 17']):
            filtered_df = self.add_akta_filters(df_copy)
        elif 'KTP' in sheet_name.upper():
            filtered_df = self.add_ktp_filters(df_copy)
        elif 'AGAMA' in sheet_name.upper():
            filtered_df = self.add_agama_filters(df_copy)
        elif 'KIA' in sheet_name.upper():
            filtered_df = self.add_kia_filters(df_copy)
        elif any(kk_keyword in sheet_name.upper() for kk_keyword in ['KARTU KELUARGA', 'KK']):
            # Make sure it's actually KK data and not KK KAWIN data
            if 'KAWIN' not in sheet_name.upper():
                filtered_df = self.add_kartu_keluarga_filters(df_copy)
            else:  # This is for KK KAWIN sheets
                filtered_df = self.add_perkawinan_filters(df_copy)
        elif 'PENDUDUK' in sheet_name.upper():
            filtered_df = self.add_penduduk_filters(df_copy)
        elif 'PENDIDIKAN' in sheet_name.upper():
            filtered_df = self.add_pendidikan_filters(df_copy)
        elif 'PEKERJAAN' in sheet_name.upper():
            filtered_df = self.add_pekerjaan_filters(df_copy)
        elif any(kawin_keyword in sheet_name.upper() for kawin_keyword in ['PERKAWINAN', 'KAWIN']):
            filtered_df = self.add_perkawinan_filters(df_copy)
        elif any(umur_keyword in sheet_name.upper() for umur_keyword in ['KEL UMUR', 'KELOMPOK UMUR', 'UMUR']):
            filtered_df = self.add_kelompok_umur_filters(df_copy)
        else:
            st.warning(f"Tidak ada filter khusus untuk lembar {sheet_name}")
            filtered_df = df_copy
        
        # Tampilkan data yang sudah difilter
        st.subheader(f"Data Terfilter - {sheet_name}")
        st.dataframe(filtered_df, use_container_width=True)
        
        # Visualisasi berdasarkan jenis lembar
        numeric_cols = filtered_df.select_dtypes(include=['float64', 'int64']).columns
        
        if len(numeric_cols) > 0:
            # Agregasi data per kecamatan untuk visualisasi yang lebih jelas
            agg_df = filtered_df.groupby('KECAMATAN')[numeric_cols].sum().reset_index()
            
            # Bar chart
            fig_bar = px.bar(
                agg_df,
                x='KECAMATAN',
                y=numeric_cols,
                title=f'Visualisasi Data {sheet_name} per Kecamatan',
                barmode='group',
                height=600
            )
            # Rotasi label x untuk kecamatan agar lebih mudah dibaca
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Define fig_pie with None as default
            fig_pie = None
            
            # Visualisasi tambahan untuk data tertentu
            if len(numeric_cols) <= 10:  # Jika kolom tidak terlalu banyak
                # Pie chart untuk total
                total_values = agg_df[numeric_cols].sum()
                fig_pie = go.Figure(data=[go.Pie(
                    labels=total_values.index,
                    values=total_values.values,
                    textinfo='percent+value',
                    hole=0.3,  
                )])
                
                # Update layout and display the pie chart within the if block
                fig_pie.update_layout(
                    title=f'Distribusi Total - {sheet_name}',
                    height=500
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Heatmap untuk perbandingan antar kecamatan
            if len(agg_df['KECAMATAN']) > 1 and len(numeric_cols) > 1:
                # Normalisasi data untuk heatmap yang lebih intuitif
                pivot_df = agg_df.set_index('KECAMATAN')
                
                # Membuat heatmap dengan colorscales yang lebih jelas
                fig_heatmap = px.imshow(
                    pivot_df,
                    labels=dict(x="Kategori", y="Kecamatan", color="Jumlah"),
                    title=f"Heatmap Data {sheet_name} per Kecamatan",
                    color_continuous_scale='Viridis',
                    aspect="auto",  # Menyesuaikan aspek rasio untuk ukuran layar
                    height=500
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Tambahkan visualisasi khusus untuk lembar tertentu
                if 'AKTA' in sheet_name.upper():
                    # For AKTA sheets, show ownership percentage
                    memiliki_cols = [col for col in pivot_df.columns if 'MEMILIKI' in str(col) and 'BELUM' not in str(col)]
                    belum_cols = [col for col in pivot_df.columns if 'BELUM MEMILIKI' in str(col)]
                    
                    if memiliki_cols and belum_cols:
                        try:
                            ratio_df = pd.DataFrame()
                            ratio_df['% Memiliki'] = pivot_df[memiliki_cols].sum(axis=1) / (pivot_df[memiliki_cols].sum(axis=1) + pivot_df[belum_cols].sum(axis=1)) * 100
                            ratio_df['% Belum Memiliki'] = 100 - ratio_df['% Memiliki']
                            
                            fig_ratio = px.bar(
                                ratio_df.reset_index(),
                                x='KECAMATAN',
                                y=['% Memiliki', '% Belum Memiliki'],
                                title="Persentase Kepemilikan Akta per Kecamatan",
                                barmode='stack',
                                height=500
                            )
                            fig_ratio.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_ratio, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Tidak dapat membuat visualisasi persentase: {str(e)}")
                            
                elif 'KK KAWIN' in sheet_name.upper() or 'PERKAWINAN' in sheet_name.upper():
                    # Special visualization for KK KAWIN or PERKAWINAN
                    try:
                        if any('KAWIN' in str(col) for col in pivot_df.columns):
                            # Group columns by marital status
                            status_groups = {
                                'BELUM KAWIN': [col for col in pivot_df.columns if 'BELUM KAWIN' in str(col)],
                                'KAWIN': [col for col in pivot_df.columns if ' KAWIN' in str(col) and 'BELUM' not in str(col)],
                                'CERAI HIDUP': [col for col in pivot_df.columns if 'CERAI HIDUP' in str(col)],
                                'CERAI MATI': [col for col in pivot_df.columns if 'CERAI MATI' in str(col)]
                            }
                            
                            # Calculate totals for each status group
                            status_totals = {}
                            for status, cols in status_groups.items():
                                if cols:
                                    status_totals[status] = pivot_df[cols].sum(axis=1)
                            
                            if status_totals:
                                ratio_df = pd.DataFrame(status_totals)
                                row_totals = ratio_df.sum(axis=1)
                                
                                # Calculate percentages
                                for col in ratio_df.columns:
                                    ratio_df[f'% {col}'] = (ratio_df[col] / row_totals * 100).round(2)
                                
                                # Keep only percentage columns for visualization
                                pct_cols = [col for col in ratio_df.columns if col.startswith('%')]
                                
                                if pct_cols:
                                    fig_pct = px.bar(
                                        ratio_df.reset_index(),
                                        x='KECAMATAN',
                                        y=pct_cols,
                                        title="Distribusi Status Perkawinan per Kecamatan (%)",
                                        barmode='stack',
                                        height=500
                                    )
                                    fig_pct.update_layout(xaxis_tickangle=-45)
                                    st.plotly_chart(fig_pct, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Tidak dapat membuat visualisasi status perkawinan: {str(e)}")
                    
                # Visualisasi untuk kartu keluarga jika relevan
                elif ('KARTU KELUARGA' in sheet_name.upper() or 'KK' in sheet_name.upper()) and 'KAWIN' not in sheet_name.upper():
                    # Jika data kartu keluarga, tambahkan visualisasi persentase
                    if ('LK (JML KEP. KELUARGA)' in pivot_df.columns and 
                        'PR (JML KEP. KELUARGA)' in pivot_df.columns and
                        'JUMLAH (JML KEP. KELUARGA)' in pivot_df.columns):
                        
                        # Hitung persentase kepala keluarga laki-laki dan perempuan
                        ratio_df = pd.DataFrame()
                        ratio_df['% KK Laki-laki'] = pivot_df['LK (JML KEP. KELUARGA)'] / pivot_df['JUMLAH (JML KEP. KELUARGA)'] * 100
                        ratio_df['% KK Perempuan'] = pivot_df['PR (JML KEP. KELUARGA)'] / pivot_df['JUMLAH (JML KEP. KELUARGA)'] * 100
                        
                        # Visualisasi persentase
                        fig_ratio = px.bar(
                            ratio_df.reset_index(),
                            x='KECAMATAN',
                            y=['% KK Laki-laki', '% KK Perempuan'],
                            title="Persentase Kepala Keluarga Berdasarkan Gender",
                            barmode='stack',
                            height=500
                        )
                        fig_ratio.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_ratio, use_container_width=True)
        else:
            st.warning("Tidak ada kolom numerik untuk divisualisasikan")


def main():
    st.set_page_config(
        page_title="Visualisasi Data Madiun",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Visualisasi Data DISPENDUKCAPIL KAB.MADIUN")
    
    # Membuat tab untuk navigasi (tanpa tab perbandingan)
    tab1, tab2 = st.tabs(["Visualisasi Data", "Tentang Aplikasi"])
    
    # File selection and handling
    st.sidebar.header("Pilihan File Data")
    
    # Check for available files
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
    
    # Option to upload a custom file
    uploaded_file = st.sidebar.file_uploader("Unggah File Excel", type=['xlsx', 'xls'])
    
    # File selection radio button (only show if there are available files)
    file_path = None
    
    if uploaded_file:
        file_path = uploaded_file
        st.sidebar.success(f"Menggunakan file yang diunggah: {uploaded_file.name}")
    elif available_files:
        file_selection = st.sidebar.radio(
            "Pilih File Data:",
            options=["Unggah File Baru"] + available_files,
            index=1 if available_files else 0
        )
        
        if file_selection == "Unggah File Baru":
            st.sidebar.info("Silakan unggah file Excel di bagian atas sidebar")
            if not uploaded_file:
                # If no file is uploaded, use the first available file as default
                if available_files:
                    file_path = os.path.join(current_dir, available_files[0])
                    st.sidebar.info(f"Menggunakan file default: {available_files[0]}")
        else:
            file_path = os.path.join(current_dir, file_selection)
            st.sidebar.success(f"Menggunakan file: {file_selection}")
    else:
        st.error("Tidak ada file data ditemukan. Silakan unggah file Excel.")
        return
    
    try:
        visualizer = MadiunDataVisualizer(file_path)
        sheet_names = visualizer.xls.sheet_names
        
        with tab1:
            st.sidebar.header("Pengaturan Visualisasi")
            selected_sheet = st.sidebar.selectbox(
                "Pilih Lembar yang Akan Divisualisasikan",
                options=sheet_names
            )
            
            # Cek apakah sheet ditemukan
            if selected_sheet not in sheet_names:
                st.error(f"Lembar {selected_sheet} tidak ditemukan dalam file")
                return
            
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
            
            # Tampilkan data mentah (opsional)
            if st.sidebar.checkbox("Tampilkan Data Mentah"):
                st.subheader(f"Data Mentah - {selected_sheet}")
                st.dataframe(df, use_container_width=True)
            
            # Visualisasi dengan filter
            visualizer.visualize_filtered_data(df, selected_sheet)
        
        with tab2:
            # Informasi tentang aplikasi
            st.header("Tentang Aplikasi Visualisasi Data DISPENDUKCAPIL KAB.MADIUN")
            
            st.markdown("""
            ### Deskripsi
            Aplikasi ini dikembangkan untuk memvisualisasikan data kependudukan di Kabupaten Madiun.
            Dengan aplikasi ini, pengguna dapat melihat berbagai informasi kependudukan seperti:
            
            - Data Akta Kelahiran
            - Data KTP Elektronik
            - Data Kartu Identitas Anak (KIA)
            - Data Agama
            - Data Kartu Keluarga
            - Data Penduduk
            - Data Pendidikan
            - Data Pekerjaan
            - Data Status Perkawinan
            
            ### Petunjuk Penggunaan
            1. Pilih file data yang ingin digunakan dari sidebar
            2. Pilih lembar data yang ingin divisualisasikan
            3. Sesuaikan filter yang tersedia
            4. Lihat hasil visualisasi dalam bentuk tabel dan grafik
            
            ### Sumber Data
            Data yang digunakan dalam aplikasi ini bersumber dari Dinas Kependudukan dan Pencatatan Sipil Kabupaten Madiun.
            """)
            
            # Tampilkan metadata file
            if st.checkbox("Tampilkan Metadata File"):
                st.subheader("Metadata File")
                
                file_name = ""
                if isinstance(file_path, str):
                    file_name = os.path.basename(file_path)
                else:
                    file_name = uploaded_file.name
                    
                metadata = {
                    "Nama File": file_name,
                    "Jumlah Lembar": len(sheet_names),
                    "Daftar Lembar": ", ".join(sheet_names)
                }
                
                st.json(metadata)
                
                # Tampilkan informasi perbandingan jika ada dua file yang tersedia
                if len(available_files) >= 2:
                    st.subheader("Informasi File Data")
                    st.info(f"Tersedia {len(available_files)} file data: {', '.join(available_files)}")
                    st.write("Anda dapat beralih antara file di sidebar untuk melihat data dari periode yang berbeda.")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()