import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import warnings
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

st.set_page_config(page_title="USA_sales", page_icon=":chart_with_upwards_trend:", layout="wide")
st.title('🌟 Tableau de Bord des Ventes - USA')

def load_data():
    uploaded_file = st.file_uploader("Choisissez un fichier CSV ou Excel", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                st.error("Format de fichier non pris en charge.")
                return None
        except FileNotFoundError:
            st.error("Le fichier est introuvable.")
            return None
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
            return None
    else:
        # Charger le fichier par défaut si aucun fichier n'est téléchargé
        df = pd.read_csv('donnees_ventes_etudiants.csv')

    state_dict = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'Californie', 'NC': 'Caroline du Nord', 'SC': 'Caroline du Sud',
        'CO': 'Colorado', 'CT': 'Connecticut', 'ND': 'Dakota du Nord',
        'SD': 'Dakota du Sud', 'DE': 'Delaware', 'FL': 'Floride',
        'GA': 'Georgie', 'HI': 'Hawaï', 'ID': 'Idaho', 'IL': 'Illinois',
        'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky',
        'LA': 'Louisiane', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachussetts',
        'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
        'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
        'NJ': 'New Jersey', 'NY': 'New York', 'NM': 'Nouveau-Mexique', 'OH': 'Ohio',
        'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvanie', 'RI': 'Rhode Island',
        'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
        'VA': 'Virginie', 'WV': 'Virginie ociidentale', 'WA': 'Washington',
        'WI': 'Wisconsin', 'WY': 'Wyoming'
    }

    if 'State' in df.columns:
        df['State Complet'] = df['State'].map(state_dict)
    else:
        st.warning("'State' n'est pas présent dans les colonnes du fichier.")

    if 'order_date' in df.columns:
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
    else:
        st.warning("'order_date' n'est pas présent dans les colonnes du fichier.")

    columns_to_keep = ['order_date', 'Region', 'State Complet', 'County', 'City', 'status', 'total', 'cust_id', 'order_id', 'full_name', 'age', 'Gender', 'category']
    available_columns = [col for col in columns_to_keep if col in df.columns]
    df = df[available_columns]

    if 'total' in df.columns:
        df['total'] = df['total'].astype('float32')
    if 'age' in df.columns:
        df['age'] = df['age'].astype('int8')

    return df

df = load_data()

if df is None:
    st.warning("Veuillez télécharger un fichier pour afficher les données.")
else:
    st.markdown("""
        <style>
        .main { background-color: #f0f2f6; }
        .stButton > button { background-color: #4CAF50; color:white; }
        .stMetric { font-size: 24px; font-weight: bold; color: #000; }
        </style>
        """, unsafe_allow_html=True)

    start_date = pd.to_datetime(df['order_date']).min()
    end_date = pd.to_datetime(df['order_date']).max()

    col1, col2 = st.columns(2)
    with col1:
        date1 = pd.to_datetime(st.date_input("Date de debut", start_date, min_value=start_date, max_value=end_date))
        
    with col2:
        date2 = pd.to_datetime(st.date_input("Date de fin", end_date, min_value=start_date, max_value=end_date))

    filtered_data = df[(df['order_date'] >= date1) & (df['order_date'] <= date2)]

    st.sidebar.header("Filtres des zones")
    region = st.sidebar.multiselect("Sélectionnez une Région", df['Region'].unique())
    state = st.sidebar.multiselect("Sélectionnez un État", df[df['Region'].isin(region)]['State Complet'].unique())
    country = st.sidebar.multiselect("Sélectionnez un Pays", df['County'].unique())
    city = st.sidebar.multiselect("Sélectionnez une Ville", df[df['State Complet'].isin(state)]['City'].unique())

    if region:
        filtered_data = filtered_data[filtered_data['Region'].isin(region)]
    if state:
        filtered_data = filtered_data[filtered_data['State Complet'].isin(state)]
    if country:
        filtered_data = filtered_data[filtered_data['County'].isin(country)]
    if city:
        filtered_data = filtered_data[filtered_data['City'].isin(city)]

    st.sidebar.header("Statut des Commandes")
    status = st.sidebar.multiselect("Statut de la commande", df['status'].unique())
    if status:
        filtered_data = filtered_data[filtered_data['status'].isin(status)]

    st.subheader("Indicateurs clés de performance (KPI)")
    st.write("")

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Nombre total de Ventes", f"${filtered_data['total'].sum():,.2f}")
    col2.metric(" Nombre distinct de Clients", filtered_data['cust_id'].nunique())
    col3.metric("📦 Nombre total de Commandes", filtered_data['order_id'].nunique())

    st.subheader("Visualisations des ventes")

    col1, col2 = st.columns([3, 1])  

    with col1:
        sales_category = filtered_data.groupby('category')['total'].sum().reset_index()
        sales_category = sales_category.sort_values(by='total', ascending=False)
        fig_cat = px.bar(
            sales_category, 
            x='category', 
            y='total', 
            color='category', 
            title="Ventes par Catégorie", 
            labels={"total": "Total des Ventes ($)"},
            template='plotly_white'
        )

        fig_cat.update_traces(texttemplate='%{y:,.2f}', textposition='outside')
        fig_cat.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        fig_cat.update_layout(title_x=0.5, title_font_size=20)
        fig_cat.update_layout(showlegend=False)

        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        fig_donut = px.pie(filtered_data, names='Region', values='total', 
                           title='Répartition des Ventes par Région', 
                           color_discrete_sequence=px.colors.sequential.RdBu)

        fig_donut.update_traces(textposition='inside', textinfo='percent+label', hole=0.6)
        fig_donut.update_layout(width=2000)

        st.plotly_chart(fig_donut, use_container_width=True)

    st.subheader("Top 10 des Meilleurs Clients")
    top_clients = filtered_data.groupby('full_name')['total'].sum().nlargest(10).reset_index()
    fig_top_clients = px.bar(top_clients, x='full_name', y='total', 
                             color='full_name', title="Top 10 Clients", 
                             labels={"total": "Total des Ventes ($)", "full_name": "Client"},
                             template='plotly_white')
    fig_top_clients.update_layout(title_x=0.5, title_font_size=20)
    st.plotly_chart(fig_top_clients, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Répartition de l'âge des Clients")
        fig_age = px.histogram(filtered_data, x='age', nbins=20, title="Distribution de l'âge des clients", 
                            template='seaborn')
        fig_age.update_layout(title_x=0.5, title_font_size=20)
        st.plotly_chart(fig_age, use_container_width=True)

    with col2:
        st.subheader("Répartition par Genre")
        sales_gender = filtered_data.groupby('Gender')['total'].sum().reset_index()
        sales_gender = sales_gender.sort_values(by='total', ascending=False)
        fig_gender = px.bar(
            sales_gender, 
            x='Gender', 
            y='total', 
            color='Gender', 
            title="Ventes par Genre", 
            labels={"total": "Total des Ventes ($)", "Gender": "Genre"},
            template='plotly_white')

        fig_gender.update_traces(texttemplate='%{y:,.2f}', textposition='inside')
        fig_gender.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        st.plotly_chart(fig_gender, use_container_width=True)

    st.subheader("Ventes par Mois")

    filtered_data['Month-Year'] = pd.to_datetime(filtered_data['order_date']).dt.to_period('M').dt.to_timestamp()
    sales_per_month = filtered_data.groupby('Month-Year')['total'].sum().reset_index()
    sales_per_month['Month-Year'] = sales_per_month['Month-Year'].dt.strftime('%B %Y')

    fig_sales = px.line(sales_per_month, x='Month-Year', y='total', 
                        title="Ventes mensuelles", labels={"total": "Total des Ventes ($)", "Month-Year": "Mois-Année"}, 
                        template='plotly_dark')

    fig_sales.update_xaxes(tickangle=45)

    st.plotly_chart(fig_sales, use_container_width=True)

    st.subheader("Carte des Ventes par État")
    @st.cache_data
    def get_location(address):
        try:
            geolocator = Nominatim(user_agent="my_streamlit_app", timeout=10)
            location = geolocator.geocode(f"{address}, United States")
            if location:
                return location.latitude, location.longitude
            return None
        except GeocoderTimedOut:
            return None

    @st.cache_data
    def prepare_map_data(df):
        state_sales = df.groupby('State Complet')['total'].sum().reset_index()
        coordinates = []
        for state in state_sales['State Complet']:
            coords = get_location(state)
            if coords:
                coordinates.append({
                    'state': state,
                    'lat': coords[0],
                    'lon': coords[1],
                    'sales': state_sales[state_sales['State Complet'] == state]['total'].iloc[0]
                })
        
        return coordinates

    map_data = prepare_map_data(filtered_data)

    if map_data:
        fig_map = go.Figure()
        fig_map.add_trace(go.Scattermapbox(
            lat=[d['lat'] for d in map_data],
            lon=[d['lon'] for d in map_data],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=[min(max(sales/1000, 8), 20) for sales in [d['sales'] for d in map_data]],
                color=[d['sales'] for d in map_data],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Ventes ($)")
            ),
            text=[f"État: {d['state']}<br>Ventes: ${d['sales']:,.2f}" for d in map_data],
            hoverinfo='text'
        ))

        fig_map.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=37.0902, lon=-95.7129),
                zoom=3
            ),
            margin={"r":0,"t":0,"l":0,"b":0},
            height=600
        )

        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.error("Impossible de charger les données de la carte")
