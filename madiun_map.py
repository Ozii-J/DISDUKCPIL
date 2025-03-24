import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import json
import os

def get_madiun_kecamatan():
    """
    Daftar kecamatan di Kabupaten Madiun
    """
    return [
        'Mejayan', 'Caruban', 'Pilangkenceng', 'Dolopo', 
        'Geger', 'Kebonsari', 'Madiun', 'Sawahan', 
        'Wonoasri', 'Balerejo', 'Jiwan', 'Kare'
    ]

def create_choropleth_map(filtered_df, sheet_name="Peta Kabupaten Madiun"):
    """
    Create a map visualization focused specifically on Madiun Regency.
    
    Returns:
    - Plotly figure
    """
    try:
        # More detailed boundary polygon for Kabupaten Madiun that follows natural borders
        # These points create a more natural, non-rectangular border
        madiun_boundary = [
        ]
        
        # Buat figure dengan natural map
        fig = go.Figure()
        
        # Add the Madiun Regency boundary with a natural shape
        fig.add_trace(go.Scattermapbox(
            mode='lines',
            lon=[point[0] for point in madiun_boundary],
            lat=[point[1] for point in madiun_boundary],
            line=dict(width=3, color='red'),  # Bold red border
            fill='toself',
            fillcolor='rgba(0, 0, 0, 0)',  # Transparent fill
            name='Kabupaten Madiun'
        ))
        
        # Sesuaikan tata letak peta - menggunakan open-street-map untuk tampilan natural
        fig.update_layout(
            mapbox_style="open-street-map",  # Natural map style
            mapbox_zoom=13,  # Adjust zoom level to fit Madiun Regency
            mapbox_center={
                "lat": -7.635,  # Center point of Kabupaten Madiun
                "lon": 111.525
            },
            title="VISUAL PETA KOTA/KABUPATEN MADIUN",
            height=600,
            margin={"r":0,"t":50,"l":0,"b":0}
        )
        
        return fig
    
    except Exception as e:
        st.error(f"Kesalahan dalam membuat peta: {str(e)}")
        return None

def render_map_tab(filtered_df=None, sheet_name="Peta Kabupaten Madiun"):
    """
    Render the map visualization tab.
    
    Args:
    - filtered_df: Optional filtered DataFrame (not used in this version)
    - sheet_name: Name to display on the map
    """
    try:
       
        
        # Buat visualisasi
        map_fig = create_choropleth_map(filtered_df, sheet_name)
        
        if map_fig:
            # Tampilkan visualisasi
            st.plotly_chart(map_fig, use_container_width=True)
        else:
            st.warning("Tidak dapat membuat visualisasi.")
        
        # Tampilkan daftar kecamatan
        st.subheader("Daftar Kecamatan Kabupaten Madiun")
        st.write(", ".join(get_madiun_kecamatan()))
    
    except Exception as e:
        st.error(f"Kesalahan dalam rendering tab peta: {str(e)}")

def load_madiun_geojson():
    """
    Placeholder function as no specific GeoJSON is available
    """
    st.warning("File GeoJSON detail Kabupaten Madiun tidak tersedia.")
    return None