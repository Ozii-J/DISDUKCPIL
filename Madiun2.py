import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.express as px
import os

# Set style
sns.set(style='dark')

# Page Configuration
st.set_page_config(
    page_title="Visualisasi Data Akta Kelahiran",
    page_icon="📊",
    layout="wide"
)

# Function to load and process data
@st.cache_data
def load_data():
    try:
        # Get the current directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx")
        
        # Display file path for debugging
        st.write(f"Mencoba membaca file dari: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            st.error(f"File tidak ditemukan di lokasi: {file_path}")
            st.info("Pastikan file Excel berada di direktori yang sama dengan script Python")
            return None
            
        df = pd.read_excel(
            file_path,
            sheet_name="AKTA_0 SD 17_DESA"
        )
        
        # Display raw data shape for debugging
        st.write(f"Ukuran data mentah: {df.shape}")
        
        # Rename columns for clarity
        column_mapping = {
            'KECAMATAN': 'Kecamatan',
            'DESA': 'Desa/Kelurahan',
            'MEMILIKI (KESELURUHAN)': 'Jumlah Memiliki',
            'BELUM MEMILIKI (KESELURUHAN)': 'Belum Memiliki',
            'JUMLAH (KESELURUHAN)': 'Total Keseluruhan',
            'MEMILIKI (0-5 TAHUN)': 'Memiliki 0-5 Tahun',
            'BELUM MEMILIKI (0-5 TAHUN)': 'Belum Memiliki 0-5 Tahun',
            'MEMILIKI (0-17 TAHUN)': 'Memiliki 0-17 Tahun',
            'BELUM MEMILIKI (0-17 TAHUN)': 'Belum Memiliki 0-17 Tahun'
        }
        
        # Display available columns for debugging
        st.write("Kolom yang tersedia:", list(df.columns))
        
        # Rename only columns that exist
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)
        
        # Convert numeric columns
        numeric_columns = [
            'Jumlah Memiliki', 'Belum Memiliki', 'Total Keseluruhan',
            'Memiliki 0-5 Tahun', 'Belum Memiliki 0-5 Tahun',
            'Memiliki 0-17 Tahun', 'Belum Memiliki 0-17 Tahun'
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Error saat memuat data: {str(e)}")
        st.write("Detail error:", e)
        return None

# Load data
df = load_data()

if df is not None:
    # Remove debug information once everything works
    st.write("Data berhasil dimuat!")
    
    # Header
    st.header('DATA KEPEMILIKAN AKTA KELAHIRAN KABUPATEN MADIUN')
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filter Data")
        kecamatan_filter = st.multiselect(
            "Pilih Kecamatan",
            options=sorted(df['Kecamatan'].unique()),
            default=sorted(df['Kecamatan'].unique())
        )
    
    # Filter the dataframe
    filtered_df = df[df['Kecamatan'].isin(kecamatan_filter)]
    
    # Calculate total metrics
    total_memiliki = filtered_df['Jumlah Memiliki'].sum()
    total_belum = filtered_df['Belum Memiliki'].sum()
    total_keseluruhan = total_memiliki + total_belum
    persentase_memiliki = (total_memiliki / total_keseluruhan) * 100 if total_keseluruhan > 0 else 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Memiliki Akta", value="{:,}".format(total_memiliki))
    with col2:
        st.metric("Total Belum Memiliki", value="{:,}".format(total_belum))
    with col3:
        st.metric("Persentase Kepemilikan", value=f"{persentase_memiliki:.2f}%")
    
    st.divider()
    
    # Distribution by Kecamatan
    st.subheader("DISTRIBUSI KEPEMILIKAN AKTA BERDASARKAN KECAMATAN")
    kecamatan_counts = filtered_df.groupby('Kecamatan')[['Jumlah Memiliki', 'Belum Memiliki']].sum().reset_index()
    
    fig = px.bar(kecamatan_counts, 
                 x='Kecamatan', 
                 y=['Jumlah Memiliki', 'Belum Memiliki'],
                 barmode='group',
                 labels={'value': 'Jumlah', 'variable': 'Status'},
                 title='Distribusi Kepemilikan Akta per Kecamatan')
    st.plotly_chart(fig, use_container_width=True)
    
    # Age group comparison
    st.subheader("PERBANDINGAN KEPEMILIKAN AKTA BERDASARKAN KELOMPOK USIA")
    age_groups = filtered_df.groupby('Kecamatan').agg({
        'Memiliki 0-5 Tahun': 'sum',
        'Belum Memiliki 0-5 Tahun': 'sum',
        'Memiliki 0-17 Tahun': 'sum',
        'Belum Memiliki 0-17 Tahun': 'sum'
    }).reset_index()
    
    fig = px.bar(age_groups,
                 x='Kecamatan',
                 y=['Memiliki 0-5 Tahun', 'Belum Memiliki 0-5 Tahun', 
                    'Memiliki 0-17 Tahun', 'Belum Memiliki 0-17 Tahun'],
                 barmode='group',
                 labels={'value': 'Jumlah', 'variable': 'Kelompok Usia'},
                 title='Perbandingan Kepemilikan Akta Berdasarkan Kelompok Usia')
    st.plotly_chart(fig, use_container_width=True)
    
    # Pie chart for overall percentage
    st.subheader("PERSENTASE KEPEMILIKAN AKTA")
    labels = ['Memiliki Akta', 'Belum Memiliki']
    sizes = [total_memiliki, total_belum]
    colors = ['#0766AD', '#FF0060']
    
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, textprops={'fontsize': 10})
    ax.axis('equal')
    st.pyplot(fig)
    
    # Data table
    st.subheader("DETAIL DATA PER KECAMATAN")
    summary_df = filtered_df.groupby('Kecamatan').agg({
        'Jumlah Memiliki': 'sum',
        'Belum Memiliki': 'sum',
        'Total Keseluruhan': 'sum'
    }).reset_index()
    summary_df['Persentase Kepemilikan'] = (summary_df['Jumlah Memiliki'] / summary_df['Total Keseluruhan'] * 100).round(2)
    st.dataframe(summary_df, use_container_width=True)

else:
    st.error("Gagal memuat data. Silakan ikuti langkah-langkah berikut:")
    st.write("1. Pastikan file Excel berada di direktori yang sama dengan script Python")
    st.write("2. Pastikan nama file Excel tepat: 'STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx'")
    st.write("3. Pastikan sheet Excel bernama 'AKTA_0 SD 17_DESA'")