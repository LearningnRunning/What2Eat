# src/utils/data_separator.py

"""
기존 단일 CSV 파일을 분리된 파일들로 변환하는 스크립트
"""

import os
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# 이제 config 모듈을 찾을 수 있습니다
from src.utils.data_loading import create_separated_csv_files


def main():
    """
    메인 실행 함수
    """
    print("🚀 CSV 파일 분리 작업을 시작합니다...")

    try:
        # 분리된 CSV 파일들 생성
        create_separated_csv_files()

        print("\n✅ CSV 파일 분리가 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("  - diner_basic.csv: 기본 정보 (ID, 이름, 주소, 좌표)")
        print("  - diner_categories.csv: 카테고리 정보")
        print("  - diner_reviews.csv: 리뷰 및 평점 정보")
        print("  - diner_menus.csv: 메뉴 정보")
        print("  - diner_tags.csv: 태그 정보")

        print("\n💡 이제 애플리케이션을 재시작하면 분리된 파일들을 사용합니다.")

    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    main()
