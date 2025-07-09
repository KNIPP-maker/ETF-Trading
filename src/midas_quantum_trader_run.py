from strategy.midas_quantum_trader import MidasQuantumTrader
from services.order_router import execute_trade
from services.data_feed import fetch_market_data
import time
from pykiwoom.kiwoom import Kiwoom
from PyQt5.QtWidgets import QApplication
import sys

# ETF 코드 매핑 (실제 주문용)
ETF_ASSET_MAP = {
    'LEVERAGE': 'KODEX 레버리지',
    'INVERSE': 'KODEX 200선물인버스2X',
}

app = QApplication(sys.argv)
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

# 실시간 데이터 수신 콜백 함수
def on_real_data(code, real_type, real_data):
    print(f"[실시간] code: {code}, type: {real_type}, data: {real_data}")

# 예시: KODEX 레버리지(122630) 실시간 체결가 등록
kiwoom.SetRealReg("1000", "122630", "10;20;27", "0")  # 10: 현재가, 20: 거래량, 27: 체결강도 등

# 콜백 등록 (pykiwoom은 직접 콜백 등록이 아니라, Kiwoom 클래스 상속 후 메서드 오버라이드 필요)
class MyKiwoom(Kiwoom):
    def OnReceiveRealData(self, code, real_type, real_data):
        print(f"[실시간] code: {code}, type: {real_type}, data: {real_data}")

my_kiwoom = MyKiwoom()
my_kiwoom.CommConnect(block=True)
my_kiwoom.SetRealReg("1000", "122630", "10;20;27", "0")

class RealTimeCollector(Kiwoom):
    def __init__(self):
        super().__init__()
        self.data = {}
        self.CommConnect(block=True)
        # 예시: KODEX 레버리지, 인버스2X, KOSPI200 선물/현물 코드 등록
        self.SetRealReg("1000", "122630;252670", "10;20;27", "0")  # ETF
        # 선물/현물, 외국인 수급 등은 별도 TR/실시간 등록 필요

    def OnReceiveRealData(self, code, real_type, real_data):
        # 실시간 데이터 수신 시 호출
        if real_type == "주식체결":
            price = real_data.get("현재가")
            volume = real_data.get("거래량")
            self.data[code] = {"price": price, "volume": volume}
            print(f"{code} 실시간 체결가: {price}, 거래량: {volume}")

# PyQt5 앱 실행
app = QApplication(sys.argv)
collector = RealTimeCollector()

def fetch_market_data(kiwoom):
    # KOSPI200 현물
    kiwoom.SetInputValue("업종코드", "201")
    spot_df = kiwoom.BlockRequest("OPT50001", 업종코드="201", output="업종현재가", next=0)
    spot = float(spot_df["현재가"].iloc[0])

    # KOSPI200 선물
    kiwoom.SetInputValue("종목코드", "101S3000")
    fut_df = kiwoom.BlockRequest("OPT50028", 종목코드="101S3000", output="선물현재가", next=0)
    futures = float(fut_df["현재가"].iloc[0])

    # 외국인 수급
    kiwoom.SetInputValue("종목코드", "201")
    flow_df = kiwoom.BlockRequest("OPT90003", 종목코드="201", output="외인기관종목별동향", next=0)
    foreign_net = int(flow_df["외국계순매수"].iloc[0])

    # ETF 가격 (실시간은 실시간 이벤트, TR은 BlockRequest)
    kiwoom.SetInputValue("종목코드", "122630")
    etf_df = kiwoom.BlockRequest("OPT10001", 종목코드="122630", output="주식기본정보", next=0)
    etf_price = float(etf_df["현재가"].iloc[0])

    return {
        "futures": futures,
        "spot": spot,
        "foreign_net": foreign_net,
        "etf_price": etf_price
    }

if __name__ == "__main__":
    trader = MidasQuantumTrader()
    while True:
        market_data = fetch_market_data(kiwoom)  # 반드시 {'futures', 'spot', 'foreign_net', 'etf_price'} 포함
        prev_position = trader.position
        trader.step(market_data)
        # 진입/청산 시 실제 주문 실행
        if prev_position != trader.position:
            if trader.position:  # 진입
                asset = ETF_ASSET_MAP.get(trader.position)
                if asset:
                    execute_trade(asset, "BUY", amount=10)
            else:  # 청산
                execute_trade("ALL", "SELL")
        time.sleep(2)

    # 예시 사용법
    market_data = {
        'futures': 300.0,
        'spot': 299.0,
        'foreign_net': 1000,
        'etf_price': 15000
    }
    trader.step(market_data)
    print(trader.get_log())

app.exec_() 