from strategy.kospi_signal_engine import kospi_signal_engine
from services.order_router import execute_trade
from services.risk_manager import check_exit
from services.data_feed import fetch_market_data
import time
from pykiwoom.kiwoom import Kiwoom
from PyQt5.QtWidgets import QApplication
import sys

class AutoStrategyV1:
    def __init__(self, desired_amount=10, interval_sec=2):
        self.desired_amount = desired_amount
        self.interval_sec = interval_sec
        self.running = False

    def run(self):
        print("[AUTO-STRATEGY v1.0] 자동매매 시작")
        self.running = True
        app = QApplication(sys.argv)
        kiwoom = Kiwoom()
        kiwoom.CommConnect(block=True)
        try:
            while self.running:
                market_data = fetch_market_data(kiwoom)
                signal = kospi_signal_engine(market_data)

                if signal == "BUY_LEVERAGE":
                    execute_trade("KODEX 레버리지", "BUY", amount=self.desired_amount)
                elif signal == "BUY_INVERSE":
                    execute_trade("KODEX 200선물인버스2X", "BUY", amount=self.desired_amount)

                if check_exit(market_data):
                    execute_trade("ALL", "SELL")

                time.sleep(self.interval_sec)
        except KeyboardInterrupt:
            print("[AUTO-STRATEGY v1.0] 자동매매 종료 (수동 중단)")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.running = False 