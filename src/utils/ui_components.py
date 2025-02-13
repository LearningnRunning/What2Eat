# src/uils/ui_components.py
import random

import streamlit as st
from streamlit_chat import message
from utils.data_processing import grade_to_stars


@st.cache_data
def choice_avatar():
    avatar_style_list =['avataaars','pixel-art-neutral','adventurer-neutral', 'big-ears-neutral']
    seed_list =[100, "Felix"] + list(range(1,140))

    avatar_style = random.choice(avatar_style_list)
    seed = random.choice(seed_list)
    return avatar_style, seed

# 메시지 카운터 변수 추가
message_counter = 0

def my_chat_message(message_txt, choiced_avatar_style, choiced_seed):
    global message_counter
    message_counter += 1
    return message(message_txt, avatar_style=choiced_avatar_style, seed=choiced_seed, key=f"message_{message_counter}")

def display_results(df_filtered, radius_int, radius_str, avatar_style, seed):
    df_filtered = df_filtered.sort_values(by="bayesian_score", ascending=False)
    if not len(df_filtered):
        my_chat_message("헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐", avatar_style, seed)
    else:
        # 나쁜 리뷰와 좋은 리뷰를 분리
        bad_reviews = []
        good_reviews = []
        df_filtered['diner_category_middle'].fillna(df_filtered['diner_category_large'], inplace=True)

        for _, row in df_filtered.iterrows():
            if row["real_bad_review_percent"] is not None and row["real_bad_review_percent"] > 20:
                bad_reviews.append(row)  # 나쁜 리뷰로 분리
            else:
                good_reviews.append(row)  # 좋은 리뷰로 분리

        # 소개 메시지 초기화
        introduction = f"{radius_str} 근처 \n {len(df_filtered)}개의 인증된 곳 발견!\n\n"

        # 좋은 리뷰 먼저 처리
        for row in good_reviews:
            introduction += generate_introduction(
                row["diner_idx"],
                row["diner_name"],
                radius_int,
                int(row["distance"] * 1000),
                row["diner_category_middle"],
                row["diner_grade"],
                row["diner_tag"],
                row["diner_menu_name"],
                row.get("score"),
            )

        # 나쁜 리뷰 마지막에 처리
        for row in bad_reviews:
            introduction += f"\n🚨 주의: [{row['diner_name']}](https://place.map.kakao.com/{row['diner_idx']})의 비추 리뷰가 {round(row['real_bad_review_percent'], 2)}%입니다.\n"

        # 최종 메시지 전송
        my_chat_message(introduction, avatar_style, seed)



def generate_introduction(
    diner_idx,
    diner_name,
    radius_kilometers,
    distance,
    diner_category_small,
    diner_grade,
    diner_tags,
    diner_menus,
    recommend_score=None,
):
    # 기본 정보
    introduction = f"[{diner_name}](https://place.map.kakao.com/{diner_idx})"

    if diner_name:
        introduction += f" ({diner_category_small})\n"
    else:
        introduction += "\n"

    # 추천 점수 및 주요 정보
    if recommend_score is not None:
        introduction += f"🍽️ 쩝쩝상위 {diner_grade}%야!\n"
        introduction += f"👍 추천지수: {recommend_score}%\n"
        if diner_tags:
            introduction += f"🔑 키워드: {'/'.join(diner_tags)}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {'/'.join(diner_menus[:3])}\n"
    else:
        introduction += f"{grade_to_stars(diner_grade)}"
        if diner_tags:
            introduction += f"🔑 키워드: {'/'.join(diner_tags[:5])}\n"
        if diner_menus:
            introduction += f"🍴 메뉴: {'/'.join(diner_menus[:3])}\n"

    # 거리 정보 추가
    if radius_kilometers >= 0.5:
        introduction += f"📍 여기서 {distance}M 정도 떨어져 있어!\n\n"
    else:
        introduction += "\n\n"

    return introduction