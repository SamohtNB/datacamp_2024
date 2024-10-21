import streamlit as st
import pandas as pd
import pydeck as pdk
import geohash2 as geohash
from apify_client import ApifyClient
import numpy as np

# Load the cleaned dataset
cities_df = pd.read_csv('cleaned_cities_with_country.csv', sep=',')

# Convert city names, country names, and country codes to lowercase for easier case-insensitive lookup
cities_df['Name'] = cities_df['Name'].str.lower()
cities_df['Country'] = cities_df['Country'].str.lower()
cities_df['Country Code'] = cities_df['Country Code'].str.lower()

# Function to get latitude, longitude, and country code of a city from the cleaned dataset
def get_city_info(city_name, country_name=None):
    city_name = city_name.lower()
    if country_name:
        country_name = country_name.lower()
        city_data = cities_df[(cities_df['Name'] == city_name) & (cities_df['Country'] == country_name)]
    else:
        city_data = cities_df[cities_df['Name'] == city_name]
    
    if not city_data.empty:
        latitude = city_data.iloc[0]['Latitude']
        longitude = city_data.iloc[0]['Longitude']
        country_code = city_data.iloc[0]['Country Code']
        return latitude, longitude, country_code
    else:
        raise ValueError(f"City '{city_name}' not found in the dataset")

# Function to convert latitude and longitude to geohash
def get_geohash(lat, lon, precision=7):
    return geohash.encode(lat, lon, precision)

# Function to extract and format necessary event information
def extract_event_info(event):
    return {
        'name': event.get('name', 'N/A'),
        'description': event.get('description', 'N/A'),
        'date': f"{event.get('dateTitle', 'N/A')} {event.get('dateSubTitle', 'N/A')}",
        'location': f"{event.get('streetAddress', 'N/A')}, {event.get('addressLocality', 'N/A')}, {event.get('addressRegion', 'N/A')}, {event.get('postalCode', 'N/A')}, {event.get('addressCountry', 'N/A')}",
        'price': f"{event.get('offer', {}).get('price', 'N/A')} {event.get('offer', {}).get('priceCurrency', 'N/A')}",
        'genre': event.get('genreName', 'N/A'),
        'ticket_url': event.get('url', 'N/A')
    }

# Function to fetch events for a given city
def fetch_events_for_city(city_name, country_name=None, selected_genres=None):
    try:
        latitude, longitude, country_code = get_city_info(city_name, country_name)
        geo_hash = get_geohash(latitude, longitude)
        
        client = ApifyClient("apify_api_UNa2lFVCITf33GSeJTwKeWKskH3euP0T4jWR")

        run_input = {
            "maxItems": 100,
            "countryCode": country_code,
            "geoHash": geo_hash,
        }

        run = client.actor("lhotanova/ticketmaster-scraper").call(run_input=run_input)

        events = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            event = extract_event_info(item)

            if selected_genres and event['genre'].lower() not in [genre.lower() for genre in selected_genres]:
                continue
            
            events.append(event)

        return events
    except ValueError as e:
        st.error(e)
        return []

# Function to display unique events with the expander below the event name
def display_events(events):
    st.subheader("Events")
    seen_event_names = set()
    for event in events:
        if event['name'] not in seen_event_names:
            st.markdown(f"### {event['name']}")
            with st.expander("Show more information"):
                st.write(f"**Description**: {event['description']}")
                st.write(f"**Date**: {event['date']}")
                st.write(f"**Location**: {event['location']}")
                st.write(f"**Price**: {event['price']}")
                st.write(f"[Buy Tickets]({event['ticket_url']})")
            seen_event_names.add(event['name'])

# Streamlit layout
st.title("Events and Map")
st.write("Welcome! Explore events in your city.")

# Display a basic map centered at Paris
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=48.8566,
        longitude=2.3522,
        zoom=10,
        pitch=50,
    ),
    layers=[]
))

# Country selection with a placeholder option
country = st.selectbox("Select a country", ["Choose an option"] + list(np.sort(cities_df['Country'].unique())), index=0)

# City selection based on selected country with a placeholder option
if country != "Choose an option":
    city = st.selectbox("Select a city", ["Choose an option"] + list(np.sort(cities_df[cities_df['Country'] == country]['Name'].unique())), index=0)

# Selected genres
selected_genres = st.multiselect("Select event genres (optional):", 
                                  options=["Concert", "Theatre", "Music", "Arts & Theatre", "Family", "Comedy", "Cultural"])

# Fetch and display events for the selected city and country
if st.button("Show Events"):
    if country != "Choose an option" and city != "Choose an option":
        events = fetch_events_for_city(city, country, selected_genres)
        if events:
            display_events(events)
        else:
            st.write("No events found.")
    else:
        st.write("Please select a country and a city.")
