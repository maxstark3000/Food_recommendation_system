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
    Now with variable prioritization feature that can increase the score for certain criteria based on priority level (1-3).
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
            df.loc[df['Ingredients'].str.lower().str.contains(ingredient, na=False), 'Ranking Score'] += ingredient_priority

    if user_type_prompt:
        user_types = [ut.strip().lower() for ut in user_type_prompt.split(',')]
        for user_type in user_types:
            df.loc[df['User type'].str.lower().str.contains(user_type, na=False), 'Ranking Score'] += user_type_priority

    if taste_prompt:
        tastes = [t.strip().lower() for t in taste_prompt.split(',')]
        for taste in tastes:
            df.loc[df['Taste'].str.lower().str.contains(taste, na=False), 'Ranking Score'] += taste_priority
    else:
        tastes = []

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
    columns_to_drop = ['No'] + ['Serving'] + ['Calories']
    ranked_df = ranked_df.drop(columns=columns_to_drop, errors='ignore')

    max_score = ranked_df['Ranking Score'].max()
    max_score_group = ranked_df[ranked_df['Ranking Score'] == max_score]
    remaining_df = ranked_df[ranked_df['Ranking Score'] != max_score]

    shuffled_max_score_group = max_score_group.sample(frac=1)

    ranked_df = pd.concat([shuffled_max_score_group, remaining_df]).reset_index(drop=True)

    ranked_df = ranked_df.head(top_n)

    if desired_calories is not None:
        ranked_df['Serving Size (grams)'] = (desired_calories / ranked_df['Calories/Serving']).apply(math.ceil).astype(str) + " gram"

    return ranked_df

# File path for the Excel data
# Use an absolute path instead of a relative path
excel_file_path = os.path.abspath("food-ver2.xlsx")  # or specify the exact path like "/path/to/your/food-ver2.xlsx"

# Debugging: Print the file path and check if the file exists
print("File path:", excel_file_path)
print("File exists:", os.path.exists(excel_file_path))

# Load data
df = load_data(excel_file_path)

# Streamlit UI
st.title("Food Recommendation App")

# Option to choose between solutions
solution = st.radio(
    "Choose a recommendation method:",
    ("Prioritized Preference Input", "Basic Filtering")
)

if solution == "Prioritized Preference Input":
    # Preferences section
    st.header("Preferences")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Include")
        
        # Preferred ingredients
        st.markdown("Ingredients (e.g., beef, cheese)")
        ingredient_priority = st.slider("", 1, 3, 1, key="ing_priority", label_visibility="collapsed")
        user_ingredient_prompt = st.text_input("", key="ingredient_input", label_visibility="collapsed")
        
        # User type
        st.markdown("User type (e.g., gain, normal, athlete)")
        user_type_priority = st.slider("", 1, 3, 1, key="type_priority", label_visibility="collapsed")
        user_user_type_prompt = st.text_input("", key="user_type_input", label_visibility="collapsed")
        
        # Preferred tastes
        st.markdown("Taste (e.g., rich, sweet)")
        taste_priority = st.slider("", 1, 3, 1, key="taste_priority", label_visibility="collapsed")
        user_taste_prompt = st.text_input("", key="taste_input", label_visibility="collapsed")
        
    with col2:
        st.subheader("Exclude (optional)")
        
        st.markdown("Ingredients to avoid (e.g., pork, egg)")
        negative_ingredient = st.text_input("", key="neg_ingredient", label_visibility="collapsed")
        
        st.markdown("User types to avoid (e.g., losing)")
        negative_user_type = st.text_input("", key="neg_user_type", label_visibility="collapsed")
        
        st.markdown("Tastes to avoid (e.g., tender, sweet)")
        negative_taste = st.text_input("", key="neg_taste", label_visibility="collapsed")
            
    # Build negative_prompt dictionary with all three categories
    user_negative_prompt = {}
    if negative_ingredient:
        user_negative_prompt['Ingredient'] = negative_ingredient
    if negative_user_type:
        user_negative_prompt['User Type'] = negative_user_type
    if negative_taste:
        user_negative_prompt['Taste'] = negative_taste

    # Set to None if empty
    if not user_negative_prompt:
        user_negative_prompt = None

    # Additional options
    st.header("Additional Options")
    user_desired_calories = st.number_input("Desired calories per serving ", value=None, min_value=0, format="%d")

    if st.button("Recommend food"):
        recommended_foods = recommend_food(
            df=df,
            ingredient_prompt=user_ingredient_prompt,
            user_type_prompt=user_user_type_prompt,
            taste_prompt=user_taste_prompt,
            negative_prompt=user_negative_prompt,
            top_n=5,
            desired_calories=user_desired_calories,
            ingredient_priority=ingredient_priority,
            user_type_priority=user_type_priority,
            taste_priority=taste_priority
        )

        # st.write("Recommended Foods:")
        st.dataframe(recommended_foods)

elif solution == "Basic Filtering":
    st.title("Basic Filtering")
    
    # Input fields
    st.subheader("Step 1: Filter by Ingredients")
    user_ingredients = st.text_input("Enter ingredients (comma-separated, e.g., beef, cheese):", key="ingredients_input")
    
    st.subheader("Step 2: Filter by User Type")
    user_types = st.text_input("Enter user types (comma-separated, e.g., gain, normal, athlete):", key="user_types_input")
    
    st.subheader("Step 3: Filter by Taste")
    user_tastes = st.text_input("Enter taste preferences (comma-separated, e.g., rich, sweet):", key="tastes_input")
    
    st.subheader("Step 4: Filter by Calories (Optional)")
    desired_calories = st.number_input("Enter your desired calorie intake per serving (optional)", min_value=50, max_value=1000, value=200, step=50)
    
    # Recommend button
    if st.button("Recommend food"):
        df_filtered = df.copy()  # Start with a copy of the original DataFrame
        
        # Filtering logic
        selected_ingredients = [ing.strip().lower() for ing in user_ingredients.split(',')] if user_ingredients else []
        if selected_ingredients:
            df_filtered = df_filtered[df_filtered['Ingredients'].str.lower().str.contains('|'.join(selected_ingredients), na=False)]
        
        selected_user_types = [ut.strip().lower() for ut in user_types.split(',')] if user_types else []
        if selected_user_types:
            df_filtered = df_filtered[df_filtered['User type'].str.lower().str.contains('|'.join(selected_user_types), na=False)]
        
        selected_tastes = [t.strip().lower() for t in user_tastes.split(',')] if user_tastes else []
        if selected_tastes:
            df_filtered = df_filtered[df_filtered['Taste'].str.lower().str.contains('|'.join(selected_tastes), na=False)]
        
        # Calculate adjusted serving size, handling potential division by zero
        if desired_calories:
            df_filtered['Adjusted Serving Size (grams)'] = df_filtered.apply(
                lambda row: f"{math.ceil(desired_calories / row['Calories/Serving'])} grams"
                if row['Calories/Serving'] != 0 else "N/A",
                axis=1
            )
            df_filtered = df_filtered[df_filtered['Calories/Serving'] <= desired_calories]
        
        # Display the filtered DataFrame
        st.subheader("Recommended Foods")
        st.dataframe(df_filtered)