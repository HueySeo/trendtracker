import requests
import json

def get_latest_version(url):
    try:
        # URL에서 JSON 데이터 가져오기 (SSL 인증서 검증 비활성화)
        response = requests.get(url, verify=False)
        response.raise_for_status()  # 요청이 성공했는지 확인

        # JSON 데이터 파싱
        data = response.json()

        # latest_version 값 추출
        latest_version = data.get('latest_version')
        return latest_version

    except requests.exceptions.RequestException as e:
        print(f"HTTP 요청 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 중 오류 발생: {e}")
        return None

# URL 설정
url = "https://raw.githubusercontent.com/HueySeo/trendtracker/main/latest_version.json"

# latest_version 값 확인
latest_version = get_latest_version(url)
if latest_version:
    print(f"Latest version: {latest_version}")
else:
    print("latest_version 값을 확인할 수 없습니다.")
