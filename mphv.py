# # -*- coding: utf-8 -*-
# """
# Created on Tue Jul 22 14:59:35 2025

# @author: asus
# """

# # -*- coding: utf-8 -*-
# """
# Created on Fri Jul 11 17:31:38 2025

# @author: asus
# """

# import streamlit as st
# from streamlit_folium import st_folium
# import folium
# import requests
# import geoglows
# import pandas as pd
# import plotly.graph_objects as go

# # --- Streamlit Page Config ---
# st.set_page_config(page_title="🌊 GEOGloWS River Dashboard", layout="wide")

# # --- Title & Description ---
# st.markdown("""
# <style>
# .big-title {
#     font-size: 2.5em;
#     font-weight: bold;
#     color: #0072B5;
#     margin-bottom: 0.5em;
# }
# .description {
#     font-size: 1.1em;
#     color: #444;
#     margin-top: -0.5em;
#     margin-bottom: 1.5em;
# }
# </style>
# <div class="big-title">🌊 GEOGloWS River ID Finder & Flow Dashboard</div>
# <div class="description">Click anywhere on the map to identify the closest river reach (COMID) and visualize retrospective and forecast streamflow data, with volume summaries.</div>
# """, unsafe_allow_html=True)

# # --- Sidebar: State Boundary Overlay ---
# st.sidebar.header("🗺️ State Boundary Overlay")
# selected_state = st.sidebar.text_input("Enter State Name", "Madhya Pradesh")

# # Load and filter the state boundary asset
# import ee
# try:
#     ee.Initialize()
# except Exception:
#     ee.Authenticate()
#     ee.Initialize()

# state_fc = ee.FeatureCollection("projects/ee-shpp/assets/State_Boundary")
# state_filtered = state_fc.filter(ee.Filter.eq('STATE', selected_state))

# # --- Build Map with State Overlay ---
# def draw_map():
#     default_location = [26.1445, 91.7362]
#     m = folium.Map(location=default_location, zoom_start=6, control_scale=True)
#     # Add state boundary as GeoJSON
#     try:
#         geojson = state_filtered.getInfo()
#         folium.GeoJson(
#             data=geojson,
#             name=f"{selected_state} Boundary",
#             style_function=lambda f: {
#                 'fillColor': 'none',
#                 'color': '#FF0000',
#                 'weight': 3,
#                 'dashArray': '5, 5'
#             }
#         ).add_to(m)
#         folium.LayerControl().add_to(m)
#     except Exception as e:
#         st.error(f"Error loading state boundary: {e}")

#     # Add click popup
#     m.add_child(folium.LatLngPopup())
#     return m

# m = draw_map()
# st_data = st_folium(m, height=600, width=1000)

# # --- River Selection & Data Display ---
# if st_data and st_data.get("last_clicked"):
#     lat = st_data["last_clicked"].get("lat")
#     lon = st_data["last_clicked"].get("lng")

#     if lat is None or lon is None:
#         st.error("❌ Invalid click location. Please try again.")
#         st.stop()

#     st.success(f"📍 Location selected: **Lat:** {lat:.5f}, **Lon:** {lon:.5f}")

#     api_url = f"https://geoglows.ecmwf.int/api/v2/getriverid/?lat={lat}&lon={lon}"
#     try:
#         response = requests.get(api_url, timeout=10)
#         response.raise_for_status()
#         data = response.json()

# -*- coding: utf-8 -*-
# """
# Created on Fri Jul 11 17:31:38 2025

# Updated to center only initially on selected state boundary (Madhya Pradesh), persist user interactions, and display latest flow instead of date-range filtering.
# """

# import streamlit as st
# from streamlit_folium import st_folium
# import folium
# import requests
# import geoglows
# import pandas as pd
# import ee
# import plotly.express as px

# # --- Streamlit Page Config ---
# st.set_page_config(page_title="🌊 GEOGloWS River Dashboard", layout="wide")

# # --- CSS Styling ---
# st.markdown("""
# <style>
# .big-title { font-size:2.5em; font-weight:bold; color:#0072B5; margin-bottom:0.2em; }
# .description { font-size:1.1em; color:#444; margin-top:-0.2em; margin-bottom:1em; }
# </style>
# """, unsafe_allow_html=True)

# # --- Header & Description ---
# st.markdown('<header><div class="big-title">🌊 GEOGloWS River Dashboard</div></header>', unsafe_allow_html=True)
# st.markdown('<section class="description">Click on the map to identify the river COMID and view the latest flow data.</section>', unsafe_allow_html=True)

# # --- Sidebar Settings ---
# st.sidebar.header("⚙️ Dashboard Settings")
# selected_state = st.sidebar.text_input("State Name:", "Madhya Pradesh")

# # --- Initialize Earth Engine ---
# try:
#     ee.Initialize()
# except Exception:
#     ee.Authenticate()
#     ee.Initialize()

# # --- Load AOI boundary ---
# state_fc = ee.FeatureCollection("projects/ee-shpp/assets/State_Boundary")
# state_filtered = state_fc.filter(ee.Filter.eq('STATE', selected_state))

# # --- Compute centroid of AOI ---
# def get_center(fc):
#     try:
#         coords = fc.geometry().centroid().coordinates().getInfo()
#         return [coords[1], coords[0]]
#     except:
#         return [26.1445, 91.7362]

# # --- Session State Management ---
# if 'last_state' not in st.session_state or st.session_state.last_state != selected_state:
#     st.session_state.map_state = {'center': get_center(state_filtered), 'zoom': 7}
#     st.session_state.last_state = selected_state
# if 'comid' not in st.session_state:
#     st.session_state.comid = None

# # --- Tabs Layout ---
# tab_map, tab_retro, tab_fc = st.tabs(["🗺️ Map & AOI", "📄 Latest Flow", "📈 Forecast Flow"])

# # --- Map & AOI Tab ---
# with tab_map:
#     m = folium.Map(
#         location=st.session_state.map_state['center'],
#         zoom_start=st.session_state.map_state['zoom'],
#         control_scale=True
#     )
#     m.add_child(folium.LatLngPopup())
#     try:
#         folium.GeoJson(
#             state_filtered.getInfo(),
#             name=f"{selected_state} Boundary",
#             style_function=lambda f: {'fillColor':'none','color':'#FF0000','weight':3,'dashArray':'5,5'}
#         ).add_to(m)
#         folium.LayerControl().add_to(m)
#     except Exception as e:
#         st.sidebar.error(f"AOI load error: {e}")

#     map_data = st_folium(
#         m,
#         height=600,
#         width=1000,
#         returned_objects=["last_clicked", "center", "zoom"],
#         key="river_map"
#     )
#     st.caption("🖱️ Click on the map to select location. Pan/zoom will persist.")

#     center = map_data.get('center')
#     if isinstance(center, dict):
#         st.session_state.map_state['center'] = [center['lat'], center['lng']]
#     elif isinstance(center, (list, tuple)):
#         st.session_state.map_state['center'] = center
#     zoom = map_data.get('zoom')
#     if isinstance(zoom, (int, float)):
#         st.session_state.map_state['zoom'] = int(zoom)

#     click = map_data.get('last_clicked')
#     if click:
#         lat, lon = click['lat'], click['lng']
#         st.success(f"📍 Selected: {lat:.5f}, {lon:.5f}")
#         try:
#             resp = requests.get(
#                 f"https://geoglows.ecmwf.int/api/v2/getriverid/?lat={lat}&lon={lon}", timeout=10
#             )
#             resp.raise_for_status()
#             js = resp.json()
#             if 'river_id' in js:
#                 st.session_state.comid = int(js['river_id'])
#                 st.info(f"COMID: {st.session_state.comid}")
#             else:
#                 st.warning("⚠️ No river found; click nearer a watercourse.")
#         except Exception as e:
#             st.error(f"API error: {e}")

# # --- Latest Flow Tab ---
# with tab_retro:
#     if st.session_state.comid:
#         st.subheader(f"Latest Retrospective Flow (COMID {st.session_state.comid})")
#         df = geoglows.data.retrospective(st.session_state.comid)
#         df[df < 0] = 0
#         df.index = pd.to_datetime(df.index)
#         latest_date = df.index.max()
#         latest_flow = df.loc[latest_date].iloc[0]
#         col1, col2 = st.columns([1, 3])
#         col1.metric("📅 Date", str(latest_date.date()))
#         col1.metric("🔺 Latest Flow (m³/s)", f"{latest_flow:.2f}")
#         col1.download_button("⬇️ CSV", df.to_csv().encode(), file_name=f"{st.session_state.comid}_flow.csv")
#         fig = px.line(
#             df,
#             x=df.index,
#             y=df.columns[0],
#             labels={'x':'Date','y':'Flow (m³/s)'},
#             title="Flow Time Series"
#         )
#         fig.update_layout(template='plotly_white')
#         col2.plotly_chart(fig, use_container_width=True)
#     else:
#         st.info("🖱️ Select a location on the Map tab.")

# # --- Forecast Flow Tab ---
# with tab_fc:
#     if st.session_state.comid:
#         st.subheader(f"Forecast Flow (COMID {st.session_state.comid})")
#         fdf = geoglows.data.forecast(st.session_state.comid)
#         fdf.index = pd.to_datetime(fdf.index)
#         fdf[fdf < 0] = 0
#         st.dataframe(fdf, height=200)
#         st.download_button("⬇️ CSV", fdf.to_csv().encode(), file_name=f"{st.session_state.comid}_forecast.csv")
#         fig2 = px.line(
#             fdf,
#             x=fdf.index,
#             y=fdf.columns[0],
#             labels={'x':'DateTime','y':'Flow (m³/s)'},
#             title="Forecast Flow Time Series"
#         )
#         fig2.update_layout(template='plotly_white')
#         st.plotly_chart(fig2, use_container_width=True)
#     else:
#         st.info("🖱️ Select a location on the Map tab.")


# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 11 17:31:38 2025

Updated: Ensemble chart now includes explicit legend entries for all components: Previous Forecast Average, Max–Min Flow envelope, 25–75 Percentile band, Ensemble Average Flow, High-Resolution Forecast, and Return Period bands.
"""

import streamlit as st
from streamlit_folium import st_folium
import folium
import requests
import geoglows
import pandas as pd
import ee
import plotly.graph_objects as go
import plotly.express as px

# --- Streamlit Setup ---
st.set_page_config(page_title="🌊 GEOGloWS River Dashboard", layout="wide")
st.markdown("""
<style>
.big-title { font-size:2.5em; font-weight:bold; color:#0072B5; }
.description { font-size:1.1em; color:#444; margin-bottom:1em; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">🌊 GEOGloWS River Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Click on the map to pick a location and view latest flows and detailed ensemble forecasts.</div>', unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.header("⚙️ Settings")
selected_state = st.sidebar.text_input("State Name", "Madhya Pradesh")

# Secure GEE initialization using secrets
service_account = st.secrets["GEE_SERVICE_ACCOUNT"]
private_key = st.secrets["GEE_PRIVATE_KEY"]

credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
ee.Initialize(credentials)

state_fc = ee.FeatureCollection("projects/ee-shpp/assets/State_Boundary")
state_sel = state_fc.filter(ee.Filter.eq('STATE', selected_state))

# --- Compute Center once per state ---
def get_center(fc):
    coords = fc.geometry().centroid().coordinates().getInfo()
    return [coords[1], coords[0]]

if 'last_state' not in st.session_state or st.session_state.last_state != selected_state:
    st.session_state.map_state = {'center': get_center(state_sel), 'zoom': 7}
    st.session_state.last_state = selected_state
if 'comid' not in st.session_state:
    st.session_state.comid = None

# --- Tabs ---
tab_map, tab_latest, tab_fc = st.tabs(["🗺️ Map & AOI", "📄 Latest Flow", "📈 Ensemble Forecast"])

# --- Map Tab ---
with tab_map:
    m = folium.Map(location=st.session_state.map_state['center'], zoom_start=st.session_state.map_state['zoom'], control_scale=True)
    m.add_child(folium.LatLngPopup())
    folium.GeoJson(state_sel.getInfo(), name=selected_state, style_function=lambda f: {'color':'red','weight':3,'fill':False}).add_to(m)
    folium.LayerControl().add_to(m)
    data = st_folium(m, height=500, width=800, returned_objects=['last_clicked','center','zoom'], key='map')
    # persist view
    c = data.get('center'); z = data.get('zoom')
    if isinstance(c, dict): st.session_state.map_state['center']=[c['lat'],c['lng']]
    if isinstance(z,(int,float)): st.session_state.map_state['zoom']=int(z)
    click = data.get('last_clicked')
    if click:
        lat,lon=click['lat'],click['lng']
        st.success(f"📍 {lat:.5f}, {lon:.5f}")
        try:
            r=requests.get(f"https://geoglows.ecmwf.int/api/v2/getriverid/?lat={lat}&lon={lon}")
            r.raise_for_status(); js=r.json()
            if 'river_id' in js:
                st.session_state.comid=int(js['river_id']); st.info(f"Reach ID: {st.session_state.comid}")
            else: st.warning("No river found; click closer to a channel.")
        except Exception as e:
            st.error(f"API error: {e}")

# --- Latest Flow Tab ---
with tab_latest:
    if st.session_state.comid:
        cid = st.session_state.comid
        df = geoglows.data.retrospective(cid)
        df[df<0]=0; df.index=pd.to_datetime(df.index)
        ld=df.index.max(); lf=df.loc[ld].iloc[0]
        st.subheader(f"Latest Flow (Reach {cid})")
        c1,c2=st.columns([1,3])
        c1.metric("Date",ld.strftime("%Y-%m-%d")); c1.metric("Flow (m³/s)",f"{lf:.2f}")
        c1.download_button("Download CSV",df.to_csv().encode(),'latest.csv')
        fig=px.line(df,x=df.index,y=df.columns[0],labels={'x':'Date','y':'Flow (m³/s)'},title="Flow Series")
        fig.update_layout(template='plotly_white'); c2.plotly_chart(fig,use_container_width=True)
    else:
        st.info("Select a location on the Map tab.")

# --- Ensemble Forecast Tab ---
with tab_fc:
    if st.session_state.comid:
        cid=st.session_state.comid
        st.subheader(f"Ensemble Forecast (Reach {cid})")
        fdf=geoglows.data.forecast(cid); fdf[fdf<0]=0; fdf.index=pd.to_datetime(fdf.index)
        # climatology avg
        hist=geoglows.data.retrospective(cid); hist_avg=hist.mean().values[0]
        # return periods
        rp={'2‑yr':1980,'5‑yr':3058,'10‑yr':3771,'25‑yr':4673}
        rp_cols={'2‑yr':'#ffff66','5‑yr':'#ffd966','10‑yr':'#ff9999','25‑yr':'#ff4d4d'}
        fig=go.Figure()
        # previous forecast avg
        fig.add_trace(go.Scatter(x=fdf.index,y=[hist_avg]*len(fdf), mode='lines', line=dict(color='gold',dash='dot'), name='Previous Forecast Avg'))
        # individual ensembles
        for col in fdf.columns:
            fig.add_trace(go.Scatter(x=fdf.index,y=fdf[col], mode='lines', line=dict(color='gray',width=1,dash='dash'), showlegend=False, name='Forecast Ensemble'))
        # envelope & bands
        y_min=fdf.min(axis=1); y_max=fdf.max(axis=1)
        y25=fdf.quantile(0.25,axis=1); y75=fdf.quantile(0.75,axis=1); ymean=fdf.mean(axis=1)
        fig.add_trace(go.Scatter(x=y_max.index,y=y_max,mode='lines',line=dict(width=0),showlegend=False))
        fig.add_trace(go.Scatter(x=y_min.index,y=y_min,mode='lines',fill='tonexty',fillcolor='rgba(173,216,230,0.3)',name='Max & Min Flow'))
        fig.add_trace(go.Scatter(x=y75.index,y=y75,mode='lines',line=dict(width=0),showlegend=False))
        fig.add_trace(go.Scatter(x=y25.index,y=y25,mode='lines',fill='tonexty',fillcolor='rgba(144,238,144,0.3)',name='25–75 Percentile'))
        fig.add_trace(go.Scatter(x=ymean.index,y=ymean, mode='lines',line=dict(color='blue',width=2),name='Ensemble Average'))
        # high-res
        hr=[c for c in fdf.columns if 'high' in c.lower()]
        if hr:
            fig.add_trace(go.Scatter(x=fdf.index,y=fdf[hr[0]],mode='lines',line=dict(color='black',width=2),name='High-Res Forecast'))
        # return-period bands
        for label,thr in rp.items(): fig.add_hrect(y0=0,y1=thr,fillcolor=rp_cols[label],opacity=0.2, line_width=0, annotation_text=f"{label}: {thr}",annotation_position='top right')
        fig.update_layout(template='plotly_white',xaxis_title='Date',yaxis_title='Streamflow (m³/s)',legend=dict(orientation='h',y=-0.2))
        st.plotly_chart(fig,use_container_width=True)
        st.download_button("Download Forecast CSV",fdf.to_csv().encode(),'forecast.csv')
    else:
        st.info("Select a location on the Map tab.")
