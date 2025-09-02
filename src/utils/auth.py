from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import firebase_admin
import requests
import streamlit as st
from firebase_admin import auth, firestore

from config.firebase_config import initialize_firebase_admin
from utils.firebase_logger import get_firebase_logger
from utils.session_manager import get_session_manager


class FirebaseAuth:
    """Firebase Authentication을 관리하는 클래스"""

    def __init__(self):
        self.session_manager = get_session_manager()

        # if not is_firebase_configured():
        #     st.error("❌ Firebase가 설정되지 않았습니다. 설정을 확인해주세요.")
        #     return

        try:
            # Firebase Admin SDK 초기화
            if not initialize_firebase_admin():
                st.error("❌ Firebase Admin SDK 초기화에 실패했습니다.")
                return
        except Exception as e:
            st.error(f"❌ Firebase 초기화 중 오류가 발생했습니다: {str(e)}")

    def is_available(self) -> bool:
        """Firebase Auth가 사용 가능한지 확인"""
        try:
            firebase_admin.get_app()
            return True
        except ValueError:
            return False

    def sign_up_with_email(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """이메일과 비밀번호로 회원가입"""
        try:
            user = auth.create_user(
                email=email, password=password, email_verified=False, disabled=False
            )

            # 회원가입 성공 시 로그 기록
            logger = get_firebase_logger()
            logger.log_signup(user.uid, "email")

            user_data = {
                "localId": user.uid,
                "email": user.email,
                "emailVerified": user.email_verified,
                "displayName": user.display_name or email.split("@")[0],
                "photoUrl": user.photo_url,
                "disabled": user.disabled,
                "metadata": {
                    "creationTime": user.user_metadata.creation_timestamp,
                    "lastSignInTime": user.user_metadata.last_sign_in_timestamp,
                },
            }

            # 회원가입 후 자동 로그인을 위해 토큰 생성
            custom_token = auth.create_custom_token(user.uid)

            # 세션에 저장
            self.session_manager.save_user_session(
                user_data,
                custom_token.decode(),
                None,  # 회원가입 시에는 refresh_token이 없음
            )

            return user_data

        except auth.EmailAlreadyExistsError:
            st.error("❌ 이미 존재하는 이메일입니다.")
        except auth.InvalidPasswordError:
            st.error("❌ 비밀번호가 너무 약합니다. 6자 이상으로 설정해주세요.")
        except auth.InvalidEmailError:
            st.error("❌ 유효하지 않은 이메일 형식입니다.")
        except Exception as e:
            st.error(f"❌ 회원가입 중 오류가 발생했습니다: {str(e)}")
        return None

    def sign_in_with_email(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """이메일과 비밀번호로 로그인 (Firebase REST API 사용)"""
        try:
            # Firebase Web API Key 가져오기
            FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]

            if not FIREBASE_WEB_API_KEY:
                st.error("❌ Firebase Web API Key가 설정되지 않았습니다.")
                return None

            # Firebase Authentication REST API를 사용하여 인증
            auth_result = self._authenticate_user_with_rest_api(
                email, password, FIREBASE_WEB_API_KEY
            )

            if auth_result["success"]:
                user_data = {
                    "localId": auth_result["uid"],
                    "email": auth_result["email"],
                    "emailVerified": True,
                    "displayName": auth_result["email"].split("@")[0],
                    "photoUrl": None,
                    "idToken": auth_result["id_token"],
                    "refreshToken": auth_result["refresh_token"],
                    "expiresIn": int((datetime.now() + timedelta(hours=1)).timestamp()),
                    "disabled": False,
                }

                # 세션 매니저를 통해 로그인 상태 저장
                if self.session_manager.save_user_session(
                    user_data, auth_result["id_token"], auth_result["refresh_token"]
                ):
                    st.success("✅ 로그인되었습니다!")
                    return user_data
                else:
                    st.error("❌ 세션 저장에 실패했습니다.")
                    return None
            else:
                st.error(f"❌ 로그인 실패: {auth_result['error']}")
                return None

        except Exception as e:
            st.error(f"❌ 로그인 중 오류가 발생했습니다: {str(e)}")
            return None

    def _authenticate_user_with_rest_api(
        self, email: str, password: str, api_key: str
    ) -> Dict[str, Any]:
        """Firebase Authentication REST API를 사용하여 이메일/비밀번호 인증"""
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"

        payload = {"email": email, "password": password, "returnSecureToken": True}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "uid": data.get("localId"),
                "email": data.get("email"),
                "id_token": data.get("idToken"),
                "refresh_token": data.get("refreshToken"),
            }
        except requests.exceptions.RequestException as e:
            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get("error", {}).get(
                    "message", "알 수 없는 오류"
                )
                if "INVALID_LOGIN_CREDENTIALS" in error_message:
                    return {
                        "success": False,
                        "error": "잘못된 이메일 또는 비밀번호입니다.",
                    }
                elif "INVALID_PASSWORD" in error_message:
                    return {"success": False, "error": "잘못된 비밀번호입니다."}
                elif "EMAIL_NOT_FOUND" in error_message:
                    return {"success": False, "error": "존재하지 않는 이메일입니다."}
                elif "INVALID_EMAIL" in error_message:
                    return {"success": False, "error": "잘못된 이메일 형식입니다."}
                else:
                    return {"success": False, "error": f"{error_message}"}
            return {"success": False, "error": f"네트워크 오류: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"인증 실패: {str(e)}"}

    def reset_password(self, email: str) -> bool:
        """비밀번호 재설정 이메일 전송"""
        try:
            # 사용자 존재 여부 확인
            auth.get_user_by_email(email)

            # 비밀번호 재설정 링크 생성
            action_code_settings = auth.ActionCodeSettings(
                url=f"https://{st.get_option('browser.serverAddress')}/reset-password",
                handle_code_in_app=True,
            )

            # 재설정 링크 이메일 전송
            auth.generate_password_reset_link(
                email, action_code_settings=action_code_settings
            )
            return True
        except auth.UserNotFoundError:
            st.error("❌ 등록되지 않은 이메일입니다.")
        except Exception as e:
            st.error(f"❌ 비밀번호 재설정 중 오류가 발생했습니다: {str(e)}")
        return False

    def sign_out(self):
        """로그아웃"""
        self.session_manager.logout()

    def verify_id_token(self, id_token: str) -> Optional[Dict[str, Any]]:
        """ID 토큰 검증"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            st.error(f"❌ 토큰 검증 중 오류가 발생했습니다: {str(e)}")
            return None


def auth_form():
    """통합 인증 폼 (로그인/회원가입/비밀번호 재설정)"""
    firebase_auth = FirebaseAuth()

    if not firebase_auth.is_available():
        st.error("❌ Firebase Authentication이 설정되지 않았습니다.")
        return False

    # 탭 생성
    login_tab, signup_tab, reset_tab = st.tabs(
        [
            "🔑 로그인",
            "👤 회원가입",
            "🔄 비밀번호 재설정",
        ]
    )

    with login_tab:
        st.subheader("로그인")

        # # Google 로그인
        # st.write("**Google 계정으로 로그인:**")
        # google_auth_component()

        # st.divider()

        # 이메일/비밀번호 로그인
        st.write("**이메일로 로그인:**")
        with st.form("login_form"):
            email = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password")
            submit_button = st.form_submit_button("로그인", use_container_width=True)

            if submit_button:
                if email and password:
                    user = firebase_auth.sign_in_with_email(email, password)
                    if user:
                        # 로그인 성공 시 자동으로 페이지 새로고침
                        st.rerun()
                else:
                    st.error("❌ 이메일과 비밀번호를 입력해주세요.")

    with signup_tab:
        st.subheader("회원가입")
        with st.form("signup_form"):
            email = st.text_input("이메일", placeholder="example@email.com")
            password = st.text_input(
                "비밀번호", type="password", help="6자 이상 입력해주세요"
            )
            confirm_password = st.text_input("비밀번호 확인", type="password")
            submit_button = st.form_submit_button("회원가입", use_container_width=True)

            if submit_button:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ 비밀번호가 일치하지 않습니다.")
                    elif len(password) < 6:
                        st.error("❌ 비밀번호는 6자 이상이어야 합니다.")
                    else:
                        user = firebase_auth.sign_up_with_email(email, password)
                        if user:
                            st.success("✅ 회원가입 성공! 자동으로 로그인됩니다.")
                            st.balloons()
                            # 회원가입 후 자동 로그인되므로 페이지 새로고침
                            st.rerun()
                else:
                    st.error("❌ 모든 필드를 입력해주세요.")

    with reset_tab:
        st.subheader("비밀번호 재설정")
        with st.form("reset_form"):
            email = st.text_input("이메일", placeholder="example@email.com")
            submit_button = st.form_submit_button(
                "재설정 이메일 보내기", use_container_width=True
            )

            if submit_button:
                if email:
                    if firebase_auth.reset_password(email):
                        st.success(
                            "✅ 비밀번호 재설정 이메일을 보냈습니다. 이메일을 확인해주세요."
                        )
                else:
                    st.error("❌ 이메일을 입력해주세요.")

    return st.session_state.get("is_authenticated", False)


def check_authentication():
    """인증 상태 확인 및 세션 복원"""
    session_manager = get_session_manager()
    return session_manager.check_authentication()


def get_current_user():
    """현재 로그인된 사용자 정보 반환"""
    session_manager = get_session_manager()
    return session_manager.get_current_user()


def logout():
    """로그아웃"""
    session_manager = get_session_manager()
    session_manager.logout()


def is_first_login() -> bool:
    """현재 사용자가 첫 로그인인지 확인"""
    try:
        user_info = get_current_user()
        if not user_info:
            return False

        uid = user_info.get("localId")
        if not uid:
            return False

        logger = get_firebase_logger()
        if not logger.is_available():
            return False

        # auth_logs에서 해당 사용자의 login 타입 로그를 조회
        login_logs = logger.get_user_logs(uid, limit=10, collection_name="auth_logs")

        # login 타입의 로그만 필터링
        login_records = [log for log in login_logs if log.get("type") == "login"]

        # 첫 번째 로그인이면 True
        return len(login_records) <= 1

    except Exception as e:
        st.error(f"첫 로그인 확인 중 오류: {str(e)}")
        return False


def has_completed_onboarding() -> bool:
    """사용자가 온보딩을 완료했는지 확인"""
    try:
        user_info = get_current_user()
        if not user_info:
            return False

        uid = user_info.get("localId")
        if not uid:
            return False

        logger = get_firebase_logger()
        if not logger.is_available():
            return False

        # onboarding_completed 로그가 있는지 확인
        onboarding_logs = logger.get_user_logs(
            uid, limit=5, collection_name="onboarding_logs"
        )

        for log in onboarding_logs:
            if log.get("type") == "onboarding_completed":
                return True

        return False

    except Exception as e:
        st.error(f"온보딩 완료 확인 중 오류: {str(e)}")
        return False


def require_auth(func):
    """인증이 필요한 페이지에 사용하는 데코레이터"""

    def wrapper(*args, **kwargs):
        if not check_authentication():
            st.warning("⚠️ 로그인이 필요한 서비스입니다.")
            auth_form()
            return
        return func(*args, **kwargs)

    return wrapper


def get_user_profile_from_firestore(uid: str = None) -> Optional[Dict[str, Any]]:
    """Firestore에서 사용자 프로필 데이터를 조회"""
    try:
        # uid가 제공되지 않은 경우 현재 로그인된 사용자의 uid 사용
        if uid is None:
            user_info = get_current_user()
            if not user_info:
                return None
            uid = user_info.get("localId")
            if not uid:
                return None

        # Firebase Admin SDK가 초기화되었는지 확인
        try:
            firebase_admin.get_app()
        except ValueError:
            # Firebase Admin SDK 초기화
            if not initialize_firebase_admin():
                st.error("❌ Firebase Admin SDK 초기화에 실패했습니다.")
                return None

        db = firestore.client()

        # onboarding_logs/profile 문서에서 직접 프로필 데이터 조회
        profile_doc = (
            db.collection("users")
            .document(uid)
            .collection("onboarding_logs")
            .document("profile")
            .get()
        )

        if profile_doc.exists:
            return profile_doc.to_dict()

        return None

    except Exception as e:
        st.error(f"❌ 프로필 데이터 조회 중 오류가 발생했습니다: {str(e)}")
        return None


def organize_user_profile_data(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Firestore에서 가져온 프로필 데이터를 정리하는 헬퍼 함수"""
    if not profile_data:
        return {}

    try:
        # 직접 저장된 프로필 데이터 (detail 래핑 없음)
        organized_data = {
            # 기본 정보
            "basic_info": {
                "age": profile_data.get("birth_year"),
                "gender": profile_data.get("gender"),
                "user_id": profile_data.get("user_id"),
                "created_at": profile_data.get("created_at"),
                "updated_at": profile_data.get("updated_at"),
                "onboarding_version": profile_data.get("onboarding_version", "1.0"),
            },
            # 예산 정보
            "budget_info": {
                "regular_budget": profile_data.get("regular_budget"),
                "special_budget": profile_data.get("special_budget"),
            },
            # 맵기 정보
            "spice_level": profile_data.get("spice_level"),
            # 식사 동반자 정보
            "dining_companions": profile_data.get("dining_companions", []),
            # 못 먹는 것들
            "dislikes": profile_data.get("dislikes", []),
            # 알러지 정보
            "allergies": profile_data.get("allergies", []),
            # 선호 카테고리 (대분류)
            "food_preferences_large": profile_data.get("food_preferences_large", []),
            # 선호 카테고리 (중분류) - 기존 호환성
            "food_preferences": profile_data.get("food_preferences", []),
            # 평점 정보
            "ratings": profile_data.get("ratings", {}),
            # 메타 정보
            "metadata": {
                "created_at": profile_data.get("created_at"),
                "updated_at": profile_data.get("updated_at"),
                "onboarding_version": profile_data.get("onboarding_version"),
            },
        }

        return organized_data

    except Exception as e:
        st.error(f"❌ 프로필 데이터 정리 중 오류가 발생했습니다: {str(e)}")
        return {}


def get_organized_user_profile(uid: str = None) -> Dict[str, Any]:
    """사용자 프로필 데이터를 조회하고 정리해서 반환하는 통합 함수"""
    profile_data = get_user_profile_from_firestore(uid)
    if not profile_data:
        return {}

    return organize_user_profile_data(profile_data)


def get_user_ratings_summary(uid: str = None) -> Dict[str, Any]:
    """사용자 평점 정보를 요약해서 반환"""
    try:
        organized_profile = get_organized_user_profile(uid)
        if not organized_profile:
            return {}

        ratings = organized_profile.get("ratings", {})
        if not ratings:
            return {
                "total_rated": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "rated_restaurants": [],
            }

        # 평점 통계 계산
        rated_restaurants = []
        rating_values = []
        rating_distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

        for restaurant_idx, rating in ratings.items():
            if rating is not None:
                diner_idx_str = restaurant_idx.split("_")[-1]
                diner_idx = int(diner_idx_str)
                rated_restaurants.append(
                    {
                        "diner_idx": diner_idx,
                        "rating": rating,
                    }
                )
                rating_values.append(rating)
                rating_distribution[str(rating)] += 1

        average_rating = sum(rating_values) / len(rating_values) if rating_values else 0

        return {
            "total_rated": len(rated_restaurants),
            "average_rating": round(average_rating, 2),
            "rating_distribution": rating_distribution,
            "rated_restaurants": sorted(
                rated_restaurants, key=lambda x: x.get("timestamp", ""), reverse=True
            ),
        }

    except Exception as e:
        st.error(f"❌ 평점 요약 생성 중 오류가 발생했습니다: {str(e)}")
        return {}


def get_user_preferences_summary(uid: str = None) -> Dict[str, Any]:
    """사용자 선호도 정보를 요약해서 반환"""
    try:
        organized_profile = get_organized_user_profile(uid)
        if not organized_profile:
            return {}

        return {
            "spice_level": organized_profile.get("spice_level"),
            "budget_range": {
                "regular": organized_profile.get("budget_info", {}).get(
                    "regular_budget"
                ),
                "special": organized_profile.get("budget_info", {}).get(
                    "special_budget"
                ),
            },
            "dining_companions": organized_profile.get("dining_companions", []),
            "food_preferences_large": organized_profile.get(
                "food_preferences_large", []
            ),
            "food_preferences": organized_profile.get("food_preferences", []),
            "dislikes": organized_profile.get("dislikes", []),
            "allergies": organized_profile.get("allergies", []),
            "demographic": {
                "age": organized_profile.get("basic_info", {}).get("age"),
                "gender": organized_profile.get("basic_info", {}).get("gender"),
            },
        }

    except Exception as e:
        st.error(f"❌ 선호도 요약 생성 중 오류가 발생했습니다: {str(e)}")
        return {}
