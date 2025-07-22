import streamlit as st
import folium
import requests
import geoglows
import pandas as pd
import ee
import plotly.graph_objects as go
import plotly.express as px
from streamlit_folium import st_folium, folium_static


# Secure GEE initialization using secrets
service_account = st.secrets["GEE_SERVICE_ACCOUNT"]
private_key = st.secrets["GEE_PRIVATE_KEY"]

credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
ee.Initialize(credentials)
# --- Streamlit Setup ---
st.set_page_config(page_title="🌊 GEOGloWS River Dashboard", layout="wide")
st.markdown("""
<style>
.big-title { font-size:2.5em; font-weight:bold; color:#0072B5; }
.description { font-size:1.1em; color:#444; margin-bottom:1em; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="big-title">🌊 GEOGloWS River Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Click on the map to pick a location and have the River ID fetched automatically.</div>', unsafe_allow_html=True)

# --- Sidebar: state selection ---
st.sidebar.header("⚙️ Settings")
selected_state = st.sidebar.text_input("State Name", "Madhya Pradesh")


state_fc = ee.FeatureCollection("projects/ee-shpp/assets/State_Boundary")
state_sel = state_fc.filter(ee.Filter.eq('STATE', selected_state))

@st.cache_data
def get_center(_fc):
    coords = _fc.geometry().centroid().coordinates().getInfo()
    return [coords[1], coords[0]]

center = get_center(state_sel)

# initialize session state
if 'comid' not in st.session_state:
    st.session_state.comid = None

# --- Tabs ---
tab_map, tab_latest, tab_fc = st.tabs(["🗺️ Map & AOI", "📄 Latest Flow", "📈 Ensemble Forecast"])

with tab_map:
    st.markdown("### Map & Automatic River ID Lookup")
    m = folium.Map(location=center, zoom_start=7, control_scale=True)
    folium.GeoJson(
        state_sel.getInfo(),
        name=selected_state,
        style_function=lambda f: {'color':'red','weight':3,'fill':False}
    ).add_to(m)
    folium.LayerControl().add_to(m)
    m.add_child(folium.LatLngPopup())
    # capture clicks
    map_data = st_folium(m, height=500, width=800)

    click = map_data.get("last_clicked")
    if click:
        lat, lon = click["lat"], click["lng"]
        st.success(f"📍 You clicked: {lat:.5f}, {lon:.5f}")
        try:
            r = requests.get(
                f"https://geoglows.ecmwf.int/api/v2/getriverid/?lat={lat}&lon={lon}"
            )
            r.raise_for_status()
            js = r.json()
            if "river_id" in js:
                st.session_state.comid = int(js["river_id"])
                st.info(f"Reach ID: {st.session_state.comid}")
            else:
                st.warning("No river found; click closer to a channel.")
        except Exception as e:
            st.error(f"API error: {e}")

with tab_latest:
    if st.session_state.comid:
        cid = st.session_state.comid
        df = geoglows.data.retrospective(cid)
        df[df < 0] = 0
        df.index = pd.to_datetime(df.index)
        last_date = df.index.max()
        last_flow = df.loc[last_date].iloc[0]

        st.subheader(f"Latest Flow (Reach {cid})")
        c1, c2 = st.columns([1, 3])
        c1.metric("Date", last_date.strftime("%Y-%m-%d"))
        c1.metric("Flow (m³/s)", f"{last_flow:.2f}")
        c1.download_button("Download CSV", df.to_csv().encode(), "latest.csv")

        fig = px.line(
            df,
            x=df.index,
            y=df.columns[0],
            labels={'x': 'Date', 'y': 'Flow (m³/s)'},
            title="Flow Series"
        )
        fig.update_layout(template='plotly_white')
        c2.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Click on the Map tab to choose a location first.")

with tab_fc:
    if st.session_state.comid:
        cid = st.session_state.comid
        st.subheader(f"Ensemble Forecast (Reach {cid})")
        fdf = geoglows.data.forecast(cid)
        fdf[fdf < 0] = 0
        fdf.index = pd.to_datetime(fdf.index)

        hist = geoglows.data.retrospective(cid)
        hist_avg = hist.mean().values[0]

        rp = {'2‑yr': 1980, '5‑yr': 3058, '10‑yr': 3771, '25‑yr': 4673}
        rp_cols = {
            '2‑yr': '#ffff66',
            '5‑yr': '#ffd966',
            '10‑yr': '#ff9999',
            '25‑yr': '#ff4d4d'
        }

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fdf.index,
            y=[hist_avg] * len(fdf),
            mode='lines',
            line=dict(color='gold', dash='dot'),
            name='Previous Forecast Avg'
        ))
        for c in fdf.columns:
            fig.add_trace(go.Scatter(
                x=fdf.index,
                y=fdf[c],
                mode='lines',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=False
            ))
        y_min = fdf.min(axis=1); y_max = fdf.max(axis=1)
        y25 = fdf.quantile(0.25, axis=1); y75 = fdf.quantile(0.75, axis=1)
        ymean = fdf.mean(axis=1)

        fig.add_trace(go.Scatter(x=y_max.index, y=y_max,
                                 mode='lines', line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=y_min.index, y=y_min,
                                 mode='lines', fill='tonexty',
                                 fillcolor='rgba(173,216,230,0.3)',
                                 name='Max & Min Flow'))
        fig.add_trace(go.Scatter(x=y75.index, y=y75,
                                 mode='lines', line=dict(width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=y25.index, y=y25,
                                 mode='lines', fill='tonexty',
                                 fillcolor='rgba(144,238,144,0.3)',
                                 name='25–75 Percentile'))
        fig.add_trace(go.Scatter(x=ymean.index, y=ymean,
                                 mode='lines',
                                 line=dict(color='blue', width=2),
                                 name='Ensemble Average'))

        hr = [c for c in fdf.columns if 'high' in c.lower()]
        if hr:
            fig.add_trace(go.Scatter(
                x=fdf.index,
                y=fdf[hr[0]],
                mode='lines',
                line=dict(color='black', width=2),
                name='High-Res Forecast'
            ))

        for label, thr in rp.items():
            fig.add_hrect(
                y0=0, y1=thr,
                fillcolor=rp_cols[label],
                opacity=0.2,
                line_width=0,
                annotation_text=f"{label}: {thr}",
                annotation_position='top right'
            )

        fig.update_layout(
            template='plotly_white',
            xaxis_title='Date',
            yaxis_title='Streamflow (m³/s)',
            legend=dict(orientation='h', y=-0.2)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.download_button("Download Forecast CSV", fdf.to_csv().encode(), "forecast.csv")
    else:
        st.info("Click on the Map tab to choose a location first.")
