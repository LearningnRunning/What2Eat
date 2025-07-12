from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import streamlit as st
from firebase_admin import auth

from utils.firebase_logger import get_firebase_logger


class SessionManager:
    """로그인 세션 관리 클래스"""

    def __init__(self):
        self.logger = get_firebase_logger()
        self._initialize_session_state()

    def _initialize_session_state(self):
        """세션 상태 초기화"""
        if "user_info" not in st.session_state:
            st.session_state.user_info = None
        if "is_authenticated" not in st.session_state:
            st.session_state.is_authenticated = False
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "token_expires_at" not in st.session_state:
            st.session_state.token_expires_at = None
        if "refresh_token" not in st.session_state:
            st.session_state.refresh_token = None

    def save_user_session(
        self, user_data: Dict[str, Any], id_token: str, refresh_token: str = None
    ):
        """사용자 세션 정보 저장"""
        try:
            # 토큰 만료 시간 설정 (1시간)
            expires_at = datetime.now() + timedelta(hours=1)

            # 세션 상태에 저장
            st.session_state.user_info = user_data
            st.session_state.is_authenticated = True
            st.session_state.auth_token = id_token
            st.session_state.token_expires_at = expires_at
            st.session_state.refresh_token = refresh_token

            # 로그인 로그 기록
            if self.logger.is_available():
                self.logger.log_login(user_data.get("localId"), "email")

            return True
        except Exception as e:
            st.error(f"❌ 세션 저장 중 오류가 발생했습니다: {str(e)}")
            return False

    def load_session_from_browser(self) -> bool:
        """브라우저에서 세션 복원 (Streamlit 세션 상태 기반)"""
        try:
            # Streamlit 세션 상태에서 복원 시도
            return self._restore_from_session_state()

        except Exception as e:
            st.warning(f"세션 복원 실패: {str(e)}")
            return False

    def _restore_from_session_state(self) -> bool:
        """Streamlit 세션 상태에서 복원 시도"""
        try:
            # 이미 인증된 상태라면 토큰 유효성 검사
            if (
                st.session_state.is_authenticated
                and st.session_state.auth_token
                and st.session_state.token_expires_at
            ):
                # 토큰 만료 확인
                if datetime.now() < st.session_state.token_expires_at:
                    # 토큰이 유효하면 Firebase에서 사용자 정보 재검증
                    return self._verify_token_with_firebase()
                else:
                    # 토큰이 만료되었으면 갱신 시도
                    return self._refresh_token_if_possible()

            return False

        except Exception as e:
            st.warning(f"세션 상태 복원 실패: {str(e)}")
            return False

    def _verify_token_with_firebase(self) -> bool:
        """Firebase에서 토큰 유효성 검증"""
        try:
            if not st.session_state.auth_token:
                return False

            # Firebase Admin SDK로 토큰 검증
            decoded_token = auth.verify_id_token(st.session_state.auth_token)

            if decoded_token:
                # 사용자 정보 업데이트
                user = auth.get_user(decoded_token["uid"])

                updated_user_info = {
                    "localId": user.uid,
                    "email": user.email,
                    "emailVerified": user.email_verified,
                    "displayName": user.display_name or user.email.split("@")[0],
                    "photoUrl": user.photo_url,
                    "disabled": user.disabled,
                }

                st.session_state.user_info = updated_user_info
                return True

            return False

        except Exception:
            # 토큰이 유효하지 않으면 로그아웃 처리
            self.clear_session()
            return False

    def _refresh_token_if_possible(self) -> bool:
        """리프레시 토큰으로 새 토큰 발급"""
        try:
            if not st.session_state.refresh_token:
                return False

            # Firebase REST API를 통해 토큰 갱신
            import requests

            api_key = st.secrets.get("FIREBASE_WEB_API_KEY")
            if not api_key:
                return False

            url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"

            payload = {
                "grant_type": "refresh_token",
                "refresh_token": st.session_state.refresh_token,
            }

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                data = response.json()

                # 새 토큰으로 세션 업데이트
                new_id_token = data.get("id_token")
                new_refresh_token = data.get("refresh_token")

                if new_id_token:
                    # 토큰 만료 시간 업데이트
                    st.session_state.auth_token = new_id_token
                    st.session_state.refresh_token = new_refresh_token
                    st.session_state.token_expires_at = datetime.now() + timedelta(
                        hours=1
                    )

                    return self._verify_token_with_firebase()

            return False

        except Exception as e:
            st.warning(f"토큰 갱신 실패: {str(e)}")
            return False

    def is_token_valid(self) -> bool:
        """현재 토큰이 유효한지 확인"""
        if not st.session_state.auth_token or not st.session_state.token_expires_at:
            return False

        # 만료 시간 확인 (5분 여유를 둠)
        buffer_time = timedelta(minutes=5)
        return datetime.now() + buffer_time < st.session_state.token_expires_at

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """현재 로그인된 사용자 정보 반환"""
        if st.session_state.is_authenticated and st.session_state.user_info:
            return st.session_state.user_info
        return None

    def clear_session(self):
        """세션 정보 완전 삭제"""
        try:
            # Streamlit 세션 상태 초기화
            st.session_state.user_info = None
            st.session_state.is_authenticated = False
            st.session_state.auth_token = None
            st.session_state.token_expires_at = None
            st.session_state.refresh_token = None

        except Exception as e:
            st.warning(f"세션 삭제 중 오류: {str(e)}")

    def check_authentication(self) -> bool:
        """인증 상태 확인 및 자동 복원"""
        try:
            # 이미 인증된 상태라면 토큰 유효성만 확인
            if st.session_state.is_authenticated:
                if self.is_token_valid():
                    return True
                else:
                    # 토큰이 만료되었으면 갱신 시도
                    return self._refresh_token_if_possible()

            # 인증되지 않은 상태라면 세션 복원 시도
            return self.load_session_from_browser()

        except Exception:
            # 오류 발생 시 로그아웃 처리
            self.clear_session()
            return False

    def logout(self):
        """로그아웃 처리"""
        try:
            # 로그아웃 로그 기록
            if (
                self.logger.is_available()
                and st.session_state.user_info
                and st.session_state.user_info.get("localId")
            ):
                self.logger.log_user_activity(
                    st.session_state.user_info.get("localId"),
                    "logout",
                    {"method": "manual"},
                )

            # 세션 완전 삭제
            self.clear_session()

            st.success("✅ 로그아웃되었습니다.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 로그아웃 중 오류가 발생했습니다: {str(e)}")


# 전역 세션 매니저 인스턴스
_session_manager = None


def get_session_manager() -> SessionManager:
    """세션 매니저 인스턴스 반환 (싱글톤 패턴)"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
