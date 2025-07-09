"""
ETF Auto Trader - Main Application (전략 예제 코드 전용)
"""

from strategy.kospi_signal_engine import kospi_signal_engine
from services.order_router import execute_trade
from services.risk_manager import check_exit
from services.data_feed import fetch_market_data
import time
from dotenv import load_dotenv
import os

# 시장 오픈 여부를 임의로 True로 반환 (실제 구현 시 거래소 시간 체크 등으로 대체)
def market_is_open():
    return True  # TODO: 실제 시장 오픈 조건으로 변경

desired_amount = 10  # 예시: 매수 수량

load_dotenv()
ACCOUNT_NO = os.getenv("ACCOUNT_NO")

if not ACCOUNT_NO:
    raise ValueError("계좌번호(ACCOUNT_NO)가 .env 파일에 없습니다.")

print(f"불러온 계좌번호: {ACCOUNT_NO}")

def place_order(code, qty, order_type="2", account_no=None):
    if not account_no:
        raise ValueError("계좌번호가 필요합니다.")
    # 주문 실행 코드
    print(f"주문 실행: 계좌 {account_no}, 종목 {code}, 수량 {qty}, 주문유형 {order_type}")

if __name__ == "__main__":
    print("[INFO] ETF 자동매매 전략 시작")
    try:
        while market_is_open():
            market_data = fetch_market_data()
            signal = kospi_signal_engine(market_data)

            if signal == "BUY_LEVERAGE":
                execute_trade("KODEX 레버리지", "BUY", amount=desired_amount)
            elif signal == "BUY_INVERSE":
                execute_trade("KODEX 200선물인버스2X", "BUY", amount=desired_amount)

            if check_exit(market_data):
                execute_trade("ALL", "SELL")

            time.sleep(2)  # 2초 대기 (실제 운용 시 적절히 조정)
    except KeyboardInterrupt:
        print("[INFO] 자동매매 종료") 