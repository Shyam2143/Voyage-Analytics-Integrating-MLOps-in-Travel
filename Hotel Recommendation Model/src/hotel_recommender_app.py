import streamlit as st
import pickle
import pandas as pd
from pathlib import Path

# Define the CFRecommender class before loading the pickle file
class CFRecommender:
    MODEL_NAME = 'Collaborative Filtering'

    def __init__(self, cf_predictions_df, items_df):
        self.cf_predictions_df = cf_predictions_df
        self.items_df = items_df

    def get_model_name(self):
        return self.MODEL_NAME

    def recommend_items(self, place, days, budget, topn=5):
        # Filter available hotels based on place, days, and budget
        filtered_hotels = self.items_df[
            (self.items_df["place"] == place) &
            (self.items_df["days"] == days) &
            (self.items_df["price"] <= budget)
        ]

        if filtered_hotels.empty:
            return pd.DataFrame()  # No hotels match criteria

        # Get top recommended hotels sorted by price
        recommendations_df = filtered_hotels.groupby("name")["price"].min().reset_index()
        recommendations_df = recommendations_df.sort_values(by="price", ascending=True).head(topn)

        return recommendations_df


# Load the trained model
project_root = Path(__file__).resolve().parents[1]
model_path = project_root / "artifacts" / "cf_recommender.pkl"
with model_path.open("rb") as f:
    cf_recommender_model = pickle.load(f)

st.title("Hotel Recommendation System")

# Get list of cities
city_list = sorted(cf_recommender_model.items_df["place"].unique())

# Streamlit UI for input
selected_city = st.selectbox("Select a City", city_list)
num_days = st.number_input("Enter Number of Days", min_value=1, max_value=30, step=1)
budget = st.number_input("Enter Maximum Price per Day", min_value=1.0, max_value=10000.0, step=10.0)

# Number of recommendations
top_n = st.slider("Number of Hotel Recommendations", 1, 10, 5)

if st.button("Get Recommendations"):
    recommendations = cf_recommender_model.recommend_items(selected_city, num_days, budget, topn=top_n)

    if recommendations.empty:
        st.error("No hotels available for the selected city, number of days, or budget. Please adjust your filters.")
    else:
        st.subheader("Recommended Hotels:")
        st.dataframe(recommendations)
