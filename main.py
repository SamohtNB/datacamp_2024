#this is the main file that will run the program

import streamlit as st
import requests
import pandas as pd
import pydeck as pdk

def get_user_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        location = data['loc'].split(',')
        latitude = float(location[0])
        longitude = float(location[1])
        return latitude, longitude
    except Exception as e:
        st.error(f"Impossible d'obtenir la localisation : {e}")
        return None, None

# Obtenir les coordonnées de l'utilisateur
latitude, longitude = get_user_location()

# Vérifier si les coordonnées ont été obtenues avec succès
if latitude is not None and longitude is not None:
    # Créer un DataFrame pour la localisation
    df = pd.DataFrame({
        'lat': [latitude],
        'lon': [longitude]
    })

    # Configuration de la carte
    st.write(f"Carte de votre emplacement : ({latitude}, {longitude})")
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=latitude,
            longitude=longitude,
            zoom=12,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=200,
            ),
        ],
    ))
else:
    st.write("Impossible d'afficher la carte. Les coordonnées ne sont pas disponibles.")
    
if __name__ == "__main__":
    st.set_page_config(page_title="Localisation de l'utilisateur",
                       page_icon="./img/logo-planitnow.png",
                       layout="wide"
                       )
    get_user_location()