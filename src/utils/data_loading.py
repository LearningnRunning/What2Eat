# src/utils/data_loading.py

import ast
import glob
import os

import pandas as pd
import streamlit as st
from PIL import Image

from config.constants import DATA_PATH


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
        # null이나 None 값 처리
        if pd.isna(input_string) or input_string is None:
            return []

        # 문자열이 아닌 경우 문자열로 변환
        if not isinstance(input_string, str):
            input_string = str(input_string)

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
    """
    분리된 CSV 파일들을 로드하고 병합하여 완전한 데이터프레임을 생성합니다.
    """
    # 데이터 디렉토리 경로
    data_dir = os.path.dirname(DATA_PATH)

    # 각 테이블 파일 경로
    basic_file = os.path.join(data_dir, "diner_basic.csv")
    categories_file = os.path.join(data_dir, "diner_categories.csv")
    reviews_file = os.path.join(data_dir, "diner_reviews.csv")
    menus_file = os.path.join(data_dir, "diner_menus.csv")
    tags_file = os.path.join(data_dir, "diner_tags.csv")

    # 기존 단일 파일이 있는지 확인
    legacy_files = glob.glob(DATA_PATH)
    whattoeat_files = [f for f in legacy_files if "whatToEat_DB" in os.path.basename(f)]

    # 분리된 파일들이 모두 존재하는 경우
    if all(
        os.path.exists(f)
        for f in [basic_file, categories_file, reviews_file, menus_file, tags_file]
    ):
        print("Loading data from separated CSV files...")
        return load_separated_data(
            basic_file,
            categories_file,
            reviews_file,
            menus_file,
            tags_file,
            logo_img_path,
            logo_small_img_path,
            guide_image_path,
        )

    # 기존 단일 파일이 있는 경우
    elif whattoeat_files:
        print("Loading data from legacy single CSV file...")
        return load_legacy_data(
            whattoeat_files, logo_img_path, logo_small_img_path, guide_image_path
        )

    else:
        raise FileNotFoundError(f"No data files found in {data_dir}")


def load_separated_data(
    basic_file,
    categories_file,
    reviews_file,
    menus_file,
    tags_file,
    logo_img_path,
    logo_small_img_path,
    guide_image_path,
):
    """
    분리된 CSV 파일들을 로드하고 병합합니다.
    """
    # 기본 정보 로드
    df_basic = pd.read_csv(basic_file)
    print(f"Loaded basic data: {len(df_basic)} restaurants")

    # 카테고리 정보 로드 및 병합
    df_categories = pd.read_csv(categories_file)
    df_merged = df_basic.merge(df_categories, on="diner_idx", how="left")

    # 리뷰 정보 로드 및 병합
    df_reviews = pd.read_csv(reviews_file)
    df_merged = df_merged.merge(df_reviews, on="diner_idx", how="left")

    # 메뉴 정보 로드 및 병합
    df_menus = pd.read_csv(menus_file)
    df_merged = df_merged.merge(df_menus, on="diner_idx", how="left")

    # 태그 정보 로드 및 병합
    df_tags = pd.read_csv(tags_file)
    df_merged = df_merged.merge(df_tags, on="diner_idx", how="left")

    # 데이터 전처리
    df_merged = preprocess_merged_data(df_merged)

    # 이미지 로드
    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)
    guide_image = Image.open(guide_image_path)

    return df_merged, banner_image, icon_image, guide_image


def load_legacy_data(
    whattoeat_files, logo_img_path, logo_small_img_path, guide_image_path
):
    """
    기존 단일 CSV 파일을 로드합니다.
    """
    # Sort by filename to get the most recent date
    whattoeat_files.sort(reverse=True)
    first_csv_file = whattoeat_files[0]
    print(f"Loading data from: {os.path.basename(first_csv_file)}")

    # Load the CSV data
    df_diner = pd.read_csv(first_csv_file, low_memory=False)

    # 데이터 전처리
    df_diner = preprocess_legacy_data(df_diner)

    # 이미지 로드
    banner_image = Image.open(logo_img_path)
    icon_image = Image.open(logo_small_img_path)
    guide_image = Image.open(guide_image_path)

    return df_diner, banner_image, icon_image, guide_image


def preprocess_merged_data(df):
    """
    병합된 데이터를 전처리합니다.
    """
    df = df.copy()

    # null 값 처리
    df["diner_category_detail"] = df["diner_category_detail"].fillna("기타")

    # 리스트 형태 컬럼 처리
    if "diner_menu_name" in df.columns:
        df["diner_menu_name"] = df["diner_menu_name"].fillna("[]")
        df["diner_menu_name"] = df["diner_menu_name"].apply(
            lambda x: safe_string_to_list(x, "diner_menu_name")
        )

    if "diner_tag" in df.columns:
        df["diner_tag"] = df["diner_tag"].fillna("[]")
        df["diner_tag"] = df["diner_tag"].apply(
            lambda x: safe_string_to_list(x, "diner_tag")
        )

    # 카카오맵 URL 생성
    df["diner_url"] = df["diner_idx"].apply(
        lambda diner_idx: f"https://place.map.kakao.com/{diner_idx}"
    )

    return df


def preprocess_legacy_data(df_diner):
    """
    기존 단일 파일 데이터를 전처리합니다.
    """
    df_diner = df_diner.copy()
    df_diner["diner_category_detail"] = df_diner["diner_category_detail"].fillna("기타")

    # null 값을 빈 리스트 문자열로 채우기
    df_diner["diner_menu_name"] = df_diner["diner_menu_name"].fillna("[]")
    df_diner["diner_menu_name"] = df_diner["diner_menu_name"].apply(
        lambda x: safe_string_to_list(x, "diner_menu_name")
    )

    # null 값을 빈 리스트 문자열로 채우기
    df_diner["diner_tag"] = df_diner["diner_tag"].fillna("[]")
    df_diner["diner_tag"] = df_diner["diner_tag"].apply(
        lambda x: safe_string_to_list(x, "diner_tag")
    )

    df_diner["diner_url"] = df_diner["diner_idx"].apply(
        lambda diner_idx: f"https://place.map.kakao.com/{diner_idx}"
    )

    return df_diner


def create_separated_csv_files():
    """
    기존 단일 CSV 파일을 분리된 파일들로 변환합니다.
    """
    # 기존 파일 찾기
    csv_files = glob.glob(DATA_PATH)
    whattoeat_files = [f for f in csv_files if "whatToEat_DB" in os.path.basename(f)]

    if not whattoeat_files:
        raise FileNotFoundError("No whatToEat_DB CSV files found")

    # 최신 파일 로드
    whattoeat_files.sort(reverse=True)
    source_file = whattoeat_files[0]
    print(f"Converting {os.path.basename(source_file)} to separated files...")

    df = pd.read_csv(source_file, low_memory=False)
    data_dir = os.path.dirname(DATA_PATH)

    # 1. 기본 정보
    basic_cols = [
        "diner_idx",
        "diner_name",
        "diner_num_address",
        "diner_lat",
        "diner_lon",
    ]
    df_basic = df[basic_cols].copy()
    df_basic.to_csv(os.path.join(data_dir, "diner_basic.csv"), index=False)
    print(f"Created diner_basic.csv with {len(df_basic)} records")

    # 2. 카테고리 정보 (실제 컬럼명에 맞게 수정)
    category_cols = [
        "diner_idx",
        "diner_category_large",
        "diner_category_middle",
        "diner_category_small",
        "diner_category_detail",
    ]
    df_categories = df[category_cols].copy()
    df_categories.to_csv(os.path.join(data_dir, "diner_categories.csv"), index=False)
    print(f"Created diner_categories.csv with {len(df_categories)} records")

    # 3. 리뷰 정보 (실제 컬럼명에 맞게 수정)
    review_cols = [
        "diner_idx",
        "diner_review_cnt",
        "diner_review_avg",
        "diner_grade",
        "bayesian_score",
        "real_bad_review_percent",
    ]
    df_reviews = df[review_cols].copy()
    df_reviews.to_csv(os.path.join(data_dir, "diner_reviews.csv"), index=False)
    print(f"Created diner_reviews.csv with {len(df_reviews)} records")

    # 4. 메뉴 정보
    menu_cols = ["diner_idx", "diner_menu_name"]
    df_menus = df[menu_cols].copy()
    df_menus.to_csv(os.path.join(data_dir, "diner_menus.csv"), index=False)
    print(f"Created diner_menus.csv with {len(df_menus)} records")

    # 5. 태그 정보
    tag_cols = ["diner_idx", "diner_tag"]
    df_tags = df[tag_cols].copy()
    df_tags.to_csv(os.path.join(data_dir, "diner_tags.csv"), index=False)
    print(f"Created diner_tags.csv with {len(df_tags)} records")

    print("✅ All separated CSV files created successfully!")
