import pickle
import os
import ast
import glob
import json
from PIL import Image
import pandas as pd
import streamlit as st
import tempfile
import firebase_admin
from firebase_admin import credentials, storage
from config.constants import DATA_PATH, MODEL_PATH

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

# # Firebase 초기화 (한 번만 실행되어야 함)
# def initialize_firebase():
#     if not firebase_admin._apps:
#         key_dict = json.loads(st.secrets['FIREBASE_KEY'])
#         # creds = service_account.Credentials.from_service_account_info(key_dict)
#         cred = credentials.Certificate(key_dict)
#         firebase_admin.initialize_app(cred, {
#             'storageBucket': 'what2eat-db.appspot.com'
#         })
# initialize_firebase()
# bucket = storage.bucket()

# def download_file_from_firebase(file_name):
    
#     blob = bucket.blob(file_name)
#     return blob.download_as_string()

@st.cache_data
def load_model():
    # trainset_knn 로드
    with open(os.path.join(MODEL_PATH, 'svd_algo.pkl'), 'rb') as f:
        algo_knn = pickle.load(f)


    # trainset_knn 로드
    with open(os.path.join(MODEL_PATH, 'trainset.pkl'), 'rb') as f:
        trainset_knn = pickle.load(f)


    # TODO: target_region='seoul_beta'
    
    # # user_item_matrix 저장
    # with open(os.path.join(MODEL_PATH, f'user_item_matrix_{target_region}_240918.pkl'), 'rb') as f:
    #     user_item_matrix = pickle.load(f)

    # with open(os.path.join(MODEL_PATH, f'user_similarity_{target_region}_240918.pkl'), 'rb') as f:
    #     user_similarity_df = pickle.load(f)
    user_item_matrix, user_similarity_df =[], []
    return algo_knn, trainset_knn, user_item_matrix, user_similarity_df
