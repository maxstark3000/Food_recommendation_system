import streamlit as st
import openpyxl
import pandas as pd
import numpy as np
import math
import os

# Configuration for Pandas display options
pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

@st.cache_data
def load_data(excel_file):
    """Loads data from the Excel file and caches it."""
    try:
        excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
        df = pd.concat(excel_data.values(), ignore_index=True)
        return df
    except FileNotFoundError as e:
        st.error(f"Error: The file {excel_file} was not found. Please check the file path.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while reading the Excel file: {e}")
        st.stop()

# File path for the Excel data
excel_file_path = os.path.abspath("food-ver2.xlsx")

# Load data
df = load_data(excel_file_path)

# Front page selection
st.title("Food Recommendation App")
st.subheader("Choose Your Recommendation Method")

solution = st.radio("Select a method:", ["Solution 1: tag-based ranking", "Solution 2: basic filtering"])

if solution == "Solution 2: Basic filtering":
    def recommend_food_basic(df, ingredient_prompt=None, user_type_prompt=None, taste_prompt=None, negative_prompt=None, top_n=5, desired_calories=None):
        """Basic food recommendation system."""
        df['Ranking Score'] = 0

        if ingredient_prompt:
            ingredients = [ing.strip().lower() for ing in ingredient_prompt.split(',')]
            for ingredient in ingredients:
                df.loc[df['Ingredients'].str.lower().str.contains(ingredient, na=False), 'Ranking Score'] += 1

        if user_type_prompt:
            user_types = [ut.strip().lower() for ut in user_type_prompt.split(',')]
            for user_type in user_types:
                df.loc[df['User type'].str.lower().str.contains(user_type, na=False), 'Ranking Score'] += 1

        if taste_prompt:
            tastes = [t.strip().lower() for t in taste_prompt.split(',')]
            for taste in tastes:
                df.loc[df['Taste'].str.lower().str.contains(taste, na=False), 'Ranking Score'] += 1

        ranked_df = df.sort_values(by='Ranking Score', ascending=False).reset_index(drop=True).head(top_n)

        if desired_calories is not None:
            ranked_df['Serving Size (grams)'] = (desired_calories / ranked_df['Calories/Serving']).apply(math.ceil).astype(str) + " gram"

        return ranked_df

    user_ingredient_prompt = st.text_input("Enter preferred ingredients (cheese, milk, beef, etc):")
    user_user_type_prompt = st.text_input("Enter your user type (normal, gain, loss, athlete):")
    user_taste_prompt = st.text_input("Enter preferred tastes (sweet, savory, rich, etc):")
    user_desired_calories = st.number_input("Enter desired calories per serving:", value=None, format="%d")

    if st.button("Recommend Foods (Basic)"):
        recommended_foods = recommend_food_basic(
            df, user_ingredient_prompt, user_user_type_prompt, user_taste_prompt, top_n=5, desired_calories=user_desired_calories
        )
        st.dataframe(recommended_foods)

elif solution == "Solution 2: tag-based ranking":
    def recommend_food_advanced(df, ingredient_prompt=None, user_type_prompt=None, taste_prompt=None, negative_prompt=None, 
                                top_n=5, desired_calories=None, ingredient_priority=1, user_type_priority=1, taste_priority=1):
        """Advanced recommendation with prioritization."""
        df['Ranking Score'] = 0

        if ingredient_prompt:
            ingredients = [ing.strip().lower() for ing in ingredient_prompt.split(',')]
            for ingredient in ingredients:
                df.loc[df['Ingredients'].str.lower().str.contains(ingredient, na=False), 'Ranking Score'] += ingredient_priority

        if user_type_prompt:
            user_types = [ut.strip().lower() for ut in user_type_prompt.split(',')]
            for user_type in user_types:
                df.loc[df['User type'].str.lower().str.contains(user_type, na=False), 'Ranking Score'] += user_type_priority

        if taste_prompt:
            tastes = [t.strip().lower() for t in taste_prompt.split(',')]
            for taste in tastes:
                df.loc[df['Taste'].str.lower().str.contains(taste, na=False), 'Ranking Score'] += taste_priority

        ranked_df = df.sort_values(by='Ranking Score', ascending=False).reset_index(drop=True).head(top_n)

        if desired_calories is not None:
            ranked_df['Serving Size (grams)'] = (desired_calories / ranked_df['Calories/Serving']).apply(math.ceil).astype(str) + " gram"

        return ranked_df

    st.header("Advanced Preferences")

    col1, col2 = st.columns(2)
    with col1:
        user_ingredient_prompt = st.text_input("Preferred ingredients:")
        ingredient_priority = st.slider("Ingredient Priority", 1, 3, 1)
        user_user_type_prompt = st.text_input("User type:")
        user_type_priority = st.slider("User Type Priority", 1, 3, 1)
        user_taste_prompt = st.text_input("Preferred tastes:")
        taste_priority = st.slider("Taste Priority", 1, 3, 1)
    
    with col2:
        negative_ingredient = st.text_input("Ingredients to avoid:")
        negative_user_type = st.text_input("User types to avoid:")
        negative_taste = st.text_input("Tastes to avoid:")
    
    user_negative_prompt = {k: v for k, v in zip(['Ingredient', 'User Type', 'Taste'], [negative_ingredient, negative_user_type, negative_taste]) if v}

    user_desired_calories = st.number_input("Desired calories per serving:", value=None, min_value=0, format="%d")

    if st.button("Recommend Foods (Advanced)"):
        recommended_foods = recommend_food_advanced(
            df, user_ingredient_prompt, user_user_type_prompt, user_taste_prompt, user_negative_prompt,
            top_n=5, desired_calories=user_desired_calories,
            ingredient_priority=ingredient_priority, user_type_priority=user_type_priority, taste_priority=taste_priority
        )
        st.dataframe(recommended_foods)
