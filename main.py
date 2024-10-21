import streamlit as st
import pandas as pd
import numpy as np
from API_Event import fetch_events_for_city

@st.cache_data
def load_data():
    return pd.read_csv('cleaned_cities_with_country.csv')

st.set_page_config(page_title="Localisation de l'utilisateur",
                    page_icon="./img/logo-planitnow.png",
                    layout="wide"
                    )

def display():
    st.title("projet DataCamp 2024")
    st.logo("./img/logo-planitnow.png")
    data = load_data()
    country = st.selectbox("Select a country", np.sort(data['Country'].unique()), index = None)
    if country:
        city = st.selectbox("Select a city", np.sort(data[data['Country'] == country]['Name']), index = None)
        if city!= None:
            st.write(f"Vous avez sélectionné la ville de {city}, {country}")
            while st.spinner("Recherche des événements en cours..."):
                events = fetch_events_for_city(city, country)
            if events != None:
                for event in events:
                    st.write(event)
            else:
                st.warning(f"Aucun événement trouvé pour la ville {city}, {country}")

    
        
if __name__ == "__main__":
    display()
    