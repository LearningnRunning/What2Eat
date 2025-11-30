# src/utils/search_filter.py
"""검색 필터링 로직 (API 기반)"""

import asyncio
from typing import List, Optional

import pandas as pd
import streamlit as st

from utils.api_client import get_yamyam_ops_client


class SearchFilter:
    """검색 필터링을 담당하는 클래스 (API 기반)"""

    def __init__(self, df_diner: pd.DataFrame = None):
        """
        Args:
            df_diner: 레거시 호환성을 위한 파라미터 (사용하지 않음)
        """
        self.df_diner = df_diner  # 레거시 호환성

    def _map_sort_by(self, sort_by: str) -> str:
        """What2Eat 정렬 기준을 yamyam-ops API 형식으로 변환"""
        sort_mapping = {
            "개인화": "personalization",
            "숨찐맛": "hidden_gem",
            "평점": "rating",
            "리뷰": "review_count",
            "거리순": "distance",
        }
        return sort_mapping.get(sort_by, "rating")

    def apply_filters(
        self,
        user_lat: float,
        user_lon: float,
        radius_km: float = 5.0,
        large_categories: Optional[List[str]] = None,
        middle_categories: Optional[List[str]] = None,
        sort_by: str = "개인화",
        period: str = "전체",
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        모든 필터 적용 (API 호출)

        Args:
            user_lat: 사용자 위도
            user_lon: 사용자 경도
            radius_km: 검색 반경 (km)
            large_categories: 대분류 카테고리 리스트
            middle_categories: 중분류 카테고리 리스트
            sort_by: 정렬 기준
            period: 기간 (현재 미사용)
            limit: 최대 결과 수

        Returns:
            필터링된 음식점 DataFrame
        """
        try:
            # API 클라이언트 가져오기
            client = get_yamyam_ops_client()
            if not client:
                st.error("❌ API 클라이언트를 초기화할 수 없습니다.")
                return pd.DataFrame()

            # 정렬 기준 변환
            api_sort_by = self._map_sort_by(sort_by)

            # 비동기 API 호출을 동기적으로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            restaurants = loop.run_until_complete(
                client.get_restaurants(
                    user_lat=user_lat,
                    user_lon=user_lon,
                    radius_km=radius_km,
                    large_categories=large_categories,
                    middle_categories=middle_categories,
                    sort_by=api_sort_by,
                    limit=limit,
                )
            )
            loop.close()

            if not restaurants:
                return pd.DataFrame()

            # DataFrame으로 변환
            df_results = pd.DataFrame(restaurants)

            # 카카오맵 URL 추가 (없는 경우)
            if "diner_url" not in df_results.columns and "diner_idx" in df_results.columns:
                df_results["diner_url"] = df_results["diner_idx"].apply(
                    lambda idx: f"https://place.map.kakao.com/{idx}"
                )

            return df_results

        except Exception as e:
            st.error(f"❌ 음식점 조회 중 오류가 발생했습니다: {str(e)}")
            return pd.DataFrame()

