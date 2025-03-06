def add_pendidikan_filters(self, df):
        """Filter khusus untuk lembar Pendidikan"""
        st.sidebar.subheader("Filter Data Pendidikan")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Filter Jenjang Pendidikan - detect from column names
        education_keywords = ['SD', 'SMP', 'SMA', 'SARJANA', 'DIPLOMA', 'S1', 'S2', 'S3', 
                           'SLTA', 'SLTP', 'TIDAK SEKOLAH', 'BELUM SEKOLAH', 'TK']
        
        # Find columns that contain education level information
        pendidikan_list = []
        for col in all_columns:
            if col not in ['KECAMATAN', 'DESA']:
                if any(keyword in col.upper() for keyword in education_keywords):
                    pendidikan_list.append(col)
        
        # Fallback if no standard education columns found
        if not pendidikan_list:
            pendidikan_list = [col for col in all_columns if col not in ['KECAMATAN', 'DESA']]
        
        # Let user select education levels
        selected_pendidikan = st.sidebar.multiselect(
            "Pilih Jenjang Pendidikan",
            options=pendidikan_list,
            default=pendidikan_list[:3] if len(pendidikan_list) > 3 else pendidikan_list
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Ensure at least some columns are selected
        if not selected_pendidikan:
            selected_pendidikan = pendidikan_list[:3] if len(pendidikan_list) > 3 else pendidikan_list
            
        # Determine which columns to include in the result
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + selected_pendidikan]
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
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Check what types of columns are available - debug info
        st.sidebar.markdown("### Available Column Categories:")
        has_age_columns = any("TAHUN" in col.upper() for col in all_columns)
        st.sidebar.write(f"Age columns available: {has_age_columns}")
        
        # Filter Kategori Usia - be more flexible with detection
        usia_keywords = ['KESELURUHAN', '0-5 TAHUN', '0-17 TAHUN']
        available_usia = [opt for opt in usia_keywords if any(opt.lower() in col.lower() for col in all_columns)]
        
        if not available_usia:
            # Fallback if no standard categories found
            available_usia = ['SEMUA']
        
        selected_usia = st.sidebar.selectbox(
            "Pilih Kategori Usia",
            options=available_usia,
            index=0
        )
        
        # Filter Status Kepemilikan - be more flexible with detection
        status_keywords = ['MEMILIKI', 'BELUM MEMILIKI']
        available_status = [opt for opt in status_keywords if any(opt.lower() in col.lower() for col in all_columns)]
        
        if not available_status:
            # Fallback if none found
            available_status = [col for col in all_columns if col not in ['KECAMATAN', 'DESA']]
        
        selected_status = st.sidebar.multiselect(
            "Pilih Status Kepemilikan",
            options=available_status,
            default=available_status
        )
        
        # Show available columns for debugging
        if st.sidebar.checkbox("Show all columns"):
            st.sidebar.write(all_columns)
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan berdasarkan usia dan status - handle more flexibly
        status_cols = []
        
        # If only looking at "SEMUA" or using a fallback
        if selected_usia == 'SEMUA':
            # Just take non-KECAMATAN/DESA columns
            status_cols = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
        else:
            # Try to find usia-related columns
            usia_cols = [col for col in df.columns if selected_usia.lower() in col.lower()]
            # Then filter to those matching status
            status_cols = [col for col in usia_cols if any(status.lower() in col.lower() for status in selected_status)]
        
        # Fallback: If no columns were selected, use at least some numeric columns
        if not status_cols:
            # Select all numeric columns except KECAMATAN and DESA
            status_cols = [col for col in df.select_dtypes(include=['float64', 'int64']).columns 
                         if col not in ['KECAMATAN', 'DESA']]
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + status_cols]

    def add_ktp_filters(self, df):
        """Filter khusus untuk lembar KTP"""
        st.sidebar.subheader("Filter Data KTP")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Filter Jenis Kelamin - be more flexible
        gender_keywords = ['LK', 'PR', 'LAKI', 'PRIA', 'WANITA', 'PEREMPUAN']
        
        # Find columns with gender indicators
        gender_cols = []
        for col in all_columns:
            if any(gender.lower() in col.lower() for gender in gender_keywords):
                for keyword in gender_keywords:
                    if keyword.lower() in col.lower():
                        gender_cols.append((col, keyword))
                        break
        
        # Extract available genders
        available_genders = list(set(gender for _, gender in gender_cols))
        
        # Fallback if no standard gender found
        if not available_genders:
            available_genders = ['LK', 'PR']
            
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=available_genders,
            default=available_genders
        )
        
        # Filter Kategori KTP - be more flexible
        ktp_keywords = ['WAJIB KTP', 'PEREKAMAN KTP-EL', 'PENCETAKAN KTP-EL']
        
        # Find available KTP categories
        available_categories = [cat for cat in ktp_keywords if any(cat.lower() in col.lower() for col in all_columns)]
        
        # Fallback if none found
        if not available_categories:
            available_categories = ['KTP']
            
        selected_category = st.sidebar.selectbox(
            "Pilih Kategori KTP",
            options=available_categories,
            index=0
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan - more flexible approach
        gender_cols = []
        
        # If using standard categories
        if selected_category in ktp_keywords:
            # Find columns that match both gender and category
            gender_cols = [col for col in all_columns 
                          if any(gender.lower() in col.lower() for gender in selected_gender)
                          and selected_category.lower() in col.lower()]
        else:
            # Fallback - just look for gender columns
            gender_cols = [col for col in all_columns 
                          if any(gender.lower() in col.lower() for gender in selected_gender)]
        
        # Fallback: If no columns were selected, use some numeric columns
        if not gender_cols:
            gender_cols = [col for col in df.select_dtypes(include=['float64', 'int64']).columns 
                          if col not in ['KECAMATAN', 'DESA']]
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + gender_cols]

    def add_agama_filters(self, df):
        """Filter khusus untuk lembar AGAMA"""
        st.sidebar.subheader("Filter Data Agama")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Filter Agama - detect available religions from column names
        agama_keywords = ['ISLAM', 'KRISTEN', 'KATHOLIK', 'HINDU', 'BUDHA', 'KONGHUCHU', 
                         'KEPERCAYAAN TERHADAP TUHAN YME']
        
        # Find available religions in the data
        available_agama = []
        for agama in agama_keywords:
            if any(agama.lower() in col.lower() for col in all_columns):
                available_agama.append(agama)
        
        # Fallback if none found
        if not available_agama:
            available_agama = [col for col in all_columns if col not in ['KECAMATAN', 'DESA']]
            
        selected_agama = st.sidebar.multiselect(
            "Pilih Agama",
            options=available_agama,
            default=[available_agama[0]] if available_agama else []
        )
        
        # Filter Jenis Data
        data_type = st.sidebar.selectbox(
            "Pilih Jenis Data",
            options=['JUMLAH', 'DETAIL GENDER'],
            index=0
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan - more flexible approach
        agama_cols = []
        
        # For JUMLAH data type
        if data_type == 'JUMLAH':
            for agama in selected_agama:
                # Look for columns with religion name and possibly "JUMLAH"
                matches = [col for col in all_columns if agama.lower() in col.lower() 
                          and ('jumlah' in col.lower() or not any(gender in col.lower() for gender in ['lk', 'pr', 'laki', 'perempuan']))]
                agama_cols.extend(matches)
        else:
            # For DETAIL GENDER
            gender_keywords = ['LK', 'PR', 'LAKI', 'PRIA', 'WANITA', 'PEREMPUAN']
            for agama in selected_agama:
                for gender in gender_keywords:
                    matches = [col for col in all_columns if agama.lower() in col.lower() and gender.lower() in col.lower()]
                    agama_cols.extend(matches)
        
        # Fallback: If no columns selected, use all non-base numeric columns
        if not agama_cols:
            agama_cols = [col for col in df.select_dtypes(include=['float64', 'int64']).columns 
                         if col not in ['KECAMATAN', 'DESA']]
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + agama_cols]

    def add_kia_filters(self, df):
        """Filter khusus untuk lembar KIA"""
        st.sidebar.subheader("Filter Data KIA")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Filter Status KIA - be more flexible
        status_keywords = ['MEMILIKI KIA', 'BELUM MEMILIKI KIA', 'MEMILIKI', 'BELUM MEMILIKI']
        
        # Find available statuses
        available_status = []
        for status in status_keywords:
            if any(status.lower() in col.lower() for col in all_columns):
                available_status.append(status)
        
        # Fallback if none found
        if not available_status:
            # Find columns that might contain KIA-related information
            available_status = [col for col in all_columns if 'kia' in col.lower() and col not in ['KECAMATAN', 'DESA']]
            if not available_status:
                available_status = [col for col in all_columns if col not in ['KECAMATAN', 'DESA']]
        
        selected_status = st.sidebar.multiselect(
            "Pilih Status KIA",
            options=available_status,
            default=[available_status[0]] if available_status else []
        )
        
        # Filter Jenis Kelamin - be more flexible
        gender_keywords = ['LK', 'PR', 'LAKI', 'PRIA', 'WANITA', 'PEREMPUAN']
        
        # Find columns with gender indicators
        available_genders = []
        for gender in gender_keywords:
            if any(gender.lower() in col.lower() for col in all_columns):
                available_genders.append(gender)
        
        # Fallback if no standard genders found
        if not available_genders:
            available_genders = ['LK', 'PR']
            
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=available_genders,
            default=available_genders
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan - more flexible approach
        status_cols = []
        
        # Standard approach - look for status and gender combinations
        for status in selected_status:
            for gender in selected_gender:
                # Look for exact match first
                exact_matches = [col for col in all_columns if 
                               (f"{gender} ({status})" == col or
                                status.lower() in col.lower() and gender.lower() in col.lower())]
                status_cols.extend(exact_matches)
        
        # Fallback: If no exact matches, look for columns containing either status or gender
        if not status_cols:
            broader_matches = [col for col in all_columns if 
                             (any(status.lower() in col.lower() for status in selected_status) or
                              any(gender.lower() in col.lower() for gender in selected_gender))
                             and col not in ['KECAMATAN', 'DESA']]
            status_cols.extend(broader_matches)
        
        # Ultimate fallback: Use all numeric columns
        if not status_cols:
            status_cols = [col for col in df.select_dtypes(include=['float64', 'int64']).columns 
                          if col not in ['KECAMATAN', 'DESA']]
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + status_cols]

    def add_kartu_keluarga_filters(self, df):
        """Filter khusus untuk lembar Kartu Keluarga"""
        st.sidebar.subheader("Filter Data Kartu Keluarga")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Show all columns for debugging
        if st.sidebar.checkbox("Show all KK columns"):
            st.sidebar.write(all_columns)
        
        # Filter Data yang akan ditampilkan - find from available columns
        data_keywords = ['JML KEP. KELUARGA', 'JUMLAH PENDUDUK', 'KAWIN', 'BELUM KAWIN', 'CERAI']
        
        # Find what categories are available in the data
        available_data = []
        for keyword in data_keywords:
            if any(keyword.lower() in col.lower() for col in all_columns):
                available_data.append(keyword)
        
        # Fallback if none found
        if not available_data:
            # Extract potential data types from column names
            potential_data = set()
            for col in all_columns:
                if '(' in col and ')' in col:
                    try:
                        data_type = col.split('(')[1].split(')')[0].strip()
                        potential_data.add(data_type)
                    except:
                        pass
            
            available_data = list(potential_data)
            if not available_data:
                available_data = ['DATA']
        
        selected_data = st.sidebar.selectbox(
            "Pilih Jenis Data",
            options=available_data,
            index=0
        )
        
        # Filter Jenis Kelamin - be more flexible
        gender_keywords = ['LK', 'PR', 'JUMLAH', 'LAKI', 'PRIA', 'WANITA', 'PEREMPUAN']
        
        # Find columns with gender indicators
        available_genders = []
        for gender in gender_keywords:
            if any(gender.lower() in col.lower() for col in all_columns):
                available_genders.append(gender)
        
        # Fallback if no standard genders found
        if not available_genders:
            available_genders = ['LK', 'PR', 'JUMLAH']
            
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=available_genders,
            default=available_genders
        )
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan - more flexible approach
        columns_to_use = []
        
        # Look for columns that might match the criteria
        for gender in selected_gender:
            # First try exact format match
            exact_match = f"{gender} ({selected_data})"
            if exact_match in all_columns:
                columns_to_use.append(exact_match)
            else:
                # Look for columns containing both gender and data type
                broader_matches = [col for col in all_columns if 
                                 gender.lower() in col.lower() and selected_data.lower() in col.lower()]
                columns_to_use.extend(broader_matches)
        
        # If "KK KAWIN" specific sheet, look for additional columns
        if "KAWIN" in selected_data or any("KAWIN" in col.upper() for col in all_columns):
            kawin_cols = [col for col in all_columns if "KAWIN" in col.upper() and col not in columns_to_use]
            columns_to_use.extend(kawin_cols)
        
        # Fallback: If no columns selected, use all numeric columns
        if not columns_to_use:
            columns_to_use = [col for col in df.select_dtypes(include=['float64', 'int64']).columns 
                            if col not in ['KECAMATAN', 'DESA']]
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + columns_to_use]

    def add_penduduk_filters(self, df):
        """Filter khusus untuk lembar Penduduk"""
        st.sidebar.subheader("Filter Data Penduduk")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique() if 'KECAMATAN' in df.columns else []
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Get all columns to analyze what's available
        all_columns = df.columns.tolist()
        
        # Filter Jenis Kelamin - be more flexible
        gender_keywords = ['LAKI-LAKI', 'PEREMPUAN', 'TOTAL', 'LK', 'PR', 'JUMLAH']
        
        # Find available genders
        available_genders = []
        for gender in gender_keywords:
            if any(gender.lower() in col.lower() for col in all_columns):
                available_genders.append(gender)
        
        # Fallback if none found
        if not available_genders:
            available_genders = ['TOTAL']
            
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=available_genders,
            default=['TOTAL'] if 'TOTAL' in available_genders else available_genders[:1]
        )
        
        # Filter Kelompok Usia
        usia_cols = [col for col in all_columns if 'USIA' in col.upper()]
        
        if usia_cols:
            selected_usia = st.sidebar.multiselect(
                "Pilih Kelompok Usia",
                options=usia_cols,
                default=[]
            )
        else:
            selected_usia = []
        
        # Terapkan filter
        if 'KECAMATAN' in df.columns and selected_kecamatan:
            filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        else:
            filtered_df = df
        
        # Kolom yang akan digunakan - more flexible approach
        gender_cols = []
        for gender in selected_gender:
            matches = [col for col in all_columns if gender.lower() in col.lower()]
            gender_cols.extend(matches)
        
        # Fallback: If no gender columns selected, use all non-base columns
        if not gender_cols:
            gender_cols = [col for col in all_columns if col not in ['KECAMATAN', 'DESA']]
        
        # Add selected usia columns
        selected_cols = list(set(gender_cols + selected_usia))
        
        # Always include KECAMATAN and DESA if they exist
        base_cols = [col for col in ['KECAMATAN', 'DESA'] if col in df.columns]
        
        # Return filtered dataframe with selected columns
        return filtered_df[base_cols + selected_cols]
        
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
                if '-' in col or 'TAHUN' in col.upper() or 'THN' in col.upper():
                    umur_cols.append(col)
                # Consider numeric cols if pattern not found
                elif col.replace('.', '', 1).isdigit():
                    umur_cols.append(col)
        
        # Jika terlalu banyak kelompok umur, buat kategori
        if len(umur_cols) > 10:
            # Kelompokkan berdasarkan rentang
            umur_categories = {
                'Balita (0-4 tahun)': [col for col in umur_cols if '0-4' in col or '0 - 4' in col or '0-5' in col],
                'Anak-anak (5-14 tahun)': [col for col in umur_cols if any(x in col for x in ['5-9', '5 - 9', '10-14', '10 - 14', '5-14', '6-14'])],
                'Remaja (15-24 tahun)': [col for col in umur_cols if any(x in col for x in ['15-19', '15 - 19', '20-24', '20 - 24', '15-24'])],
                'Dewasa Muda (25-34 tahun)': [col for col in umur_cols if any(x in col for x in ['25-29', '25 - 29', '30-34', '30 - 34', '25-34'])],
                'Dewasa (35-54 tahun)': [col for col in umur_cols if any(x in col for x in ['35-39', '35 - 39', '40-44', '40 - 44', '45-49', '45 - 49', '50-54', '50 - 54', '35-54'])],
                'Lansia (55+ tahun)': [col for col in umur_cols if any(x in col for x in ['55-59', '55 - 59', '60-64', '60 - 64', '65-69', '65 - 69', '70-74', '70 - 74', '75+', '75 +', '55+', '60+'])]}