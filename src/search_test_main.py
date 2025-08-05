"""
검색 엔진 테스트 앱
"""

import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# 프로젝트 루트 경로를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.utils.search_engine import DinerSearchEngine

# 페이지 설정
st.set_page_config(page_title="음식점 검색 엔진 테스트", page_icon="🍽️", layout="wide")

# 제목
st.title("🍽️ 음식점 검색 엔진 테스트")
st.markdown("---")


def handle_feedback(score, text, row):
    """피드백을 처리하는 함수"""
    st.success(f"✅ 평가 완료! {row['name']}에 {score}점을 주셨습니다.")
    if text:
        st.info(f"💬 의견: {text}")

    # 피드백 데이터를 session_state에 저장
    if "feedback_data" not in st.session_state:
        st.session_state.feedback_data = []

    st.session_state.feedback_data.append(
        {
            "diner_idx": row["idx"],
            "diner_name": row["name"],
            "score": score,
            "comment": text,
            "match_type": row["match_type"],
            "timestamp": time.time(),
        }
    )


@st.cache_data
def load_diner_data():
    """데이터를 로드합니다."""
    try:
        # 가장 최신 데이터 파일 사용
        data_file = "data/seoul_data/whatToEat_DB_seoul_diner_20250301_plus_review_cnt.csv"
        df = pd.read_csv(data_file)

        # 기본 정보만 추출 (diner_idx, diner_name)
        if "diner_idx" in df.columns and "diner_name" in df.columns:
            basic_df = df[["diner_idx", "diner_name"]].dropna()
            st.success(f"✅ 데이터 로드 완료: {len(basic_df)}개 음식점")
            return basic_df
        else:
            st.error("❌ 데이터 파일에 필요한 컬럼(diner_idx, diner_name)이 없습니다.")
            return None
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        return None


def get_search_suggestions(query, df_basic, max_suggestions=5):
    """검색어에 대한 추천 검색어를 반환합니다."""
    if not query or len(query) < 2:
        return []
    
    suggestions = []
    
    # 1. 정확한 부분 매칭
    exact_matches = df_basic[df_basic['diner_name'].str.contains(query, case=False, na=False)]
    suggestions.extend(exact_matches['diner_name'].head(max_suggestions).tolist())
    
    # 2. 시작 부분 매칭
    start_matches = df_basic[df_basic['diner_name'].str.startswith(query, na=False)]
    suggestions.extend(start_matches['diner_name'].head(max_suggestions).tolist())
    
    # 3. 자주 검색되는 키워드 기반 추천
    popular_keywords = [
        "맛있는집", "스시로", "피자헛", "맥도날드", "버거킹", 
        "스타벅스", "투썸플레이스", "이디야", "할리스", "파리바게트",
        "교촌치킨", "BBQ", "네네치킨", "굽네치킨", "처갓집",
        "롯데리아", "서브웨이", "도미노피자", "미스터피자", "파파존스"
    ]
    
    for keyword in popular_keywords:
        if query.lower() in keyword.lower() and keyword not in suggestions:
            suggestions.append(keyword)
    
    # 중복 제거 및 최대 개수 제한
    unique_suggestions = list(dict.fromkeys(suggestions))[:max_suggestions]
    
    return unique_suggestions


@st.dialog("🔍 음식점 검색")
def search_dialog(engine: DinerSearchEngine, params: dict):
    """검색 다이얼로그 함수"""
    st.subheader("음식점 검색")
    
    # 검색 입력
    col1, col2 = st.columns([3, 1])
    with col1:
        # 샘플 검색어가 있으면 사용
        default_query = st.session_state.get("sample_query", "")
        query = st.text_input(
            "음식점 이름을 입력하세요",
            placeholder="예: 맛있는집, 스시로, 피자헛...",
            help="정확한 매칭, 부분 매칭, 자모 매칭을 지원합니다.",
            key="dialog_search_input"
        )
        
        # 추천 검색어 표시
        if query and len(query) >= 2:
            results = engine.search(
                    query=query,
                    top_k=params["top_k"],
                    jamo_threshold=params["jamo_threshold"],
                    jamo_candidate_threshold=params["jamo_candidate_threshold"],
                )
            if results.empty:
                st.warning("검색 결과가 없습니다.")
            else:
                st.success(f"✅ 검색 완료! {len(results)}개 결과를 찾았습니다.")
                
                # 추천 검색어 버튼들
                suggestions = results['name'].to_list()
                if suggestions:
                    st.write("💡 추천 검색어:")
                    cols = st.columns(min(len(suggestions), 3))  # 최대 3열로 표시
                    for i, suggestion in enumerate(suggestions):
                        with cols[i % 3]:
                            if st.button(suggestion, key=f"suggest_{suggestion}"):
                                # 선택된 음식점 정보를 session_state에 저장
                                selected_diner = results[results['name'] == suggestion].iloc[0]
                                st.session_state.selected_diner = {
                                    "name": selected_diner['name'],
                                    "idx": selected_diner['idx'],
                                    "match_type": selected_diner['match_type']
                                }
                                st.rerun()

                # 선택된 음식점에 대한 피드백 섹션
                if "selected_diner" in st.session_state:
                    st.markdown("---")
                    st.subheader("📊 선택된 음식점 평가")
                    selected = st.session_state.selected_diner
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{selected['name']}** ({selected['match_type']})")
                    with col2:
                        feedback = st.feedback(
                            options="stars",
                            key=f"feedback_selected_{selected['idx']}",
                        )
                        # 피드백 결과 처리
                        if feedback is not None:
                            score = feedback
                            handle_feedback(score, "선택된 음식점 평가", selected)
                    
                    # 선택 해제 버튼
                    if st.button("선택 해제", key="clear_selection"):
                        del st.session_state.selected_diner
                        st.rerun()

                # 전체 검색 결과에 대한 피드백
                st.markdown("---")
                st.subheader("📊 전체 검색 결과 평가")
                st.info("각 음식점에 대해 1~5점으로 평가해주세요!")

                for i, (_, row) in enumerate(results.iterrows(), 1):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{i}. {row['name']}** ({row['match_type']})")
                    with col2:
                        feedback = st.feedback(
                            options="stars",
                            key=f"feedback_{row['idx']}_{i}",
                        )
                        # 피드백 결과 처리
                        if feedback is not None:
                            score = feedback
                            handle_feedback(score, "전체 검색 결과 평가", row)

    


def main():
    # 사이드바 설정
    st.sidebar.header("🔧 검색 설정")

    # 데이터 로드
    with st.spinner("데이터를 로드하는 중..."):
        df_basic = load_diner_data()

    if df_basic is None:
        st.stop()

    # 데이터를 session_state에 저장 (다이얼로그에서 사용하기 위해)
    st.session_state.df_basic = df_basic

    # 검색 엔진 초기화
    search_engine = DinerSearchEngine()
    search_engine.load_basic_data(df_basic)

    # 검색 파라미터 설정 (기본값)
    st.sidebar.subheader("검색 파라미터")
    top_k = st.sidebar.slider("상위 결과 수", min_value=1, max_value=20, value=5)
    jamo_threshold = st.sidebar.slider(
        "자모 임계값", min_value=0.5, max_value=1.0, value=0.9, step=0.05
    )
    jamo_candidate_threshold = st.sidebar.slider(
        "자모 후보 임계값", min_value=0.3, max_value=0.9, value=0.7, step=0.05
    )

    # 검색 영역
    st.header("🔍 음식점 검색")
    # 다이얼로그에서 설정한 파라미터 사용
    params = st.session_state.get("search_params", {
        "top_k": top_k,
        "jamo_threshold": jamo_threshold,
        "jamo_candidate_threshold": jamo_candidate_threshold
    })
    # 검색 다이얼로그 호출 버튼
    if st.button("🔍 검색하기", type="primary", use_container_width=True):
        search_dialog(search_engine, params)

    # 피드백 데이터 표시
    if hasattr(st.session_state, "feedback_data") and st.session_state.feedback_data:
        st.markdown("---")
        st.subheader("📝 평가 기록")

        feedback_df = pd.DataFrame(st.session_state.feedback_data)
        if not feedback_df.empty:
            # 최근 평가부터 표시
            feedback_df = feedback_df.sort_values("timestamp", ascending=False)

            for _, row in feedback_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{row['diner_name']}** ({row['match_type']})")
                with col2:
                    st.write(f"점수: {'⭐' * int(row['score'])}")
                with col3:
                    if row["comment"]:
                        st.write(f"💬 {row['comment']}")

            # 평가 통계
            st.subheader("📊 평가 통계")
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_score = feedback_df["score"].mean()
                st.metric("평균 점수", f"{avg_score:.1f}점")
            with col2:
                total_feedback = len(feedback_df)
                st.metric("총 평가 수", f"{total_feedback}개")
            with col3:
                match_type_counts = feedback_df["match_type"].value_counts()
                most_common = (
                    match_type_counts.index[0]
                    if not match_type_counts.empty
                    else "없음"
                )
                st.metric("가장 많은 매칭 타입", most_common)

    # 통계 정보
    st.markdown("---")
    st.subheader("📈 데이터 통계")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 음식점 수", f"{len(df_basic):,}개")

    with col2:
        # 음식점명 길이 통계
        name_lengths = df_basic["diner_name"].str.len()
        avg_length = name_lengths.mean()
        st.metric("평균 음식점명 길이", f"{avg_length:.1f}자")

    with col3:
        # 한글 음식점 수
        korean_names = df_basic["diner_name"].str.contains(r"[가-힣]", na=False)
        korean_count = korean_names.sum()
        st.metric("한글 음식점 수", f"{korean_count:,}개")


if __name__ == "__main__":
    main()
