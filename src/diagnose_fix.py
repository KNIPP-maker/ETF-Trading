import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")

async def test_request(server_name, base_url, content_type_header):
    print(f"\n🧪 테스트: [{server_name}] + [헤더: {content_type_header}]")
    
    # 1. 토큰 발급
    token_url = f"{base_url}/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecretkey": SECRET_KEY
    }
    
    token = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get("access_token")
                    print(f"  ✅ 토큰 발급 성공 (앞 10자리): {token[:10]}...")
                else:
                    print(f"  ❌ 토큰 발급 실패: {await response.text()}")
                    return
    except Exception as e:
        print(f"  ❌ 연결 실패: {e}")
        return

    # 2. 데이터 조회 (삼성전자 현재가)
    data_url = f"{base_url}/api/dostk/mrkcond"
    headers = {
        "Authorization": f"Bearer {token}",
        "content-type": content_type_header,
        "api-id": "ka10004"
    }
    body = {"stk_cd": "005930"}

    async with aiohttp.ClientSession() as session:
        async with session.post(data_url, headers=headers, json=body) as response:
            text = await response.text()
            if response.status == 200:
                print(f"  🎉🎉 성공! 데이터를 받았습니다!")
                print(f"  결과: {text[:50]}...")
                return True
            else:
                print(f"  💥 실패 (코드 {response.status}): {text}")
                return False

async def main():
    print("============================================")
    print("🕵️ 키움증권 API 정밀 진단 시작")
    print("============================================")
    
    if not APP_KEY:
        print("❌ .env 파일이 비어있습니다.")
        return

    # Case 1: 실전 서버 + 띄어쓰기 없는 헤더 (권장)
    success = await test_request("실전서버", "https://api.kiwoom.com", "application/json;charset=UTF-8")
    
    if not success:
        # Case 2: 실전 서버 + 심플 헤더
        await test_request("실전서버(심플)", "https://api.kiwoom.com", "application/json")
        
        # Case 3: 모의 서버 + 띄어쓰기 없는 헤더
        await test_request("모의서버", "https://mockapi.kiwoom.com", "application/json;charset=UTF-8")

    print("\n============================================")
    print("📢 진단 결과 및 해결책")
    print("1. 만약 모든 테스트가 '8005' 실패라면 -> [API 서비스 신청 누락] 입니다.")
    print("   👉 키움 OpenAPI 홈페이지 > 로그인 > 마이페이지 > 'API 서비스 이용신청' 내역 확인")
    print("   👉 신청 상태가 '정상'인지, 계좌번호가 연결되어 있는지 확인하세요.")
    print("2. 하나라도 성공했다면 -> 해당 설정을 kiwoom_client.py에 적용하면 됩니다.")
    print("============================================")

if __name__ == "__main__":
    asyncio.run(main())