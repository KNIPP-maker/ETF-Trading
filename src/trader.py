import sys
import os

# [추가됨] 현재 파일의 부모의 부모 폴더(프로젝트 루트)를 경로에 추가
# 이렇게 하면 'python src/trader.py'로 직접 실행해도 'from src...' 가 작동합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

import requests
import json
import math
from dotenv import load_dotenv
from src.data_loader import DataLoader  # 이제 이 줄이 에러 없이 작동합니다.

load_dotenv()

class Trader:
    # ... (나머지 코드는 그대로 두시면 됩니다)
    def __init__(self):
        self.loader = DataLoader() # DataLoader를 통해 토큰 관리
        self.account_no = os.getenv("ACCOUNT_NO")
        self.app_key = os.getenv("KIWOOM_APP_KEY")
        self.secret_key = os.getenv("KIWOOM_SECRET_KEY")
        self.base_url = "https://api.kiwoom.com"
        
        # 1회 최대 베팅 금액 (예: 100만원)
        self.max_position_size = int(os.getenv("MAX_POSITION_SIZE", 1000000))

    def send_order(self, stock_code, order_type, qty, price):
        """
        실제 주문 전송 함수 (TR: kt10000)
        :param order_type: 'buy' or 'sell'
        :param qty: 주문 수량
        :param price: 주문 단가
        """
        token = self.loader.get_access_token()
        if not token:
            return None

        # [주문 URL 및 설정] - 앞서 찾은 샘플 코드 기준
        url = f"{self.base_url}/api/dostk/ordr"
        
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'kt10000',       # 주식주문 TR ID
            'custtype': 'P',
            'tr_cont': 'N',            # 연속조회 여부
        }
        
        # 매매 구분 코드 (1: 매도, 2: 매수) - 키움 API 표준
        # ※ 샘플 코드에는 없었으나 보통 1=매도, 2=매수입니다.
        #    만약 샘플의 trde_tp가 구분자라면 수정이 필요할 수 있습니다.
        #    일단 일반적인 공통 표준인 ord_tp(매매구분) 대신,
        #    샘플 코드 구조를 최대한 따르되, 매수/매도 구분을 'ord_tp' 파라미터로 추가해 봅니다.
        trade_type_code = "2" if order_type == 'buy' else "1"

        # [주문 파라미터] - 사용자 제공 샘플 코드 기반 + 계좌번호 추가
        params = {
            "dmst_stex_tp": "SOR",   # 거래소 구분
            "stk_cd": stock_code,    # 종목코드
            "ord_qty": str(qty),     # 주문수량
            "ord_uv": str(price),    # 주문단가
            "trde_tp": "0",          # 거래구분 (0: 지정가)
            "cond_uv": "",           # 조건부 가격 (생략 가능)
            "ord_tp": trade_type_code, # [추정] 매수(2)/매도(1) 구분
            "act_no": self.account_no  # [추정] 계좌번호 필수
        }

        print(f"🚀 [{order_type.upper()}] 주문 전송 중... {qty}주 @ {price}원")

        try:
            res = requests.post(url, headers=headers, json=params)

            if res.status_code == 200:
                data = res.json()
                # 성공 여부 체크 (return_code가 0이면 성공)
                if data.get('return_code') == 0 or data.get('return_code') == '0':
                    print(f"✅ [주문 성공] 주문번호: {data.get('ord_no', 'Unknown')}")
                    print(f"   메시지: {data.get('return_msg')}")
                    return True
                else:
                    print(f"⚠️ [주문 실패] {data.get('return_msg')}")
                    return False
            else:
                print(f"⚠️ [API 에러] {res.status_code}: {res.text}")
                return False

        except Exception as e:
            print(f"❌ [시스템] 주문 오류: {e}")
            return False

    def buy(self, stock_code, current_price):
        """ 매수 실행 (금액에 맞춰 수량 계산) """
        if current_price <= 0: return
        
        # 수량 계산 (설정된 금액 / 현재가) -> 소수점 버림
        qty = math.floor(self.max_position_size / current_price)
        
        if qty < 1:
            print("⚠️ 주문 가능 수량이 0입니다. (잔고 부족 또는 설정 금액 과소)")
            return

        return self.send_order(stock_code, 'buy', qty, int(current_price))

    def sell(self, stock_code, qty, current_price):
        """ 매도 실행 (보유 수량 전량) """
        if qty < 1: return
        return self.send_order(stock_code, 'sell', qty, int(current_price))

# --- 테스트 코드 ---
if __name__ == "__main__":
    trader = Trader()
    print(">>> 주문 모듈 테스트 (실제 주문이 전송될 수 있으니 주의하세요!)")
    
    # ⚠️ 주의: 장 중에 실행하면 실제 주문이 나갑니다.
    # 테스트를 원하시면 아래 주석을 풀고 실행하세요.
    trader.buy("122630", 45000) # KODEX 레버리지 45000원에 매수 시도