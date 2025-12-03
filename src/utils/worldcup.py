# src/utils/worldcup.py

import math
import random
from typing import List, Dict, Optional, Any
import streamlit as st
import pandas as pd
import requests


class WorldCupManager:
    """맛집 월드컵 관리 클래스"""
    
    def __init__(self, df_diner: pd.DataFrame, api_url: str = st.secrets.get("API_URL")):
        self.df_diner = df_diner
        self.api_url = api_url
        self.category_icons = {
            "카페": "☕",
            "일식": "🍜",
            "한식": "🍲",
            "양식": "🍝",
            "디저트": "🍰",
            "기타": "🍽"
        }
    
    def get_similar_restaurants(self, diner_idx: int) -> List[int]:
        """Redis에서 유사 식당 ID 리스트 가져오기"""
        try:
            response = requests.post(
                self.api_url,
                json={"keys": [f"diner:{diner_idx}:similar_diner_ids"]},
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                key = f"diner:{diner_idx}:similar_diner_ids"
                similar_ids = data.get(key, [])
                return similar_ids if isinstance(similar_ids, list) else []
        except Exception as e:
            print(f"Redis 조회 실패: {e}")
        
        return []
    
    def build_tournament_candidates(self, size: int = 8) -> List[Dict[str, Any]]:
        """토너먼트 후보 생성 (첫 2개는 랜덤, 나머지는 유사 식당)"""
        # 1단계: 랜덤으로 첫 2개 선택
        initial_candidates = self.df_diner.sample(n=2).to_dict("records")
        
        # 2단계: 첫 번째 식당의 유사 식당 가져오기
        first_diner_idx = initial_candidates[0].get("diner_idx")
        similar_ids = self.get_similar_restaurants(first_diner_idx) if first_diner_idx else []
        
        # 3단계: 유사 식당을 DataFrame에서 찾기
        similar_restaurants = []
        if similar_ids:
            similar_df = self.df_diner[self.df_diner["diner_idx"].isin(similar_ids)]
            similar_restaurants = similar_df.to_dict("records")

        # 4단계: 부족한 경우 두 번째 식당의 유사 식당 추가
        needed = size - 2
        if len(similar_restaurants) < needed:
            if similar_restaurants:
                second_diner_idx = similar_restaurants[0].get("diner_idx")
            else:
                second_diner_idx = initial_candidates[1].get("diner_idx")
            second_similar_ids = self.get_similar_restaurants(second_diner_idx) if second_diner_idx else []
            
            if second_similar_ids:
                # 이미 선택된 ID 제외
                existing_ids = {r["diner_idx"] for r in similar_restaurants}
                new_similar_ids = [sid for sid in second_similar_ids if sid not in existing_ids]
                
                if new_similar_ids:
                    second_similar_df = self.df_diner[self.df_diner["diner_idx"].isin(new_similar_ids)]
                    similar_restaurants.extend(second_similar_df.to_dict("records"))

        # 5단계: 여전히 부족하면 랜덤으로 채우기
        if len(similar_restaurants) < needed:
            existing_indices = {r["diner_idx"] for r in initial_candidates + similar_restaurants}
            remaining_df = self.df_diner[~self.df_diner["diner_idx"].isin(existing_indices)]
            
            if not remaining_df.empty:
                num_random = min(needed - len(similar_restaurants), len(remaining_df))
                random_restaurants = remaining_df.sample(n=num_random).to_dict("records")
                similar_restaurants.extend(random_restaurants)

        # 6단계: 최종 후보 리스트 생성 (초기 2개 + 유사/랜덤)
        all_candidates = initial_candidates + similar_restaurants[:needed]
        random.shuffle(all_candidates)
        
        return all_candidates
    
    def start_tournament(self, size: int = 8):
        """토너먼트 시작"""
        candidates = self.build_tournament_candidates(size)
        
        # 매치 생성
        matches = []
        for i in range(0, len(candidates), 2):
            pair = candidates[i:i + 2]
            if len(pair) == 2:
                matches.append(pair)
            else:
                matches.append([pair[0], None])
        
        st.session_state.matches = matches
        st.session_state.current_match_index = 0
        st.session_state.round = 1
        st.session_state.winners = []
        st.session_state.tournament_started = True
    
    def select_winner(self, winner_idx: int):
        """승자 선택 및 다음 라운드 진행"""
        winner = st.session_state.matches[st.session_state.current_match_index][winner_idx]
        st.session_state.winners.append(winner)
        st.session_state.current_match_index += 1
        
        # 라운드 종료 확인
        if st.session_state.current_match_index >= len(st.session_state.matches):
            if len(st.session_state.winners) == 1:
                # 토너먼트 종료
                st.session_state.matches = []
                st.session_state.tournament_finished = True
                return
            
            # 다음 라운드 준비
            next_matches = []
            winners = st.session_state.winners
            for i in range(0, len(winners), 2):
                pair = winners[i:i + 2]
                if len(pair) == 2:
                    next_matches.append(pair)
                else:
                    next_matches.append([pair[0], None])
            
            st.session_state.matches = next_matches
            st.session_state.winners = []
            st.session_state.current_match_index = 0
            st.session_state.round += 1
    
    @staticmethod
    def get_category_text(large: Any, middle: Any) -> str:
        """카테고리 텍스트 생성"""
        large = None if (large is None or (isinstance(large, float) and math.isnan(large))) else large
        middle = None if (middle is None or (isinstance(middle, float) and math.isnan(middle))) else middle
        
        if not large and not middle:
            return "음식점"
        elif large and middle:
            return f"{large} — {middle}"
        else:
            return large or middle
    
    def render_restaurant_card(self, restaurant: Dict[str, Any], idx: int):
        """식당 카드 렌더링"""
        category_icon = self.category_icons.get(restaurant["diner_category_large"], "🍽")
        category_text = self.get_category_text(
            restaurant["diner_category_large"],
            restaurant.get("diner_category_middle")
        )
        
        st.markdown(
            f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 12px;
                        padding: 20px; text-align: center; 
                        background-color: #ffffff;
                        box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
                        margin-bottom: 20px;'>
                <div style='font-size:60px;'>{category_icon}</div>
                <h4 style='margin-top: 10px; margin-bottom: 5px;'>{restaurant['diner_name']}</h4>
                <p style='color: gray; margin-top: 0;'>{category_text}</p>
                <a href='{restaurant["diner_url"]}' target='_blank' style='
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
            unsafe_allow_html=True
        )
        
        st.button(
            "✅ 선택",
            key=f"select_button_{restaurant['diner_idx']}_{st.session_state.round}_{st.session_state.current_match_index}",
            on_click=self.select_winner,
            args=(idx,),
            use_container_width=True
        )
    
    def render_worldcup_page(self):
        """월드컵 페이지 렌더링"""
        st.title("⚽ 맛집 이상형 월드컵")
        
        # 세션 초기화
        for key, default in {
            "round": 1,
            "matches": [],
            "current_match_index": 0,
            "winners": [],
            "tournament_started": False,
            "tournament_finished": False
        }.items():
            if key not in st.session_state:
                st.session_state[key] = default
        
        # 토너먼트 시작 버튼
        if not st.session_state.tournament_started or st.session_state.tournament_finished:
            if st.button("🎮 토너먼트 시작", type="primary", use_container_width=True):
                self.start_tournament(size=8)
                st.session_state.tournament_finished = False
                st.rerun()
        
        # 최종 우승자 표시
        if st.session_state.tournament_finished and st.session_state.winners:
            winner = st.session_state.winners[0]
            st.success(f"🏆 최종 우승: {winner['diner_name']}")
            st.markdown(f"[🔗 음식점 보기]({winner['diner_url']})")
            
            if st.button("🔄 다시 하기", use_container_width=True):
                st.session_state.tournament_started = False
                st.session_state.tournament_finished = False
                st.rerun()
            return
        
        # 현재 매치 표시
        if (st.session_state.matches and 
            st.session_state.current_match_index < len(st.session_state.matches)):
            
            st.markdown(
                f"<h3 style='text-align:center;'>Round {st.session_state.round} — "
                f"Match {st.session_state.current_match_index + 1}/{len(st.session_state.matches)}</h3>",
                unsafe_allow_html=True
            )
            
            current_match = st.session_state.matches[st.session_state.current_match_index]
            col1, col2 = st.columns(2)
            
            for idx, col in enumerate([col1, col2]):
                with col:
                    if idx < len(current_match) and current_match[idx]:
                        self.render_restaurant_card(current_match[idx], idx)
                    else:
                        st.write("자동 진출 (bye)")


def get_worldcup_manager(df_diner: pd.DataFrame) -> WorldCupManager:
    """WorldCupManager 싱글톤 인스턴스 반환"""
    if "worldcup_manager" not in st.session_state:
        st.session_state.worldcup_manager = WorldCupManager(df_diner)
    return st.session_state.worldcup_manager