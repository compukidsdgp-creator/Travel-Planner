import streamlit as st
import requests
import google.generativeai as genai
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# ---------------- CONFIG ----------------
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
mapkey=st.secrets["GOOGLE_API_KEY"]
GOOGLE_API_KEY = mapkey

model = genai.GenerativeModel("gemini-2.5-flash")

st.set_page_config(page_title="AI Travel Planner", layout="wide")

st.title("✈️ AI Travel Planner")

# ---------------- INPUT ----------------
with st.form("travel_form"):
    source = st.text_input("Enter Your Location")
    destination = st.text_input("Enter Destination")
    submit = st.form_submit_button("Plan My Trip")
    
if submit:
    st.session_state.source = source
    st.session_state.destination = destination
    st.session_state.show_result = True
    
if "show_result" not in st.session_state:
    st.session_state.show_result = False

if st.session_state.show_result:

    source = st.session_state.source
    destination = st.session_state.destination
    
    if destination == "":
        st.warning("Please enter destination")
    else:

        # ---------------- STEP 1: GET CURRENT LOCATION ----------------
        geolocator = Nominatim(user_agent="travel_app")
        current_location = geolocator.geocode(source)

        dest_location = geolocator.geocode(destination)

        if dest_location:

            # ---------------- STEP 2: DISTANCE CALCULATION ----------------
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={current_location.latitude},{current_location.longitude}&destinations={dest_location.latitude},{dest_location.longitude}&key={GOOGLE_API_KEY}"

            response = requests.get(url).json()

            distance = response["rows"][0]["elements"][0]["distance"]["text"]

            st.subheader("📍 Distance")
            st.write(f"Distance from your location: **{distance}**")
            
            # Create map centered between source & destination
            mid_lat = (current_location.latitude + dest_location.latitude) / 2
            mid_lon = (current_location.longitude + dest_location.longitude) / 2

            m = folium.Map(location=[mid_lat, mid_lon], zoom_start=5)

            # Add markers
            folium.Marker(
            [current_location.latitude, current_location.longitude],
            tooltip="Your Location",
            icon=folium.Icon(color="green")
            ).add_to(m)

            folium.Marker(
                [dest_location.latitude, dest_location.longitude],
                tooltip="Destination",
                icon=folium.Icon(color="red")
            ).add_to(m)
            
            # Draw line between points
            folium.PolyLine(
            locations=[
                [current_location.latitude, current_location.longitude],
                [dest_location.latitude, dest_location.longitude]
            ],
            color="blue",
            weight=5
            ).add_to(m)
            
            st.subheader("🗺️ Route Map")
            st_folium(m, width=700, height=500)
            

            # ---------------- STEP 3: TRAVEL OPTIONS ----------------
            travel_prompt = f"""
            Suggest best travel options from {source} to {destination}.
            Include approximate time and cost. keep it under 100 words.
            """

            travel_response = model.generate_content(travel_prompt)

            st.subheader("🚆 Travel Options")
            st.write(travel_response.text)

            # ---------------- STEP 4: HOTEL SUGGESTIONS ----------------
            hotel_prompt = f"""
            Suggest 5 good hotels in {destination} with price range and type.Also keep it under 100 words.
            """

            hotel_response = model.generate_content(hotel_prompt)
            
            with st.spinner("🏨 Finding best hotels..."):
              hotel_response = model.generate_content(hotel_prompt)

            st.subheader("🏨 Hotels")
            st.write(hotel_response.text)

            # ---------------- STEP 5: ITINERARY ----------------
            itinerary_prompt = f"""
            Create a 5-day travel itinerary for {destination}.
            Include places to visit. use bullet points.
            """

            itinerary_response = model.generate_content(itinerary_prompt)
            
            with st.spinner("🗓️ Creating your itinerary..."):
              itinerary_response = model.generate_content(itinerary_prompt)

            st.subheader("🗓️ 5-Day Itinerary")
            st.write(itinerary_response.text)

        else:
            st.error("Destination not found")
