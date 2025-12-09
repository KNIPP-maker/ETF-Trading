import pandas as pd
import os
from datetime import datetime

class TradeLogger:
    def __init__(self):
        self.log_dir = "logs"
        self.file_path = f"{self.log_dir}/trade_journal_{datetime.now().strftime('%Y%m%d')}.csv"
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # 로그 파일이 없으면 헤더 생성
        if not os.path.exists(self.file_path):
            df = pd.DataFrame(columns=[
                "Timestamp", "Ticker", "Action", "OrderQty", "OrderPrice",
                "Basis", "SignalType", "DecisionTime", "Slippage"
            ])
            df.to_csv(self.file_path, index=False)

    def log_trade(self, trade_data):
        """
        매매 기록 저장
        trade_data = {
            "ticker": "KODEX 레버리지",
            "action": "BUY",
            "qty": 100,
            "price": 15000,
            "basis": 0.25, # 당시 괴리율
            "signal": "BASIS_DIV", # 진입 사유
            "latency": 0.15 # 신호 발생 후 주문까지 걸린 시간 (초)
        }
        """
        entry = {
            "Timestamp": datetime.now().strftime('%H:%M:%S.%f')[:-3],
            "Ticker": trade_data.get('ticker'),
            "Action": trade_data.get('action'),
            "OrderQty": trade_data.get('qty'),
            "OrderPrice": trade_data.get('price'),
            "Basis": trade_data.get('basis', 0.0),
            "SignalType": trade_data.get('signal', 'Manual'),
            "DecisionTime": f"{trade_data.get('latency', 0):.3f}s",
            "Slippage": "Calc Later" # 체결 후 업데이트 가능
        }
        
        df = pd.DataFrame([entry])
        df.to_csv(self.file_path, mode='a', header=False, index=False)
        print(f"📝 [매매일지 기록] {entry['Ticker']} {entry['Action']} (Basis: {entry['Basis']})")