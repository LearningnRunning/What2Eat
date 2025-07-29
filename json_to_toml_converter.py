import json
import os


def json_to_firebase_key_string(json_file_path):
    """
    JSON 파일을 읽어서 secrets.toml의 FIREBASE_KEY 형식으로 변환하는 함수

    Args:
        json_file_path (str): JSON 파일의 경로

    Returns:
        str: secrets.toml에 사용할 수 있는 FIREBASE_KEY 문자열
    """
    try:
        # JSON 파일 읽기
        with open(json_file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        # JSON을 문자열로 변환하고 이스케이프 처리
        json_string = json.dumps(json_data, separators=(",", ":"))

        # 백슬래시와 따옴표 이스케이프 처리
        escaped_string = json_string.replace("\\", "\\\\").replace('"', '\\"')

        # FIREBASE_KEY 형식으로 반환
        return f'FIREBASE_KEY = "{escaped_string}"'

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {json_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"유효하지 않은 JSON 파일입니다: {json_file_path}")
        return None
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None


def create_secrets_toml(json_file_path, output_path=".streamlit/secrets.toml"):
    """
    JSON 파일을 읽어서 secrets.toml 파일을 생성하는 함수

    Args:
        json_file_path (str): JSON 파일의 경로
        output_path (str): 출력할 secrets.toml 파일의 경로
    """
    firebase_key_line = json_to_firebase_key_string(json_file_path)

    if firebase_key_line:
        # .streamlit 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # secrets.toml 파일 생성
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("# Streamlit secrets configuration\n")
            file.write("# Firebase configuration\n")
            file.write(firebase_key_line + "\n")

        print(f"secrets.toml 파일이 생성되었습니다: {output_path}")
    else:
        print("secrets.toml 파일 생성에 실패했습니다.")


# 사용 예시
if __name__ == "__main__":
    # 현재 프로젝트의 JSON 파일 경로
    json_file = "static/what2eat-e21e3-firebase-adminsdk-fbsvc-2e0f3162c5.json"

    # 1. FIREBASE_KEY 문자열만 생성
    firebase_key_string = json_to_firebase_key_string(json_file)
    if firebase_key_string:
        print("생성된 FIREBASE_KEY:")
        print(firebase_key_string)
        print()

    # 2. secrets.toml 파일 전체 생성
    create_secrets_toml(json_file)
