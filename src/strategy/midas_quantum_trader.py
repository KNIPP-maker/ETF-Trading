import traceback
from datetime import datetime
import json
import pandas as pd
# import matplotlib.pyplot as plt  # matplotlib 없이 시연하기 위해 주석 처리

class MidasQuantumTrader:
    def __init__(self):
        self.position = None  # 'LEVERAGE', 'INVERSE', or None
        self.entry_prices = []
        self.trade_log = []
        self.max_entry_count = 2
        self.entry_count = 0
        self.log_file = "trade_log.txt"
        self.json_file = "trade_log.json"
        self.initial_balance = 10000000  # 1천만원 가정
        self.balance = self.initial_balance
        self.position_size = 0
        self.position_type = None
        self.report_dir = "report"

    def log_event(self, event):
        self.trade_log.append(event)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{event}\n")
        except Exception as e:
            print(f"[ERROR] 로그 파일 저장 실패: {e}")

    def save_json_log(self):
        try:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump([self._event_to_dict(ev) for ev in self.trade_log], f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"[ERROR] JSON 로그 저장 실패: {e}")

    def _event_to_dict(self, event):
        # event: (datetime, str, price)
        return {"time": str(event[0]), "event": event[1], "price": event[2]}

    def should_enter(self, kospi_futures, kospi_spot, foreign_flow):
        try:
            gap = (kospi_futures - kospi_spot) / kospi_spot * 100
            if self.entry_count < self.max_entry_count:
                if gap >= 0.3 and foreign_flow > 0:
                    return 'LEVERAGE'
                elif gap <= -0.3 and foreign_flow < 0:
                    return 'INVERSE'
            return None
        except Exception as e:
            err = f"{datetime.now()} [ERROR] 진입 조건 계산 실패: {e}\n{traceback.format_exc()}"
            print(err)
            self.log_event(err)
            return None

    def enter_position(self, position_type, current_price):
        self.position = position_type
        self.entry_prices.append(current_price)
        self.entry_count += 1
        self.position_type = position_type
        self.position_size += 1
        event = (datetime.now(), f"ENTER {position_type}", current_price)
        self.log_event(event)
        self.save_json_log()

    def should_exit(self, current_price):
        try:
            if not self.entry_prices:
                return False
            avg_entry = sum(self.entry_prices) / len(self.entry_prices)
            profit_ratio = (current_price - avg_entry) / avg_entry * 100 if self.position == 'LEVERAGE' else (avg_entry - current_price) / avg_entry * 100
            if profit_ratio >= 1.0 or profit_ratio <= -0.6:
                return True
            return False
        except Exception as e:
            err = f"{datetime.now()} [ERROR] 청산 조건 계산 실패: {e}\n{traceback.format_exc()}"
            print(err)
            self.log_event(err)
            return False

    def exit_position(self, current_price):
        event = (datetime.now(), f"EXIT {self.position}", current_price)
        self.log_event(event)
        # 수익/손실 반영 (단순: 진입수량만큼)
        if self.entry_prices:
            avg_entry = sum(self.entry_prices) / len(self.entry_prices)
            if self.position == 'LEVERAGE':
                pnl = (current_price - avg_entry) * self.position_size
            else:
                pnl = (avg_entry - current_price) * self.position_size
            self.balance += pnl
        self.position = None
        self.entry_prices = []
        self.position_size = 0
        self.position_type = None
        self.save_json_log()

    def step(self, market_data):
        try:
            kospi_futures = market_data['futures']
            kospi_spot = market_data['spot']
            foreign_flow = market_data['foreign_net']
            current_price = market_data['etf_price']
            if self.position:
                if self.should_exit(current_price):
                    self.exit_position(current_price)
            else:
                entry_signal = self.should_enter(kospi_futures, kospi_spot, foreign_flow)
                if entry_signal:
                    self.enter_position(entry_signal, current_price)
        except Exception as e:
            err = f"{datetime.now()} [ERROR] step() 예외: {e}\n{traceback.format_exc()}"
            print(err)
            self.log_event(err)

    def get_log(self):
        return self.trade_log

    def generate_report(self):
        import os
        os.makedirs(self.report_dir, exist_ok=True)
        # 1. JSON 저장
        self.save_json_log()
        # 2. DataFrame 변환
        df = pd.DataFrame([self._event_to_dict(ev) for ev in self.trade_log])
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time")
        # 3. 누적 수익률/잔고 계산
        balance = self.initial_balance
        balances = [balance]
        returns = [0]
        for i, row in df.iterrows():
            if row["event"].startswith("EXIT"):
                # 진입가, 청산가, 포지션 등은 단순화(실전은 더 정교하게)
                if i > 0:
                    entry_idx = df.iloc[:i][df["event"].str.startswith("ENTER")].last_valid_index()
                    if entry_idx is not None:
                        entry_price = df.iloc[entry_idx]["price"]
                        exit_price = row["price"]
                        if "LEVERAGE" in row["event"]:
                            pnl = exit_price - entry_price
                        else:
                            pnl = entry_price - exit_price
                        balance += pnl
            balances.append(balance)
            returns.append((balance - self.initial_balance) / self.initial_balance * 100)
        df["balance"] = balances[:len(df)]
        df["return(%)"] = returns[:len(df)]
        # 4. CSV/JSON 저장
        df.to_csv(os.path.join(self.report_dir, "trade_report.csv"), index=False)
        df.to_json(os.path.join(self.report_dir, "trade_report.json"), orient="records", force_ascii=False, date_format="iso")
        # 5. 그래프 저장 (matplotlib 없이 시연하기 위해 주석 처리)
        # plt.figure(figsize=(10,5))
        # plt.plot(df["time"], df["balance"], label="Balance")
        # plt.title("누적 잔고 변화")
        # plt.xlabel("Time")
        # plt.ylabel("Balance")
        # plt.legend()
        # plt.tight_layout()
        # plt.savefig(os.path.join(self.report_dir, "balance_curve.png"))
        # plt.close()
        # plt.figure(figsize=(10,5))
        # plt.plot(df["time"], df["return(%)"], label="Return (%)")
        # plt.title("누적 수익률 변화")
        # plt.xlabel("Time")
        # plt.ylabel("Return (%)")
        # plt.legend()
        # plt.tight_layout()
        # plt.savefig(os.path.join(self.report_dir, "return_curve.png"))
        # plt.close()
        print(f"[REPORT] 리포트 생성 완료: {self.report_dir}/trade_report.* (그래프는 matplotlib 없이 생략)")