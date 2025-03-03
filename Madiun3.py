import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objs as go
import os
import numpy as np



class MadiunDataVisualizer:
    def __init__(self, file_path):
        """
        Inisialisasi visualizer untuk file Excel Madiun
        
        Parameters:
        - file_path (str): Path lengkap ke file Excel
        """
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
    
    def clean_dataframe(self, df):
        """
        Membersihkan DataFrame dari kolom yang tidak relevan
        
        Parameters:
        - df (pandas.DataFrame): DataFrame input
        
        Returns:
        - pandas.DataFrame: DataFrame yang sudah dibersihkan
        """
        # Kolom yang akan diabaikan
        ignore_patterns = [
            'NO', 'NOMOR', 'NUMBER', 'N0', 
            'TAHUN', 'YEAR', 'PERIODE', 'REKAP'
        ]
        
        # Filter kolom yang tidak mengandung pola yang diabaikan
        relevant_columns = [
            col for col in df.columns 
            if not any(pattern in col.upper() for pattern in ignore_patterns)
        ]
        
        return df[relevant_columns]
    
    def identify_location_columns(self, df):
        """
        Identifikasi kolom Kecamatan dan Desa
        
        Parameters:
        - df (pandas.DataFrame): DataFrame input
        
        Returns:
        - dict: Kamus kolom lokasi
        """
        # Kandidat kolom Kecamatan
        kecamatan_candidates = [
            'KECAMATAN', 'KEC', 'DISTRICT', 
            'WILAYAH KECAMATAN', 'NAMA KECAMATAN'
        ]
        
        # Kandidat kolom Desa
        desa_candidates = [
            'DESA', 'KELURAHAN', 'VILLAGE', 
            'NAMA DESA', 'NAMA KELURAHAN'
        ]
        
        # Temukan kolom
        location_columns = {}
        for col in df.columns:
            col_upper = col.upper()
            
            # Cek Kecamatan
            if not location_columns.get('kecamatan') and \
               any(candidate in col_upper for candidate in kecamatan_candidates):
                location_columns['kecamatan'] = col
            
            # Cek Desa
            if not location_columns.get('desa') and \
               any(candidate in col_upper for candidate in desa_candidates):
                location_columns['desa'] = col
        
        return location_columns
    
    def group_ktp_desa_data(self, df, sheet_name):
        """
        Kelompokkan data KTP Desa berdasarkan Kecamatan dan Jenis Kelamin
        """
        # Identifikasi kolom lokasi
        location_columns = self.identify_location_columns(df)
        
        # Cari kolom yang mengandung LK/PR
        lk_columns = [col for col in df.columns if 'LK' in col.upper()]
        pr_columns = [col for col in df.columns if 'PR' in col.upper()]
        
        # Jika tidak ada kolom LK/PR, gunakan semua kolom numerik
        if not (lk_columns or pr_columns):
            numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
            lk_columns = [col for col in numeric_columns if 'LAKI' in col.upper()]
            pr_columns = [col for col in numeric_columns if 'PEREMPUAN' in col.upper()]
        
        # Jika masih tidak ada, tampilkan peringatan
        if not (lk_columns or pr_columns):
            st.warning("Tidak dapat menemukan kolom Laki-laki/Perempuan")
            return None
        
        # Proses pengelompokan
        grouped_data = []
        
        # Cek apakah kolom Kecamatan tersedia
        if location_columns.get('kecamatan'):
            # Grupkan berdasarkan Kecamatan
            kecamatan_groups = df.groupby(location_columns['kecamatan'])
            
            # Untuk setiap Kecamatan
            for kecamatan, group_df in kecamatan_groups:
                kecamatan_data = {'Kecamatan': kecamatan}
                
                # Proses Laki-laki
                if lk_columns:
                    lk_total = group_df[lk_columns].sum().sum()
                    kecamatan_data['Total Laki-laki'] = lk_total
                
                # Proses Perempuan
                if pr_columns:
                    pr_total = group_df[pr_columns].sum().sum()
                    kecamatan_data['Total Perempuan'] = pr_total
                
                grouped_data.append(kecamatan_data)
            
            # Konversi ke DataFrame
            grouped_df = pd.DataFrame(grouped_data)
            
            # Tampilkan data yang dikelompokkan
            st.subheader(f"Ringkasan Data Berdasarkan Kecamatan - {sheet_name}")
            st.dataframe(grouped_df, use_container_width=True)
            
            # Visualisasi
            # Grafik Batang Laki-laki vs Perempuan
            fig_bar = px.bar(
                grouped_df, 
                x='Kecamatan', 
                y=['Total Laki-laki', 'Total Perempuan'],
                title=f'Jumlah Laki-laki vs Perempuan per Kecamatan - {sheet_name}',
                barmode='group'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Pie Chart Persentase
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Laki-laki', 'Perempuan'],
                values=[
                    grouped_df['Total Laki-laki'].sum(), 
                    grouped_df['Total Perempuan'].sum()
                ],
                textinfo='percent+value',
                title=f'Persentase Laki-laki vs Perempuan - {sheet_name}'
            )])
            st.plotly_chart(fig_pie, use_container_width=True)
            
            return grouped_df
        else:
            st.warning("Tidak dapat mengelompokkan data: Kolom Kecamatan tidak ditemukan")
            return None
    
    def group_agama_data(self, df, sheet_name):
        """
        Kelompokkan data Agama berdasarkan Kecamatan
        """
        # Identifikasi kolom lokasi
        location_columns = self.identify_location_columns(df)
        
        # Identifikasi kolom agama
        agama_columns = [col for col in df.columns if 'JUMLAH' in col.upper()]
        
        # Filter kolom agama
        agama_list = [
            col.split('(')[1].split(')')[0] 
            for col in agama_columns 
            if '(' in col and ')' in col
        ]
        
        # Proses pengelompokan
        grouped_data = []
        
        # Cek apakah kolom Kecamatan tersedia
        if location_columns.get('kecamatan'):
            # Grupkan berdasarkan Kecamatan
            kecamatan_groups = df.groupby(location_columns['kecamatan'])
            
            # Untuk setiap Kecamatan
            for kecamatan, group_df in kecamatan_groups:
                kecamatan_data = {'Kecamatan': kecamatan}
                
                # Proses setiap agama
                for agama in agama_list:
                    agama_col = f'JUMLAH ({agama})'
                    if agama_col in df.columns:
                        total = group_df[agama_col].sum()
                        kecamatan_data[agama] = total
                
                grouped_data.append(kecamatan_data)
            
            # Konversi ke DataFrame
            grouped_df = pd.DataFrame(grouped_data)
            
            # Tampilkan data yang dikelompokkan
            st.subheader(f"Ringkasan Data Agama Berdasarkan Kecamatan - {sheet_name}")
            st.dataframe(grouped_df, use_container_width=True)
            
            # Visualisasi
            # Daftar agama yang ada di data
            agama_columns = [col for col in grouped_df.columns if col != 'Kecamatan']
            
            # Grafik Batang Distribusi Agama per Kecamatan
            fig_bar = px.bar(
                grouped_df, 
                x='Kecamatan', 
                y=agama_columns,
                title=f'Distribusi Agama per Kecamatan - {sheet_name}',
                barmode='group'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Pie Chart Total Agama
            total_agama = grouped_df[agama_columns].sum()
            fig_pie = go.Figure(data=[go.Pie(
                labels=total_agama.index,
                values=total_agama.values,
                textinfo='percent+value',
                title=f'Persentase Total Agama - {sheet_name}'
            )])
            st.plotly_chart(fig_pie, use_container_width=True)
            
            return grouped_df
        else:
            st.warning("Tidak dapat mengelompokkan data: Kolom Kecamatan tidak ditemukan")
            return None
    
    def visualize_sheet(self, df, sheet_name):
        """
        Visualisasi umum dengan pengelompokan khusus
        """
        # Bersihkan DataFrame dari kolom yang tidak relevan
        cleaned_df = self.clean_dataframe(df)
        
        # Tentukan jenis visualisasi berdasarkan nama lembar
        if 'KTP' in sheet_name.upper():
            self.group_ktp_desa_data(cleaned_df, sheet_name)
        elif 'AGAMA' in sheet_name.upper():
            self.group_agama_data(cleaned_df, sheet_name)
        elif 'AKTA' in sheet_name.upper():
            # Gunakan metode sebelumnya untuk lembar AKTA
            from importlib import reload
            import sys
            reload(sys.modules[__name__])
            self.group_by_kecamatan_and_age(cleaned_df, sheet_name)
        elif 'KIA' in sheet_name.upper():
            # Mirip dengan KTP, fokus pada kategori khusus
            self.group_ktp_desa_data(cleaned_df, sheet_name)
        else:
            st.warning(f"Tidak ada penanganan khusus untuk lembar {sheet_name}")

def main():
    # Konfigurasi halaman Streamlit
    st.set_page_config(
        page_title="Visualisasi Data Madiun",
        page_icon="📊",
        layout="wide"
    )
    
    # Judul aplikasi
    st.title("📊 Visualisasi Data DISPENDUKCAPIL KAB.MADIUN")
    
    # Dapatkan path file Excel
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx")
    
    # Periksa keberadaan file
    if not os.path.exists(file_path):
        st.error(f"File tidak ditemukan: {file_path}")
        return
    
    # Sidebar untuk pemilihan lembar
    st.sidebar.header("Pilih Lembar Excel")
    visualizer = MadiunDataVisualizer(file_path)
    
    # Dapatkan daftar lembar
    sheet_names = visualizer.xls.sheet_names
    selected_sheet = st.sidebar.selectbox(
        "Pilih Lembar yang Akan Divisualisasikan",
        options=sheet_names
    )
    
    # Baca lembar yang dipilih
    df = pd.read_excel(file_path, sheet_name=selected_sheet)
    
    # Tampilkan data mentah
    st.subheader(f"Data Mentah - {selected_sheet}")
    st.dataframe(df, use_container_width=True)
    
    # Visualisasi dengan pengelompokan
    visualizer.visualize_sheet(df, selected_sheet)

if __name__ == "__main__":
    main()

    