# src/utils/data_loading.py

import ast
import glob
import os
import pickle

import pandas as pd
import streamlit as st
from config.constants import DATA_PATH, MODEL_PATH
from PIL import Image


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

    df_diner["diner_url"] = df_diner["diner_idx"].apply(
        lambda diner_idx: f"https://place.map.kakao.com/{diner_idx}"
    )

    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)
    guide_image = Image.open(guide_image_path)

    return df_diner, banner_image, icon_image, guide_image