
import openpyxl
import pandas as pd
import numpy as np
import math



# Cấu hình Pandas để hiển thị rộng hơn
pd.set_option('display.width', 1000)  # Tăng chiều rộng hiển thị (thử các giá trị lớn hơn nếu cần)
pd.set_option('display.max_columns', None)  # Hiển thị tất cả các cột
pd.set_option('display.expand_frame_repr', False) # Không xuống dòng DataFrame

def recommend_food(excel_file, calories_prompt_per100=None, ingredient_prompt=None, user_type_prompt=None, taste_prompt=None, negative_prompt=None, top_n=5, desired_calories=None):
    """
    Đề xuất món ăn từ file Excel, sắp xếp theo điểm, ngẫu nhiên trong nhóm điểm số cao nhất, và tính toán serving size.
    """

    excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
    df = pd.concat(excel_data.values(), ignore_index=True)
    df['Ranking Score'] = 0

    if calories_prompt_per100 is not None:
        calories_first_digit_prompt = str(int(calories_prompt_per100)).split('.')[0][0]
        df['Calories/Serving_str_first_digit'] = df['Calories/Serving'].astype(str).str[0]
        df = df[df['Calories/Serving_str_first_digit'] == calories_first_digit_prompt]
        df = df.drop(columns=['Calories/Serving_str_first_digit'])

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

    if negative_prompt:
        if 'Ingredient' in negative_prompt and negative_prompt['Ingredient']:
            neg_ingredients = [ing.strip().lower() for ing in negative_prompt['Ingredient'].split(',')]
            for neg_ingredient in neg_ingredients:
                df = df[~df['Ingredients'].str.lower().str.contains(neg_ingredient, na=False)]
        if 'User Type' in negative_prompt and negative_prompt['User Type']:
            neg_user_types = [ut.strip().lower() for ut in negative_prompt['User Type'].split(',')]
            for neg_user_type in neg_user_types:
                df = df[~df['User type'].str.lower().str.contains(neg_user_type, na=False)]
        if 'Taste' in negative_prompt and negative_prompt['Taste']:
            neg_tastes = [t.strip().lower() for t in negative_prompt['Taste'].split(',')]
            for neg_taste in neg_tastes:
                df = df[~df['Taste'].str.lower().str.contains(neg_taste, na=False)]

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



excel_file_path = 'food-ver2.xlsx'

# Input của người dùng
user_ingredient_prompt = 'beef, cheese'
user_user_type_prompt = 'athlete'
user_taste_prompt = 'rich'
user_negative_prompt = {'Taste': 'tender'} 
user_desired_calories = 400


# Gọi hàm đề xuất
recommended_foods = recommend_food(
    excel_file=excel_file_path,
    ingredient_prompt=user_ingredient_prompt,
    user_type_prompt=user_user_type_prompt,
    taste_prompt=user_taste_prompt,
    negative_prompt=user_negative_prompt,
    top_n=5,
    desired_calories=user_desired_calories
)
print(recommended_foods)

