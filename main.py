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
excel_file_path = "/mnt/data/food-ver2.xlsx"
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
    st.title("Solution 2 - Step-by-Step Filtering")
    
    # Step 1: User selects ingredients
    ingredient_options = df['Ingredients'].dropna().unique().tolist()
    selected_ingredients = st.multiselect("Select ingredients you want to use", ingredient_options)
    
    # Step 2: Filter ingredients
    df_filtered = df[df['Ingredients'].isin(selected_ingredients)]
    
    # Step 3: Filter by Calories > 200
    df_filtered = df_filtered[df_filtered['Calories/Serving'] > 200]
    
    # Step 4: Additional Filtering (e.g., avoiding 'rich' foods)
    avoid_rich = st.checkbox("Avoid rich foods?")
    if avoid_rich:
        df_filtered = df_filtered[~df_filtered['User type'].str.contains('rich', case=False, na=False)]
    
    # Step 5: Allow user to input desired calories and adjust portion sizes
    desired_calories = st.number_input("Enter your desired calorie intake per serving", min_value=50, max_value=1000, value=200, step=50)
    df_filtered['Adjusted Serving Size (grams)'] = (desired_calories / df_filtered['Calories/Serving']).apply(math.ceil).astype(str) + " grams"
    
    # Display Final Result
    st.subheader("Final Result")
    st.dataframe(df_filtered)
