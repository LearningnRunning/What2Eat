import pandas as pd
from PIL import Image
import ast
import streamlit as st

@st.cache_data
def load_excel_data(logo_img_path, logo_small_img_path):
    # Load the Excel data and create the DataFrame
    df_diner = pd.read_csv('./data/seoul_data/whatToEat_DB_seoul_diner_202400902.csv')
    df_diner['diner_category_detail'].fillna('', inplace=True)
    df_diner["diner_menu"] = df_diner["diner_menu"].apply(ast.literal_eval)

    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)

    return df_diner, banner_image, icon_image
