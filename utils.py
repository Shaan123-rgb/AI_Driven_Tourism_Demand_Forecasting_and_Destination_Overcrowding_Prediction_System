# utils.py — helper functions: data loading, preprocessing, formatting

import pandas as pd
import numpy as np
import streamlit as st
import os
import plotly.io as pio
import plotly.graph_objects as go

DATASET_PATH = "dataset/travel_data.csv"

# ─────────────────────────────────────────────────────────────────────────────
# Plotly styling — crisp white charts on the dark aurora background
# Call set_plotly_template() once at app startup (called from apply_styles)
# ─────────────────────────────────────────────────────────────────────────────

def set_plotly_template():
    
    clean = go.layout.Template()
    clean.layout = {
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor":  "#F8FAFC",
        "font": {"family": "DM Sans, -apple-system, sans-serif",
                 "color": "#0F172A", "size": 13},
        "title": {"font": {"size": 16, "weight": "bold", "color": "#0F172A"},
                  "x": 0.03, "xanchor": "left"},
        "xaxis": {"gridcolor": "#E2E8F0", "linecolor": "#CBD5E1",
                  "zerolinecolor": "#CBD5E1", "showgrid": True,
                  "tickfont": {"color": "#475569", "size": 11}},
        "yaxis": {"gridcolor": "#E2E8F0", "linecolor": "#CBD5E1",
                  "zerolinecolor": "#CBD5E1", "showgrid": True,
                  "tickfont": {"color": "#475569", "size": 11}},
        "colorway": ["#0D9488", "#2563EB", "#F59E0B", "#EF4444",
                     "#8B5CF6", "#06B6D4", "#EC4899", "#84CC16"],
        "legend": {"bgcolor": "rgba(248,250,252,0.95)",
                   "bordercolor": "#E2E8F0", "borderwidth": 1,
                   "font": {"color": "#334155", "size": 12}},
        "margin": {"l": 40, "r": 20, "t": 50, "b": 40},
        "hoverlabel": {"bgcolor": "#0F172A", "font": {"color": "#FFFFFF",
                       "family": "DM Sans, sans-serif", "size": 12},
                       "bordercolor": "#0D9488"},
    }
    pio.templates["tourism_clean"] = clean
    pio.templates.default = "tourism_clean"

def style_chart(fig):
    
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F8FAFC",
        font=dict(family="DM Sans, -apple-system, sans-serif",
                  color="#0F172A", size=13),
        xaxis=dict(gridcolor="#E2E8F0", linecolor="#CBD5E1", showgrid=True),
        yaxis=dict(gridcolor="#E2E8F0", linecolor="#CBD5E1", showgrid=True),
        legend=dict(bgcolor="rgba(248,250,252,0.95)",
                    bordercolor="#E2E8F0", borderwidth=1),
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# load the data
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_data(path: str = DATASET_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=["Date"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df

def save_uploaded_dataset(uploaded_file) -> str:
    os.makedirs("dataset", exist_ok=True)
    path = f"dataset/{uploaded_file.name}"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

# ─────────────────────────────────────────────────────────────────────────────
# Formatting / display helpers
# ─────────────────────────────────────────────────────────────────────────────

def fmt_number(n) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))

def risk_badge(label: str) -> str:
    icons = {"Low": "🟢 Low", "Medium": "🟡 Medium", "High": "🔴 High"}
    return icons.get(label, label)

# ─────────────────────────────────────────────────────────────────────────────
# Feature engineering helpers
# ─────────────────────────────────────────────────────────────────────────────

SEASON_MAP   = {"Winter": 0, "Spring": 1, "Summer": 2, "Monsoon": 3, "Autumn": 4}
WEATHER_MAP  = {"Sunny": 0, "Cloudy": 1, "Rainy": 2, "Snowy": 3, "Windy": 4, "Foggy": 5}
DOW_MAP      = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6}
BOOL_MAP     = {"Yes": 1, "No": 0, "TRUE": 1, "FALSE": 0}

def get_season(date) -> str:
    month = date.month
    if month in [11, 12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5, 6]:
        return "Summer"
    elif month in [7, 8, 9]:
        return "Monsoon"
    else:
        return "Festive"  # October

def encode_df(df: pd.DataFrame) -> pd.DataFrame:
    # light encoding for ml — returns a copy.
    d = df.copy()
    for col in d.select_dtypes(include="object").columns:
        d[col] = d[col].astype("category").cat.codes
    return d

def get_crowd_label(visitors: int, df: pd.DataFrame) -> str:
    # convert raw visitor count to low/medium/high relative to dataset.
    q33 = df["Visitors_Count"].quantile(0.33)
    q66 = df["Visitors_Count"].quantile(0.66)
    if visitors <= q33:
        return "Low"
    elif visitors <= q66:
        return "Medium"
    return "High"

# ─────────────────────────────────────────────────────────────────────────────
# Place & destination helpers
# ─────────────────────────────────────────────────────────────────────────────

DESTINATION_INFO: dict = {
    "Goa": {
        "desc": "Sun, sand & sea — India's party capital.",
        "peak": ["Winter"], "moderate": ["Festive", "Summer"], "off": ["Monsoon"],
        "off_perks": "Low costs, less crowded beaches, lush scenery.",
        "off_warnings": "Heavy rain, non-operational water sports, rough seas."
    },
    "Rajasthan": {
        "desc": "Land of kings, forts and golden deserts.",
        "peak": ["Winter", "Festive"], "moderate": ["Summer"], "off": ["Monsoon"],
        "off_perks": "Emerald green forts, luxury hotels at low prices.",
        "off_warnings": "Humidity and sudden downpours, high heat in early summer."
    },
    "Kerala": {
        "desc": "God's Own Country — backwaters & spices.",
        "peak": ["Winter"], "moderate": ["Festive", "Summer"], "off": ["Monsoon"],
        "off_perks": "Ayurveda healing, waterfalls in full glory.",
        "off_warnings": "Possibility of travel disruptions due to heavy rains."
    },
    "Himachal Pradesh": {
        "desc": "Snow peaks, trekking & hill stations.",
        "peak": ["Summer", "Winter"], "moderate": ["Festive"], "off": ["Monsoon"],
        "off_perks": "Cloud-covered peaks, mist, peaceful ambience.",
        "off_warnings": "Landslide risks during heavy rains, road blockages."
    },
    "Uttarakhand": {
        "desc": "Yoga capital, Char Dham & Rishikesh.",
        "peak": ["Summer", "Festive"], "moderate": ["Winter"], "off": ["Monsoon"],
        "off_perks": "Raging rivers, mystic foggy mountains, budget stays.",
        "off_warnings": "Heavy rainfall, river floods, landslide-prone areas."
    },
    "Agra": {
        "desc": "Home of the iconic Taj Mahal.",
        "peak": ["Winter", "Festive"], "moderate": ["Monsoon"], "off": ["Summer"],
        "off_perks": "Easy access to monuments with no long queues.",
        "off_warnings": "Extremely high temperatures (up to 45°C), dehydrating heat."
    },
    "Ladakh": {
        "desc": "High-altitude desert with stunning landscapes.",
        "peak": ["Summer"], "moderate": ["Festive"], "off": ["Winter", "Monsoon"],
        "off_perks": "Unique photography opportunities of snowy terrain.",
        "off_warnings": "Freezing temperatures (-20°C), closed mountain passes."
    },
    "Andaman": {
        "desc": "Crystal clear waters & coral reefs.",
        "peak": ["Winter"], "moderate": ["Festive", "Summer"], "off": ["Monsoon"],
        "off_perks": "Extremely calm island vibe, rainforest beauty.",
        "off_warnings": "High ferry cancellation risks due to weather, limited sea sports."
    },
    "Varanasi": {
        "desc": "One of the world's oldest living cities.",
        "peak": ["Winter", "Festive"], "moderate": ["Monsoon"], "off": ["Summer"],
        "off_perks": "Peaceful river banks, late-night spiritual calm.",
        "off_warnings": "Intense heat and humidity, exhausting daytime travel."
    },
    "Mysore": {
        "desc": "City of palaces, sandalwood & silk.",
        "peak": ["Festive", "Winter"], "moderate": ["Summer"], "off": ["Monsoon"],
        "off_perks": "Lush royal gardens, rain-washed heritage structures.",
        "off_warnings": "Moderate rainfall, potential humidity."
    },
}

TRAVEL_TIPS: list = [
    "📅 Book tickets 4-6 weeks in advance for peak season.",
    "💊 Carry a basic first-aid kit and any prescription medicines.",
    "📲 Download offline maps before travelling to remote areas.",
    "🧴 Apply sunscreen and stay hydrated, especially in summer.",
    "🔒 Keep digital and physical copies of all ID documents.",
    "💰 Carry some local cash; many places don't accept cards.",
    "🌦 Check weather forecasts 3-4 days before your trip.",
    "🚗 Book transportation ahead for holiday weekends.",
    "🍽 Try local street food at hygienic, popular stalls.",
    "📸 Respect photography rules at religious sites.",
]

BUDGET_PLANS: dict = {
    "Beach":  {
        "places": ["Goa", "Andaman", "Lakshadweep", "Varkala", "Puri"],
        "tips": "Travel off-peak (Apr–Jun) for cheaper hotels. Use local buses.",
    },
    "Hill":   {
        "places": ["Shimla", "Manali", "Ooty", "Munnar", "Darjeeling"],
        "tips": "Book accommodation near the ridge for best views.",
    },
    "City":   {
        "places": ["Mumbai", "Delhi", "Bangalore", "Kolkata", "Chennai"],
        "tips": "Use metro rail to cut transport costs significantly.",
    },
    "Heritage": {
        "places": ["Rajasthan", "Agra", "Hampi", "Khajuraho", "Pattadakal"],
        "tips": "Combo tickets for multiple monuments save 20-30%.",
    },
    "Adventure": {
        "places": ["Rishikesh", "Ladakh", "Spiti", "Coorg", "Meghalaya"],
        "tips": "Book group packages — costs drop by 40% vs solo.",
    },
    "Wildlife": {
        "places": ["Jim Corbett", "Ranthambore", "Kaziranga", "Bandipur", "Sundarbans"],
        "tips": "Early morning safaris have better sightings.",
    },
}

CHATBOT_KB: list = [
    {
        "intent": "destinations_goa",
        "questions": ["What is the best time to visit Goa?", "Tell me about Goa", "Goa travel tips", "When should I go to Goa?", "Beaches in India"],
        "answer": "Goa is famous for its beaches, nightlife, and Portuguese heritage. The best time to visit is November to February — cool, dry, and festive!"
    },
    {
        "intent": "destinations_rajasthan",
        "questions": ["Tell me about Rajasthan", "Rajasthan travel info", "Best time to visit Rajasthan", "Rajasthan forts"],
        "answer": "Rajasthan is the land of kings, forts, and deserts. Visit between October and March for pleasant weather."
    },
    {
        "intent": "destinations_kerala",
        "questions": ["Tell me about Kerala", "Kerala backwaters", "When to visit Kerala", "Kerala travel tips"],
        "answer": "Kerala is 'God's Own Country', offering serene backwaters, Ayurveda, and lush greenery. Best visited from September to March."
    },
    {
        "intent": "destinations_himachal",
        "questions": ["Tell me about Himachal Pradesh", "Himachal snow", "Best time for Himachal", "Shimla and Manali", "Mountains"],
        "answer": "Himachal Pradesh is home to stunning hill stations like Manali, Shimla, and Spiti. Snow lovers should visit from December to February."
    },
    {
        "intent": "budget_planning",
        "questions": ["How do I plan a budget trip?", "I want a cheap trip", "Budget travel tips", "How much money do I need?", "Cost splitting", "Save money"],
        "answer": "Start with a clear budget. A solid split is: 40% stay, 30% transport, 20% food, and 10% experiences. Travel off-peak and use local transport to save more!"
    },
    {
        "intent": "overcrowding_avoidance",
        "questions": ["How to avoid crowds?", "Is it too crowded?", "I want a peaceful trip", "Crowd avoidance tips", "Offbeat travel", "Less tourists"],
        "answer": "To avoid crowds: travel on weekdays instead of weekends, visit during shoulder seasons, and try to reach popular attractions early in the morning."
    },
    {
        "intent": "packing_tips",
        "questions": ["What should I pack?", "Packing list for India", "Essentials to carry", "Luggage advice", "What clothes to wear"],
        "answer": "Pack light! Carry basics: ID proof/passport, weather-appropriate clothing, comfortable walking shoes, a power bank, sunscreen, and a basic first-aid kit."
    },
    {
        "intent": "visa_info",
        "questions": ["Do I need a visa for India?", "India e-Visa", "How to get a visa", "Tourist visa rules"],
        "answer": "For international tourists, India offers an e-Visa for citizens of 167+ countries. You can apply easily at indianvisaonline.gov.in."
    },
    {
        "intent": "food_safety",
        "questions": ["Is street food safe?", "What to eat in India", "Food tips", "Drinking water in India", "Indian cuisine", "Spicy food"],
        "answer": "India has incredibly diverse cuisine. Try local dhabas for authentic food, but stick to busy stalls where food is hot. Always drink bottled or filtered water."
    },
    {
        "intent": "transportation",
        "questions": ["How to travel around India?", "Trains in India", "Transport options", "Booking flights and buses", "IRCTC", "Getting around"],
        "answer": "India has a massive network of trains, buses, flights, and cabs. IRCTC is the official platform for train bookings, which are highly recommended for long distances."
    },
    {
        "intent": "general_safety",
        "questions": ["Is India safe for tourists?", "Safety tips", "Solo travel safety", "Women safety in India", "Is it dangerous?"],
        "answer": "India is generally safe for tourists. Keep your belongings secure in crowded places, use registered or app-based taxis (like Uber/Ola), and share your itinerary with family."
    },
    {
        "intent": "greeting",
        "questions": ["Hello", "Hi", "Hey", "Good morning", "Who are you?", "Help", "What can you do?", "Start"],
        "answer": "Hello! 👋 I'm your AI travel assistant. Ask me about destinations, budgets, tips, packing, safety, or just say the name of a state to get quick stats!"
    }
]
