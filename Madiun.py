import streamlit as st
import pandas as pd
import numpy as np
import hydralit_components as hc
import altair as alt
import re

# Page Configuration
st.set_page_config(
    page_title="Visualisasi Data Akta Kelahiran",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state='collapsed',
)

# Navigation Menu
menu_data = [
    {'icon': "fa fa-database", 'label': "Dataset"},
    {'id': 'Data Filter', 'icon': 'fa fa-filter', 'label': "Filter Data"},
    {'id': 'subid12', 'icon': "📈", 'label': "Line Chart"},
    {'id': 'subid11', 'icon': "📊", 'label': "Barchart"},
    {'id': 'Pie', 'icon': "◔", 'label': "Pie Chart"},
]

over_theme = {
    'txc_inactive': 'black',
    'menu_background': 'lightblue',
    'txc_active': 'yellow',
    'option_active': 'black'
}

# Custom CSS for metrics
st.markdown("""
<style>
div[data-testid="metric-container"] {
   background-color: rgba(20, 205, 200, 1);
   border: 1px solid rgba(242, 39, 19, 1);
   padding: 5% 5% 5% 10%;
   border-radius: 5px;
   color: rgb(224,255,255);
   overflow-wrap: break-word;
}

div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
   overflow-wrap: break-word;
   white-space: break-spaces;
   font-size: large;
   color: red;
}
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    try:
        # Load the Excel file with error handling
        try:
            df = pd.read_excel(
                io="DISDUKCPIL/STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx",
                engine='openpyxl',
                sheet_name=0
            )
            if df.empty:
                st.error("The Excel file is empty. Please check the data source.")
                return None
        except FileNotFoundError:
            st.error("Excel file not found. Please ensure the file exists at: DISDUKCPIL/STAT_SMT_I_2024 WEB AKTA KELAHIRAN 18 TAHUN_DESA.xlsx")
            return None
        except Exception as e:
            st.error(f"Error loading Excel file: {str(e)}")
            return None

        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Display file info and column names
        st.success("File loaded successfully!")
        st.write(f"Total rows: {len(df)}")
        with st.expander("Show Column Names"):
            st.write("Columns in the DataFrame:", list(df.columns))

        # Find the correct column names dynamically
        def find_column(pattern):
            matching_cols = [col for col in df.columns if re.search(pattern, col, re.IGNORECASE)]
            return matching_cols[0] if matching_cols else None
        
        # Dynamically find column names
        keseluruhan_memiliki = find_column(r'KESELURUHAN.*MEMILIKI')
        keseluruhan_belum_memiliki = find_column(r'KESELURUHAN.*BELUM MEMILIKI')
        usia_0_5_memiliki = find_column(r'USIA 0-5.*MEMILIKI')
        usia_0_5_belum_memiliki = find_column(r'USIA 0-5.*BELUM MEMILIKI')
        usia_0_17_memiliki = find_column(r'USIA 0-17.*MEMILIKI')
        usia_0_17_belum_memiliki = find_column(r'USIA 0-17.*BELUM MEMILIKI')
        kecamatan = find_column(r'KECAMATAN')
        desa = find_column(r'DESA/KELURAHAN')
        
        # Validate required columns
        required_columns = {
            'Keseluruhan Memiliki': keseluruhan_memiliki,
            'Keseluruhan Belum Memiliki': keseluruhan_belum_memiliki,
            'Usia 0-5 Memiliki': usia_0_5_memiliki,
            'Usia 0-5 Belum Memiliki': usia_0_5_belum_memiliki,
            'Usia 0-17 Memiliki': usia_0_17_memiliki,
            'Usia 0-17 Belum Memiliki': usia_0_17_belum_memiliki,
            'Kecamatan': kecamatan,
            'Desa/Kelurahan': desa
        }
        
        missing_columns = [name for name, col in required_columns.items() if col is None]
        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.info("Please ensure the Excel file contains these columns with the expected naming patterns.")
            return None

        # Rename columns
        df = df.rename(columns={
            keseluruhan_memiliki: 'Jumlah',
            keseluruhan_belum_memiliki: 'Total Belum Memiliki',
            usia_0_5_memiliki: 'Memiliki 0-5 Tahun',
            usia_0_5_belum_memiliki: 'Belum Memiliki 0-5 Tahun',
            usia_0_17_memiliki: 'Memiliki 0-17 Tahun',
            usia_0_17_belum_memiliki: 'Belum Memiliki 0-17 Tahun',
            kecamatan: 'Kecamatan',
            desa: 'Desa/Kelurahan'
        })
        
        # Convert numeric columns and fill NaN with 0
        numeric_columns = [
            'Jumlah', 'Total Belum Memiliki',
            'Memiliki 0-5 Tahun', 'Belum Memiliki 0-5 Tahun',
            'Memiliki 0-17 Tahun', 'Belum Memiliki 0-17 Tahun'
        ]
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Create navigation bar
menu_id = hc.nav_bar(
    menu_definition=menu_data,
    override_theme=over_theme,
    home_name='Home',
    hide_streamlit_markers=True,
    sticky_nav=True,
    sticky_mode='pinned',
)

# Load the data
df = load_data()

if df is not None:
    # Home page
    if menu_id == 'Home':
        st.write("""# Visualisasi Data Akta Kelahiran Kabupaten Madiun""")
        st.write("Aplikasi ini menampilkan data kepemilikan akta kelahiran kab.Madiun dengan sumber data dari dispendukcapil Kab.Madiun")

    # Dataset page
    elif menu_id == 'Dataset':
        st.write("""## Dataset Keseluruhan""")
        st.write(f"Total jumlah baris: {len(df)}")
        st.dataframe(df, use_container_width=True)

    # Data Filter page
    elif menu_id == 'Data Filter':
        st.write("""## Filter Data Akta Kelahiran""")
        
        # Create filter sidebar
        st.sidebar.header("Filter Data")
        
        # Filter by Kecamatan
        kecamatan_filter = st.sidebar.multiselect(
            "Pilih Kecamatan",
            sorted(df['Kecamatan'].unique()),
            default=sorted(df['Kecamatan'].unique())
        )
        
        # Apply filters
        filtered_df = df[df['Kecamatan'].isin(kecamatan_filter)]
        
        # Display filtered data
        st.dataframe(filtered_df[['Kecamatan', 'Desa/Kelurahan', 'Jumlah']], use_container_width=True)

    # Line Chart page
    elif menu_id == 'subid12':
        st.write("""## Line Charts Kepemilikan Akta per Kecamatan""")
        
        # Group data by Kecamatan
        kecamatan_summary = df.groupby('Kecamatan')['Jumlah'].sum().reset_index()
        
        # Create line chart
        chart = alt.Chart(kecamatan_summary).mark_line(point=True).encode(
            x='Kecamatan:N',
            y='Jumlah:Q',
            tooltip=['Kecamatan', 'Jumlah']
        ).properties(height=400, width=800)
        
        st.altair_chart(chart)

    # Bar Chart page
    elif menu_id == 'subid11':
        st.write("""## Bar Chart Kepemilikan Akta per Kecamatan""")
        
        # Group data by Kecamatan
        kecamatan_summary = df.groupby('Kecamatan')['Jumlah'].sum().reset_index()
        
        # Create bar chart
        chart = alt.Chart(kecamatan_summary).mark_bar().encode(
            x='Kecamatan:N',
            y='Jumlah:Q',
            color=alt.Color('Kecamatan:N', legend=None),
            tooltip=['Kecamatan', 'Jumlah']
        ).properties(height=400, width=800)
        
        st.altair_chart(chart)

    # Pie Chart page
    elif menu_id == 'Pie':
        st.write("""## Pie Chart Kepemilikan Akta per Kecamatan""")
        
        # Group data by Kecamatan
        kecamatan_summary = df.groupby('Kecamatan')['Jumlah'].sum().reset_index()
        
        # Create pie chart
        chart = alt.Chart(kecamatan_summary).mark_arc().encode(
            theta=alt.Theta(field="Jumlah", type="quantitative"),
            color=alt.Color(field="Kecamatan", type="nominal"),
            tooltip=['Kecamatan', 'Jumlah']
        ).properties(width=600, height=600)
        
        st.altair_chart(chart)

else:
    st.error("Gagal memuat data")
