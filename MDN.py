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
        cols_to_use = [col for col in df.columns if selected_usia.lower() in col.lower()]
        status_cols = [col for col in cols_to_use if any(status in col.upper() for status in selected_status)]
        
        return filtered_df[['KECAMATAN', 'DESA'] + status_cols]

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
            default=pekerjaan_options[:5] if len(pekerjaan_options) > 5 else pekerjaan_options
        )
        
        # Terapkan filter
        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
        
        return filtered_df[['KECAMATAN', 'DESA'] + selected_pekerjaan]

    def add_perkawinan_filters(self, df):
        """Filter khusus untuk lembar Status Perkawinan"""
        st.sidebar.subheader("Filter Data Status Perkawinan")
        
        # Filter Kecamatan
        kecamatan_list = df['KECAMATAN'].unique()
        selected_kecamatan = st.sidebar.multiselect(
            "Pilih Kecamatan",
            options=kecamatan_list,
            default=kecamatan_list
        )
        
        # Filter Status Perkawinan
        status_list = [col for col in df.columns if col not in ['KECAMATAN', 'DESA']]
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
        if 'AKTA' in sheet_name.upper():
            filtered_df = self.add_akta_filters(df)
        elif 'KTP' in sheet_name.upper():
            filtered_df = self.add_ktp_filters(df)
        elif 'AGAMA' in sheet_name.upper():
            filtered_df = self.add_agama_filters(df)
        elif 'KIA' in sheet_name.upper():
            filtered_df = self.add_kia_filters(df)
        elif 'KARTU KELUARGA' in sheet_name.upper() or 'KK' in sheet_name.upper():
            filtered_df = self.add_kartu_keluarga_filters(df)
        elif 'PENDUDUK' in sheet_name.upper():
            filtered_df = self.add_penduduk_filters(df)
        elif 'PENDIDIKAN' in sheet_name.upper():
            filtered_df = self.add_pendidikan_filters(df)
        elif 'PEKERJAAN' in sheet_name.upper():
            filtered_df = self.add_pekerjaan_filters(df)
        elif 'PERKAWINAN' in sheet_name.upper() or 'KAWIN' in sheet_name.upper():
            filtered_df = self.add_perkawinan_filters(df)
        else:
            st.warning(f"Tidak ada filter khusus untuk lembar {sheet_name}")
            filtered_df = df
        
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
            
            # Visualisasi tambahan untuk data tertentu
            if len(numeric_cols) <= 10:  # Jika kolom tidak terlalu banyak
                # Pie chart untuk total
                total_values = agg_df[numeric_cols].sum()
                fig_pie = go.Figure(data=[go.Pie(
                    labels=total_values.index,
                    values=total_values.values,
                    textinfo='percent+value',
                    hole=0.3,  # Donut chart untuk tampilan lebih modern
                )])
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
                
                # Tambahkan visualisasi persentase untuk tiap kecamatan
                if 'KARTU KELUARGA' in sheet_name.upper() or 'KK' in sheet_name.upper():
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
    
    def compare_sheets(self, sheet_names):
        """Membandingkan data dari beberapa lembar"""
        st.subheader("Perbandingan Antar Lembar Data")
        
        selected_sheets = st.multiselect(
            "Pilih Lembar yang Akan Dibandingkan",
            options=sheet_names,
            default=sheet_names[:2] if len(sheet_names) > 1 else sheet_names
        )
        
        if len(selected_sheets) < 2:
            st.warning("Pilih minimal 2 lembar untuk perbandingan")
            return
        
        # Pilih kolom untuk perbandingan
        comparison_data = {}
        selected_kecamatan = []
        
        for sheet in selected_sheets:
            df = pd.read_excel(self.file_path, sheet_name=sheet)
            
            if 'KECAMATAN' in df.columns:
                if not selected_kecamatan:
                    selected_kecamatan = st.multiselect(
                        "Pilih Kecamatan untuk Perbandingan",
                        options=df['KECAMATAN'].unique(),
                        default=df['KECAMATAN'].unique()[0]
                    )
                
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if numeric_cols.any():
                    selected_col = st.selectbox(
                        f"Pilih Kolom dari {sheet}",
                        options=numeric_cols,
                        key=f"compare_{sheet}"
                    )
                    
                    if selected_kecamatan and selected_col:
                        filtered_df = df[df['KECAMATAN'].isin(selected_kecamatan)]
                        comparison_data[sheet] = filtered_df.groupby('KECAMATAN')[selected_col].sum().reset_index()
        
        if comparison_data:
            # Gabungkan data perbandingan
            comparison_result = []
            
            for sheet, data in comparison_data.items():
                data_dict = {'Lembar': sheet}
                for _, row in data.iterrows():
                    data_dict[row['KECAMATAN']] = row[1]  # Kolom kedua (setelah KECAMATAN)
                comparison_result.append(data_dict)
            
            comparison_df = pd.DataFrame(comparison_result)
            
            # Tampilkan hasil perbandingan
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visualisasi perbandingan
            fig_comparison = px.bar(
                comparison_df,
                x='Lembar',
                y=selected_kecamatan,
                title="Perbandingan Antar Lembar",
                barmode='group'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)

def main():
    st.set_page_config(
        page_title="Visualisasi Data Madiun",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Visualisasi Data DISPENDUKCAPIL KAB.MADIUN")
    
    # Membuat tab untuk navigasi
    tab1, tab2, tab3 = st.tabs(["Visualisasi Data", "Perbandingan Antar Data", "Tentang Aplikasi"])
    
    # Deteksi file Excel
    uploaded_file = st.sidebar.file_uploader("Unggah File Excel", type=['xlsx', 'xls'])
    
    if uploaded_file:
        file_path = uploaded_file
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_file = "STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx"
        file_path = os.path.join(current_dir, default_file)
        
        if not os.path.exists(file_path):
            st.error(f"File default tidak ditemukan: {file_path}")
            st.info("Silakan unggah file Excel untuk melanjutkan")
            return
        else:
            st.sidebar.info(f"Menggunakan file default: {default_file}")
    
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
            # Perbandingan antar lembar
            visualizer.compare_sheets(sheet_names)
        
        with tab3:
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
            1. Pilih lembar data yang ingin divisualisasikan pada sidebar
            2. Sesuaikan filter yang tersedia
            3. Lihat hasil visualisasi dalam bentuk tabel dan grafik
            4. Untuk membandingkan data antar lembar, gunakan tab "Perbandingan Antar Data"
            
            ### Sumber Data
            Data yang digunakan dalam aplikasi ini bersumber dari Dinas Kependudukan dan Pencatatan Sipil Kabupaten Madiun.
            """)
            
            # Tampilkan metadata file
            if st.checkbox("Tampilkan Metadata File"):
                st.subheader("Metadata File")
                
                metadata = {
                    "Nama File": os.path.basename(file_path) if isinstance(file_path, str) else uploaded_file.name,
                    "Jumlah Lembar": len(sheet_names),
                    "Daftar Lembar": ", ".join(sheet_names)
                }
                
                st.json(metadata)
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()