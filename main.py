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

def recommend_food(df, calories_prompt_per100=None, ingredient_prompt=None, user_type_prompt=None, taste_prompt=None, 
                  negative_prompt=None, top_n=5, desired_calories=None,
                  ingredient_priority=1, user_type_priority=1, taste_priority=1):
    """
    Recommends food from a DataFrame, sorted by score, randomized within the highest score group, and calculates serving size.
    """
    df['Ranking Score'] = 0

    if calories_prompt_per100 is not None:
        calories_first_digit_prompt = str(int(calories_prompt_per100)).split('.')[0][0]
        df['Calories/Serving_str_first_digit'] = df['Calories/Serving'].astype(str).str[0]
        df = df[df['Calories/Serving_str_first_digit'] == calories_first_digit_prompt]
        df = df.drop(columns=['Calories/Serving_str_first_digit'])

    # For each preference, add points based on priority level (1-3)
    if ingredient_prompt:
        ingredients = [ing.strip().lower() for ing in ingredient_prompt.split(',')]
        for ingredient in ingredients:
            df.loc[df['Ingredients'].astype(str).str.lower().str.contains(ingredient, na=False), 'Ranking Score'] += ingredient_priority

    if user_type_prompt:
        user_types = [ut.strip().lower() for ut in user_type_prompt.split(',')]
        for user_type in user_types:
            df.loc[df['User type'].astype(str).str.lower().str.contains(user_type, na=False), 'Ranking Score'] += user_type_priority

    if taste_prompt:
        tastes = [t.strip().lower() for t in taste_prompt.split(',')]
        for taste in tastes:
            df.loc[df['Taste'].astype(str).str.lower().str.contains(taste, na=False), 'Ranking Score'] += taste_priority

    # Fixed Negative Filtering Logic
    if negative_prompt:
        if 'Ingredient' in negative_prompt and negative_prompt['Ingredient']:
            neg_ingredients = [ing.strip().lower() for ing in negative_prompt['Ingredient'].split(',')]
            for neg_ingredient in neg_ingredients:
                df = df[~df['Ingredients'].astype(str).str.lower().str.contains(neg_ingredient, na=False)]
        if 'User Type' in negative_prompt and negative_prompt['User Type']:
            neg_user_types = [ut.strip().lower() for ut in negative_prompt['User Type'].split(',')]
            for neg_user_type in neg_user_types:
                df = df[~df['User type'].astype(str).str.lower().str.contains(neg_user_type, na=False)]
        if 'Taste' in negative_prompt and negative_prompt['Taste']:
            neg_tastes = [t.strip().lower() for t in negative_prompt['Taste'].split(',')]
            for neg_taste in neg_tastes:
                df = df[~df['Taste'].astype(str).str.lower().str.contains(neg_taste, na=False)]

    ranked_df = df.sort_values(by='Ranking Score', ascending=False).reset_index(drop=True)
    ranked_df = ranked_df.head(top_n)

    if desired_calories is not None:
        ranked_df['Serving Size (grams)'] = (desired_calories / ranked_df['Calories/Serving']).apply(math.ceil).astype(str) + " gram"

    return ranked_df

# Load data
file_path = "food-ver2.xlsx"  # Adjust path if necessary
df = load_data(file_path)

# Streamlit UI
st.title("Food Recommendation App")

solution = st.radio("Choose a recommendation method:", ("Prioritized Preference Input", "Basic Filtering"))

if solution == "Prioritized Preference Input":
    st.header("Preferences")

    user_ingredient_prompt = st.text_input("Preferred Ingredients (comma-separated)")
    user_type_prompt = st.text_input("Preferred User Type (comma-separated)")
    user_taste_prompt = st.text_input("Preferred Taste (comma-separated)")

    st.subheader("Exclude")
    negative_ingredient = st.text_input("Ingredients to avoid")
    negative_user_type = st.text_input("User types to avoid")
    negative_taste = st.text_input("Tastes to avoid")

    user_negative_prompt = {}
    if negative_ingredient:
        user_negative_prompt['Ingredient'] = negative_ingredient
    if negative_user_type:
        user_negative_prompt['User Type'] = negative_user_type
    if negative_taste:
        user_negative_prompt['Taste'] = negative_taste
    if not user_negative_prompt:
        user_negative_prompt = None

    user_desired_calories = st.number_input("Desired calories per serving", min_value=0, format="%d")

    if st.button("Recommend food"):
        recommended_foods = recommend_food(
            df=df,
            ingredient_prompt=user_ingredient_prompt,
            user_type_prompt=user_type_prompt,
            taste_prompt=user_taste_prompt,
            negative_prompt=user_negative_prompt,
            top_n=5,
            desired_calories=user_desired_calories
        )
        st.dataframe(recommended_foods)
