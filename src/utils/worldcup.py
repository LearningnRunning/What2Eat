# src/utils/worldcup.py

import math
import random
from typing import List, Dict, Optional, Any
from collections import Counter
import streamlit as st
import requests


class WorldCupManager:
    """맛집 월드컵 관리 클래스"""
    
    def __init__(self, api_url: str = st.secrets.get("API_URL")):
        self.api_url = api_url
        self.category_icons = {
            "카페": "☕",
            "일식": "🍜",
            "한식": "🍲",
            "양식": "🍝",
            "디저트": "🍰",
            "기타": "🍽"
        }

    def get_random_diners(self, n: int = 2) -> List[Dict[str, Any]]:
        """API에서 랜덤 식당 가져오기"""
        try:
            response = requests.get(
                f"{self.api_url}/kakao/diners",
                params={"n": n},
                timeout=5
            )
            
            if response.status_code == 200:
                diners = response.json()
                # API response가 리스트 형태인지 확인
                if isinstance(diners, list):
                    return diners
                # 단일 객체로 반환될 경우를 대비
                elif isinstance(diners, dict):
                    return [diners]
        except Exception as e:
            print(f"랜덤 식당 조회 실패: {e}")
        
        return []

    def get_diner_by_idx(self, diner_idx: int) -> Optional[Dict[str, Any]]:
        """diner_idx로 특정 식당 정보 가져오기"""
        try:
            response = requests.get(
                f"{self.api_url}/kakao/diners/{diner_idx}",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"식당 정보 조회 실패 (diner_idx: {diner_idx}): {e}")
        
        return None
    
    def get_similar_restaurants(self, diner_idx: int) -> List[int]:
        """Redis에서 유사 식당 ID 리스트 가져오기"""
        try:
            response = requests.post(
                self.api_url + "/api/v1/redis/read",
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
    
    def build_tournament_candidates(self, selected_diner: Dict[str, Any], other_diner: Dict[str, Any], size: int = 8) -> List[Dict[str, Any]]:
        """토너먼트 후보 생성 (유저가 선택한 식당 + 유사 식당 6개 + 선택 안한 식당 1개)"""
        # 1단계: 선택한 식당을 첫 번째 후보로 추가
        all_candidates = [selected_diner, other_diner]
        
        # 2단계: 선택한 식당의 유사 식당 ID 가져오기
        selected_diner_idx = selected_diner.get("diner_idx")
        similar_ids = self.get_similar_restaurants(selected_diner_idx) if selected_diner_idx else []
        
        # 3단계: 유사 식당 정보 가져오기
        similar_restaurants = []
        needed = size - 2  # 이미 2개(선택한 식당 + 선택 안한 식당)가 있으므로 6개 필요
        
        if similar_ids:
            existing_ids = {selected_diner["diner_idx"], other_diner["diner_idx"]}
            for sim_id in similar_ids:
                if len(similar_restaurants) >= needed:
                    break
                if sim_id not in existing_ids:
                    diner = self.get_diner_by_idx(sim_id)
                    if diner:
                        similar_restaurants.append(diner)
                        existing_ids.add(sim_id)
        
        # 4단계: 부족하면 추가 랜덤 식당으로 채우기
        if len(similar_restaurants) < needed:
            shortage = needed - len(similar_restaurants)
            additional_random = self.get_random_diners(n=shortage * 2)  # 여유있게 요청
            
            existing_ids = {r["diner_idx"] for r in all_candidates + similar_restaurants}
            for diner in additional_random:
                if len(similar_restaurants) >= needed:
                    break
                if diner["diner_idx"] not in existing_ids:
                    similar_restaurants.append(diner)
                    existing_ids.add(diner["diner_idx"])
        
        # 5단계: 최종 후보 리스트 생성 (선택한 식당 + 선택 안한 식당 + 유사 식당들)
        all_candidates.extend(similar_restaurants[:needed])
        random.shuffle(all_candidates)
        
        return all_candidates
    
    def show_initial_selection(self):
        """초기 2개 식당 선택 화면"""
        if "initial_diners" not in st.session_state:
            initial_diners = self.get_random_diners(n=2)
            if len(initial_diners) < 2:
                st.error("초기 식당을 불러오는데 실패했습니다. 다시 시도해주세요.")
                return False
            st.session_state.initial_diners = initial_diners
        
        st.markdown("<h3 style='text-align:center;'>🎯 시작할 식당을 선택하세요</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:gray;'>선택한 식당과 비슷한 맛집들로 토너먼트가 구성됩니다</p>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        for idx, col in enumerate([col1, col2]):
            with col:
                restaurant = st.session_state.initial_diners[idx]
                self.render_initial_selection_card(restaurant, idx)
        
        return True
    
    def render_initial_selection_card(self, restaurant: Dict[str, Any], idx: int):
        """초기 선택용 식당 카드 렌더링"""
        category_icon = self.category_icons.get(restaurant.get("diner_category_large"), "🍽")
        category_text = self.get_category_text(
            restaurant.get("diner_category_large"),
            restaurant.get("diner_category_middle")
        )
        
        # diner_url이 없을 경우 카카오맵 URL 생성
        diner_url = restaurant.get("diner_url")
        if not diner_url:
            diner_name = restaurant.get("diner_name", "")
            diner_url = f"https://map.kakao.com/?q={diner_name}"
        
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
                <a href='{diner_url}' target='_blank' style='
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
        
        if st.button(
            "🎯 이 식당으로 시작",
            key=f"initial_select_{restaurant['diner_idx']}",
            use_container_width=True,
            type="primary"
        ):
            self.start_tournament_with_selection(idx)
    
    def start_tournament_with_selection(self, selected_idx: int):
        """선택된 식당으로 토너먼트 시작"""
        selected_diner = st.session_state.initial_diners[selected_idx]
        other_diner = st.session_state.initial_diners[1 - selected_idx]
        
        # 토너먼트 후보 생성 (선택한 식당 기반 유사 식당 포함)
        candidates = self.build_tournament_candidates(selected_diner, other_diner, size=8)
        
        if not candidates or len(candidates) < 8:
            st.error(f"토너먼트를 시작하기에 충분한 식당(8개)을 불러오지 못했습니다.")
            return
        
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
        st.session_state.initial_selection_done = True
        # 선택한 식당들을 추적하기 위한 리스트 초기화
        st.session_state.all_selected_diners = []
        
        # 초기 식당 선택 정보 제거
        if "initial_diners" in st.session_state:
            del st.session_state.initial_diners
        
        st.rerun()
    
    def select_winner(self, winner_idx: int):
        """승자 선택 및 다음 라운드 진행"""
        winner = st.session_state.matches[st.session_state.current_match_index][winner_idx]
        st.session_state.winners.append(winner)
        
        # 선택한 식당을 추적 리스트에 추가
        if "all_selected_diners" not in st.session_state:
            st.session_state.all_selected_diners = []
        st.session_state.all_selected_diners.append(winner)
        
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
    
    def render_statistics(self):
        """토너먼트 종료 후 통계 표시"""
        if not st.session_state.get("all_selected_diners"):
            return
        
        st.markdown("---")
        st.markdown("### 📊 토너먼트 통계")
        
        selected_diners = st.session_state.all_selected_diners
        
        # 기본 통계
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 선택 횟수", f"{len(selected_diners)}번")
        with col2:
            unique_count = len(set(d["diner_idx"] for d in selected_diners))
            st.metric("선택한 식당 수", f"{unique_count}개")
        with col3:
            if st.session_state.winners:
                winner = st.session_state.winners[0]
                winner_count = sum(1 for d in selected_diners if d["diner_idx"] == winner["diner_idx"])
                st.metric("우승 식당 선택 횟수", f"{winner_count}번")
        
        # 카테고리 분석
        st.markdown("#### 🍽️ 선호 카테고리")
        categories = [d.get("diner_category_large", "기타") for d in selected_diners if d.get("diner_category_large")]
        
        if categories:
            category_counts = Counter(categories)
            
            # 카테고리별 선택 횟수 표시
            cols = st.columns(min(len(category_counts), 4))
            for idx, (category, count) in enumerate(category_counts.most_common()):
                with cols[idx % len(cols)]:
                    icon = self.category_icons.get(category, "🍽")
                    percentage = (count / len(selected_diners)) * 100
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 10px; 
                                    background-color: #f0f2f6; border-radius: 8px; margin-bottom: 10px;'>
                            <div style='font-size: 30px;'>{icon}</div>
                            <div style='font-weight: bold;'>{category}</div>
                            <div style='color: #666;'>{count}번 ({percentage:.1f}%)</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # 선택한 식당 목록 (확장 가능)
        with st.expander("📝 선택한 모든 식당 보기"):
            # 식당별 선택 횟수 계산
            diner_counts = {}
            for diner in selected_diners:
                idx = diner["diner_idx"]
                if idx not in diner_counts:
                    diner_counts[idx] = {"diner": diner, "count": 0}
                diner_counts[idx]["count"] += 1
            
            # 선택 횟수 순으로 정렬
            sorted_diners = sorted(diner_counts.values(), key=lambda x: x["count"], reverse=True)
            
            for item in sorted_diners:
                diner = item["diner"]
                count = item["count"]
                
                category_text = self.get_category_text(
                    diner.get("diner_category_large"),
                    diner.get("diner_category_middle")
                )
                
                # diner_url 처리
                diner_url = diner.get("diner_url")
                if not diner_url:
                    diner_name = diner.get("diner_name", "")
                    diner_url = f"https://map.kakao.com/?q={diner_name}"
                
                # 우승 식당 표시
                is_winner = (st.session_state.winners and 
                           diner["diner_idx"] == st.session_state.winners[0]["diner_idx"])
                winner_badge = "🏆 " if is_winner else ""
                
                st.markdown(
                    f"""
                    <div style='padding: 10px; margin-bottom: 8px; 
                                border-left: 4px solid {"#FFD700" if is_winner else "#1f77b4"}; 
                                background-color: #f9f9f9;'>
                        <strong>{winner_badge}{diner['diner_name']}</strong> 
                        <span style='color: #666;'>({category_text})</span>
                        <span style='float: right; color: #1f77b4; font-weight: bold;'>{count}번 선택</span>
                        <br>
                        <a href='{diner_url}' target='_blank' style='font-size: 0.9em; color: #1f77b4;'>
                            🔗 상세보기
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    def render_restaurant_card(self, restaurant: Dict[str, Any], idx: int):
        """식당 카드 렌더링"""
        category_icon = self.category_icons.get(restaurant.get("diner_category_large"), "🍽")
        category_text = self.get_category_text(
            restaurant.get("diner_category_large"),
            restaurant.get("diner_category_middle")
        )
        
        # diner_url이 없을 경우 카카오맵 URL 생성
        diner_url = restaurant.get("diner_url")
        if not diner_url:
            diner_name = restaurant.get("diner_name", "")
            diner_url = f"https://map.kakao.com/?q={diner_name}"
        
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
                <a href='{diner_url}' target='_blank' style='
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
            "tournament_finished": False,
            "initial_selection_done": False,
            "all_selected_diners": []
        }.items():
            if key not in st.session_state:
                st.session_state[key] = default
        
        # 토너먼트 시작 전 - 초기 선택 화면
        if not st.session_state.tournament_started or st.session_state.tournament_finished:
            if st.session_state.tournament_finished:
                # 최종 우승자 표시
                if st.session_state.winners:
                    winner = st.session_state.winners[0]
                    st.success(f"🏆 최종 우승: {winner['diner_name']}")
                    
                    # diner_url 처리
                    diner_url = winner.get("diner_url")
                    if not diner_url:
                        diner_name = winner.get("diner_name", "")
                        diner_url = f"https://map.kakao.com/?q={diner_name}"
                    
                    st.markdown(f"[🔗 음식점 보기]({diner_url})")
                    
                    # 통계 표시
                    self.render_statistics()
                
                if st.button("🔄 다시 하기", use_container_width=True):
                    # 모든 세션 상태 초기화
                    for key in ["tournament_started", "tournament_finished", "initial_selection_done", 
                               "matches", "winners", "current_match_index", "round", "initial_diners",
                               "all_selected_diners"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            else:
                # 초기 선택 화면
                self.show_initial_selection()
            return
        
        # 토너먼트 진행 중 - 현재 매치 표시
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


def get_worldcup_manager() -> WorldCupManager:
    """WorldCupManager 싱글톤 인스턴스 반환"""
    if "worldcup_manager" not in st.session_state:
        st.session_state.worldcup_manager = WorldCupManager()
    return st.session_state.worldcup_manager