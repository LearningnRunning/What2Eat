#!/usr/bin/env python3
"""
분리된 데이터 로딩 테스트 스크립트
"""

import os
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))

from config.constants import GUIDE_IMG_PATH, LOGO_SMALL_IMG_PATH, LOGO_TITLE_IMG_PATH
from utils.data_loading import load_static_data


def test_separated_data_loading():
    """분리된 데이터 로딩을 테스트합니다."""
    print("🧪 분리된 데이터 로딩 테스트를 시작합니다...")

    try:
        # 데이터 로딩
        df_diner, banner_image, icon_image, guide_image = load_static_data(
            LOGO_TITLE_IMG_PATH, LOGO_SMALL_IMG_PATH, GUIDE_IMG_PATH
        )

        print("✅ 데이터 로딩 성공!")
        print(f"📊 총 음식점 수: {len(df_diner):,}개")
        print(f"📋 컬럼 수: {len(df_diner.columns)}개")
        print("📝 컬럼 목록:")
        for i, col in enumerate(df_diner.columns, 1):
            print(f"  {i:2d}. {col}")

        # 기본 정보 확인
        print("\n🔍 기본 정보 확인:")
        print(f"  - diner_idx: {df_diner['diner_idx'].dtype}")
        print(f"  - diner_name: {df_diner['diner_name'].dtype}")
        print(f"  - diner_lat: {df_diner['diner_lat'].dtype}")
        print(f"  - diner_lon: {df_diner['diner_lon'].dtype}")

        # 카테고리 정보 확인
        print("\n🏷️ 카테고리 정보 확인:")
        print(f"  - diner_category_large: {df_diner['diner_category_large'].dtype}")
        print(f"  - diner_category_middle: {df_diner['diner_category_middle'].dtype}")
        print(f"  - diner_category_small: {df_diner['diner_category_small'].dtype}")

        # 리뷰 정보 확인
        print("\n⭐ 리뷰 정보 확인:")
        print(f"  - diner_review_cnt: {df_diner['diner_review_cnt'].dtype}")
        print(f"  - diner_review_avg: {df_diner['diner_review_avg'].dtype}")
        print(f"  - diner_grade: {df_diner['diner_grade'].dtype}")

        # 메뉴 정보 확인
        print("\n🍽️ 메뉴 정보 확인:")
        print(f"  - diner_menu_name: {type(df_diner['diner_menu_name'].iloc[0])}")
        sample_menu = df_diner["diner_menu_name"].iloc[0]
        print(
            f"  - 샘플 메뉴: {sample_menu[:3] if len(sample_menu) > 3 else sample_menu}"
        )

        # 태그 정보 확인
        print("\n🏷️ 태그 정보 확인:")
        print(f"  - diner_tag: {type(df_diner['diner_tag'].iloc[0])}")
        sample_tag = df_diner["diner_tag"].iloc[0]
        print(f"  - 샘플 태그: {sample_tag[:3] if len(sample_tag) > 3 else sample_tag}")

        # URL 생성 확인
        print("\n🔗 URL 생성 확인:")
        print(f"  - diner_url: {df_diner['diner_url'].iloc[0]}")

        print("\n✅ 모든 테스트가 성공적으로 완료되었습니다!")

    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    test_separated_data_loading()
