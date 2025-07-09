from strategy.kospi_signal_engine import kospi_signal_engine
from services.order_router import execute_trade
from services.risk_manager import check_exit
from services.data_feed import fetch_market_data
import time

class SingleEntryExitMVP:
    def __init__(self, desired_amount=10, interval_sec=2):
        self.position = None  # None, "LEVERAGE", "INVERSE"
        self.entry_price = None
        self.desired_amount = desired_amount
        self.interval_sec = interval_sec
        self.running = False

    def run(self):
        print("[SINGLE-ENTRY-EXIT MVP] 자동매매 시작")
        self.running = True
        try:
            while self.running:
                market_data = fetch_market_data()
                signal = kospi_signal_engine(market_data)
                price = market_data.get("price")

                if self.position is None:
                    if signal == "BUY_LEVERAGE":
                        execute_trade("KODEX 레버리지", "BUY", amount=self.desired_amount)
                        self.position = "LEVERAGE"
                        self.entry_price = price
                        print(f"[ENTRY] LEVERAGE 진입 @ {price}")
                    elif signal == "BUY_INVERSE":
                        execute_trade("KODEX 200선물인버스2X", "BUY", amount=self.desired_amount)
                        self.position = "INVERSE"
                        self.entry_price = price
                        print(f"[ENTRY] INVERSE 진입 @ {price}")
                else:
                    if check_exit(market_data, self.entry_price):
                        execute_trade("ALL", "SELL")
                        print(f"[EXIT] {self.position} 청산 @ {price}")
                        self.position = None
                        self.entry_price = None

                time.sleep(self.interval_sec)
        except KeyboardInterrupt:
            print("[SINGLE-ENTRY-EXIT MVP] 자동매매 종료 (수동 중단)")
        except Exception as e:
            print(f"[ERROR] {e}")
        finally:
            self.running = False 