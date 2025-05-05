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
   load_config, get_logo_path, 
   MadiunDataVisualizer, get_available_files
)
# Import the map visualization module
from madiun_map import create_choropleth_map, render_map_tab, load_madiun_geojson

# ============= VISUALIZATION FUNCTIONS =============

def create_visualizations(filtered_df, sheet_name):
   """Create visualizations based on filtered data"""
   numeric_cols = filtered_df.select_dtypes(include=['float64', 'int64']).columns
   
   if len(numeric_cols) > 0:
       # Ensure KECAMATAN column exists
       if 'KECAMATAN' not in filtered_df.columns:
           st.warning("Kolom KECAMATAN tidak ditemukan. Beberapa fitur mungkin tidak berfungsi.")
           return
           
       # Determine if we should display by desa
       show_by_desa = 'DESA' in filtered_df.columns and len(filtered_df['DESA'].unique()) > 1 and filtered_df['KECAMATAN'].nunique() == 1
       
       # Agregasi data berdasarkan kecamatan atau desa
       if show_by_desa:
           agg_df = filtered_df.groupby('DESA')[numeric_cols].sum().reset_index()
           x_col = 'DESA'
           x_label = 'Desa'
       else:
           agg_df = filtered_df.groupby('KECAMATAN')[numeric_cols].sum().reset_index()
           x_col = 'KECAMATAN'
           x_label = 'Kecamatan'
           
       # PERUBAHAN: Tampilkan grafik persentase terlebih dahulu untuk SEMUA KASUS
       # (baik untuk semua kecamatan maupun untuk satu kecamatan dengan banyak desa)
       if len(agg_df) > 1 and len(numeric_cols) > 1:
           # Normalisasi data untuk perbandingan proporsi
           pivot_df = agg_df.set_index(x_col)
           prop_df = pivot_df.copy()
           
           for idx in prop_df.index:
               row_sum = prop_df.loc[idx].sum()
               if row_sum > 0:  # Hindari pembagian dengan nol
                   prop_df.loc[idx] = (prop_df.loc[idx] / row_sum) * 100
           
           # Stacked bar chart untuk persentase
           fig_prop = px.bar(
               prop_df.reset_index(),
               x=x_col,
               y=prop_df.columns,
               title=f"Proporsi Data {sheet_name} per {x_label} (%)",
               barmode='stack',
               height=500
           )
           fig_prop.update_layout(xaxis_tickangle=-45)
           st.plotly_chart(fig_prop, use_container_width=True)
        
       # Bar chart berdasarkan kecamatan/desa (nilai absolut)
       fig_bar = px.bar(
           agg_df,
           x=x_col,
           y=numeric_cols,
           title=f'Visualisasi Data {sheet_name} per {x_label}',
           barmode='group',
           height=600
       )
       # Rotasi label x untuk kecamatan/desa agar lebih mudah dibaca
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
       
       # Heatmap untuk perbandingan 
       if len(agg_df) > 1 and len(numeric_cols) > 1:
           # Set index untuk pivot_df (jika belum diset di atas)
           if 'pivot_df' not in locals():
               pivot_df = agg_df.set_index(x_col)
               
           # Membuat heatmap dengan colorscales yang lebih jelas
           fig_heatmap = px.imshow(
               pivot_df,
               labels=dict(x="Kategori", y=x_label, color="Jumlah"),
               title=f"Heatmap Data {sheet_name} per {x_label}",
               color_continuous_scale='Viridis',
               aspect="auto",  # Menyesuaikan aspek rasio untuk ukuran layar
               height=500
           )
           st.plotly_chart(fig_heatmap, use_container_width=True)
           
           # Tambahkan visualisasi khusus untuk lembar tertentu
           create_special_visualizations(pivot_df, sheet_name, show_by_desa)
               
           # Tambahan visualisasi - Line Chart untuk trend visual
           if len(numeric_cols) > 1:
               fig_line = px.line(
                   agg_df,
                   x=x_col,
                   y=numeric_cols,
                   title=f"Tren Data {sheet_name} per {x_label}",
                   markers=True,
                   height=500
               )
               fig_line.update_layout(xaxis_tickangle=-45)
               st.plotly_chart(fig_line, use_container_width=True)
   else:
       st.warning("Tidak ada kolom numerik untuk divisualisasikan")

def create_special_visualizations(pivot_df, sheet_name, show_by_desa=False):
   """Create special visualizations based on sheet type"""
   # Tentukan label untuk x-axis berdasarkan tampilan
   x_label = 'Desa' if show_by_desa else 'Kecamatan'
   
   if 'AKTA' in sheet_name.upper():
       # Skip the percentage bar chart specifically for AKTA 0 SD 17 sheets
       if not any(akta_keyword in sheet_name.upper() for akta_keyword in ['AKTA 0 SD 17', 'AKTA 0-17']):
           # For AKTA sheets, show ownership percentage but skip for AKTA 0-17
           memiliki_cols = [col for col in pivot_df.columns if 'MEMILIKI' in str(col) and 'BELUM' not in str(col)]
           belum_cols = [col for col in pivot_df.columns if 'BELUM MEMILIKI' in str(col)]
           
           if memiliki_cols and belum_cols:
               try:
                   ratio_df = pd.DataFrame()
                   ratio_df['% Memiliki'] = pivot_df[memiliki_cols].sum(axis=1) / (pivot_df[memiliki_cols].sum(axis=1) + pivot_df[belum_cols].sum(axis=1)) * 100
                   ratio_df['% Belum Memiliki'] = 100 - ratio_df['% Memiliki']
                   
                   fig_ratio = px.bar(
                       ratio_df.reset_index(),
                       x=pivot_df.index.name,  # This will be either 'KECAMATAN' or 'DESA'
                       y=['% Memiliki', '% Belum Memiliki'],
                       title=f"Persentase Kepemilikan Akta per {x_label}",
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
                           x=pivot_df.index.name,  # This will be either 'KECAMATAN' or 'DESA'
                           y=pct_cols,
                           title=f"Distribusi Status Perkawinan per {x_label} (%)",
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
               x=pivot_df.index.name,  # This will be either 'KECAMATAN' or 'DESA'
               y=['% KK Laki-laki', '% KK Perempuan'],
               title=f"Persentase Kepala Keluarga Berdasarkan Gender per {x_label}",
               barmode='stack',
               height=500
           )
           fig_ratio.update_layout(xaxis_tickangle=-45)
           st.plotly_chart(fig_ratio, use_container_width=True)

# ============= WELCOME PAGE =============

def welcome_page():
   """Display the welcome page with Madiun logo and Start button"""
   # Apply the custom theme
   set_custom_theme()
   
   # Create a nice container for welcome screen
   st.markdown('<div class="login-container">', unsafe_allow_html=True)
   
   # Logo display in center
   col1, col2, col3 = st.columns([2.15, 2, 1])
   
   with col2:
       # Tampilkan logo dengan ukuran yang lebih besar
       logo_path = get_logo_path()
       if logo_path:
           try:
               st.image(Image.open(logo_path), width=200)
           except Exception as e:
               st.warning(f"Error loading logo: {str(e)}")
               st.warning("Logo tidak dapat ditampilkan. Pastikan file logo valid.")
       else:
           st.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.jpg' atau 'madiun_logo.png' ke direktori aplikasi.")
   
   # Header aplikasi setelah logo
   st.markdown("<h1 style='text-align: center;'>DISPENDUKCAPIL KAB.MADIUN</h1>", unsafe_allow_html=True)
   st.markdown("<h3 style='text-align: center;'>Sistem Visualisasi Data Kependudukan</h3>", unsafe_allow_html=True)
   
   # Deskripsi singkat tentang aplikasi
   st.markdown("<p style='text-align: center; margin: 30px 0;'>Aplikasi ini menyediakan visualisasi data kependudukan Kabupaten Madiun secara interaktif, memudahkan akses dan analisis informasi kependudukan.</p>", unsafe_allow_html=True)
   
   # Tombol Start di tengah
   col1, col2, col3 = st.columns([1, 2, 1])
   
   with col2:
       start_button = st.button("MULAI APLIKASI", use_container_width=True)
       
       if start_button:
           with st.spinner("Mempersiapkan aplikasi..."):
               time.sleep(1)  # Slight delay for better UX
               # Set default values in session state
               st.session_state.logged_in = True
               st.session_state.username = "guest"
               st.session_state.user_data = {"name": "Pengguna", "role": "guest"}
               st.success("Selamat datang di Sistem Visualisasi Data Kependudukan!")
               time.sleep(0.5)  # Short delay before redirecting
               st.experimental_rerun()
   
   # Close the login container
   st.markdown('</div>', unsafe_allow_html=True)
   
   # Footer
   st.markdown("<div style='text-align: center; margin-top: 50px;'>&copy; 2025 Dinas Kependudukan dan Pencatatan Sipil Kabupaten Madiun</div>", unsafe_allow_html=True)

def add_logo():
   """Add the Madiun logo to the Streamlit sidebar"""
   logo_path = get_logo_path()
   
   if logo_path:
       try:
           st.sidebar.image(Image.open(logo_path), width=140)
       except Exception as e:
           st.sidebar.warning(f"Error loading logo: {str(e)}")
           st.sidebar.warning("Logo tidak dapat ditampilkan. Pastikan file logo valid.")
   else:
       st.sidebar.warning("Logo tidak ditemukan. Silakan tambahkan file 'madiun_logo.jpg' atau 'madiun_logo.png' ke direktori aplikasi.")

def user_profile_section():
   """Display simplified user information in the sidebar"""
   st.sidebar.subheader("Pengguna")
   
   # Display user info if available, otherwise show generic info
   name = st.session_state.user_data.get("name", "Pengguna") if hasattr(st.session_state, "user_data") else "Pengguna"
   st.sidebar.write(f"Nama: {name}")
   
   # Add logout button that resets the session
   if st.sidebar.button("Keluar") :
       st.session_state.logged_in = False
       st.session_state.username = None
       st.session_state.user_data = None
       st.experimental_rerun()

# ============= MENU NAVIGASI YANG DITINGKATKAN =============

def create_beautiful_menu():
   """Buat menu navigasi yang menarik dengan emoji di dalam tombol"""
   
   # Tambahkan CSS untuk styling tombol
   st.markdown("""
   <style>
   /* Styling untuk tombol menu */
   div.stButton > button {
       background-color: white;
       color: #333;
       border-radius: 8px;
       box-shadow: 0 2px 5px rgba(0,0,0,0.1);
       padding: 20px 10px;
       transition: all 0.3s;
       font-size: 8px;
       height: 60px;
       display: block;
       width: 85%;
       margin: 0;
       line-height: 1.2;
       white-space: normal;
   }
   
   div.stButton > button:first-line {
       font-size: 16px;
       margin-bottom: 8px;
       display: block;
   }
   
   div.stButton > button:hover {
       transform: translateY(-3px);
       box-shadow: 0 4px 8px rgba(0,0,0,0.15);
       background-color: #f0f7f4;
   }
   </style>
   """, unsafe_allow_html=True)
   
   # Inisialisasi tab aktif jika belum ada
   if "active_tab" not in st.session_state:
       st.session_state.active_tab = "viz_data"
   
   # Buat layout horizontal untuk item menu
   col1, col2, col3, col4 = st.columns(4)
   
   # Buat tombol menu dengan emoji
   with col1:
       if st.button("📊\nVisualisasi Data", use_container_width=True):
           st.session_state.active_tab = "viz_data"
           st.experimental_rerun()
   
   with col2:
       if st.button("🔄\nPerbandingan File", use_container_width=True):
           st.session_state.active_tab = "compare"
           st.experimental_rerun()
   
   with col3:
       if st.button("🗺️\nVisualisasi Peta", use_container_width=True):
           st.session_state.active_tab = "map_viz"
           st.experimental_rerun()
   
   with col4:
       if st.button("ℹ️\nTentang Aplikasi", use_container_width=True):
           st.session_state.active_tab = "about"
           st.experimental_rerun()
   
   # Styling khusus untuk tab aktif
   tab_indices = {
       "viz_data": 1,
       "compare": 2,
       "map_viz": 3,
       "about": 4
   }
   
   active_index = tab_indices[st.session_state.active_tab]
   st.markdown(f"""
   <style>
   div[data-testid="stHorizontalBlock"] > div:nth-child({active_index}) button {{
       background-color: #0b5f34 !important;
       color: white !important;
   }}
   </style>
   """, unsafe_allow_html=True)
   
   return st.session_state.active_tab

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
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
       
       return filter_data['get_filtered_df']([selected_kecamatan], selected_usia, selected_status, selected_desa)
       
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
       
       return filter_data['get_filtered_df']([selected_kecamatan], selected_gender, selected_status, selected_desa)
   
   else:
       # Fallback for unknown format
       return filter_data['get_filtered_df']([selected_kecamatan], selected_desa)

def render_ktp_filters(filter_data):
   """Render filter UI for KTP sheet"""
   st.sidebar.subheader("Filter Data KTP")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_gender, selected_category, selected_desa)

def render_agama_filters(filter_data):
   """Render filter UI for AGAMA sheet"""
   st.sidebar.subheader("Filter Data Agama")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_agama, data_type, selected_desa)

def render_kia_filters(filter_data):
   """Render filter UI for KIA sheet"""
   st.sidebar.subheader("Filter Data KIA")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
   # Filter Status KIA
   selected_status = st.sidebar.multiselect(
       "Pilih Status KIA",
       options=filter_data['status_options'],
       default=['MEMILIKI KIA']
   )
   
   # Remove gender filter for KIA data
   # Since backend expects this parameter, we'll pass all gender options by default
   selected_gender = filter_data['gender_options']
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_status, selected_gender, selected_desa)

def render_kartu_keluarga_filters(filter_data):
   """Render filter UI for Kartu Keluarga sheet"""
   st.sidebar.subheader("Filter Data Kartu Keluarga")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_data, selected_gender, selected_desa)

def render_penduduk_filters(filter_data):
   """Render filter UI for Penduduk sheet"""
   st.sidebar.subheader("Filter Data Penduduk")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_gender, selected_usia, selected_desa)

def render_kelompok_umur_filters(filter_data):
   """Render filter UI for Kelompok Umur sheet"""
   st.sidebar.subheader("Filter Data Kelompok Umur")
   
   # Filter Kecamatan with selectbox (keep ALL option) if kecamatan exists
   selected_kecamatan = 'ALL'
   selected_desa = []
   
   if filter_data['kecamatan_list']:
       selected_kecamatan = st.sidebar.selectbox(
           "Pilih Kecamatan",
           options=filter_data['kecamatan_list'],
           index=0  # Default to ALL
       )
       
       # Show desa selection only if a specific kecamatan is selected
       if selected_kecamatan != 'ALL':
           desa_list = filter_data['get_desa_list']([selected_kecamatan])
           if desa_list:
               selected_desa_single = st.sidebar.selectbox(
                   "Pilih Desa",
                   options=["SEMUA DESA"] + desa_list,
                   index=0
               )
               # Convert to list format expected by backend
               if selected_desa_single != "SEMUA DESA":
                   selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_umur, selected_display, selected_desa)

def render_pendidikan_filters(filter_data):
   """Render filter UI for Pendidikan sheet"""
   st.sidebar.subheader("Filter Data Pendidikan")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
   # Filter Jenjang Pendidikan
   selected_pendidikan = st.sidebar.multiselect(
       "Pilih Jenjang Pendidikan",
       options=filter_data['pendidikan_list'],
       default=filter_data['pendidikan_list'][:3] if len(filter_data['pendidikan_list']) > 3 else filter_data['pendidikan_list']
   )
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_pendidikan, selected_desa)

def render_pekerjaan_filters(filter_data):
   """Render filter UI for Pekerjaan sheet"""
   st.sidebar.subheader("Filter Data Pekerjaan")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
   
   return filter_data['get_filtered_df']([selected_kecamatan], selected_pekerjaan, selected_desa)

def render_perkawinan_filters(filter_data):
   """Render filter UI for Perkawinan sheet"""
   st.sidebar.subheader("Filter Data Status Perkawinan")
   
   # Filter Kecamatan with selectbox (keep ALL option)
   selected_kecamatan = st.sidebar.selectbox(
       "Pilih Kecamatan",
       options=filter_data['kecamatan_list'],
       index=0  # Default to ALL
   )
   
   # Show desa selection only if a specific kecamatan is selected
   selected_desa = []
   if selected_kecamatan != 'ALL':
       desa_list = filter_data['get_desa_list']([selected_kecamatan])
       selected_desa_single = st.sidebar.selectbox(
           "Pilih Desa",
           options=["SEMUA DESA"] + desa_list,
           index=0
       )
       # Convert to list format expected by backend
       if selected_desa_single != "SEMUA DESA":
           selected_desa = [selected_desa_single]
   
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
       
       return filter_data['get_filtered_df']([selected_kecamatan], selected_status, selected_gender, selected_desa)
   else:
       # Old PERKAWINAN format without gender breakdown
       # Filter Status Perkawinan
       selected_status = st.sidebar.multiselect(
           "Pilih Status Perkawinan",
           options=filter_data['status_list'],
           default=filter_data['status_list']
       )
       
       return filter_data['get_filtered_df']([selected_kecamatan], selected_status, selected_desa)

def compare_files_page():
   """Halaman perbandingan data antar file"""
   st.header("Perbandingan Data Antar File")
   
   # Dapatkan file yang tersedia
   available_files = get_available_files()
   
   if len(available_files) < 2:
       st.warning("Tidak cukup file untuk dibandingkan. Harap unggah minimal 2 file Excel.")
       return
   
   # Pilih file untuk perbandingan
   col1, col2 = st.columns(2)
   
   with col1:
       file1 = st.selectbox("Pilih File Pertama", available_files)
   
   with col2:
       file2 = st.selectbox("Pilih File Kedua", 
                          [f for f in available_files if f != file1], 
                          index=0 if len(available_files) > 1 else None)
   
   # Dapatkan path lengkap file
   current_dir = os.path.dirname(os.path.abspath(__file__))
   file1_path = os.path.join(current_dir, file1)
   file2_path = os.path.join(current_dir, file2)
   
   # Ambil nama lembar dari kedua file
   xls1 = pd.ExcelFile(file1_path)
   xls2 = pd.ExcelFile(file2_path)
   
   # Pilih lembar untuk perbandingan
   sheet_name = st.selectbox(
       "Pilih Lembar untuk Dibandingkan", 
       sorted(set(xls1.sheet_names) & set(xls2.sheet_names))
   )
   
   if sheet_name:
       # Baca data dari kedua file
       df1 = pd.read_excel(file1_path, sheet_name=sheet_name)
       df2 = pd.read_excel(file2_path, sheet_name=sheet_name)
       
       # Konversi nama kolom ke string untuk konsistensi
       df1.columns = [str(col) for col in df1.columns]
       df2.columns = [str(col) for col in df2.columns]
       
       # Pilih kolom numerik untuk perbandingan
       numeric_cols1 = df1.select_dtypes(include=['float64', 'int64']).columns
       numeric_cols2 = df2.select_dtypes(include=['float64', 'int64']).columns
       
       # Temukan kolom yang sama di kedua file
       common_numeric_cols = sorted(set(numeric_cols1) & set(numeric_cols2))
       
       if not common_numeric_cols:
           st.warning("Tidak ada kolom numerik yang sama untuk dibandingkan.")
           return
       
       # Pilih kolom untuk perbandingan
       selected_cols = st.multiselect(
           "Pilih Kolom untuk Dibandingkan", 
           options=common_numeric_cols,
           default=common_numeric_cols[:min(4, len(common_numeric_cols))]
       )
       
       if selected_cols:
           # Gabungkan data dengan kolom yang dipilih
           # Pastikan 'KECAMATAN' adalah kolom utama
           if 'KECAMATAN' in df1.columns and 'KECAMATAN' in df2.columns:
               # Merge data berdasarkan kecamatan
               merged_df = pd.merge(
                   df1[['KECAMATAN'] + list(selected_cols)].groupby('KECAMATAN').sum(), 
                   df2[['KECAMATAN'] + list(selected_cols)].groupby('KECAMATAN').sum(), 
                   left_index=True, 
                   right_index=True, 
                   suffixes=(f' ({file1})', f' ({file2})')
               )
           else:
               # Jika tidak ada kolom kecamatan, gunakan agregasi global
               merged_df = pd.DataFrame({
                   f'{col} ({file1})': [df1[col].sum()] for col in selected_cols
               })
               merged_df.update(pd.DataFrame({
                   f'{col} ({file2})': [df2[col].sum()] for col in selected_cols
               }))
           
           # Tampilkan tabel perbandingan
           st.subheader("Tabel Perbandingan")
           st.dataframe(merged_df, use_container_width=True)
           
           # Deteksi apakah ini AKTA 0-17 dan memiliki kolom kepemilikan
           is_akta_0_17 = any(akta_keyword in sheet_name.upper() for akta_keyword in ['AKTA 0 SD 17', 'AKTA 0-17'])
           
           # Cek jika ada kolom MEMILIKI dan BELUM MEMILIKI untuk AKTA 0-17
           has_ownership_cols = is_akta_0_17 and (
               any('MEMILIKI' in col for col in selected_cols) or 
               any('BELUM MEMILIKI' in col for col in selected_cols)
           )
           
           # Visualisasi perbandingan
           st.subheader("Visualisasi Perbandingan 3D")
           
           # Create 3D bar chart using Scatter3d traces
           fig_3d = go.Figure()
           
           # Define grid for our visualization
           x_vals = list(range(len(merged_df.index)))
           
           # Create 3D visualization for file1 and file2
           for col_idx, col in enumerate(selected_cols):
               col1_name = f'{col} ({file1})'
               col2_name = f'{col} ({file2})'
               
               # Use different positions for each file
               y_pos1 = col_idx * 2
               y_pos2 = col_idx * 2 + 1
               
               # Add data for file1
               for kec_idx, kecamatan in enumerate(merged_df.index):
                   value = merged_df.loc[kecamatan, col1_name]
                   fig_3d.add_trace(
                       go.Scatter3d(
                           x=[kec_idx, kec_idx, kec_idx, kec_idx, kec_idx],
                           y=[y_pos1, y_pos1, y_pos1+0.8, y_pos1+0.8, y_pos1],
                           z=[0, value, value, 0, 0],
                           mode='lines',
                           line=dict(color='#1f77b4', width=4),
                           surfaceaxis=0,
                           name=f'{col} - {file1}' if kec_idx == 0 else None,
                           showlegend=True if kec_idx == 0 else False,
                           hoverinfo='text',
                           hovertext=f'{kecamatan} - {col}: {value} ({file1})'
                       )
                   )
                   
                   # Add a marker at the top of the bar for better visibility
                   fig_3d.add_trace(
                       go.Scatter3d(
                           x=[kec_idx],
                           y=[y_pos1+0.4],
                           z=[value],
                           mode='markers',
                           marker=dict(
                               size=4,
                               color='#1f77b4',
                           ),
                           showlegend=False,
                           hoverinfo='text',
                           hovertext=f'{kecamatan} - {col}: {value} ({file1})'
                       )
                   )
               
               # Add data for file2
               for kec_idx, kecamatan in enumerate(merged_df.index):
                   value = merged_df.loc[kecamatan, col2_name]
                   fig_3d.add_trace(
                       go.Scatter3d(
                           x=[kec_idx, kec_idx, kec_idx, kec_idx, kec_idx],
                           y=[y_pos2, y_pos2, y_pos2+0.8, y_pos2+0.8, y_pos2],
                           z=[0, value, value, 0, 0],
                           mode='lines',
                           line=dict(color='#ff7f0e', width=4),
                           surfaceaxis=0,
                           name=f'{col} - {file2}' if kec_idx == 0 else None,
                           showlegend=True if kec_idx == 0 else False,
                           hoverinfo='text',
                           hovertext=f'{kecamatan} - {col}: {value} ({file2})'
                       )
                   )
                   
                   # Add a marker at the top of the bar for better visibility
                   fig_3d.add_trace(
                       go.Scatter3d(
                           x=[kec_idx],
                           y=[y_pos2+0.4],
                           z=[value],
                           mode='markers',
                           marker=dict(
                               size=4,
                               color='#ff7f0e',
                           ),
                           showlegend=False,
                           hoverinfo='text',
                           hovertext=f'{kecamatan} - {col}: {value} ({file2})'
                       )
                   )
           
           # Update layout
           fig_3d.update_layout(
               title=f'Perbandingan Data 3D {sheet_name}',
               scene=dict(
                   xaxis_title='Kecamatan',
                   yaxis_title='Kategori',
                   zaxis_title='Jumlah',
                   xaxis=dict(
                       ticktext=merged_df.index.tolist(),
                       tickvals=list(range(len(merged_df.index)))
                   ),
                   yaxis=dict(
                       ticktext=[f"{col}" for col in selected_cols],
                       tickvals=[col_idx * 2 + 0.5 for col_idx in range(len(selected_cols))]
                   ),
                   aspectratio=dict(x=1.5, y=1, z=1)
               ),
               height=700,
               margin=dict(l=0, r=0, b=0, t=40),
               legend=dict(
                   title=dict(text="Dataset"),
                   itemsizing="constant",
                   x=0.9,
                   y=0.9
               )
           )
           
           # Add camera views
           fig_3d.update_layout(
               updatemenus=[dict(
                   type='buttons',
                   showactive=False,
                   buttons=[
                       dict(
                           label="Tampilan Depan",
                           method="relayout",
                           args=["scene.camera", dict(
                               up=dict(x=0, y=0, z=1),
                               center=dict(x=0, y=0, z=0),
                               eye=dict(x=0, y=-2.5, z=0)
                           )]
                       ),
                       dict(
                           label="Tampilan Atas",
                           method="relayout",
                           args=["scene.camera", dict(
                               up=dict(x=0, y=1, z=0),
                               center=dict(x=0, y=0, z=0),
                               eye=dict(x=0, y=0, z=2.5)
                           )]
                       ),
                       dict(
                           label="Tampilan Samping",
                           method="relayout",
                           args=["scene.camera", dict(
                               up=dict(x=0, y=0, z=1),
                               center=dict(x=0, y=0, z=0),
                               eye=dict(x=2.5, y=0, z=0)
                           )]
                       ),
                       dict(
                           label="Tampilan Isometrik",
                           method="relayout",
                           args=["scene.camera", dict(
                               up=dict(x=0, y=0, z=1),
                               center=dict(x=0, y=0, z=0),
                               eye=dict(x=1.5, y=1.5, z=1.5)
                           )]
                       ),
                   ],
                   direction="down",
                   pad={"r": 10, "t": 10},
                   x=0.9,
                   y=0.05,
                   xanchor="right",
                   yanchor="bottom"
               )]
           )
           
           # Tampilkan grafik
           st.plotly_chart(fig_3d, use_container_width=True)
           
           # Add a note about 3D interaction
           st.info("🔄 Anda dapat memutar, memperbesar, dan menggeser grafik 3D untuk melihat perbandingan data dari berbagai sudut. Gunakan tombol 'Tampilan' untuk melihat dari perspektif yang berbeda.")
           
           # Hitung dan tampilkan perubahan persentase
           st.subheader("Analisis Perubahan")
           
           # Tabel persentase perubahan
           change_df = pd.DataFrame(index=merged_df.index)
           
           for col in selected_cols:
               col1_name = f'{col} ({file1})'
               col2_name = f'{col} ({file2})'
               
               # Hitung persentase perubahan (dengan penanganan division by zero)
               change_col = f'% Perubahan {col}'
               # Hindari division by zero dengan memeriksa nilai nol
               change_df[change_col] = merged_df.apply(
                   lambda row: ((row[col2_name] - row[col1_name]) / row[col1_name] * 100).round(2) 
                   if row[col1_name] != 0 else float('nan'), 
                   axis=1
               )
           
           # Tampilkan tabel perubahan
           st.dataframe(change_df, use_container_width=True)
           
           # Visualisasi perubahan persentase
           # Skip stacked bar chart untuk AKTA 0-17 yang memiliki kolom kepemilikan
           if has_ownership_cols:
               # Untuk AKTA 0-17 yang memiliki kolom kepemilikan, tampilkan pesan info
               st.info("Visualisasi persentase stacked bar chart untuk data kepemilikan AKTA 0-17 tidak ditampilkan secara sengaja sesuai permintaan.")
           else:
               # Untuk sheet lainnya, tampilkan visualisasi perubahan persentase normal
               fig_change = go.Figure()
               
               for col in selected_cols:
                   change_col = f'% Perubahan {col}'
                   
                   fig_change.add_trace(go.Bar(
                       x=change_df.index,
                       y=change_df[change_col],
                       name=change_col
                   ))
               
               fig_change.update_layout(
                   title='Persentase Perubahan Antar File',
                   xaxis_title='Kecamatan',
                   yaxis_title='Persentase Perubahan (%)',
                   height=500
               )
               
               st.plotly_chart(fig_change, use_container_width=True)

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
   if not st.session_state.get("logged_in", False):
       welcome_page()
       return
   
   # If logged in or started, show the main application
   # Add logo at the top of the sidebar
   add_logo()
   
   # Add user profile section in sidebar
   user_profile_section()
   
   st.title("DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KAB.MADIUN")
   
   # PERUBAHAN: Menggunakan menu yang telah ditingkatkan
   active_tab = create_beautiful_menu()
   
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
     
       # PERUBAHAN: Kode untuk setiap tab telah dikonversi ke bagian if-elif
       
       if active_tab == "viz_data":
           # Konten untuk visualisasi data (tab1)
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
           
           # MODIFIKASI: Tampilkan data mentah per kecamatan saja (tanpa desa) untuk tampilan default
           st.subheader(f"Data Mentah - {selected_sheet}")
           
           # Convert all column names to string to avoid errors
           df.columns = [str(col) for col in df.columns]
           
           # Create a summarized view by kecamatan for default display
           if 'KECAMATAN' in df.columns and 'DESA' in df.columns:
               # Group by KECAMATAN and sum all numeric columns
               numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
               default_df = df.groupby('KECAMATAN')[numeric_cols].sum().reset_index()
               
               # Add a note about the default view
               st.info("Menampilkan ringkasan data per kecamatan. Gunakan filter untuk melihat data detail per desa.")
               
               # Display the summarized data
               st.dataframe(default_df, use_container_width=True)
               
               # Add option to view full data including desa
               if st.checkbox("Tampilkan Data Lengkap (Termasuk Desa)"):
                   st.dataframe(df, use_container_width=True)
           else:
               # If no KECAMATAN or DESA column, show original data
               st.dataframe(df, use_container_width=True)
           
           # Add a filter button to trigger filtering
           filter_section = st.sidebar.expander("Pengaturan Filter", expanded=True)
           
           filtered_df = None
           
           with filter_section:
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
               
               # Filter button at the bottom of the filter section
               filter_applied = st.button("Terapkan Filter", use_container_width=True)
           
           # Only show filtered data and visualizations if filter is applied
           if filter_applied and filtered_df is not None:
               # Tampilkan data yang sudah difilter
               st.subheader(f"Data Terfilter - {selected_sheet}")
               st.dataframe(filtered_df, use_container_width=True)
               
               # Create visualizations
               create_visualizations(filtered_df, selected_sheet)
       
       elif active_tab == "compare":
           # Konten untuk perbandingan antar file (tab2)
           compare_files_page()

       elif active_tab == "map_viz":
           # Konten untuk visualisasi peta (tab3)
           # Untuk keperluan ini, kita perlu data yang terfilter
           # Karena kita tidak lagi di dalam tab, kita perlu membuat variable filtered_df
           # Sebagai contoh, kita akan menggunakan lembar pertama
           selected_sheet = sheet_names[0]
           df = pd.read_excel(file_path, sheet_name=selected_sheet)
           df.columns = [str(col) for col in df.columns]
           filtered_df = df  # Gunakan df mentah jika tidak ada filter khusus
           
           # Tampilkan tab visualisasi peta
           render_map_tab(filtered_df, selected_sheet)
           
       elif active_tab == "about":
           # Konten untuk tentang aplikasi (tab4)
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
           4. Klik tombol "Terapkan Filter" untuk melihat hasil
           5. Lihat hasil visualisasi dalam bentuk tabel dan grafik
           
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