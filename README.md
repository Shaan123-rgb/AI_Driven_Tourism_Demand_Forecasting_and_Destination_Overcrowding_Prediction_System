# 🌍 AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System

Welcome to the **TourismAI** repository! This is an advanced, production-ready web application designed to help travel agents and tourists make data-driven, intelligent travel decisions. It bridges the gap between traditional Machine Learning (predicting numbers) and Generative AI (explaining data with human logic).

## ✨ Key Features

1. **🔮 Machine Learning Forecaster**
   - Utilizes a trained Random Forest regression model to predict exact visitor crowds based on historical data, weather, seasonality, and local trends.
2. **🧠 Generative AI Insights (Groq LLM)**
   - Automatically translates numerical predictions and destination comparisons into highly specific, actionable travel strategies and tips using Llama-3.1-8b.
3. **🤖 Hybrid AI Travel Chatbot**
   - A lightning-fast travel assistant that uses local heuristics for instant data retrieval and seamlessly falls back to Generative AI for complex itinerary generation and budgeting.
4. **📊 Interactive Business Intelligence (BI) Dashboard**
   - Clean, highly interactive Plotly charts and correlation heatmaps to analyze revenue drivers and overcrowding metrics.
5. **🗺️ Interactive Vector Map Explorer**
   - Hardware-accelerated PyDeck vector maps that allow you to explore clustered tourist locations visually with customized hover analytics.
6. **🔒 Secure Role-Based Authentication**
   - Distinct dashboards tailored specifically for "Travel Agents" (who need raw data and advanced analytics) and standard "Users" (who just want to plan their trips).

## 🚀 Technology Stack

- **Frontend & Routing:** Streamlit, Streamlit-Option-Menu
- **Data Processing & ML:** Pandas, NumPy, Scikit-Learn
- **Generative AI Engine:** Groq API (`llama-3.1-8b-instant`)
- **Visualizations:** Plotly Express, Plotly Graph Objects, PyDeck (WebGL)
- **Styling:** Custom CSS with Glassmorphism UI and Dark-Mode optimization

## 🛠️ Local Installation & Setup

1. **Clone the repository** (or download the folder):
   ```bash
   git clone https://github.com/your-username/ai-tourism-dashboard.git
   cd ai-tourism-dashboard
   ```

2. **Install the dependencies:**
   Make sure you have Python 3.9+ installed.
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API Keys:**
   Create a `.streamlit` folder in the root directory, and inside it, create a `secrets.toml` file. Add your Groq API key:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_api_key_here"
   ```

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

## 🌐 Deployment (Streamlit Cloud)

This app is fully optimized for **Streamlit Community Cloud**. 
To deploy:
1. Push this code to a public GitHub repository.
2. Link the repository to your Streamlit Cloud account.
3. Go to your App Settings -> **Secrets** and paste in your `GROQ_API_KEY`.
4. Deploy and share the public URL!

## 🔐 Default Demo Accounts
If you are testing the authentication system locally, you can use the following default generated accounts:
* **Admin (Travel Agent):** `admin` / `admin123`
* **Demo User:** `user1` / `user123`

---
*Developed for advanced predictive analytics and modern AI implementation in the tourism sector.*
