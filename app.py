

import os, io, random
from datetime import date
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express       as px
import plotly.graph_objects as go
import pydeck as pdk
from streamlit_option_menu  import option_menu

from auth  import show_login_page, logout, update_profile
from utils import (load_data, save_uploaded_dataset, fmt_number, risk_badge,
                   DESTINATION_INFO, TRAVEL_TIPS, BUDGET_PLANS, CHATBOT_KB,
                   get_crowd_label, get_season, set_plotly_template)

from styles import apply_styles
# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()
# set_plotly_template()   # sets paper_bgcolor=white on every Plotly chart

#  CHATBOT

from chatbot import get_hybrid_response

def show_chatbot():
    st.subheader("🤖 AI Travel Chatbot")
    st.caption("Ask about destinations, best times, budgets, packing, safety, and more!")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            ("assistant", "Hello! 👋 I'm your AI travel assistant. Ask me anything about travel in India!")
        ]

    # render history using native chat_message
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    user_msg = st.chat_input("Ask me anything about your trip...")

    if user_msg:
        st.session_state.chat_history.append(("user", user_msg))
        with st.chat_message("user"):
            st.write(user_msg)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your query..."):
                df = load_data()
                reply = get_hybrid_response(user_msg, df)
                st.write(reply)
                st.session_state.chat_history.append(("assistant", reply))

    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = [("assistant", "Hello! 👋 Starting fresh — what would you like to know?")]
        st.rerun()

#  BUDGET TRIP PLANNER

def show_budget_planner():
    st.subheader("💰 Budget Trip Planner")
    
    df = load_data()
    # Provide destination options based on the dataset if available
    if not df.empty and "Place_Name" in df.columns:
        dest_options = sorted(df["Place_Name"].dropna().unique().tolist())
    else:
        dest_options = ["Goa", "Manali", "Jaipur", "Agra", "Mumbai", "Varanasi", "Kerala Backwaters"]

    col1, col2, col3 = st.columns(3)
    with col1:
        budget = st.number_input("Total Budget (₹)", min_value=1000, max_value=500000,
                                  value=15000, step=1000)
    with col2:
        dest = st.selectbox("Select Destination", dest_options)
    with col3:
        days = st.number_input("Number of Days", min_value=1, max_value=30, value=5)

    travel_date = st.date_input("Travel Date")

    if st.button("🗺 Generate My Trip Plan", use_container_width=True):
        st.success(f"✅ Generating custom trip plan for **{dest}** ({days} days, ₹{budget:,} budget)...")
        
        from chatbot import generate_itinerary
        
        with st.spinner("🧠 Groq AI is analyzing local attractions and budgeting..."):
            ai_itinerary = generate_itinerary(dest, budget, days, travel_date.strftime("%B %d, %Y"))
            
        st.divider()
        st.markdown(ai_itinerary)

#  PLACE SEARCH (User)

def show_place_search():
    st.subheader("🔍 Place Search & Details")
    df = load_data()
    if df.empty:
        st.warning("Dataset not loaded.")
        return

    query = st.text_input("Search destination / state / place name", placeholder="e.g. Goa, Temple, Beach…")
    if query:
        mask = (
            df["Location_State"].str.contains(query, case=False, na=False) |
            df["Place_Name"].str.contains(query, case=False, na=False) |
            df["Place_Type"].str.contains(query, case=False, na=False)
        )
        results = df[mask].drop_duplicates("Place_Name").head(10)
        if results.empty:
            st.warning("No places found. Try a different search term.")
        else:
            for _, row in results.iterrows():
                with st.expander(f"📍 {row['Place_Name']}  —  {row['Location_State']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("⭐ Google Rating", row["Google_Rating"])
                    c2.metric("👥 Avg Visitors", fmt_number(row["Visitors_Count"]))
                    c3.metric("🎟 Ticket Price", f"₹{row['Ticket_Price']}")
                    st.write(f"**Type:** {row['Place_Type']}  |  **Zone:** {row['Zone']}  |  **Best Season:** {row['Season']}")
                    crowd = get_crowd_label(row["Visitors_Count"], df)
                    st.write(f"**Crowd Level:** {crowd}")
                    info = DESTINATION_INFO.get(row["Location_State"], {})
                    if info:
                        best = ", ".join(info.get("peak", []))
                        st.write(f"**Best Time:** {best if best else '-'}")
                        desc = info.get("desc", "")
                        if desc:
                            st.info(desc)
                    
                    # AI Quick Guide button for each place
                    btn_key = f"ai_guide_{row['Place_Name']}_{row['Location_State']}"
                    if st.button(f"🧠 Get AI Quick Guide", key=btn_key):
                        with st.spinner("Generating AI guide..."):
                            from chatbot import generate_place_summary
                            guide = generate_place_summary(
                                row['Place_Name'], row['Location_State'], 
                                row['Place_Type'], row['Google_Rating']
                            )
                            if guide:
                                st.markdown(guide)
                            else:
                                st.write("Configure `GROQ_API_KEY` to unlock AI guides.")

#  PROFILE

def show_profile():
    st.subheader("👤 Profile & Settings")
    u = st.session_state.user
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"**{u.get('full_name','—')}**\n\nRole: {u.get('role','—')}")
    with col2:
        st.write(f"**Username:** {u.get('username','—')}")
        st.write(f"**Email:** {u.get('email','—')}")
        st.write(f"**Role:** {u.get('role','—')}")

    st.divider()
    st.subheader("✏️ Edit Profile")
    with st.form("edit_profile"):
        c1, c2 = st.columns(2)
        with c1:
            new_username  = st.text_input("Username",  value=u.get("username",""))
            new_full_name = st.text_input("Full Name", value=u.get("full_name",""))
        with c2:
            new_email    = st.text_input("Email",        value=u.get("email",""))
            new_password = st.text_input("New Password (leave blank to keep)", type="password")
        save = st.form_submit_button("💾 Save Changes", use_container_width=True)

    if save:
        ok, msg = update_profile(u["username"], new_username, new_password, new_email, new_full_name)
        if ok:
            st.success(msg)
        else:
            st.error(msg)

#  TRAVEL AGENT — OVERVIEW

def show_overview():
    st.subheader("📊 Dataset Overview")
    df = load_data()
    if df.empty:
        st.warning("No dataset loaded. Go to **Dataset** tab to upload one.")
        return

    # ── Primary KPIs ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    total_visitors = df["Visitors_Count"].sum()
    total_revenue  = df["Revenue"].sum() if "Revenue" in df.columns else (df["Visitors_Count"] * df["Ticket_Price"]).sum()
    avg_rating     = df["Google_Rating"].mean()
    unique_places  = df["Place_Name"].nunique()

    c1.metric("👥 Total Visitors", fmt_number(total_visitors))
    c2.metric("💰 Total Revenue", f"₹{fmt_number(total_revenue)}")
    c3.metric("⭐ Avg Rating", f"{avg_rating:.2f}")
    c4.metric("📍 Destinations", unique_places)

    # ── Secondary KPIs (new dataset columns) ─────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    avg_occupancy = df["Hotel_Occupancy_Rate"].mean() if "Hotel_Occupancy_Rate" in df.columns else 0
    event_count   = df[df["Special_Event"] != "None"]["Special_Event"].count() if "Special_Event" in df.columns else 0
    unique_states = df["Location_State"].nunique()
    anomaly_pct   = (df["Anomaly_Flag"] == "Yes").mean() * 100 if "Anomaly_Flag" in df.columns else 0

    c5.metric("🏨 Avg Occupancy", f"{avg_occupancy:.1f}%")
    c6.metric("🎉 Event Records", fmt_number(event_count))
    c7.metric("🗺 States Covered", unique_states)
    c8.metric("⚠️ Anomaly Rate", f"{anomaly_pct:.1f}%")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Visitor Distribution")
        fig = px.histogram(df, x="Visitors_Count", nbins=40, title="Histogram of Visitor Counts")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Season Distribution")
        fig = px.pie(df, names="Season", title="Records by Season")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sample Data")
    st.dataframe(df.sample(min(10, len(df))), use_container_width=True)

    st.subheader("Column Summary")
    summary = pd.DataFrame({
        "Column": df.columns,
        "Type":   df.dtypes.values,
        "Non-Null": df.count().values,
        "Missing":  df.isnull().sum().values,
        "Unique":   df.nunique().values,
    })
    st.dataframe(summary, use_container_width=True)

#  TRAVEL AGENT — DATASET TAB

def show_dataset_tab():
    st.subheader("📂 Dataset Management")
    uploaded = st.file_uploader("Upload CSV / Excel", type=["csv", "xlsx"])
    if uploaded:
        with st.spinner("Saving…"):
            path = save_uploaded_dataset(uploaded)
            load_data.clear()
        st.success(f"Dataset saved: `{path}`")

    df = load_data()
    if df.empty:
        st.info("No dataset loaded yet.")
        return

    st.divider()
    st.subheader("🛠️ Data Engineering Pipeline (Raw to ML-Ready)")
    st.write("To ensure enterprise-grade machine learning accuracy, raw tourism data is processed through a robust Pandas cleaning pipeline before ingestion.")
    
    with st.expander("Show Data Cleaning Pipeline Code (01_data_cleaning_pipeline.py)"):
        st.markdown("""
        **Pipeline Capabilities:**
        - Text Standardization (Typos, Casing)
        - Missing Value Imputation (Median/Mode strategies)
        - Advanced Outlier Capping (99.5th Percentile clipping for Visitors & Revenue)
        - Cross-Column Physics Validation (Ensuring Revenue-to-Visitor ratio realism)
        """)
        
        try:
            with open("data_engineering/01_data_cleaning_pipeline.py", "r", encoding="utf-8") as f:
                code_content = f.read()
            st.code(code_content, language="python")
        except FileNotFoundError:
            st.error("Could not load data cleaning pipeline code.")
            
    st.write("**Before: Raw Messy Data Sample** (Contains NaNs, outliers, and typos)")
    try:
        raw_df = pd.read_csv("dataset/raw_tourism_dataset.csv", low_memory=False)
        # Show a sample containing missing values to highlight the messiness
        messy_sample = raw_df[raw_df.isna().any(axis=1)].head(5)
        if messy_sample.empty:
            messy_sample = raw_df.head(5)
        st.dataframe(messy_sample, use_container_width=True)
    except FileNotFoundError:
        st.warning("Raw dataset file not found.")

    st.divider()
    st.subheader("🔍 Cleaned Dataset (Active Workspace)")
    st.write("**After: Processed, ML-Ready Data** (Filters only apply to this cleaned version)")
    col1, col2, col3 = st.columns(3)
    with col1:
        states = ["All"] + sorted(df["Location_State"].dropna().unique().tolist())
        state_filter = st.selectbox("State", states)
    with col2:
        seasons = ["All"] + sorted(df["Season"].dropna().unique().tolist())
        season_filter = st.selectbox("Season", seasons)
    with col3:
        min_v, max_v = int(df["Visitors_Count"].min()), int(df["Visitors_Count"].max())
        visitor_range = st.slider("Visitors Count", min_v, max_v, (min_v, max_v))

    fdf = df.copy()
    if state_filter  != "All": fdf = fdf[fdf["Location_State"] == state_filter]
    if season_filter != "All": fdf = fdf[fdf["Season"]         == season_filter]
    fdf = fdf[(fdf["Visitors_Count"] >= visitor_range[0]) &
              (fdf["Visitors_Count"] <= visitor_range[1])]

    st.info(f"Showing {len(fdf):,} of {len(df):,} records")
    st.dataframe(fdf, use_container_width=True)

    csv_bytes = fdf.to_csv(index=False).encode()
    st.download_button("⬇ Download Filtered CSV", csv_bytes, "filtered_data.csv", "text/csv")

#  TRAVEL AGENT — DASHBOARD / CHARTS

def show_dashboard():
    st.subheader("📈 Tourism Insights Dashboard")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return

    if "Date" in df.columns and df["Date"].notna().any():
        trend = df.groupby(df["Date"].dt.to_period("M").astype(str))["Visitors_Count"].sum().reset_index()
        trend.columns = ["Month", "Visitors"]
        fig = px.line(trend, x="Month", y="Visitors", title="Monthly Tourist Trends", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    colA, colB = st.columns(2)
    with colA:
        top = df.groupby("Location_State")["Visitors_Count"].sum().nlargest(10).reset_index()
        fig = px.bar(top, x="Visitors_Count", y="Location_State", orientation="h",
                     title="Top 10 States by Total Visitors", color="Visitors_Count")
        st.plotly_chart(fig, use_container_width=True)

    with colB:
        season_df = df["Season"].value_counts().reset_index()
        season_df.columns = ["Season", "Count"]
        fig = px.pie(season_df, names="Season", values="Count", title="Season-wise Distribution")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🔥 Correlation Heatmap")
    num_df = df[["Visitors_Count", "Google_Rating", "Review_Count_Lakhs",
                 "Ticket_Price", "Revenue"]].dropna()
    corr = num_df.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.columns,
        colorscale="RdBu", zmid=0,
        text=np.round(corr.values, 2), texttemplate="%{text}",
    ))
    fig.update_layout(title="Correlation Matrix of Numeric Features")
    st.plotly_chart(fig, use_container_width=True)

    colC, colD = st.columns(2)
    with colC:
        if "Tourist_Type" in df.columns:
            tt = df["Tourist_Type"].value_counts().reset_index()
            tt.columns = ["Type", "Count"]
            fig = px.bar(tt, x="Type", y="Count", title="Tourist Type Breakdown", color="Type")
            st.plotly_chart(fig, use_container_width=True)

    with colD:
        if "Zone" in df.columns:
            zone_df = df["Zone"].value_counts().reset_index()
            zone_df.columns = ["Zone", "Count"]
            fig = px.bar(zone_df, x="Zone", y="Count", title="Zone-wise Records", color="Zone")
            st.plotly_chart(fig, use_container_width=True)

    # Section 1: Top Destinations & Seasonal Trend
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Top Destinations Bar Chart
        top_places = df.groupby("Place_Name")["Visitors_Count"].sum().nlargest(10).reset_index()
        fig1 = px.bar(top_places, x="Place_Name", y="Visitors_Count", 
                      title="Top 10 Tourist Destinations", 
                      color="Visitors_Count", color_continuous_scale="Viridis")
        fig1.update_layout(xaxis_title="Destination", yaxis_title="Total Visitors")
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Insight: Most popular tourist destinations overall.")

    with col2:
        # 2. Seasonal Trend Line Chart
        # Use Month if available, else use Season
        if "Month" in df.columns:
            trend_col = "Month"
        elif "Date" in df.columns and df["Date"].notna().any():
            # If Date is available but Month isn't, create it temporarily
            try:
                # Need to convert to datetime first if it's not already
                if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
                    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                
                df["Month"] = df["Date"].dt.month_name()
                trend_col = "Month"
            except:
                trend_col = "Season"
        else:
            trend_col = "Season"
            
        trend = df.groupby(trend_col)["Visitors_Count"].sum().reset_index()
        # Sort months correctly if it's 'Month'
        if trend_col == "Month":
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            trend["Month"] = pd.Categorical(trend["Month"], categories=months, ordered=True)
            trend = trend.sort_values("Month")

        fig2 = px.line(trend, x=trend_col, y="Visitors_Count", markers=True,
                       title=f"{trend_col}-wise Tourist Demand",
                       color_discrete_sequence=["#ff7f0e"])
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Insight: Tourism demand variation over time.")

    # Section 2: Heatmap & Scatter Plot
    col3, col4 = st.columns(2)
    
    with col3:
        # 3. State-wise Heatmap (State vs Season)
        heatmap_data = df.groupby(["Location_State", "Season"])["Visitors_Count"].mean().reset_index()
        heatmap_pivot = heatmap_data.pivot(index="Location_State", columns="Season", values="Visitors_Count").fillna(0)
        fig3 = px.imshow(heatmap_pivot, text_auto=True, aspect="auto",
                         title="Seasonal Hotspots by State (Avg Visitors)",
                         color_continuous_scale="Blues")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Insight: Seasonal tourism hotspots across different states.")

    with col4:
        # 4. Ratings vs Visitors Scatter Plot
        fig4 = px.scatter(df, x="Google_Rating", y="Visitors_Count", 
                          color="Season", hover_data=["Place_Name"],
                          title="Ratings vs Visitor Count",
                          opacity=0.7)
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("Insight: Does a higher rating mean more tourists? (Usually, yes)")

#  ADVANCED ANALYTICS (ADMIN ONLY)

def show_advanced_analytics():
    st.subheader("🔬 Advanced Analytics Dashboard")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return

    # Visuals 1 & 2
    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Sunburst Chart (Simplified to avoid overcrowding)
        # Using Zone -> Location_State -> Place_Type for a cleaner, high-level structural view
        if "Zone" in df.columns and "Place_Type" in df.columns:
            fig1 = px.sunburst(df.dropna(subset=['Zone', 'Location_State', 'Place_Type', 'Visitors_Count']), 
                               path=['Zone', 'Location_State', 'Place_Type'], 
                               values='Visitors_Count', 
                               title="Tourism Distribution (Zone → State → Type)",
                               color='Visitors_Count', color_continuous_scale='RdBu')
        else:
            fig1 = px.sunburst(df.dropna(subset=['Location_State', 'Season', 'Visitors_Count']), 
                               path=['Location_State', 'Season'], 
                               values='Visitors_Count', 
                               title="Tourism Distribution Structure",
                               color='Visitors_Count', color_continuous_scale='RdBu')
            
        fig1.update_layout(margin=dict(t=40, l=0, r=0, b=0))
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Insight: Hierarchical structure of tourism distribution.")

    with col2:
        # 2. Treemap
        fig2 = px.treemap(df.dropna(subset=['Location_State', 'Place_Name', 'Visitors_Count']), 
                          path=['Location_State', 'Place_Name'], 
                          values='Visitors_Count',
                          title="Destination Contribution by State",
                          color='Visitors_Count', color_continuous_scale='Greens')
        fig2.update_layout(margin=dict(t=40, l=0, r=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Insight: High vs low performing locations within states.")

    # Visuals 3 & 4
    col3, col4 = st.columns(2)
    
    with col3:
        # 3. Sankey Diagram (Simplified for flow)
        if "Weather_Type" in df.columns and "Tourist_Type" in df.columns:
            flow_df = df.dropna(subset=['Season', 'Weather_Type', 'Tourist_Type', 'Visitors_Count'])
            flow1 = flow_df.groupby(['Season', 'Weather_Type'])['Visitors_Count'].sum().reset_index()
            flow1.columns = ['source', 'target', 'value']
            flow2 = flow_df.groupby(['Weather_Type', 'Tourist_Type'])['Visitors_Count'].sum().reset_index()
            flow2.columns = ['source', 'target', 'value']
            flows = pd.concat([flow1, flow2])
            
            all_nodes = list(pd.unique(flows[['source', 'target']].values.ravel('K')))
            node_mapping = {node: i for i, node in enumerate(all_nodes)}
            
            flows['source_idx'] = flows['source'].map(node_mapping)
            flows['target_idx'] = flows['target'].map(node_mapping)
            
            fig3 = go.Figure(data=[go.Sankey(
                node = dict(
                  pad = 15,
                  thickness = 20,
                  line = dict(color = "black", width = 0.5),
                  label = all_nodes,
                  color = "blue"
                ),
                link = dict(
                  source = flows['source_idx'],
                  target = flows['target_idx'],
                  value = flows['value']
              ))])
            fig3.update_layout(title_text="Tourism Flow (Season → Weather → Category)", font_size=10, margin=dict(t=40, l=0, r=0, b=0))
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("Insight: Flow of tourism behavior and external factors.")
        else:
            st.info("Weather_Type or Tourist_Type missing for Sankey diagram.")

    with col4:
        # 4. Violin Plot
        fig4 = px.violin(df, y="Visitors_Count", x="Location_State", color="Location_State",
                         box=True, points=False,
                         title="Distribution of Visitors Count Across States")
        fig4.update_layout(xaxis_title="State", yaxis_title="Visitors Count", showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)
        st.caption("Insight: Data spread and variability in visitor volumes.")

    # ML ANALYTICS VISUALS
    st.divider()
    st.subheader("Machine Learning Model Explainability")
    
    from model import train_models, _prepare_features
    
    with st.spinner("Loading XGBoost models for analytics..."):
        models = train_models()
        
    if models is None:
        st.warning("ML models could not be loaded.")
        return

    # ── Model Performance Metrics ────────────────────────────────────────
    metrics = models["metrics"]
    m1, m2, m3 = st.columns(3)
    m1.metric("R² Score (Excellent)", f"{metrics['r2']:.4f}")
    m2.metric("MAE (Low Error)", fmt_number(metrics['mae']))
    m3.metric("RMSE (Low Variance)", fmt_number(metrics['rmse']))
    st.caption("XGBoost Regressor — 300 estimators, lr=0.05, depth=8")
        
    colA, colB = st.columns(2)
    
    with colA:
        # 1. XGBoost Feature Importance Plot
        xgb = models["xgb_reg"]
        features = models["feature_cols"]
        importances = xgb.feature_importances_
        
        feat_df = pd.DataFrame({"Feature": features, "Importance": importances})
        feat_df = feat_df.sort_values("Importance", ascending=True)
        
        figA = px.bar(feat_df, x="Importance", y="Feature", orientation='h',
                      title="XGBoost Feature Importance",
                      color="Importance", color_continuous_scale="Reds")
        st.plotly_chart(figA, use_container_width=True)
        st.caption("Insight: Here the XGBoost Regressor model has been used to determine the key factors driving the demand forecast.")

    with colB:
        # 2. Value Proposition Matrix (Price vs Rating)
        val_df = df.dropna(subset=['Google_Rating', 'Ticket_Price', 'Visitors_Count', 'Place_Type']).copy()
        
        figB = px.scatter(val_df, x='Google_Rating', y='Ticket_Price', 
                          size='Visitors_Count', color='Place_Type',
                          hover_name='Place_Name',
                          title="Value Proposition Matrix (Price vs Rating)",
                          opacity=0.7, render_mode="webgl",
                          size_max=40)
        
        # Add quadrant lines (using medians as dividers)
        median_rating = val_df['Google_Rating'].median()
        median_price = val_df['Ticket_Price'].median()
        figB.add_vline(x=median_rating, line_width=1, line_dash="dash", line_color="gray")
        figB.add_hline(y=median_price, line_width=1, line_dash="dash", line_color="gray")
        
        figB.update_layout(xaxis_title="Google Rating (Quality)", yaxis_title="Ticket Price (Cost)")
        st.plotly_chart(figB, use_container_width=True)
        st.caption("Insight: Identifies Hidden Gems (High Rating, Low Cost) vs Premium Spots (High Rating, High Cost).")

    # 3. Actual vs Predicted (using cached test predictions)
    st.write("### XGBoost: Actual vs Predicted")
    
    y_test = models["y_test"]
    y_pred = models["y_pred"]
    
    pred_df = pd.DataFrame({"Actual": y_test, "Predicted": y_pred})
    
    figC = px.scatter(pred_df, x="Actual", y="Predicted", 
                      title=f"Actual vs Predicted Visitor Counts (R²: {metrics['r2']:.4f})",
                      opacity=0.5, render_mode="webgl")
                      
    # Perfect prediction reference line
    min_val, max_val = float(y_test.min()), float(y_test.max())
    figC.add_trace(go.Scatter(x=[min_val, max_val], y=[min_val, max_val],
                              mode='lines', name='Ideal Fit',
                              line=dict(color='rgba(255, 0, 0, 0.7)', dash='dash')))
                              
    st.plotly_chart(figC, use_container_width=True)
    st.caption("Insight: Points clustering tightly around the red dashed line indicate excellent XGBoost accuracy.")

    # ── Enterprise Forecasting Visuals ───────────────────────────────────
    st.divider()
    st.subheader("Enterprise Forecasting Analytics")

    colE, colF = st.columns(2)

    with colE:
        # 4. Seasonal Demand Forecast
        if "Month" in df.columns:
            month_order = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            seasonal = df.groupby("Month").agg(
                Avg_Visitors=("Visitors_Count", "mean"),
                Avg_Revenue=("Revenue", "mean")
            ).reindex(month_order).reset_index()
            
            figE = go.Figure()
            figE.add_trace(go.Scatter(x=seasonal["Month"], y=seasonal["Avg_Visitors"],
                                      mode="lines+markers", name="Avg Visitors",
                                      line=dict(color="#0ea5e9", width=3),
                                      fill="tozeroy", fillcolor="rgba(14,165,233,0.1)"))
            figE.update_layout(title="Monthly Demand Forecast Trend",
                               xaxis_title="Month", yaxis_title="Avg Visitors")
            st.plotly_chart(figE, use_container_width=True)
            st.caption("Insight: Seasonal demand patterns across all destinations.")

    with colF:
        # 5. Revenue Prediction Trend
        if "Month" in df.columns and "Revenue" in df.columns:
            rev_trend = df.groupby("Month")["Revenue"].mean().reindex(month_order).reset_index()
            rev_trend.columns = ["Month", "Avg_Revenue"]
            
            figF = go.Figure()
            figF.add_trace(go.Bar(x=rev_trend["Month"], y=rev_trend["Avg_Revenue"],
                                  marker_color="#8B5CF6", name="Avg Revenue"))
            figF.update_layout(title="Monthly Revenue Forecast",
                               xaxis_title="Month", yaxis_title="Avg Revenue (₹)")
            st.plotly_chart(figF, use_container_width=True)
            st.caption("Insight: Revenue peaks correlate with high-demand seasons.")

    colG, colH = st.columns(2)

    with colG:
        # 6. Event Impact Analysis
        if "Special_Event" in df.columns:
            event_impact = df.groupby("Special_Event").agg(
                Avg_Visitors=("Visitors_Count", "mean"),
                Avg_Revenue=("Revenue", "mean"),
                Count=("Visitors_Count", "count")
            ).reset_index()
            
            figG = px.bar(event_impact, x="Special_Event", y="Avg_Visitors",
                          color="Avg_Revenue", text="Count",
                          title="Event Impact on Tourism Demand",
                          color_continuous_scale="Viridis")
            figG.update_layout(xaxis_title="Event Type", yaxis_title="Avg Visitors")
            st.plotly_chart(figG, use_container_width=True)
            st.caption("Insight: Special events significantly boost visitor volume and revenue.")

    with colH:
        # 7. Hotel Occupancy vs Visitors
        if "Hotel_Occupancy_Rate" in df.columns:
            occ_sample = df.sample(min(2000, len(df)), random_state=42)
            figH = px.scatter(occ_sample, x="Hotel_Occupancy_Rate", y="Visitors_Count",
                              color="Season", hover_data=["Place_Name"],
                              title="Hotel Occupancy vs Visitor Count",
                              opacity=0.6, render_mode="webgl")
            figH.update_layout(xaxis_title="Hotel Occupancy Rate (%)",
                               yaxis_title="Visitors Count")
            st.plotly_chart(figH, use_container_width=True)
            st.caption("Insight: Occupancy rates as a leading indicator for crowding.")

#  PREDICTION TAB

def show_prediction():
    from model import train_models, predict, predict_intelligence
    st.subheader("Trip Overcrowding & Experience Predictor")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return

    # Show XGBoost model confidence metrics
    models = train_models()
    if models:
        metrics = models["metrics"]
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Model R² (Excellent)", f"{metrics['r2']:.4f}")
        mc2.metric("MAE (Low Error)", fmt_number(metrics['mae']))
        mc3.metric("RMSE (Low Variance)", fmt_number(metrics['rmse']))
        st.caption("Powered by XGBoost Regressor (300 estimators)")

    st.divider()
    st.subheader("Plan Your Trip")
    col1, col2, col3 = st.columns(3)
    with col1:
        places_list = sorted(df["Place_Name"].dropna().unique().tolist())
        place_input = st.selectbox("Where do you want to go?", places_list)
        
    with col2:
        num_users = st.number_input("How many people are going?", 1, 1000, 2)
        
    with col3:
        travel_date = st.date_input("When do you plan to travel?", min_value=date.today())

    if st.button("🔍 Predict Experience", use_container_width=True):
        match = df[df["Place_Name"] == place_input].iloc[0]
        state = match["Location_State"]
        p_type = match["Place_Type"]
        ticket_price = match["Ticket_Price"]
        rating = match["Google_Rating"]
        
        season = get_season(travel_date)
        is_weekend = travel_date.weekday() >= 5
        weather = "Sunny"
        
        with st.spinner("Analyzing data…"):
            # ML Model Prediction
            result = predict(state, p_type, season, weather,
                             num_users, is_weekend, ticket_price, rating, 
                             travel_date=travel_date, place_name=place_input)
            
            # Rule-based Travel Intelligence Prediction
            intel = predict_intelligence(state, travel_date)

        if result is None:
            st.error("Prediction failed.")
            return

        st.divider()
        
        if intel:
            st.subheader(f"Results for {place_input}")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📊 Predicted Visitors", fmt_number(result["demand"]))
            c2.metric("📅 Typical Average", fmt_number(result.get("avg_visitors", 0)))
            
            with c3:
                # Emoji map for Risk
                e_map = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
                risk_emoji = e_map.get(intel['risk'], "")
                st.write(f"### Crowd Risk")
                st.write(f"**{intel['risk']} {risk_emoji}**")
                
            st.divider()
            st.subheader("💡 Rule-Based Suggestion")
            
            # Banner based on risk level
            msg = f"{intel['reason'].upper()}!"
            if intel['risk'] == "High":
                st.error(f"⚠️ {msg}")
            elif intel['risk'] == "Medium":
                st.warning(f"🟡 {msg}")
            else:
                st.success(f"✅ {msg}")
                
            st.write(intel['suggestion'])
            st.caption(f"**Season:** {intel['season']}  |  **Month:** {intel['month']}")
            
            # GENERATIVE AI INSIGHTS
            st.divider()
            st.subheader("🧠 Generative AI Strategy")
            with st.spinner("Generating real-time AI strategy..."):
                from chatbot import generate_prediction_insights
                ai_insight = generate_prediction_insights(place_input, travel_date.strftime("%B %d, %Y"), int(result["demand"]), intel['risk'])
                
                if ai_insight:
                    st.info(ai_insight)
                else:
                    st.write("Configure `GROQ_API_KEY` to unlock advanced Generative AI insights.")

        st.divider()
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("💡 Travel Tips")
            info = DESTINATION_INFO.get(state, {})
            if info:
                st.write(f"**Best Time:** {info.get('best_time', 'N/A')}")
                st.info(info.get('tips', 'No specific tips for this state.'))
            else:
                st.write("• Research local customs before visiting.")
                st.write("• Keep a copy of your ID handy.")
            
            st.subheader("🎒 What to Carry")
            items = ["Water bottle", "Power bank", "ID Proof", "Comfortable shoes"]
            if season == "Winter": items += ["Light jacket", "Moisturizer"]
            elif season == "Summer": items += ["Sunscreen", "Sunglasses", "Cotton clothes"]
            elif season == "Monsoon": items += ["Umbrella", "Raincoat", "Waterproof bag"]
            
            if p_type in ["Beach", "Island"]: items += ["Swimwear", "Flip flops"]
            elif p_type in ["Temple", "Heritage Site"]: items += ["Modest clothing", "Hat"]
            
            for item in items:
                st.write(f"• {item}")

        with colB:
            if intel and intel['risk'] in ["High", "Medium"]:
                st.subheader("🔄 Recommended Alternatives")
                st.write(f"Since {place_input} might be crowded, consider these nearby or similar spots in {state}:")
                alts = df[(df["Location_State"] == state) & (df["Place_Name"] != place_input)].head(3)
                if alts.empty:
                    alts = df[df["Place_Name"] != place_input].sample(3)
                
                for _, alt in alts.iterrows():
                    alt_crowd = get_crowd_label(alt["Visitors_Count"], df)
                    st.write(f"📍 **{alt['Place_Name']}** ({alt['Place_Type']})")
                    st.write(f"Rating: ⭐ {alt['Google_Rating']} | Typical Crowd: {alt_crowd}")
            else:
                st.subheader("🌟 Must-See Nearby")
                nearby = df[(df["Location_State"] == state) & (df["Place_Name"] != place_input)].head(2)
                for _, n in nearby.iterrows():
                    st.write(f"• **{n['Place_Name']}** — just a short trip away!")

#  COMPARISON TAB

def show_comparison():
    st.subheader("⚖️ Place Comparison")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return

    places = sorted(df["Place_Name"].dropna().unique().tolist())
    
    col1, col2 = st.columns(2)
    with col1:
        place1 = st.selectbox("Select First Place", places, index=0)
    with col2:
        place2 = st.selectbox("Select Second Place", places, index=min(1, len(places)-1))

    if place1 == place2:
        st.warning("Please select two different places to compare.")
        return

    d1 = df[df["Place_Name"] == place1].iloc[0]
    d2 = df[df["Place_Name"] == place2].iloc[0]

    st.divider()
    comparison_data = {
        "Feature": ["State", "Type", "Rating", "Avg Visitors", "Ticket Price", "Best Season"],
        place1: [d1['Location_State'], d1['Place_Type'], d1['Google_Rating'], fmt_number(d1['Visitors_Count']), f"₹{d1['Ticket_Price']}", d1['Season']],
        place2: [d2['Location_State'], d2['Place_Type'], d2['Google_Rating'], fmt_number(d2['Visitors_Count']), f"₹{d2['Ticket_Price']}", d2['Season']]
    }
    st.table(pd.DataFrame(comparison_data))

    col1, col2 = st.columns(2)
    def get_pros_cons(row):
        pros = []
        cons = []
        if row['Google_Rating'] >= 4.5: pros.append("Excellent rating")
        if row['Ticket_Price'] == 0: pros.append("Free entry")
        elif row['Ticket_Price'] < 100: pros.append("Budget-friendly")
        else: cons.append("Higher entry fee")
        crowd = get_crowd_label(row['Visitors_Count'], df)
        if crowd == "Low": pros.append("Peaceful/Low crowd")
        elif crowd == "High": cons.append("Often overcrowded")
        return pros, cons

    with col1:
        st.write(f"### 📍 {place1}")
        p1, c1 = get_pros_cons(d1)
        st.write("**Advantages:**")
        for p in p1: st.write(f"✅ {p}")
        st.write("**Disadvantages:**")
        for c in c1: st.write(f"❌ {c}")

    with col2:
        st.write(f"### 📍 {place2}")
        p2, c2 = get_pros_cons(d2)
        st.write("**Advantages:**")
        for p in p2: st.write(f"✅ {p}")
        st.write("**Disadvantages:**")
        for c in c2: st.write(f"❌ {c}")

    st.divider()
    st.divider()
    st.subheader("💡 Rule-Based Suggestion")
    if d1['Google_Rating'] > d2['Google_Rating']:
        st.write(f"If you prioritize **quality and experience**, **{place1}** is better with a higher rating of {d1['Google_Rating']}.")
    else:
        st.write(f"If you prioritize **quality and experience**, **{place2}** is better with a higher rating of {d2['Google_Rating']}.")
    
    if d1['Visitors_Count'] < d2['Visitors_Count']:
        st.write(f"If you prefer **peace and quiet**, choose **{place1}** as it attracts fewer visitors.")
    else:
        st.write(f"If you prefer **peace and quiet**, choose **{place2}** as it attracts fewer visitors.")

    # GENERATIVE AI INSIGHTS
    st.divider()
    st.subheader("🧠 Generative AI Comparison")
    with st.spinner("Generating real-time AI comparison..."):
        from chatbot import generate_comparison_insights
        ai_insight = generate_comparison_insights(
            place1, d1['Location_State'], d1['Google_Rating'], d1['Place_Type'],
            place2, d2['Location_State'], d2['Google_Rating'], d2['Place_Type']
        )
        
        if ai_insight:
            st.info(ai_insight)
        else:
            st.write("Configure `GROQ_API_KEY` to unlock advanced Generative AI comparisons.")

#  TRAVEL AGENT — MAP EXPLORER

STATE_COORDS = {
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
    "Andaman": (11.7401, 92.6586),
    "Goa": (15.2993, 74.1240),
    "Rajasthan": (27.0238, 74.2179),
    "Kerala": (10.8505, 76.2711),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Karnataka": (15.3173, 75.7139),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Assam": (26.2006, 92.9376),
    "Odisha": (20.9517, 85.0985),
    "Telangana": (18.1124, 79.0193),
    "Nagaland": (26.1584, 94.5624),
    "Tamil Nadu": (11.1271, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "West Bengal": (22.9868, 87.8550),
    "Gujarat": (22.2587, 71.1924),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Punjab": (31.1471, 75.3412),
    "Uttarakhand": (30.0668, 79.0193),
    "Delhi": (28.7041, 77.1025),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.2996, 78.2932),
    "Bihar": (25.0961, 85.3131),
    "Jharkhand": (23.6102, 85.2799),
    "Chhattisgarh": (21.2787, 81.8661),
    "Haryana": (29.0588, 76.0856),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Sikkim": (27.5330, 88.5122),
    "Tripura": (23.9408, 91.9882),
    "Lakshadweep": (10.5667, 72.6417),
    "Puducherry": (11.9416, 79.8083),
    "Chandigarh": (30.7333, 76.7794),
    "Dadra and Nagar Haveli": (20.1809, 73.0169),
    "Daman and Diu": (20.4283, 72.8397),
    "Andhra Pradesh": (15.9129, 79.7400),
}

def show_map_explorer():
    st.subheader("🗺 Interactive Map Explorer")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return
    states = sorted(df["Location_State"].dropna().unique().tolist())
    selected = st.selectbox("Select State", states)
    sub = df[df["Location_State"] == selected]
    coords = STATE_COORDS.get(selected, (20.5937, 78.9629))
    map_df = sub.drop_duplicates("Place_Name").head(30).copy()
    
    # Generate mock coordinates clustered around state center
    rng = np.random.default_rng(42)
    map_df["lat"] = coords[0] + rng.uniform(-0.5, 0.5, len(map_df))
    map_df["lon"] = coords[1] + rng.uniform(-0.5, 0.5, len(map_df))
    
    # Normalize Visitors_Count for radius
    max_vis = map_df["Visitors_Count"].max() if not map_df.empty else 1
    # Convert visitors to a reasonable radius in meters (5km to 20km)
    map_df["radius"] = (map_df["Visitors_Count"] / max_vis) * 15000 + 5000 
    
    # Create PyDeck layer
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="[14, 165, 233, 200]", # Vibrant Blue
        get_line_color="[255, 255, 255, 255]",
        line_width_min_pixels=1,
        pickable=True,
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        latitude=coords[0],
        longitude=coords[1],
        zoom=6,
        pitch=0,
    )

    # Render sharp vector map using Carto provider (no black screen, perfectly sharp)
    st.pydeck_chart(pdk.Deck(
        map_provider="carto",
        map_style="dark",
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{Place_Name}</b><br/>Rating: ⭐ {Google_Rating}<br/>Visitors: 👥 {Visitors_Count}",
            "style": {
                "backgroundColor": "#1e293b",
                "color": "white"
            }
        }
    ))
    
    st.divider()
    st.subheader(f"Places in {selected}")
    cols = ["Place_Name", "Place_Type", "Google_Rating", "Visitors_Count", "Season", "Ticket_Price"]
    cols = [c for c in cols if c in sub.columns]
    top_places = sub[cols].drop_duplicates("Place_Name").sort_values("Google_Rating", ascending=False).head(15)
    for _, row in top_places.iterrows():
        with st.expander(f"📍 {row['Place_Name']} ({row.get('Place_Type','')})"):
            c1, c2, c3 = st.columns(3)
            c1.metric("⭐ Rating",  row.get("Google_Rating", "-"))
            c2.metric("👥 Avg Visitors", fmt_number(row.get("Visitors_Count", 0)))
            c3.metric("🎟 Ticket", f"₹{row.get('Ticket_Price', 0)}")
            st.write(f"**Best Season:** {row.get('Season', '-')}")

#  TRAVEL AGENT — ALERTS

def show_alerts():
    st.subheader("Alerts & Recommendations")
    df = load_data()
    if df.empty:
        st.warning("Dataset not available.")
        return
    q66 = df["Visitors_Count"].quantile(0.66)
    high_risk = (df[df["Visitors_Count"] >= q66]
                 .groupby("Location_State")["Visitors_Count"]
                 .mean().nlargest(8).reset_index())
    high_risk.columns = ["State", "Avg Visitors"]
    st.error(f"⚠️ {len(high_risk)} states have HIGH overcrowding risk!")
    for _, row in high_risk.iterrows():
        with st.expander(f"🔴 {row['State']} — Avg {fmt_number(row['Avg Visitors'])} visitors"):
            st.write("**Crowd Management Strategies:**")
            strategies = [
                "Implement timed entry slots and advance booking only.",
                "Promote off-peak visiting hours with discounts.",
                "Develop alternate tourist circuits in the same region.",
                "Deploy digital crowd monitoring at hotspots.",
                "Coordinate with local authorities on traffic management.",
            ]
            import random
            for s in random.sample(strategies, 3):
                st.write(f"• {s}")
                
            st.write("---")
            
            # Use an AI button to prevent massive latency on initial load
            if st.button(f"🤖 Generate AI Strategies", key=f"ai_strat_{row['State']}"):
                with st.spinner(f"Generating state-specific AI strategies for {row['State']}..."):
                    from chatbot import generate_crowd_management_strategies
                    ai_strategies = generate_crowd_management_strategies(row['State'], int(row['Avg Visitors']))
                    st.info(ai_strategies)
            else:
                st.caption("Click to generate highly specific crowd management strategies via AI.")

import requests

def show_image_search():
    st.subheader("Destination Image Search")
    st.write("Search for high-quality images of any destination in India!")
    
    query = st.text_input("Enter destination (e.g. Taj Mahal, Goa Beaches, Munnar):")
    
    if query:
        with st.spinner(f"Fetching images for {query}..."):
            # Increased limit to 6 to try and get multiple images
            url = f"https://en.wikipedia.org/w/api.php?action=query&generator=search&gsrsearch={query}&gsrlimit=6&prop=pageimages&format=json&pithumbsize=800"
            headers = {
                "User-Agent": "TourismAIAssistant/1.0 (https://streamlit.io; demo-project)"
            }
            try:
                res = requests.get(url, headers=headers)
                res.raise_for_status()
                data = res.json()
                pages = data.get("query", {}).get("pages", {})
                
                images_found = []
                for page_id in pages:
                    if "thumbnail" in pages[page_id]:
                        img_url = pages[page_id]["thumbnail"]["source"]
                        img_title = pages[page_id].get("title", query)
                        images_found.append((img_url, img_title))
                
                if images_found:
                    st.success(f"Found {len(images_found)} images related to '{query}'!")
                    cols = st.columns(2)
                    for i, (img_url, img_title) in enumerate(images_found):
                        with cols[i % 2]:
                            st.image(img_url, caption=f"📍 {img_title}", use_container_width=True)
                else:
                    st.warning(f"No exact image found for '{query}'. Here is a beautiful destination in India instead:")
                    st.image("https://images.unsplash.com/photo-1524492412937-b28074a5d7da", caption="Incredible India (Taj Mahal)", use_container_width=True)
            except Exception as e:
                st.error(f"Failed to load image: {str(e)}")

def show_home():
    st.title("🌟 AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System")
    st.markdown("Welcome to the ultimate AI-powered travel management system. Use the navigation sidebar to explore insights, predict demand, and plan itineraries.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Intelligence Engine")
        st.write("Our rule-based intelligence system analyzes specific seasonal patterns (Winter, Summer, Monsoon, Festive) to predict peak demand and overcrowding risk for your selected destination.")
        
        st.subheader("XGBoost Forecaster")
        st.write("A production-grade XGBoost model (300 estimators, tuned hyperparameters) predicts expected visitor counts based on historical data, weather, events, and seasonal trends — delivering enterprise-level forecasting accuracy.")
        
    with col2:
        st.subheader("BI Dashboard")
        st.write("Dynamic visualizations and correlation heatmaps help travel agents and enthusiasts understand the underlying factors driving tourism revenue and popularity.")
        
        st.subheader("💬 Smart AI Assistant")
        st.write("Our integrated chatbot is ready to answer your questions about destinations, budget planning, and travel tips, providing a seamless planning experience.")

    st.info("💡 **Pro Tip:** Use the sidebar to navigate through the different tools. As a Travel Agent, you have exclusive access to the Advanced Prediction and Dataset management tools.")

#  DASHBOARDS

def travel_agent_dashboard():
    with st.sidebar:
        st.title("🌍 AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System")
        st.write(f"Welcome, {st.session_state.user.get('full_name','Agent')}!")
        selected = option_menu(
            menu_title=None,
            options=["Home", "Overview", "Dataset", "Dashboard", "Advanced Analytics", "Prediction", "Comparison",
                     "Budget Planner", "Map Explorer", "Chatbot",
                     "Alerts", "Profile", "Logout"],
            icons=["house", "bar-chart-line", "database", "graph-up", "graph-up-arrow", "cpu", "arrow-left-right",
                   "wallet2", "map", "robot",
                   "bell", "person-circle", "box-arrow-right"],
            default_index=0,
            styles={
                "container": {
                    "padding":          "1rem 0.5rem !important",
                    "background-color": "transparent !important",
                    "border":           "none !important",
                },
                "icon": {
                    "color":            "#94a3b8",
                    "font-size":        "18px",
                    "margin-right":     "8px",
                },
                "nav-link": {
                    "font-family":      "'Plus Jakarta Sans', sans-serif",
                    "font-size":        "1.05rem",
                    "font-weight":      "500",
                    "color":            "#94a3b8",
                    "padding":          "0.8rem 1rem",
                    "margin":           "0.3rem 0",
                    "border-radius":    "12px",
                    "transition":       "all 0.3s ease",
                    "--hover-color":    "rgba(255, 255, 255, 0.05)",
                },
                "nav-link-selected": {
                    "background-color": "#0ea5e9",
                    "color":            "#ffffff",
                    "font-weight":      "700",
                    "box-shadow":       "0 4px 10px rgba(14, 165, 233, 0.3)",
                },
            },
        )

    if selected == "Home":             show_home()
    elif selected == "Overview":        show_overview()
    elif selected == "Dataset":       show_dataset_tab()
    elif selected == "Dashboard":     show_dashboard()
    elif selected == "Advanced Analytics": show_advanced_analytics()
    elif selected == "Prediction":    show_prediction()
    elif selected == "Comparison":    show_comparison()
    elif selected == "Budget Planner":show_budget_planner()
    elif selected == "Map Explorer":  show_map_explorer()
    elif selected == "Chatbot":       show_chatbot()
    elif selected == "Alerts":        show_alerts()
    elif selected == "Profile":       show_profile()
    elif selected == "Logout":
        logout()
        st.rerun()

def user_dashboard():
    with st.sidebar:
        st.title("🌍 AI-Driven Tourism Demand Forecasting and Destination Overcrowding Prediction System")
        st.write(f"Hi, {st.session_state.user.get('full_name','Traveller')}!")
        selected = option_menu(
            menu_title=None,
            options=["Home", "Chatbot", "Budget Planner", "Place Search", "Prediction", "Map Explorer", "Image Search", "Comparison", "Profile", "Logout"],
            icons=["house", "robot", "wallet2", "search", "cpu", "map", "image", "arrow-left-right", "person-circle", "box-arrow-right"],
            default_index=0,
            styles={
                "container": {
                    "padding":          "1rem 0.5rem !important",
                    "background-color": "transparent !important",
                    "border":           "none !important",
                },
                "icon": {
                    "color":            "#94a3b8",
                    "font-size":        "18px",
                    "margin-right":     "8px",
                },
                "nav-link": {
                    "font-family":      "'Plus Jakarta Sans', sans-serif",
                    "font-size":        "1.05rem",
                    "font-weight":      "500",
                    "color":            "#94a3b8",
                    "padding":          "0.8rem 1rem",
                    "margin":           "0.3rem 0",
                    "border-radius":    "12px",
                    "transition":       "all 0.3s ease",
                    "--hover-color":    "rgba(255, 255, 255, 0.05)",
                },
                "nav-link-selected": {
                    "background-color": "#0ea5e9",
                    "color":            "#ffffff",
                    "font-weight":      "700",
                    "box-shadow":       "0 4px 10px rgba(14, 165, 233, 0.3)",
                },
            },
        )

    if selected == "Home":             show_home()
    elif selected == "Chatbot":          show_chatbot()
    elif selected == "Budget Planner": show_budget_planner()
    elif selected == "Place Search":   show_place_search()
    elif selected == "Prediction":     show_prediction()
    elif selected == "Map Explorer":   show_map_explorer()
    elif selected == "Image Search":   show_image_search()
    elif selected == "Comparison":     show_comparison()
    elif selected == "Profile":        show_profile()
    elif selected == "Logout":
        logout()
        st.rerun()

#  ENTRY POINT

def main():
    if not st.session_state.get("logged_in"):
        show_login_page()
    else:
        role = st.session_state.user.get("role", "User")
        if role == "Travel Agent":
            travel_agent_dashboard()
        else:
            user_dashboard()

if __name__ == "__main__":
    main()
