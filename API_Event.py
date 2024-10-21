import pandas as pd
import geohash2 as geohash
from apify_client import ApifyClient

# Load the dataset with the correct separator
cities_df = pd.read_csv('geonames-all-cities-with-a-population-500.csv', sep=';')

# Function to get latitude, longitude, and country code of a city from the dataset
def get_city_info(city_name, country_name=None):
    if country_name:
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
        'ticket_url': event.get('url', 'N/A')
    }

def print_event_info(event_info):
    print(f"Event Name: {event_info['name']}")
    print(f"Description: {event_info['description']}")
    print(f"Date & Time: {event_info['date']}")
    print(f"Location: {event_info['location']}")
    print(f"Price: {event_info['price']}")
    print(f"Ticket URL: {event_info['ticket_url']}")
    print("-" * 50)  # Separator for readability

# Function to fetch events for a given city
def fetch_events_for_city(city_name, country_name=None):
    try:
        # Get the latitude, longitude, and country code for the city
        latitude, longitude, country_code = get_city_info(city_name, country_name)
        
        # Convert latitude and longitude to geohash
        geo_hash = get_geohash(latitude, longitude)
        
        # Initialize the ApifyClient with your Apify API token
        client = ApifyClient("apify_api_dOzn3RQKJXRzA0qImhNEWs1otQ5lau0JMH4t")

        # Prepare the Actor input using the geohash and country code
        run_input = {
            "maxItems": 10,  # Limit to 10 items
            "countryCode": country_code,
            "geoHash": geo_hash,
        }

        # Run the Actor and wait for it to finish
        run = client.actor("lhotanova/ticketmaster-scraper").call(run_input=run_input)

        # Iterate over events and print formatted information
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            event_info = extract_event_info(item)
            print_event_info(event_info)

    except ValueError as e:
        print(e)

# Example usage
city_name = input("Enter the city name: ")
country_name = input("Enter the country name (or leave blank for automatic lookup): ") or None

fetch_events_for_city(city_name, country_name)
