# What2Eat 🍽️

맛집 추천 AI 서비스

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
make install
```

### 2. 데이터 준비
```bash
# CSV 파일을 분리된 파일들로 변환 (선택사항)
make separate-data
```

### 3. 애플리케이션 실행
```bash
make run
```

## 📊 데이터 구조

### 기존 방식 (단일 CSV)
- `whatToEat_DB_seoul_diner_20250301_plus_review_cnt.csv`: 모든 데이터가 하나의 파일에 포함

### 새로운 방식 (분리된 CSV)
데이터를 용도별로 분리하여 효율적으로 관리:

- **`diner_basic.csv`**: 기본 정보
  - `diner_idx`: 음식점 고유 ID
  - `diner_name`: 음식점 이름
  - `diner_num_address`: 주소
  - `diner_lat`, `diner_lon`: 좌표

- **`diner_categories.csv`**: 카테고리 정보
  - `diner_idx`: 음식점 고유 ID
  - `diner_category_large`: 대분류
  - `diner_category_middle`: 중분류
  - `diner_category_detail`: 소분류
  - `diner_count`: 카테고리별 음식점 수

- **`diner_reviews.csv`**: 리뷰 및 평점 정보
  - `diner_idx`: 음식점 고유 ID
  - `diner_review_cnt`: 리뷰 수
  - `diner_review_avg`: 평균 평점
  - `diner_grade`: 등급

- **`diner_menus.csv`**: 메뉴 정보
  - `diner_idx`: 음식점 고유 ID
  - `diner_menu_name`: 메뉴명 리스트
  - `diner_menu_price`: 메뉴 가격 리스트

- **`diner_tags.csv`**: 태그 정보
  - `diner_idx`: 음식점 고유 ID
  - `diner_tag`: 태그 리스트

## 🔧 사용 가능한 명령어

```bash
make help          # 사용 가능한 명령어 확인
make install       # 의존성 설치
make dev           # 개발 의존성 포함 설치
make run           # 애플리케이션 실행
make test          # 테스트 실행
make lint          # 코드 린팅
make format        # 코드 포맷팅
make separate-data # CSV 파일 분리
make clean         # 캐시 및 임시 파일 정리
```

## 💡 데이터 분리의 장점

1. **메모리 효율성**: 필요한 데이터만 로드하여 메모리 사용량 감소
2. **로딩 속도**: 검색 엔진은 기본 정보만, UI는 필요한 정보만 로드
3. **유지보수성**: 각 데이터 타입별로 독립적인 업데이트 가능
4. **확장성**: 새로운 데이터 타입 추가 시 기존 구조에 영향 없음

## 🔄 마이그레이션

기존 단일 CSV 파일에서 분리된 파일들로 마이그레이션:

```bash
# 1. 데이터 분리 실행
make separate-data

# 2. 애플리케이션 재시작
make run
```

분리된 파일들이 존재하면 자동으로 사용하고, 없으면 기존 단일 파일을 사용합니다. 