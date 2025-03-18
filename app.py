import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
import numpy as np
import time
from PIL import Image

# Import backend functions and classes
from backend import (
    load_config, verify_password, get_logo_path, 
    MadiunDataVisualizer, get_available_files
)

# ============= VISUALIZATION FUNCTIONS =============

def create_visualizations(filtered_df, sheet_name):
    """Create visualizations based on filtered data"""
    numeric_cols = filtered_df.select_dtypes(include=['float64', 'int64']).columns
    
    if len(numeric_cols) > 0:
        # Ensure KECAMATAN column exists
        if 'KECAMATAN' not in filtered_df.columns:
            st.warning("Kolom KECAMATAN tidak ditemukan. Beberapa fitur mungkin tidak berfungsi.")
            return
            
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
                hole=0.3,  
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
            
            # Tambahkan visualisasi khusus untuk lembar tertentu
            create_special_visualizations(pivot_df, sheet_name)
            
            # Tambahan visualisasi - Stacked Bar Chart untuk perbandingan proporsi
            if len(numeric_cols) > 1:
                # Normalisasi data untuk perbandingan proporsi
                prop_df = pivot_df.copy()
                for idx in prop_df.index:
                    row_sum = prop_df.loc[idx].sum()
                    if row_sum > 0:  # Hindari pembagian dengan nol
                        prop_df.loc[idx] = (prop_df.loc[idx] / row_sum) * 100
                
                fig_prop = px.bar(
                    prop_df.reset_index(),
                    x='KECAMATAN',
                    y=prop_df.columns,
                    title=f"Proporsi Data {sheet_name} per Kecamatan (%)",
                    barmode='stack',
                    height=500
                )
                fig_prop.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_prop, use_container_width=True)
                
            # Tambahan visualisasi - Line Chart untuk trend visual
            if len(numeric_cols) > 1:
                fig_line = px.line(
                    agg_df,
                    x='KECAMATAN',
                    y=numeric_cols,
                    title=f"Tren Data {sheet_name} per Kecamatan",
                    markers=True,
                    height=500
                )
                fig_line.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("Tidak ada kolom numerik untuk divisualisasikan")

def create_special_visualizations(pivot_df, sheet_name):
    """Create special visualizations based on sheet type"""
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

# ============= SISTEM LOGIN - HALAMAN LOGIN =============

def login_page():
    """Display the login page with Madiun logo"""
    # Apply the custom theme
    set_custom_theme()
    
    # Create a nice container for login form
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Pendekatan sederhana kembali ke penggunaan kolom yang tepat
    logo_col1, logo_col2, logo_col3 = st.columns([2.2, 2, 1])
    
    with logo_col2:
        # Tampilkan logo dengan ukuran yang lebih kecil
        logo_path = get_logo_path()
        if logo_path:
            try:
                st.image(Image.open(logo_path), width=150)  # Ukuran dikurangi menjadi 150px
            except Exception as e:
                st.warning(f"Error loading logo: {str(e)}")
                st.warning("Logo tidak dapat ditampilkan. Pastikan file logo valid.")
        else:
            st.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.jpg' atau 'madiun_logo.png' ke direktori aplikasi.")
    
    # Header aplikasi setelah logo
    st.markdown("<h1 style='text-align: center;'>DISPENDUKCAPIL KAB.MADIUN</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sistem Visualisasi Data Kependudukan</h3>", unsafe_allow_html=True)
    
    # Form login dengan kotak terpusat
    st.markdown("<p style='text-align: center; margin-top: 30px;'>Silakan masuk untuk melanjutkan</p>", unsafe_allow_html=True)
    
    # Gunakan kolom untuk form login
    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
    
    with login_col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Buat kolom untuk tombol
        button_col1, button_col2 = st.columns([1, 1])
        
        with button_col1:
            login_button = st.button("Masuk", use_container_width=True)
        
        with button_col2:
            help_button = st.button("Bantuan", use_container_width=True)
            
        if login_button:
            if username and password:
                with st.spinner("Memeriksa kredensial..."):
                    time.sleep(1)  # Simulate verification delay
                    success, user_data = verify_password(username, password)
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_data = user_data
                        st.success(f"Selamat datang, {user_data['name']}!")
                        time.sleep(1)  # Short delay before redirecting
                        st.experimental_rerun()
                    else:
                        st.error("Username atau password salah. Silakan coba lagi.")
            else:
                st.warning("Silakan masukkan username dan password.")
                
        if help_button:
            st.info("""
            ### Bantuan Login
            - Username dan password default: admin / admin123
            - Jika Anda mengalami masalah login, silakan hubungi administrator.
            - Atau gunakan akun staff: dispendukcapil / madiun2024
            """)
    
    # Close the login container
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='text-align: center; margin-top: 50px;'>&copy; 2024 Dinas Kependudukan dan Pencatatan Sipil Kabupaten Madiun</div>", unsafe_allow_html=True)

def add_logo():
    """Add the Madiun logo to the Streamlit sidebar"""
    logo_path = get_logo_path()
    
    if logo_path:
        try:
            st.sidebar.image(Image.open(logo_path), width=150)
        except Exception as e:
            st.sidebar.warning(f"Error loading logo: {str(e)}")
            st.sidebar.warning("Logo tidak dapat ditampilkan. Pastikan file logo valid.")
    else:
        st.sidebar.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.jpg' atau 'madiun_logo.png' ke direktori aplikasi.")

def user_profile_section():
    """Display user profile information in the sidebar"""
    st.sidebar.subheader("Profil Pengguna")
    st.sidebar.write(f"Nama: {st.session_state.user_data['name']}")
    st.sidebar.write(f"Role: {st.session_state.user_data['role'].capitalize()}")
    
    if st.sidebar.button("Keluar"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_data = None
        st.experimental_rerun()

# ============= TEMA WARNA KUSTOM =============

def set_custom_theme():
    """Set custom theme with green and white colors"""
    # Warna tema: Hijau Madiun dan Putih
    st.markdown(
        """
        <style>
        /* Warna background utama */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* Sidebar dengan warna putih */
        section[data-testid="stSidebar"] {
            background-color: white;
            border-right: 2px solid #0b5f34;
        }
        
        /* Text berwarna hijau di sidebar untuk header */
        section[data-testid="stSidebar"] .stMarkdown h1, 
        section[data-testid="stSidebar"] .stMarkdown h2, 
        section[data-testid="stSidebar"] .stMarkdown h3 {
            color: #0b5f34 !important;
        }
        
        /* Tombol dengan warna hijau */
        .stButton button {
            background-color: #0b5f34;
            color: white;
            border: none;
        }
        
        .stButton button:hover {
            background-color: #0d7a43;
        }
        
        /* Judul dengan garis bawah hijau */
        h1, h2, h3 {            
            padding-bottom: 10px;
            color: #0b5f34;
        }
        
        /* Tabs style */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #e6f3ed;
            color: #0b5f34;
            border-radius: 4px 4px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0b5f34 !important;
            color: white !important;
        }
        
        /* Box dengan border hijau */
        div[data-testid="stForm"] {
            border: 1px solid #0b5f34;
            border-radius: 10px;
            padding: 20px;
        }
        
        /* Login background */
        .login-container {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        /* Data frame styling */
        div[data-testid="stDataFrame"] > div {
            border: 1px solid #0b5f34;
        }
        
        div[data-testid="stDataFrame"] th {
            background-color: #0b5f34;
            color: white;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

# ============= RENDER SIDEBAR FILTERS =============

def render_akta_filters(filter_data):
    """Render filter UI for AKTA sheet"""
    st.sidebar.subheader("Filter Data AKTA")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    if filter_data['type'] == 'age_format':
        # First semester format (AKTA 0 SD 17 DESA)
        # Filter Kategori Usia
        selected_usia = st.sidebar.selectbox(
            "Pilih Kategori Usia",
            options=filter_data['usia_options']
        )
        
        # Filter Status Kepemilikan
        selected_status = st.sidebar.multiselect(
            "Pilih Status Kepemilikan",
            options=filter_data['status_options'],
            default=filter_data['status_options']
        )
        
        return filter_data['get_filtered_df'](selected_kecamatan, selected_usia, selected_status)
        
    elif filter_data['type'] == 'gender_format':
        # Second semester format (AKTA with gender breakdown)
        # Filter Jenis Kelamin
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=filter_data['gender_options'],
            default=filter_data['gender_options']
        )
        
        # Filter Status Kepemilikan
        selected_status = st.sidebar.multiselect(
            "Pilih Status Kepemilikan",
            options=filter_data['status_options'],
            default=filter_data['status_options']
        )
        
        return filter_data['get_filtered_df'](selected_kecamatan, selected_gender, selected_status)
    
    else:
        # Fallback for unknown format
        return filter_data['get_filtered_df'](selected_kecamatan)

def render_ktp_filters(filter_data):
    """Render filter UI for KTP sheet"""
    st.sidebar.subheader("Filter Data KTP")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Jenis Kelamin
    selected_gender = st.sidebar.multiselect(
        "Pilih Jenis Kelamin",
        options=filter_data['gender_options'],
        default=filter_data['gender_options']
    )
    
    # Filter Kategori KTP
    selected_category = st.sidebar.selectbox(
        "Pilih Kategori KTP",
        options=filter_data['ktp_categories']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_gender, selected_category)

def render_agama_filters(filter_data):
    """Render filter UI for AGAMA sheet"""
    st.sidebar.subheader("Filter Data Agama")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Agama
    selected_agama = st.sidebar.multiselect(
        "Pilih Agama",
        options=filter_data['agama_list'],
        default=['ISLAM']
    )
    
    # Filter Jenis Data
    data_type = st.sidebar.selectbox(
        "Pilih Jenis Data",
        options=['JUMLAH', 'DETAIL GENDER']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_agama, data_type)

def render_kia_filters(filter_data):
    """Render filter UI for KIA sheet"""
    st.sidebar.subheader("Filter Data KIA")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Status KIA
    selected_status = st.sidebar.multiselect(
        "Pilih Status KIA",
        options=filter_data['status_options'],
        default=['MEMILIKI KIA']
    )
    
    # Filter Jenis Kelamin
    selected_gender = st.sidebar.multiselect(
        "Pilih Jenis Kelamin",
        options=filter_data['gender_options'],
        default=filter_data['gender_options']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_status, selected_gender)

def render_kartu_keluarga_filters(filter_data):
    """Render filter UI for Kartu Keluarga sheet"""
    st.sidebar.subheader("Filter Data Kartu Keluarga")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Data yang akan ditampilkan
    selected_data = st.sidebar.selectbox(
        "Pilih Jenis Data",
        options=filter_data['data_options'],
        index=0
    )
    
    # Filter Jenis Kelamin
    selected_gender = st.sidebar.multiselect(
        "Pilih Jenis Kelamin",
        options=filter_data['gender_options'],
        default=filter_data['gender_options']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_data, selected_gender)

def render_penduduk_filters(filter_data):
    """Render filter UI for Penduduk sheet"""
    st.sidebar.subheader("Filter Data Penduduk")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Jenis Kelamin
    selected_gender = st.sidebar.multiselect(
        "Pilih Jenis Kelamin",
        options=filter_data['gender_options'],
        default=['TOTAL']
    )
    
    # Filter Kelompok Usia (jika ada)
    selected_usia = []
    if filter_data['usia_groups']:
        selected_usia = st.sidebar.multiselect(
            "Pilih Kelompok Usia",
            options=filter_data['usia_groups'],
            default=[]
        )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_gender, selected_usia)

def render_kelompok_umur_filters(filter_data):
    """Render filter UI for Kelompok Umur sheet"""
    st.sidebar.subheader("Filter Data Kelompok Umur")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Kelompok Umur
    available_umur_options = []
    
    # Jika terlalu banyak kelompok umur, buat kategori
    if filter_data['umur_categories']:
        selected_category = st.sidebar.selectbox(
            "Pilih Kategori Umur",
            options=list(filter_data['umur_categories'].keys())
        )
        available_umur_options = filter_data['umur_categories'][selected_category]
    else:
        available_umur_options = filter_data['umur_cols']
    
    selected_umur = st.sidebar.multiselect(
        "Pilih Kelompok Umur",
        options=available_umur_options,
        default=available_umur_options[:5] if len(available_umur_options) > 5 else available_umur_options
    )
    
    # Filter Jenis Tampilan
    selected_display = st.sidebar.radio(
        "Jenis Tampilan",
        options=['Jumlah Absolut', 'Persentase']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_umur, selected_display)

def render_pendidikan_filters(filter_data):
    """Render filter UI for Pendidikan sheet"""
    st.sidebar.subheader("Filter Data Pendidikan")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Filter Jenjang Pendidikan
    selected_pendidikan = st.sidebar.multiselect(
        "Pilih Jenjang Pendidikan",
        options=filter_data['pendidikan_list'],
        default=filter_data['pendidikan_list'][:3] if len(filter_data['pendidikan_list']) > 3 else filter_data['pendidikan_list']
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_pendidikan)

def render_pekerjaan_filters(filter_data):
    """Render filter UI for Pekerjaan sheet"""
    st.sidebar.subheader("Filter Data Pekerjaan")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    # Kelompokkan pekerjaan jika terlalu banyak
    pekerjaan_options = filter_data['pekerjaan_list']
    if filter_data['pekerjaan_groups']:
        selected_group = st.sidebar.selectbox(
            "Pilih Kelompok Pekerjaan",
            options=list(filter_data['pekerjaan_groups'].keys())
        )
        pekerjaan_options = filter_data['pekerjaan_groups'][selected_group]
    
    selected_pekerjaan = st.sidebar.multiselect(
        "Pilih Jenis Pekerjaan",
        options=pekerjaan_options,
        default=pekerjaan_options[:6] if len(pekerjaan_options) > 6 else pekerjaan_options
    )
    
    return filter_data['get_filtered_df'](selected_kecamatan, selected_pekerjaan)

def render_perkawinan_filters(filter_data):
    """Render filter UI for Perkawinan sheet"""
    st.sidebar.subheader("Filter Data Status Perkawinan")
    
    # Filter Kecamatan
    selected_kecamatan = st.sidebar.multiselect(
        "Pilih Kecamatan",
        options=filter_data['kecamatan_list'],
        default=filter_data['kecamatan_list']
    )
    
    if filter_data['type'] == 'gender_breakdown':
        # This is the KK KAWIN or PERKAWINAN format with gender breakdown
        # Filter Status Perkawinan
        selected_status = st.sidebar.multiselect(
            "Pilih Status Perkawinan",
            options=filter_data['status_categories'],
            default=filter_data['status_categories']
        )
        
        # Filter Jenis Kelamin
        selected_gender = st.sidebar.multiselect(
            "Pilih Jenis Kelamin",
            options=filter_data['gender_options'],
            default=filter_data['gender_options']
        )
        
        return filter_data['get_filtered_df'](selected_kecamatan, selected_status, selected_gender)
    else:
        # Old PERKAWINAN format without gender breakdown
        # Filter Status Perkawinan
        selected_status = st.sidebar.multiselect(
            "Pilih Status Perkawinan",
            options=filter_data['status_list'],
            default=filter_data['status_list']
        )
        
        return filter_data['get_filtered_df'](selected_kecamatan, selected_status)

# ============= MAIN FUNCTION =============

def main():
    # Get the logo path for favicon
    logo_path = get_logo_path()
    
    # Use madiun logo as favicon if exists, otherwise use default emoji
    if logo_path:
        try:
            # Open the image and use it as favicon
            favicon = Image.open(logo_path)
            st.set_page_config(
                page_title="Visualisasi Data DISPENDUKCAPIL Madiun",
                page_icon=favicon,
                layout="wide"
            )
        except Exception as e:
            # Fallback to emoji if error loading image
            print(f"Error loading logo as favicon: {e}")
            st.set_page_config(
                page_title="Visualisasi Data DISPENDUKCAPIL Madiun",
                page_icon="📊",
                layout="wide"
            )
    else:
        # Use default emoji if logo doesn't exist
        st.set_page_config(
            page_title="Visualisasi Data DISPENDUKCAPIL Madiun",
            page_icon="📊",
            layout="wide"
        )
    
    # Apply the custom theme
    set_custom_theme()
    
    # Initialize session state for login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.user_data = None
    
    # Check if user is logged in
    if not st.session_state.logged_in:
        login_page()
        return
    
    # If logged in, show the main application
    # Add logo at the top of the sidebar
    add_logo()
    
    # Add user profile section in sidebar
    user_profile_section()
    
    st.title("DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KAB.MADIUN")
    
    # Membuat tab untuk navigasi (tanpa tab perbandingan)
    tab1, tab2 = st.tabs(["Visualisasi Data", "Tentang Aplikasi"])
    
    # File selection and handling
    st.sidebar.header("Pilihan File Data")
    
    # Get available files
    available_files = get_available_files()
    
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
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(current_dir, available_files[0])
                    st.sidebar.info(f"Menggunakan file default: {available_files[0]}")
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
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
            
            # Convert all column names to string to avoid errors
            df.columns = [str(col) for col in df.columns]
            
            # Apply appropriate filter based on sheet name
            if any(akta_keyword in selected_sheet.upper() for akta_keyword in ['AKTA', 'AKTA 0', 'AKTA 0 SD 17']):
                filter_data = visualizer.add_akta_filters(df)
                filtered_df = render_akta_filters(filter_data)
            elif 'KTP' in selected_sheet.upper():
                filter_data = visualizer.add_ktp_filters(df)
                filtered_df = render_ktp_filters(filter_data)
            elif 'AGAMA' in selected_sheet.upper():
                filter_data = visualizer.add_agama_filters(df)
                filtered_df = render_agama_filters(filter_data)
            elif 'KIA' in selected_sheet.upper():
                filter_data = visualizer.add_kia_filters(df)
                filtered_df = render_kia_filters(filter_data)
            elif any(kk_keyword in selected_sheet.upper() for kk_keyword in ['KARTU KELUARGA', 'KK']):
                # Make sure it's actually KK data and not KK KAWIN data
                if 'KAWIN' not in selected_sheet.upper():
                    filter_data = visualizer.add_kartu_keluarga_filters(df)
                    filtered_df = render_kartu_keluarga_filters(filter_data)
                else:  # This is for KK KAWIN sheets
                    filter_data = visualizer.add_perkawinan_filters(df)
                    filtered_df = render_perkawinan_filters(filter_data)
            elif 'PENDUDUK' in selected_sheet.upper():
                filter_data = visualizer.add_penduduk_filters(df)
                filtered_df = render_penduduk_filters(filter_data)
            elif 'PENDIDIKAN' in selected_sheet.upper():
                filter_data = visualizer.add_pendidikan_filters(df)
                filtered_df = render_pendidikan_filters(filter_data)
            elif 'PEKERJAAN' in selected_sheet.upper():
                filter_data = visualizer.add_pekerjaan_filters(df)
                filtered_df = render_pekerjaan_filters(filter_data)
            elif any(kawin_keyword in selected_sheet.upper() for kawin_keyword in ['PERKAWINAN', 'KAWIN']):
                filter_data = visualizer.add_perkawinan_filters(df)
                filtered_df = render_perkawinan_filters(filter_data)
            elif any(umur_keyword in selected_sheet.upper() for umur_keyword in ['KEL UMUR', 'KELOMPOK UMUR', 'UMUR']):
                filter_data = visualizer.add_kelompok_umur_filters(df)
                filtered_df = render_kelompok_umur_filters(filter_data)
            else:
                st.warning(f"Tidak ada filter khusus untuk lembar {selected_sheet}")
                filtered_df = df
            
            # Tampilkan data yang sudah difilter
            st.subheader(f"Data Terfilter - {selected_sheet}")
            st.dataframe(filtered_df, use_container_width=True)
            
            # Create visualizations
            create_visualizations(filtered_df, selected_sheet)
        
        with tab2:
             # Show logo in the about section
#            logo_path = get_logo_path()
 #           if logo_path:
  #              logo_col1, logo_col2, logo_col3 = st.columns([2.2, 2, 1])
   #             with logo_col2:
    #                st.image(Image.open(logo_path), width=100)

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