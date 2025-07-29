# What2Eat Firebase 계정 시스템 및 로깅 기능

## 📋 개요

What2Eat 앱에 Firebase를 기반으로 한 사용자 계정 시스템과 활동 로깅 기능이 추가되었습니다.

**🔐 중요 변경사항**: 이제 모든 기능을 이용하려면 **로그인이 필수**입니다!

## 🔧 추가된 기능

### 1. 필수 로그인 시스템
- **필수 인증**: 모든 앱 기능 이용 시 로그인 필수
- **세션 지속성**: 새로고침이나 탭 재접속 시에도 로그인 상태 유지
- **자동 토큰 갱신**: 토큰 만료 시 자동으로 갱신하여 끊김 없는 사용 경험
- **안전한 로그아웃**: 완전한 세션 정리 및 보안 로그아웃

### 2. 사용자 인증 시스템
- **회원가입**: 이메일/비밀번호 기반 계정 생성 (자동 로그인)
- **로그인**: Firebase REST API를 통한 안전한 로그인
- **세션 관리**: 토큰 기반 세션 관리 및 자동 갱신
- **비밀번호 재설정**: 이메일을 통한 비밀번호 재설정

### 3. 활동 로깅 시스템
- **실시간 로깅**: 모든 사용자 활동 실시간 추적
- **개인화된 분석**: 개인별 활동 패턴 분석 및 통계
- **보안 로깅**: 로그인/로그아웃 등 보안 관련 활동 추적
- **상세 추적**: 페이지 방문, 검색, 클릭 등 모든 상호작용 로깅

### 4. 향상된 사용자 경험
- **환영 페이지**: 로그인하지 않은 사용자를 위한 앱 소개 페이지
- **개인 대시보드**: 활동 로그 및 통계 확인
- **세션 상태 표시**: 현재 세션 상태 실시간 표시
- **끊김 없는 경험**: 토큰 자동 갱신으로 중단 없는 서비스 이용

## 🚀 설치 및 설정

### 1. Firebase 프로젝트 설정

1. [Firebase Console](https://console.firebase.google.com/)에서 새 프로젝트 생성
2. Authentication 활성화 (이메일/비밀번호 로그인 방식 설정)
3. Firestore Database 생성
4. 서비스 계정 키 생성 및 다운로드

### 2. 환경 변수 설정

`env.example` 파일을 참고하여 환경 변수를 설정하세요:

```bash
# Firebase 설정
FIREBASE_WEB_API_KEY=your-firebase-web-api-key-here
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

### 3. Streamlit Secrets 설정 (권장)

`.streamlit/secrets.toml` 파일에 Firebase 설정을 추가하세요:

```toml
# Firebase Web API Key (필수!)
FIREBASE_WEB_API_KEY = "your-web-api-key-here"

[firebase]
api_key = "your-api-key"
auth_domain = "your-project.firebaseapp.com"
project_id = "your-project-id"
storage_bucket = "your-project.appspot.com"
messaging_sender_id = "your-sender-id"
app_id = "your-app-id"

[firebase_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

## 🔐 로그인 필수 시스템

### 작동 방식

1. **초기 접속**: 로그인하지 않은 사용자는 환영 페이지와 로그인 폼만 표시
2. **로그인 후**: 모든 앱 기능(채팅, 랭킹, 활동 로그) 이용 가능
3. **세션 유지**: 브라우저 새로고침이나 탭 재접속 시에도 로그인 상태 유지
4. **자동 갱신**: 토큰 만료 전 자동 갱신으로 끊김 없는 사용

### 세션 지속성 기능

- **토큰 관리**: JWT 토큰 기반 인증 및 자동 갱신
- **상태 복원**: 페이지 새로고침 시 자동 로그인 상태 복원
- **보안 유지**: 토큰 만료 시 안전한 재인증 또는 로그아웃
- **실시간 상태**: 사이드바에서 현재 세션 상태 확인 가능

## 📊 로깅 시스템 구조 (성격별 컬렉션 분리)

### Firestore 데이터 구조

```
users/
  └── {user_id}/
      ├── auth_logs/          🔐 인증 관련 로그
      ├── navigation_logs/    🧭 네비게이션 관련 로그
      ├── search_logs/        🔍 검색 관련 로그
      ├── interaction_logs/   ⚡ 상호작용 관련 로그
      ├── restaurant_logs/    🍽️ 음식점 관련 로그
      └── activity_logs/      📋 기타 활동 로그
          └── {log_id}/
              ├── type: string (활동 유형)
              ├── detail: object (상세 정보)
              ├── timestamp: timestamp
              ├── session_id: string
              └── user_agent: string
```

### 컬렉션별 로그 유형

#### 🔐 인증 로그 (auth_logs)
- `login`: 로그인 (자동 로깅)
- `logout`: 로그아웃 (자동 로깅)
- `signup`: 회원가입 (자동 로깅)

#### 🧭 네비게이션 로그 (navigation_logs)
- `page_visit`: 페이지 방문
- `chat_step_progress`: 채팅 단계 진행
- `location_change`: 위치 변경

#### 🔍 검색 로그 (search_logs)
- `location_search`: 위치 검색
- `menu_search`: 메뉴 검색
- `chat_interaction`: 채팅 상호작용

#### ⚡ 상호작용 로그 (interaction_logs)
- `category_filter`: 카테고리 필터링
- `ranking_view`: 랭킹 조회
- `radius_selection`: 반경 선택
- `search_method_selection`: 검색 방법 선택
- `sort_option_change`: 정렬 옵션 변경

#### 🍽️ 음식점 로그 (restaurant_logs)
- `restaurant_click`: 음식점 클릭 (강화된 정보)
- `restaurant_detail_view`: 음식점 상세정보 조회
- `map_view`: 지도 보기
- `restaurant_favorite`: 음식점 즐겨찾기

### 강화된 음식점 클릭 로깅

음식점 클릭 시 다음 상세 정보가 자동으로 기록됩니다:

```json
{
  "type": "restaurant_click",
  "detail": {
    "restaurant_name": "음식점명",
    "restaurant_url": "카카오맵 URL",
    "restaurant_idx": "음식점 고유 ID",
    "category": "음식점 카테고리",
    "location": "지역 정보",
    "grade": 3.0,              // 쩝슐랭 등급
    "review_count": 150,        // 리뷰 수
    "distance": 0.5,           // 거리(km)
    "from_page": "ranking"     // 클릭한 페이지
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "session_id": "session_123",
  "user_agent": "Mozilla/5.0..."
}
```

## 🎯 사용법

### 1. 첫 방문 및 회원가입

1. 앱 접속 시 환영 페이지 표시
2. "회원가입" 탭에서 이메일/비밀번호로 계정 생성
3. 회원가입 후 자동 로그인되어 모든 기능 이용 가능

### 2. 로그인 및 세션 관리

1. "로그인" 탭에서 기존 계정으로 로그인
2. 로그인 후 브라우저를 닫아도 다음 접속 시 자동 로그인
3. 사이드바에서 현재 세션 상태 확인 가능
4. 필요 시 "로그아웃" 버튼으로 안전한 로그아웃

### 3. 앱 기능 이용

- **🤤 오늘 머먹?**: 대화형 맛집 추천 서비스
- **🕺🏽 니가 가본 그집**: 지역별 맛집 랭킹
- **📊 내 활동 로그**: 개인 활동 기록 및 통계

### 4. 활동 로그 확인

1. 사이드바에서 "📊 내 활동 로그" 선택
2. "📝 최근 활동" 탭에서 모든 활동 내역 확인 (컬렉션별 이모지 표시)
3. "📈 통계" 탭에서 영역별/활동별 통계 확인
4. "📂 컬렉션별 로그" 탭에서 특정 영역의 로그만 조회

## 🔒 보안 및 개인정보 보호

### 강화된 보안 기능

- **토큰 기반 인증**: JWT 토큰을 통한 안전한 세션 관리
- **자동 토큰 갱신**: 만료 전 자동 갱신으로 보안 유지
- **세션 격리**: 개인별 완전 격리된 데이터 저장
- **안전한 로그아웃**: 모든 토큰 및 세션 데이터 완전 삭제

### 개인정보 보호

- Firebase Authentication을 통한 안전한 인증
- 개인 정보는 Firebase 보안 규칙에 따라 보호
- 활동 로그는 개인별로 격리되어 저장
- 민감한 정보는 환경 변수로 관리

## 🐛 문제 해결

### 일반적인 문제들

1. **로그인 실패**
   - Firebase Web API Key 설정 확인
   - 이메일/비밀번호 정확성 확인
   - 네트워크 연결 상태 확인

2. **세션 유지 실패**
   - 브라우저 쿠키/로컬 스토리지 설정 확인
   - 토큰 만료 시간 확인
   - Firebase 프로젝트 설정 확인

3. **로그 저장 실패**
   - Firestore 권한 설정 확인
   - 서비스 계정 키 유효성 확인
   - 네트워크 연결 상태 확인

### 세션 관련 문제

- **자동 로그인 실패**: 브라우저 설정에서 쿠키/로컬 스토리지 허용 확인
- **토큰 만료**: 정상적인 현상이며, 자동 갱신 시도 후 실패 시 재로그인 필요
- **세션 상태 오류**: 페이지 새로고침 또는 로그아웃 후 재로그인

## 📈 향후 개발 계획

- [ ] 소셜 로그인 (Google, 카카오 등)
- [ ] 개인 맞춤 추천 시스템 (활동 로그 기반)
- [ ] 사용자 프로필 관리
- [ ] 즐겨찾기 기능
- [ ] 리뷰 작성 및 관리
- [ ] 친구 기능 및 공유
- [ ] 오프라인 모드 지원
- [ ] 푸시 알림 기능

## 🤝 기여하기

버그 리포트나 기능 제안은 GitHub Issues를 통해 제출해주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 