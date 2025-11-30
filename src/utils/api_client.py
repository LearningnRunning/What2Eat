"""
yamyam-ops API 클라이언트
Firebase 인증을 사용하여 yamyam-ops PostgreSQL과 통신
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
import streamlit as st

logger = logging.getLogger(__name__)


class YamYamOpsClient:
    """yamyam-ops API 클라이언트"""

    def __init__(self, base_url: str, timeout: float = 10.0):
        """
        Args:
            base_url: yamyam-ops API 베이스 URL
            timeout: 요청 타임아웃 (초)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_firebase_token(self) -> Optional[str]:
        """세션에서 JWT Access Token 가져오기 (yamyam-ops용)"""
        try:
            # 먼저 JWT Access Token 확인 (yamyam-ops API용)
            if hasattr(st.session_state, "jwt_access_token") and st.session_state.jwt_access_token:
                # JWT 토큰 만료 확인
                if hasattr(st.session_state, "jwt_expires_at") and st.session_state.jwt_expires_at:
                    if datetime.now() < st.session_state.jwt_expires_at:
                        return st.session_state.jwt_access_token
                    else:
                        # JWT 토큰이 만료되었으면 갱신 시도
                        if self._refresh_jwt_token():
                            return st.session_state.jwt_access_token
                
            # JWT 토큰이 없거나 만료된 경우, Firebase ID Token으로 폴백
            # (하위 호환성을 위해)
            from utils.auth import get_current_user

            user_info = get_current_user()
            if user_info:
                # Firebase ID Token 가져오기
                if hasattr(st.session_state, "auth_token") and st.session_state.auth_token:
                    return st.session_state.auth_token
                    
            return None
        except Exception as e:
            logger.error(f"Token 가져오기 실패: {e}")
            return None
    
    def _refresh_jwt_token(self) -> bool:
        """JWT Refresh Token으로 Access Token 갱신"""
        try:
            if not hasattr(st.session_state, "jwt_refresh_token") or not st.session_state.jwt_refresh_token:
                return False
            
            api_url = st.secrets.get("YAMYAM_OPS_API_URL")
            if not api_url:
                return False
            
            url = f"{api_url.rstrip('/')}/api/v1/auth/refresh"
            payload = {"refresh_token": st.session_state.jwt_refresh_token}
            
            response = httpx.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                st.session_state.jwt_access_token = data.get("access_token")
                expires_in = data.get("expires_in")
                if expires_in:
                    st.session_state.jwt_expires_at = datetime.now() + timedelta(seconds=expires_in)
                return True
            else:
                logger.error(f"JWT 토큰 갱신 실패: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"JWT 토큰 갱신 중 오류: {e}")
            return False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """
        API 요청 실행 (재시도 로직 포함)

        Args:
            method: HTTP 메서드 (GET, POST, PATCH 등)
            endpoint: API 엔드포인트
            data: 요청 데이터 (POST, PATCH용)
            params: 쿼리 파라미터 (GET용)
            max_retries: 최대 재시도 횟수

        Returns:
            응답 데이터 또는 None (실패 시)
        """
        token = self._get_firebase_token()
        if not token:
            logger.error("Firebase token을 가져올 수 없습니다.")
            return None

        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    if method.upper() == "GET":
                        response = await client.get(url, headers=headers, params=params)
                    elif method.upper() == "POST":
                        response = await client.post(url, headers=headers, json=data, params=params)
                    elif method.upper() == "PATCH":
                        response = await client.patch(url, headers=headers, json=data, params=params)
                    else:
                        logger.error(f"지원하지 않는 HTTP 메서드: {method}")
                        return None

                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP 에러 (시도 {attempt + 1}/{max_retries}): {e.response.status_code} - {e.response.text}"
                )
                if e.response.status_code == 409:  # Conflict (중복 사용자)
                    # 중복은 에러가 아니므로 응답 반환
                    return e.response.json()
                if attempt == max_retries - 1:
                    return None

            except httpx.TimeoutException:
                logger.error(f"타임아웃 (시도 {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return None

            except Exception as e:
                logger.error(f"요청 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None

        return None

    async def sync_user_from_firebase(
        self, firebase_uid: str, email: Optional[str], name: str
    ) -> bool:
        """
        Firebase 회원가입 직후 PostgreSQL에 사용자 생성

        Args:
            firebase_uid: Firebase UID
            email: 이메일
            name: 이름

        Returns:
            성공 여부
        """
        try:
            result = await self._make_request(
                "POST",
                "/users/sync-from-firebase",
                data={"firebase_uid": firebase_uid, "email": email, "name": name},
            )

            if result:
                logger.info(f"사용자 동기화 성공: {firebase_uid}")
                return True
            else:
                logger.error(f"사용자 동기화 실패: {firebase_uid}")
                return False

        except Exception as e:
            logger.error(f"사용자 동기화 중 예외 발생: {e}")
            return False

    async def get_restaurants(
        self,
        user_lat: Optional[float] = None,
        user_lon: Optional[float] = None,
        radius_km: Optional[float] = None,
        large_categories: Optional[list] = None,
        middle_categories: Optional[list] = None,
        sort_by: str = "rating",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> Optional[list]:
        """
        음식점 목록 조회 (필터링 및 정렬)

        Args:
            user_lat: 사용자 위도
            user_lon: 사용자 경도
            radius_km: 검색 반경 (km)
            large_categories: 대분류 카테고리 리스트
            middle_categories: 중분류 카테고리 리스트
            sort_by: 정렬 기준 (rating, distance, review_count 등)
            limit: 최대 결과 수
            offset: 페이지네이션 오프셋

        Returns:
            음식점 리스트 또는 None
        """
        try:
            # 쿼리 파라미터 구성
            params = {}
            if user_lat is not None:
                params["user_lat"] = user_lat
            if user_lon is not None:
                params["user_lon"] = user_lon
            if radius_km is not None:
                params["radius_km"] = radius_km
            if large_categories:
                # 여러 카테고리를 지원하려면 리스트로 전달 (FastAPI가 자동 처리)
                # 단일 값으로 전달하는 경우 첫 번째 값만 사용
                params["diner_category_large"] = large_categories[0] if large_categories else None
            if middle_categories:
                params["diner_category_middle"] = middle_categories[0] if middle_categories else None
            if sort_by:
                params["sort_by"] = sort_by
            if limit is not None:
                params["limit"] = limit
            if offset and offset > 0:
                params["offset"] = offset

            # GET 요청 (httpx가 쿼리 파라미터를 자동으로 URL 인코딩)
            # FastAPI는 trailing slash를 리다이렉트하므로 슬래시 추가
            result = await self._make_request("GET", "/kakao/diners/", params=params)
            return result if result else []

        except Exception as e:
            logger.error(f"음식점 조회 중 예외 발생: {e}")
            return None

    async def get_restaurant_by_idx(self, diner_idx: int) -> Optional[Dict[str, Any]]:
        """
        특정 음식점 상세 조회

        Args:
            diner_idx: 음식점 인덱스

        Returns:
            음식점 정보 또는 None
        """
        try:
            result = await self._make_request("GET", f"/kakao/diners/{diner_idx}/")
            return result

        except Exception as e:
            logger.error(f"음식점 상세 조회 중 예외 발생: {e}")
            return None

    async def get_category_statistics(
        self, category_type: str, parent_category: Optional[str] = None
    ) -> Optional[list]:
        """
        카테고리별 음식점 수 통계 조회

        Args:
            category_type: "large" 또는 "middle"
            parent_category: 중분류 조회 시 대분류 카테고리명

        Returns:
            카테고리 통계 리스트 또는 None
        """
        try:
            params = {}
            if category_type == "large":
                endpoint = "/kakao/diners/categories/large/"
            elif category_type == "middle":
                if not parent_category:
                    logger.error("중분류 조회 시 parent_category 필수")
                    return None
                endpoint = "/kakao/diners/categories/middle/"
                params["large_category"] = parent_category
            else:
                logger.error(f"잘못된 category_type: {category_type}")
                return None

            result = await self._make_request("GET", endpoint, params=params if params else None)
            return result if result else []

        except Exception as e:
            logger.error(f"카테고리 통계 조회 중 예외 발생: {e}")
            return None

    async def save_onboarding_data(
        self, profile_data: Dict[str, Any], ratings_data: Dict[str, int]
    ) -> bool:
        """
        온보딩 완료 시 프로필 데이터를 PostgreSQL에 저장

        Args:
            profile_data: 온보딩 프로필 데이터
            ratings_data: 음식점 평가 데이터

        Returns:
            성공 여부
        """
        try:
            # 데이터 변환 (What2Eat 형식 → yamyam-ops 형식)
            onboarding_data = {
                "location": profile_data.get("location"),
                "location_method": profile_data.get("location_method"),
                "user_lat": st.session_state.get("user_lat"),
                "user_lon": st.session_state.get("user_lon"),
                "birth_year": profile_data.get("birth_year"),
                "gender": profile_data.get("gender"),
                "dining_companions": profile_data.get("dining_companions"),
                "regular_budget": profile_data.get("regular_budget"),
                "special_budget": profile_data.get("special_budget"),
                "spice_level": profile_data.get("spice_level"),
                "allergies": profile_data.get("allergies"),
                "dislikes": profile_data.get("dislikes"),
                "food_preferences_large": profile_data.get("food_preferences_large"),
                "food_preferences_middle": profile_data.get("food_preferences_middle"),
                "restaurant_ratings": ratings_data,
            }

            result = await self._make_request(
                "PATCH", "/users/me/onboarding", data=onboarding_data
            )

            if result:
                logger.info("온보딩 데이터 저장 성공")
                return True
            else:
                logger.error("온보딩 데이터 저장 실패")
                return False

        except Exception as e:
            logger.error(f"온보딩 데이터 저장 중 예외 발생: {e}")
            return False


def get_yamyam_ops_client() -> Optional[YamYamOpsClient]:
    """yamyam-ops API 클라이언트 싱글톤 인스턴스 가져오기"""
    try:
        # secrets에서 API URL 가져오기
        api_url = st.secrets.get("YAMYAM_OPS_API_URL")
        if not api_url:
            logger.warning("YAMYAM_OPS_API_URL이 설정되지 않았습니다.")
            return None

        return YamYamOpsClient(api_url)

    except Exception as e:
        logger.error(f"yamyam-ops 클라이언트 초기화 실패: {e}")
        return None

