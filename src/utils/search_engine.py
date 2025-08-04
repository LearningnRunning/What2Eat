"""
음식점 검색 엔진
"""

import logging

import pandas as pd

# 로거 설정
logger = logging.getLogger(__name__)

import re

from fuzzywuzzy import fuzz
from jamo import hangul_to_jamo


class DinerSearchEngine:
    """음식점 검색 엔진"""

    def __init__(self):
        self.diner_infos = []

    def load_basic_data(self, df_basic):
        """
        기본 정보만 로드하여 검색 엔진을 초기화합니다.

        Args:
            df_basic: diner_idx, diner_name이 포함된 기본 정보 DataFrame
        """
        self.diner_infos = []

        for _, row in df_basic.iterrows():
            self.diner_infos.append(
                {"idx": str(row["diner_idx"]), "name": row["diner_name"]}
            )

        logger.info(f"검색 엔진 초기화 완료: {len(self.diner_infos)}개 음식점")

    def search(
        self,
        query: str,
        top_k: int = 5,
        jamo_threshold: float = 0.9,
        jamo_candidate_threshold: float = 0.7,
    ) -> pd.DataFrame:
        """
        음식점을 검색합니다.

        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 수

        Returns:
            검색 결과 DataFrame
        """
        norm_query = self._normalize(query)

        # 1. 정확한 매칭
        exact_matches = [
            d for d in self.diner_infos if self._normalize(d["name"]) == norm_query
        ]
        if exact_matches:
            results = pd.DataFrame(exact_matches).assign(match_type="정확한 매칭")
            return self._add_kakao_map_links(results)

        # 2. 부분 매칭
        partial_matches = [
            d for d in self.diner_infos if norm_query in self._normalize(d["name"])
        ]
        if partial_matches:
            results = pd.DataFrame(partial_matches).assign(match_type="부분 매칭")
            return self._add_kakao_map_links(results)

        # 3. 자모 기반 직접 매칭
        jamo_scores = []
        for d in self.diner_infos:
            is_jamo, score = self._jamo_similarity(
                norm_query, self._normalize(d["name"]), threshold=jamo_threshold
            )
            if is_jamo:
                results = pd.DataFrame(
                    [
                        {
                            "name": d["name"],
                            "idx": d["idx"],
                            "jamo_score": score,
                            "match_type": "자모 매칭",
                        }
                    ]
                )
                return self._add_kakao_map_links(results)
            else:
                if score > jamo_candidate_threshold:
                    jamo_scores.append((d, score))

        jamo_top = sorted(jamo_scores, key=lambda x: x[1], reverse=True)[:top_k]

        if jamo_top:
            results = pd.DataFrame(jamo_top).assign(match_type="자모 매칭")
            return self._add_kakao_map_links(results)

        return pd.DataFrame().assign(match_type="검색 결과 없음")

    def _normalize(self, text: str) -> str:
        """
        텍스트를 정규화합니다.

        Args:
            text: 정규화할 텍스트

        Returns:
            정규화된 텍스트
        """
        return re.sub(r"[^가-힣a-zA-Z0-9]", "", text.lower().strip())

    def _jamo_similarity(
        self, a: str, b: str, threshold: float = 0.9
    ) -> tuple[bool, float]:
        """
        두 문자열의 자모 유사도를 계산합니다.

        Args:
            a: 첫 번째 문자열
            b: 두 번째 문자열
            threshold: 자모 유사도 임계값

        Returns:
            (자모 매칭 여부, 유사도 점수)
        """
        a_jamo = " ".join(hangul_to_jamo(a))
        b_jamo = " ".join(hangul_to_jamo(b))
        score = fuzz.ratio(a_jamo, b_jamo)

        if score > threshold:
            return True, score
        else:
            matches = sum(x == y for x, y in zip(a_jamo, b_jamo, strict=False))
            return False, matches / max(len(a_jamo), len(b_jamo), 1)

    def _add_kakao_map_links(self, df: pd.DataFrame) -> pd.DataFrame:
        """검색 결과에 카카오맵 링크를 추가합니다."""
        if df.empty:
            return df

        # 카카오맵 링크 컬럼 추가
        df = df.copy()
        # name 컬럼을 카카오맵 링크로 변환
        df["name"] = df.apply(
            lambda row: f"[{row['name']}](https://place.map.kakao.com/{row['idx']})",
            axis=1,
        )

        return df
