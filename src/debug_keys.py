import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# 윈도우 비동기 에러 방지
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.kiwoom_client import KiwoomRESTClient

load_dotenv()

async def check_real_keys():
    print("============== [키움 API 필드명 정밀 진단] ==============")
    kiwoom = KiwoomRESTClient()
    
    # 1. 토큰 발급
    await kiwoom._ensure_token()
    if not kiwoom.access_token:
        print("❌ 토큰 발급 실패. 진단을 중단합니다.")
        return

    # 2. 잔고 조회 (ka01690) - 필드명 확인용
    print("\n[진단 1] 잔고 조회 (ka01690) 응답 전체 출력:")
    balance = await kiwoom.get_account_balance()
    if balance:
        print(json.dumps(balance, indent=4, ensure_ascii=False))
    else:
        print("❌ 잔고 응답 없음")

    # 3. 주식 현재가 (ka10004) - 필드명 확인용
    print("\n[진단 2] 삼성전자(005930) 현재가 응답 전체 출력:")
    price = await kiwoom.get_current_price("005930")
    if price:
        print(json.dumps(price, indent=4, ensure_ascii=False))
    else:
        print("❌ 시세 응답 없음")

    await kiwoom.close()
    print("\n=======================================================")
    print("👉 위 로그에서 '예수금'이나 '총자산'에 해당하는 영어 필드명(Key)을 찾아주세요.")

if __name__ == "__main__":
    try:
        asyncio.run(check_real_keys())
    except KeyboardInterrupt:
        pass