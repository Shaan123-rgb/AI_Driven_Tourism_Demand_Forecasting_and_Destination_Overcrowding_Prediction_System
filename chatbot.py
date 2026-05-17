

import os
import streamlit as st
from groq import Groq
import pandas as pd
from utils import fmt_number, TRAVEL_TIPS, CHATBOT_KB
import random

# ==========================================
# 2. TIER 1: DATASET LOGIC
# ==========================================

def dataset_match(query: str, df: pd.DataFrame) -> str:
    # check if the query specifically asks about a state in our dataset.
    q = query.lower().strip()
    if df.empty:
        return ""
        
    for state in df["Location_State"].unique():
        if state.lower() in q:
            sub = df[df["Location_State"] == state]
            avg_v = int(sub["Visitors_Count"].mean())
            places = sub["Place_Name"].unique()[:3]
            season = sub['Season'].mode()[0]
            
            return (f"**{state}** sees ~{fmt_number(avg_v)} visitors on average.\n\n"
                    f"**Top spots:** {', '.join(places)}\n"
                    f"**Best season:** {season}")
    return ""

# ==========================================
# use groq if nothing else works
# ==========================================

def get_groq_fallback(query: str) -> str:
    # call groq api as a fallback for queries not covered by dataset or kb.
    # Attempt to get API key from st.secrets, then os.environ
    api_key = None
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
        
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")
        
    if not api_key:
        return ("To answer this specific question, I need access to the Groq API, "
                "but `GROQ_API_KEY` is not configured in the secrets or environment variables. "
                "Please configure it to enable the full AI fallback capability!")

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful and knowledgeable tourism assistant for India. Provide informative, engaging, and structured responses. Aim for around 4-6 sentences to give enough detail without being overly verbose. Do not hallucinate numbers."},
                {"role": "user", "content": query}
            ],
            temperature=0.5,
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Sorry, I encountered an error connecting to the AI: {str(e)}"

def generate_itinerary(dest: str, budget: int, days: int, travel_date: str) -> str:
    # uses groq to generate a highly dynamic, customized daily itinerary.
    api_key = None
    try: api_key = st.secrets.get("GROQ_API_KEY")
    except: pass
    if not api_key: api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        return "⚠️ **Groq API Key not found!** Please set `GROQ_API_KEY` in secrets to enable dynamic AI itinerary generation."

    prompt = f"""
    Create a highly realistic and dynamic {days}-day trip itinerary for {dest} in India.
    Total Budget: ₹{budget}
    Travel Date: {travel_date}
    
    Requirements:
    1. Provide a realistic breakdown of the budget (Accommodation, Transport, Food, Activities) that makes sense for {dest}. For example, if it's an expensive city, accommodation will cost more.
    2. Provide a day-by-day bulleted itinerary with SPECIFIC, famous landmarks/restaurants in {dest}. Do not use generic terms like "Visit a local market".
    3. Include one local pro-tip for this specific destination based on the travel date.
    
    CRITICAL FORMATTING RULES:
    - You MUST use large Markdown headings (e.g., `##` or `###`) for the Main Title, the Budget Breakdown, and EVERY Day title (e.g. `### Day 1: Arrival`). Do NOT just use bold text for titles.
    - Keep it concise but specific.
    """
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert, local Indian travel planner. Generate highly specific, realistic itineraries. Do not use generic placeholders."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Generation Failed: {str(e)}"

def generate_prediction_insights(place: str, date: str, visitors: int, risk: str) -> str:
    # uses groq to generate business/travel insights based on predicted crowd.
    api_key = None
    try: api_key = st.secrets.get("GROQ_API_KEY")
    except: pass
    if not api_key: api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return ""
    
    prompt = f"The destination '{place}' is predicted to have {visitors} visitors on {date}. The crowding risk level is {risk}.\nWrite a single, concise paragraph (3 sentences max) offering specific actionable advice for a travel agent managing clients going there on this date."
    
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert AI travel business consultant. Do not use generic filler. Be highly specific."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=150,
        )
        return response.choices[0].message.content
    except Exception:
        return ""

def generate_comparison_insights(place1: str, state1: str, rating1: float, type1: str, place2: str, state2: str, rating2: float, type2: str) -> str:
    # uses groq to generate a human-like comparison between two places.
    api_key = None
    try: api_key = st.secrets.get("GROQ_API_KEY")
    except: pass
    if not api_key: api_key = os.environ.get("GROQ_API_KEY")
    if not api_key: return ""
    
    prompt = f"Compare these two Indian destinations for a traveler: {place1} (a {type1} in {state1}, rating: {rating1}) vs {place2} (a {type2} in {state2}, rating: {rating2}).\nWrite a short, engaging 3-sentence recommendation helping a traveler choose between the two based on their distinct vibes."
    
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an expert AI travel consultant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=150,
        )
        return response.choices[0].message.content
    except Exception:
        return ""

# handles hybrid chat logic==========================================
# HYBRID RESPONSE LOGIC
# ==========================================

def get_hybrid_response(query: str, df: pd.DataFrame) -> str:
    
    # try dataset match first
    dataset_reply = dataset_match(query, df)
    if dataset_reply:
        return dataset_reply

    # fallback to keyword search
    query_lower = query.lower().strip()
    
    # filter out common stopwords so they dont inflate match scores
    stopwords = {"what", "can", "the", "be", "at", "is", "a", "an", "to", "in",
                 "for", "of", "do", "how", "i", "my", "me", "you", "it", "this",
                 "that", "are", "was", "will", "should", "would", "about", "with"}
    query_words = set(''.join(c for c in query_lower if c.isalnum() or c.isspace()).split())
    query_content_words = query_words - stopwords
    
    best_match = None
    best_score = 0
    
    for item in CHATBOT_KB:
        # greeting intent should only trigger on very short, exact-style matches
        if item.get("intent") == "greeting":
            for q in item["questions"]:
                if query_lower == q.lower().strip():
                    return item['answer']
            continue  # skip greeting from keyword scoring entirely
        
        for q in item["questions"]:
            q_clean = ''.join(c for c in q.lower() if c.isalnum() or c.isspace())
            q_words = set(q_clean.split()) - stopwords
            
            if not q_words or not query_content_words:
                continue
                
            overlap = len(q_words.intersection(query_content_words))
            score = overlap / max(len(q_words), 1)
            
            if score > best_score:
                best_score = score
                best_match = item['answer']
                
    if best_score >= 0.5 and best_match:
        return best_match
        
    # Tier 3: Groq Fallback for anything the KB cant handle
    return get_groq_fallback(query)
