import streamlit as st
import pandas as pd
import pydeck as pdk
import geohash2 as geohash
from apify_client import ApifyClient
from opencage.geocoder import OpenCageGeocode
import numpy as np
import time

# Initialize the ApifyClient with your API token
client = ApifyClient("apify_api_UNa2lFVCITf33GSeJTwKeWKskH3euP0T4jWR")

# Initialize the OpenCage Geocode client with your API key
api_key = 'faa7dd93e4254cdcacb7132ee09118b9'
geocoder = OpenCageGeocode(api_key)

# Pre-defined coordinates for Disneyland Paris
DISNEYLAND_COORDINATES = (48.8674, 2.7836)

# Load the cleaned dataset
cities_df = pd.read_csv('cleaned_cities_with_country.csv', sep=',')

# Convert city names, country names, and country codes to lowercase for easier case-insensitive lookup
cities_df['Name'] = cities_df['Name'].str.lower()
cities_df['Country'] = cities_df['Country'].str.lower()
cities_df['Country Code'] = cities_df['Country Code'].str.lower()

# Function to geocode an address with OpenCage or handle special cases like Disneyland
def geocode_address(address, event_name):
    # Check if the event is related to Disneyland Paris
    if 'disney' in event_name.lower():
        return DISNEYLAND_COORDINATES
    try:
        result = geocoder.geocode(address)
        if result and len(result):
            return result[0]['geometry']['lat'], result[0]['geometry']['lng']
        else:
            return None, None
    except Exception as e:
        print(f"Error occurred: {e}")
        time.sleep(1)
        return None, None

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

# Function to extract and format necessary event information
def extract_event_info(event):
    return {
        'name': event.get('name', 'N/A'),
        'description': event.get('description', 'N/A'),
        'date': f"{event.get('dateTitle', 'N/A')} {event.get('dateSubTitle', 'N/A')}",
        'location': f"{event.get('streetAddress', 'N/A')}, {event.get('addressLocality', 'N/A')}, {event.get('addressRegion', 'N/A')}, {event.get('postalCode', 'N/A')}, {event.get('addressCountry', 'N/A')}",
        'price': f"{event.get('offer', {}).get('price', 'N/A')} {event.get('offer', {}).get('priceCurrency', 'N/A')}",
        'genre': event.get('genreName', 'N/A'),
        'ticket_url': event.get('url', 'N/A'),
        'streetAddress': event.get('streetAddress', 'N/A'),
        'addressLocality': event.get('addressLocality', 'N/A'),
        'addressRegion': event.get('addressRegion', 'N/A'),
        'postalCode': event.get('postalCode', 'N/A'),
        'addressCountry': event.get('addressCountry', 'N/A')
    }

# Function to fetch events for a given city and geocode their addresses
def fetch_events_for_city(city_name, country_name=None, selected_genres=None):
    try:
        latitude, longitude, country_code = get_city_info(city_name, country_name)
        geo_hash = geohash.encode(latitude, longitude)

        run_input = {
            "maxItems": 100,
            "countryCode": country_code,
            "geoHash": geo_hash,
        }

        run = client.actor("lhotanova/ticketmaster-scraper").call(run_input=run_input)

        events = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            event = extract_event_info(item)

            # Filter by genres
            if selected_genres and event['genre'].lower() not in [genre.lower() for genre in selected_genres]:
                continue

            # Concatenate the full address
            full_address = f"{event['streetAddress']}, {event['addressLocality']}, {event['addressRegion']}, {event['postalCode']}, {event['addressCountry']}"

            # Geocode the event's address
            lat, lon = geocode_address(full_address, event['name'])
            event['latitude'] = lat
            event['longitude'] = lon

            events.append(event)

        return events
    except ValueError as e:
        st.error(e)
        return []

# Function to display events with their geocoded locations on a map with hover tooltips
def display_events(events):
    st.subheader("Events")
    map_data = pd.DataFrame(
        [{'latitude': event['latitude'], 'longitude': event['longitude'], 'name': event['name']} for event in events if event['latitude'] and event['longitude']],
        columns=['latitude', 'longitude', 'name']
    )

    if not map_data.empty:
        # Define the pydeck layer with tooltips for event names
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=map_data,
            get_position='[longitude, latitude]',
            get_radius=200,
            get_color=[255, 0, 0],
            pickable=True
        )

        # Create tooltip object
        tooltip = {"html": "<b>Event Name:</b> {name}", "style": {"color": "white"}}

        # Display the map with tooltips
        view_state = pdk.ViewState(latitude=48.8566, longitude=2.3522, zoom=10, pitch=50)
        r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
        st.pydeck_chart(r)

    for event in events:
        if event['latitude'] and event['longitude']:
            st.markdown(f"### {event['name']}")
            with st.expander("Show more information"):
                st.write(f"**Description**: {event['description']}")
                st.write(f"**Date**: {event['date']}")
                st.write(f"**Location**: {event['location']}")
                st.write(f"**Price**: {event['price']}")
                st.write(f"**Coordinates**: Latitude = {event['latitude']}, Longitude = {event['longitude']}")
                st.write(f"[Buy Tickets]({event['ticket_url']})")

# Streamlit layout with customizations
# Add logo
col1, col2, col3 = st.columns([1, 2, 1])  # Three columns for centering
with col2:
    st.markdown("<h1 style='text-align: center;'>Plan It Now</h1>", unsafe_allow_html=True)

# Logo centered
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", width=300)  # Adjust the path if needed

# Phrase or accroche centered
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<h3 style='text-align: center;'>Find what you can do today!</h3>", unsafe_allow_html=True)

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
