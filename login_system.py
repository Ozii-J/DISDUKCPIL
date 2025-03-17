import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
import numpy as np
from PIL import Image
import hashlib
import time
import json

# Configuration and utilities
def load_config():
    """Load user configuration or create default if not exists"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_config.json")
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f)
    else:
        # Default configuration with admin user
        default_config = {
            "users": {
                "admin": {
                    "password": hashlib.sha256("admin123".encode()).hexdigest(),
                    "role": "admin",
                    "name": "Administrator"
                },
                "dispendukcapil": {
                    "password": hashlib.sha256("madiun2024".encode()).hexdigest(),
                    "role": "staff",
                    "name": "Staff Dispendukcapil"
                }
            }
        }
        
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
        return default_config

def verify_password(username, password):
    """Verify username and password"""
    config = load_config()
    if username in config["users"]:
        stored_password = config["users"][username]["password"]
        if stored_password == hashlib.sha256(password.encode()).hexdigest():
            return True, config["users"][username]
    return False, None

def login_page():
    """Display the login page with Madiun logo"""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Display logo at the top center
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "madiun_logo.png")
        if os.path.exists(logo_path):
            st.image(Image.open(logo_path), width=200)
        else:
            st.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.png' ke direktori aplikasi.")
        
        st.markdown("<h1 style='text-align: center;'>DISPENDUKCAPIL KAB.MADIUN</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Sistem Visualisasi Data Kependudukan</h3>", unsafe_allow_html=True)
        
        # Login form with custom styling
        st.markdown("<p style='text-align: center; margin-top: 30px;'>Silakan masuk untuk melanjutkan</p>", unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        # Create columns for the buttons
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
        
        st.markdown("<div style='text-align: center; margin-top: 50px;'>&copy; 2024 Dinas Kependudukan dan Pencatatan Sipil Kabupaten Madiun</div>", unsafe_allow_html=True)

class MadiunDataVisualizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.xls = pd.ExcelFile(file_path)
    
    # [All the existing methods from your original code would go here]
    # For brevity, I'm not copying all of them, but they should remain unchanged
    
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
    
    # [Include all other filter methods from your original code]
    
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
        # [Continue with the rest of your visualize_filtered_data method]
        # This is where you would add your specific visualization code for each sheet type

def add_logo():
    """Add the Madiun logo to the Streamlit sidebar"""
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "madiun_logo.jpg")
    
    if os.path.exists(logo_path):
        st.sidebar.image(Image.open(logo_path), width=150)
    else:
        st.sidebar.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.jpg' ke direktori aplikasi.")

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

def main():
    st.set_page_config(
        page_title="Visualisasi Data DISPENDUKCAPIL Madiun",
        page_icon="📊",
        layout="wide"
    )
    
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
    
    st.title("📊 Visualisasi Data DISPENDUKCAPIL KAB.MADIUN")
    
    # Membuat tab untuk navigasi
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
            
            # Add logo in the about section too
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "madiun_logo.png")
            if os.path.exists(logo_path):
                logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
                with logo_col2:
                    st.image(Image.open(logo_path), width=200)
            
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