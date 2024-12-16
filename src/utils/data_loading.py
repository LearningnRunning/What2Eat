import pickle
import os
import ast
import glob
import ast

from PIL import Image
import pandas as pd
import streamlit as st

from config.constants import DATA_PATH, MODEL_PATH


def safe_string_to_list(input_string, column_name):
    """
    안전하게 문자열을 리스트로 변환 (JSON이나 Python 리스트 형식 모두 처리 가능)

    Args:
        input_string (str): 리스트 형식의 문자열
        column_name (str): 현재 컬럼 이름

    Returns:
        list: 변환된 리스트 (변환 실패 시 빈 리스트 반환)
    """
    try:
        # 문자열을 리스트로 안전하게 변환
        input_list = ast.literal_eval(input_string)

        # 특정 컬럼에 대해 추가 처리
        if column_name == "diner_menu_price":
            # 빈 문자열 제외하고 정수로 변환
            return [int(x) for x in input_list if x != ""]
        else:
            return [x for x in input_list if x != ""]

    except (ValueError, SyntaxError, TypeError):
        # 변환 실패 시 빈 리스트 반환
        return []


@st.cache_data
def load_static_data(logo_img_path, logo_small_img_path, guide_image_path):
    # Get the first CSV file in the directory
    csv_files = glob.glob(DATA_PATH)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {DATA_PATH}")

    first_csv_file = csv_files[0]

    # Load the CSV data and create the DataFrame
    df_diner = pd.read_csv(first_csv_file)
    df_diner["diner_category_detail"].fillna("기타", inplace=True)
    # df_diner["diner_menu"] = df_diner["diner_menu"].apply(ast.literal_eval)

    df_diner["diner_menu_name"] = df_diner["diner_menu_name"].apply(
        lambda x: safe_string_to_list(x, "diner_menu_name")
    )

    df_diner["diner_tag"] = df_diner["diner_tag"].apply(
        lambda x: safe_string_to_list(x, "diner_tag")
    )

    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)
    guide_image = Image.open(guide_image_path)

    return df_diner, banner_image, icon_image, guide_image


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

# st.cache_resource
# def load_model():
#     # trainset_knn 로드
#     with open(os.path.join(MODEL_PATH, 'svd_algo.pkl'), 'rb') as f:
#         algo_knn = pickle.load(f)


#     # trainset_knn 로드
#     with open(os.path.join(MODEL_PATH, 'trainset.pkl'), 'rb') as f:
#         trainset_knn = pickle.load(f)


#     # TODO: target_region='seoul_beta'

#     # # user_item_matrix 저장
#     # with open(os.path.join(MODEL_PATH, f'user_item_matrix_{target_region}_240918.pkl'), 'rb') as f:
#     #     user_item_matrix = pickle.load(f)

#     # with open(os.path.join(MODEL_PATH, f'user_similarity_{target_region}_240918.pkl'), 'rb') as f:
#     #     user_similarity_df = pickle.load(f)
#     user_item_matrix, user_similarity_df =[], []
#     return algo_knn, trainset_knn, user_item_matrix, user_similarity_df
