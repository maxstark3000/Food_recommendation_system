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

def tag_based_ranking(df, calories_prompt_per100=None, ingredient_prompt=None, user_type_prompt=None, taste_prompt=None, 
                  negative_prompt=None, top_n=5, desired_calories=None,
                  ingredient_priority=1, user_type_priority=1, taste_priority=1):
    """
    Tag-Based Ranking: Recommends food sorted by score, randomized within the highest score group.
    Uses a prioritization system to weigh ingredient, user type, and taste preferences.
    """
    df['Ranking Score'] = 0

    if calories_prompt_per100 is not None:
        calories_first_digit_prompt = str(int(calories_prompt_per100)).split('.')[0][0]
        df['Calories/Serving_str_first_digit'] = df['Calories/Serving'].astype(str).str[0]
        df = df[df['Calories/Serving_str_first_digit'] == calories_first_digit_prompt]
        df = df.drop(columns=['Calories/Serving_str_first_digit'])

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

    if negative_prompt:
        for category, values in negative_prompt.items():
            neg_values = [v.strip().lower() for v in values.split(',')]
            for neg_value in neg_values:
                df = df[~df[category].str.lower().str.contains(neg_value, na=False)]

    ranked_df = df.sort_values(by='Ranking Score', ascending=False).reset_index(drop=True)
    ranked_df = ranked_df.head(top_n)

    if desired_calories is not None:
        ranked_df['Serving Size (grams)'] = (desired_calories / ranked_df['Calories/Serving']).apply(math.ceil).astype(str) + " gram"

    return ranked_df

def basic_step_by_step_filtering(df, calories_threshold=200):
    """
    Basic Step-by-Step Filtering: Follows a strict step-by-step filtering process.
    """
    filtered_df = df[df['Calories/Serving'] > calories_threshold]
    
    if 'Taste' in df.columns:
        unique_tastes = filtered_df['Taste'].unique()
        for taste in unique_tastes:
            temp_df = filtered_df[filtered_df['Taste'] == taste]
            if not temp_df.empty:
                filtered_df = temp_df
                break
    
    return filtered_df.reset_index(drop=True)

# File path for the Excel data
excel_file_path = os.path.abspath("food-ver2.xlsx")

df = load_data(excel_file_path)

# Streamlit UI
st.set_page_config(page_title="Food Recommendation App", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Tag-Based Ranking", "Basic Step-by-Step Filtering"])

if page == "Tag-Based Ranking":
    st.title("Tag-Based Ranking Recommendation")
    
    st.header("Preferences")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Include")
        ingredient_priority = st.slider("Ingredient Priority", 1, 3, 1)
        user_ingredient_prompt = st.text_input("Preferred Ingredients")
        user_type_priority = st.slider("User Type Priority", 1, 3, 1)
        user_user_type_prompt = st.text_input("Preferred User Types")
        taste_priority = st.slider("Taste Priority", 1, 3, 1)
        user_taste_prompt = st.text_input("Preferred Tastes")
    
    with col2:
        st.subheader("Exclude (optional)")
        negative_ingredient = st.text_input("Avoid Ingredients")
        negative_user_type = st.text_input("Avoid User Types")
        negative_taste = st.text_input("Avoid Tastes")
    
    user_negative_prompt = {}
    if negative_ingredient:
        user_negative_prompt['Ingredients'] = negative_ingredient
    if negative_user_type:
        user_negative_prompt['User type'] = negative_user_type
    if negative_taste:
        user_negative_prompt['Taste'] = negative_taste
    if not user_negative_prompt:
        user_negative_prompt = None
    
    if st.button("Recommend food"):
        recommended_foods = tag_based_ranking(
            df=df,
            ingredient_prompt=user_ingredient_prompt,
            user_type_prompt=user_user_type_prompt,
            taste_prompt=user_taste_prompt,
            negative_prompt=user_negative_prompt
        )
        st.dataframe(recommended_foods)

elif page == "Basic Step-by-Step Filtering":
    st.title("Basic Step-by-Step Filtering Recommendation")
    
    calories_threshold = st.number_input("Calories Threshold", value=200, min_value=0)
    
    if st.button("Recommend food"):
        recommended_foods = basic_step_by_step_filtering(df, calories_threshold)
        st.dataframe(recommended_foods)
