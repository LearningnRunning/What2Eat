# src/pages/worldcup_page.py
"""맛집 이상형 월드컵 페이지"""

import math
import random

import streamlit as st

from utils.app import What2EatApp
from utils.firebase_logger import get_firebase_logger


def _log_user_activity(activity_type: str, detail: dict) -> bool:
    """사용자 활동 로깅 헬퍼 메서드"""
    logger = get_firebase_logger()
    if "user_info" not in st.session_state or not st.session_state.user_info:
        return False

    uid = st.session_state.user_info.get("localId")
    if not uid:
        return False

    return logger.log_user_activity(uid, activity_type, detail)


def render():
    """월드컵 페이지 렌더링"""
    # 페이지 방문 로그
    _log_user_activity("page_visit", {"page_name": "worldcup"})

    # 앱 인스턴스 가져오기
    if "app" not in st.session_state:
        st.session_state.app = What2EatApp()
    app = st.session_state.app

    st.title("⚽ 맛집 이상형 월드컵")
    df_diner = app.df_diner

    # 세션 초기화
    for key, default in {
        "round": 1,
        "matches": [],
        "current_match_index": 0,
        "winners": [],
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    CATEGORY_ICONS = {
        "카페": "☕",
        "일식": "🍜",
        "한식": "🍲",
        "양식": "🍝",
        "디저트": "🍰",
        "기타": "🍽",
    }

    def get_category_text(large, middle):
        large = (
            None
            if (large is None or (isinstance(large, float) and math.isnan(large)))
            else large
        )
        middle = (
            None
            if (middle is None or (isinstance(middle, float) and math.isnan(middle)))
            else middle
        )
        if not large and not middle:
            return "음식점"
        elif large and middle:
            return f"{large} — {middle}"
        else:
            return large or middle

    def start_tournament(size=8):
        candidates = df_diner.sample(n=size).to_dict("records")
        random.shuffle(candidates)
        matches = []
        for i in range(0, len(candidates), 2):
            pair = candidates[i : i + 2]
            if len(pair) == 2:
                matches.append(pair)
            else:
                matches.append([pair[0], None])
        st.session_state.matches = matches
        st.session_state.current_match_index = 0
        st.session_state.round = 1
        st.session_state.winners = []

    def select_winner(winner_idx):
        # 현재 매치에서 선택된 winner 저장
        winner = st.session_state.matches[st.session_state.current_match_index][winner_idx]
        st.session_state.winners.append(winner)
        st.session_state.current_match_index += 1

        # 라운드 종료 시
        if st.session_state.current_match_index >= len(st.session_state.matches):
            if len(st.session_state.winners) == 1:
                st.session_state.matches = []
                st.success(f"🏆 최종 우승: {st.session_state.winners[0]['diner_name']}")
                st.markdown(
                    f"[음식점 보기]({st.session_state.winners[0]['diner_url']})"
                )
                return
            # 다음 라운드 매치 준비
            next_matches = []
            w = st.session_state.winners
            for i in range(0, len(w), 2):
                pair = w[i : i + 2]
                if len(pair) == 2:
                    next_matches.append(pair)
                else:
                    next_matches.append([pair[0], None])
            st.session_state.matches = next_matches
            st.session_state.winners = []
            st.session_state.current_match_index = 0
            st.session_state.round += 1

    # 토너먼트 시작
    if st.button("토너먼트 시작", type="primary"):
        start_tournament(size=8)

    # 현재 매치 출력
    if (
        st.session_state.matches
        and st.session_state.current_match_index < len(st.session_state.matches)
    ):
        st.markdown(
            f"<h3 style='text-align:center;'>Round {st.session_state.round} — Match {st.session_state.current_match_index + 1}/{len(st.session_state.matches)}</h3>",
            unsafe_allow_html=True,
        )

        current_match = st.session_state.matches[st.session_state.current_match_index]
        col1, col2 = st.columns(2)

        for idx, col in enumerate([col1, col2]):
            with col:
                if idx < len(current_match) and current_match[idx]:
                    r = current_match[idx]
                    st.markdown(
                        f"""
                        <div style='border: 1px solid #e0e0e0; border-radius: 12px;
                                    padding: 20px; text-align: center; 
                                    background-color: #ffffff;
                                    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
                                    margin-bottom: 20px;'>
                            <div style='font-size:60px;'>{CATEGORY_ICONS.get(r["diner_category_large"], "🍽")}</div>
                            <h4 style='margin-top: 10px; margin-bottom: 5px;'>{r['diner_name']}</h4>
                            <p style='color: gray; margin-top: 0;'>{get_category_text(r['diner_category_large'], r.get('diner_category_middle', None))}</p>
                            <a href='{r["diner_url"]}' target='_blank' style='
                                display:inline-block;
                                padding:8px 16px;
                                margin-top:10px;
                                background-color:#1f77b4;
                                color:white;
                                border-radius:6px;
                                text-decoration:none;
                            '>🔍 음식점 보기</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.button(
                        "✅ 선택",
                        key=f"select_button_{r['diner_idx']}",
                        on_click=select_winner,
                        args=(idx,),
                        use_container_width=True,
                    )
                else:
                    st.write("자동 진출 (bye)")

