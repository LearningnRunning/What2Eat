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
st.set_page_config(page_title="  검색 엔진 테스트", page_icon="🍽️", layout="wide")

# 제목
st.title("🍽️   검색 엔진 테스트")
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
        data_file = "data/whatToEat_DB_seoul_diner_20250301.csv"
        df = pd.read_csv(data_file)

        # 기본 정보만 추출 (diner_idx, diner_name)
        if "diner_idx" in df.columns and "diner_name" in df.columns:
            basic_df = df[["diner_idx", "diner_name"]].dropna()
            st.success(f"✅ 데이터 로드 완료: {len(basic_df)}개  ")
            return basic_df
        else:
            st.error("❌ 데이터 파일에 필요한 컬럼(diner_idx, diner_name)이 없습니다.")
            return None
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {str(e)}")
        return None


def main():
    # 사이드바 설정
    st.sidebar.header("🔧 검색 설정")

    # 데이터 로드
    with st.spinner("데이터를 로드하는 중..."):
        df_basic = load_diner_data()

    if df_basic is None:
        st.stop()

    # 검색 엔진 초기화
    search_engine = DinerSearchEngine()
    search_engine.load_basic_data(df_basic)

    # 검색 파라미터 설정
    st.sidebar.subheader("검색 파라미터")
    top_k = st.sidebar.slider("상위 결과 수", min_value=1, max_value=20, value=5)
    jamo_threshold = st.sidebar.slider(
        "자모 임계값", min_value=0.5, max_value=1.0, value=0.9, step=0.05
    )
    jamo_candidate_threshold = st.sidebar.slider(
        "자모 후보 임계값", min_value=0.3, max_value=0.9, value=0.7, step=0.05
    )

    # 검색 영역
    st.header("🔍   검색")

    # 검색 입력과 결과를 popover로 분리
    with st.popover("🔍 검색하기", help="클릭하여 검색창을 열어보세요"):
        st.subheader("  검색")

        # 검색 입력
        col1, col2 = st.columns([3, 1])
        with col1:
            # 샘플 검색어가 있으면 사용
            default_query = st.session_state.get("sample_query", "")
            query = st.text_input(
                "  이름을 입력하세요",
                value=default_query,
                placeholder="예: 맛있는집, 스시로, 피자헛...",
                help="정확한 매칭, 부분 매칭, 자모 매칭을 지원합니다.",
            )
            # 샘플 검색어 사용 후 초기화
            if "sample_query" in st.session_state:
                del st.session_state.sample_query

        with col2:
            search_button = st.button("검색", type="primary", use_container_width=True)

        # 검색 실행
        if search_button and query.strip():
            # 검색 결과를 session_state에 저장
            st.session_state.search_query = query.strip()
            st.session_state.search_results = None
            st.session_state.searching = True
            st.rerun()

    # 검색 결과 표시 (메인 화면)
    if hasattr(st.session_state, "searching") and st.session_state.searching:
        st.subheader("🔍 검색 결과")

        # 검색 실행
        with st.spinner("검색 중..."):
            try:
                results = search_engine.search(
                    query=st.session_state.search_query,
                    top_k=top_k,
                    jamo_threshold=jamo_threshold,
                    jamo_candidate_threshold=jamo_candidate_threshold,
                )

                # 검색 완료 상태로 변경
                st.session_state.search_results = results
                st.session_state.searching = False

            except Exception as e:
                st.error(f"❌ 검색 중 오류가 발생했습니다: {str(e)}")
                st.session_state.searching = False

    # 검색 결과가 있으면 표시
    if (
        hasattr(st.session_state, "search_results")
        and st.session_state.search_results is not None
    ):
        results = st.session_state.search_results

        if not results.empty and "검색 결과 없음" not in results["match_type"].values:
            st.success(f"✅ 검색 완료! {len(results)}개 결과를 찾았습니다.")

            # st.write_stream을 사용하여 결과를 스트리밍으로 표시
            def generate_results():
                yield f"**검색어**: {st.session_state.search_query}\n\n"
                yield f"**총 {len(results)}개 결과**\n\n"

                for i, (_, row) in enumerate(results.iterrows(), 1):
                    yield f"### {i}. {row['name']}\n"
                    yield f"- **  ID**: {row['idx']}\n"
                    yield f"- **매칭 타입**: {row['match_type']}\n"
                    if "jamo_score" in row and pd.notna(row["jamo_score"]):
                        yield f"- **자모 점수**: {row['jamo_score']:.2f}\n"
                    yield "\n"
                    time.sleep(0.1)  # 스트리밍 효과

                yield "---\n"
                yield "**검색 통계**\n"
                match_counts = results["match_type"].value_counts()
                for match_type, count in match_counts.items():
                    yield f"- {match_type}: {count}개\n"

            # 스트리밍으로 결과 표시
            st.write_stream(generate_results)

            # 각 결과에 대한 피드백 버튼
            st.subheader("📊 검색 결과 평가")
            st.info("각  에 대해 1~5점으로 평가해주세요!")

            for i, (_, row) in enumerate(results.iterrows(), 1):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{i}. {row['name']}** ({row['match_type']})")
                with col2:
                    feedback = st.feedback(
                        options="stars",
                        key=f"feedback_{row['idx']}_{i}",
                        # on_submit=lambda score, text: handle_feedback(score, text, row),
                    )
                    st.write(f"feedback: {feedback}")

        else:
            st.warning("⚠️ 검색 결과가 없습니다.")
            st.info("💡 다른 검색어를 시도해보세요.")

    # 샘플 검색어 제안
    st.markdown("---")
    st.subheader("💡 샘플 검색어")

    sample_queries = [
        "맛있는집",
        "스시로",
        "피자헛",
        "맥도날드",
        "버거킹",
        "스타벅스",
        "투썸플레이스",
        "이디야",
        "할리스",
        "파리바게트",
    ]

    cols = st.columns(5)
    for i, query_sample in enumerate(sample_queries):
        with cols[i % 5]:
            if st.button(query_sample, key=f"sample_{i}"):
                st.session_state.sample_query = query_sample
                st.rerun()

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
        st.metric("총   수", f"{len(df_basic):,}개")

    with col2:
        #  명 길이 통계
        name_lengths = df_basic["diner_name"].str.len()
        avg_length = name_lengths.mean()
        st.metric("평균  명 길이", f"{avg_length:.1f}자")

    with col3:
        # 한글   수
        korean_names = df_basic["diner_name"].str.contains(r"[가-힣]", na=False)
        korean_count = korean_names.sum()
        st.metric("한글   수", f"{korean_count:,}개")


if __name__ == "__main__":
    main()
