import ast
import glob
from PIL import Image
import pandas as pd
import streamlit as st


from config.constants import DATA_PATH

@st.cache_data
def load_excel_data(logo_img_path, logo_small_img_path):
    # Get the first CSV file in the directory
    csv_files = glob.glob(DATA_PATH)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_PATH}")
    
    first_csv_file = csv_files[0]

    # Load the CSV data and create the DataFrame
    df_diner = pd.read_csv(first_csv_file)
    df_diner['diner_category_detail'].fillna('', inplace=True)
    df_diner["diner_menu"] = df_diner["diner_menu"].apply(ast.literal_eval)

    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)

    return df_diner, banner_image, icon_image
