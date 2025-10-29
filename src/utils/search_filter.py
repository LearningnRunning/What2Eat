# src/utils/search_filter.py
"""검색 필터링 로직"""

from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
import streamlit as st

from utils.data_processing import haversine


class SearchFilter:
    """검색 필터링을 담당하는 클래스"""

    def __init__(self, df_diner: pd.DataFrame):
        self.df_diner = df_diner

    def filter_by_location(
        self, user_lat: float, user_lon: float, radius_km: float = 5.0
    ) -> pd.DataFrame:
        """위치 기반 필터링"""
        # 거리 계산
        df_filtered = self.df_diner.copy()
        df_filtered["distance"] = df_filtered.apply(
            lambda row: haversine(
                user_lat, user_lon, row["diner_lat"], row["diner_lon"]
            ),
            axis=1,
        )

        # 반경 내 필터링
        df_filtered = df_filtered[df_filtered["distance"] <= radius_km]

        return df_filtered

    def filter_by_category(
        self,
        df: pd.DataFrame,
        large_categories: Optional[List[str]] = None,
        middle_categories: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """카테고리 기반 필터링"""
        df_filtered = df.copy()

        # 대분류 필터링
        if large_categories:
            df_filtered = df_filtered[
                df_filtered["diner_category_large"].isin(large_categories)
            ]

        # 중분류 필터링
        if middle_categories:
            df_filtered = df_filtered[
                df_filtered["diner_category_middle"].isin(middle_categories)
            ]

        return df_filtered

    def filter_by_period(
        self, df: pd.DataFrame, period: str = "전체"
    ) -> pd.DataFrame:
        """기간 기반 필터링 (리뷰 날짜 기준)"""
        # 현재 데이터에 날짜 정보가 없으므로 전체 반환
        # 향후 리뷰 날짜 데이터가 추가되면 구현
        if period == "전체":
            return df
        elif period == "1개월":
            # TODO: 리뷰 날짜 컬럼이 있으면 구현
            return df
        elif period == "3개월":
            # TODO: 리뷰 날짜 컬럼이 있으면 구현
            return df
        return df

    def sort_results(self, df: pd.DataFrame, sort_by: str = "개인화") -> pd.DataFrame:
        """정렬 로직"""
        df_sorted = df.copy()

        if sort_by == "개인화":
            # 베이지안 점수 기준
            df_sorted = df_sorted.sort_values(
                by=["diner_grade", "bayesian_score"], ascending=[False, False]
            )
        elif sort_by == "숨찐맛":
            # 쩝슐랭 등급 기준
            df_sorted = df_sorted.sort_values(
                by=["diner_grade", "diner_review_cnt"], ascending=[False, False]
            )
        elif sort_by == "평점":
            # 평점 기준
            df_sorted = df_sorted.sort_values(
                by=["diner_grade", "bayesian_score"], ascending=[False, False]
            )
        elif sort_by == "리뷰":
            # 리뷰 개수 기준
            df_sorted = df_sorted.sort_values(
                by=["diner_review_cnt", "diner_grade"], ascending=[False, False]
            )
        elif sort_by == "거리순":
            # 거리 기준
            if "distance" in df_sorted.columns:
                df_sorted = df_sorted.sort_values(
                    by=["distance", "diner_grade"], ascending=[True, False]
                )

        return df_sorted

    def apply_filters(
        self,
        user_lat: float,
        user_lon: float,
        radius_km: float = 5.0,
        large_categories: Optional[List[str]] = None,
        middle_categories: Optional[List[str]] = None,
        sort_by: str = "개인화",
        period: str = "전체",
    ) -> pd.DataFrame:
        """모든 필터 적용"""
        # 1. 위치 기반 필터링
        df_filtered = self.filter_by_location(user_lat, user_lon, radius_km)

        # 2. 카테고리 필터링
        df_filtered = self.filter_by_category(
            df_filtered, large_categories, middle_categories
        )

        # 3. 기간 필터링
        df_filtered = self.filter_by_period(df_filtered, period)

        # 4. 정렬
        df_filtered = self.sort_results(df_filtered, sort_by)

        return df_filtered

