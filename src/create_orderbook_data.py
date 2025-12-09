import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

if not os.path.exists("data"):
    os.makedirs("data")

def create_hft_data():
    print("⏳ [SOLAB] 호가(Orderbook) 포함 초고빈도 데이터 생성 중...")
    
    dates = pd.date_range(end=datetime.today(), periods=5, freq='B') # 5일치 (충분)
    
    data = {
        "timestamp": [],
        "lev_price": [],
        "inv_price": [],
        "bid_qty": [], # 매수 잔량 (총합)
        "ask_qty": []  # 매도 잔량 (총합)
    }
    
    lev_p = 15000
    inv_p = 4000
    
    for date in dates:
        curr_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=9)
        
        # 하루 23,400초 (1초 단위 데이터)
        # 스캘핑은 초 단위 승부입니다.
        for _ in range(390 * 60): 
            # 호가 불균형 생성 (-1 ~ 1)
            # 양수면 매수세 우위 -> 가격 상승 압력
            imbalance = np.random.normal(0, 0.5)
            
            # 호가 잔량 시뮬레이션
            base_qty = 100000
            bid = int(base_qty * (1 + imbalance))
            ask = int(base_qty * (1 - imbalance))
            
            # 가격 움직임 (호가 불균형이 가격을 밀어올림)
            # imbalance가 0.5 이상이면 가격 상승 확률 급증
            drift = imbalance * 0.0001 
            noise = np.random.normal(0, 0.00005)
            change = drift + noise
            
            lev_p *= (1 + change * 2) # 레버리지 2배 민감
            inv_p *= (1 + change * -2)
            
            data["timestamp"].append(curr_time)
            data["lev_price"].append(int(lev_p))
            data["inv_price"].append(int(inv_p))
            data["bid_qty"].append(bid)
            data["ask_qty"].append(ask)
            
            curr_time += timedelta(seconds=1)

    df = pd.DataFrame(data)
    df.to_csv("data/HFT_DATA.csv", index=False)
    print(f"✅ 생성 완료: {len(df)}개 틱 데이터 (초단위)")

if __name__ == "__main__":
    create_hft_data()