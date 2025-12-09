import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

if not os.path.exists("data"):
    os.makedirs("data")

def create_minute_data():
    print("⏳ [SOLAB] 초단타용 1분봉 데이터 생성 중 (1개월치)...")
    
    # 1. 날짜 생성 (20거래일 = 약 1달)
    dates = pd.date_range(end=datetime.today(), periods=20, freq='B')
    
    minute_data = {
        "timestamp": [],
        "kospi": [],
        "futures": [],
        "lev": [],
        "inv": []
    }
    
    # 초기가
    kospi_p = 350.0
    lev_p = 15000
    inv_p = 4000
    
    for date in dates:
        # 하루 390분 (09:00 ~ 15:30)
        current_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=9)
        
        # 장 시작 시 갭 (Overnight Gap)
        kospi_p *= (1 + np.random.normal(0, 0.005))
        
        for _ in range(390):
            # 1분간의 변동 (랜덤 워크)
            change = np.random.normal(0, 0.0005) # 0.05% 변동
            kospi_p *= (1 + change)
            
            # 선물 괴리율 (Basis): 장중에는 더 격렬하게 움직임 (-0.3 ~ +0.3)
            # 평균회귀 속성이 강함
            basis = np.random.normal(0, 0.15)
            futures_p = kospi_p + basis
            
            # ETF 가격 반영 (2배 레버리지)
            lev_p *= (1 + change * 2)
            inv_p *= (1 + change * -2)
            
            minute_data["timestamp"].append(current_time)
            minute_data["kospi"].append(kospi_p)
            minute_data["futures"].append(futures_p)
            minute_data["lev"].append(int(lev_p))
            minute_data["inv"].append(int(inv_p))
            
            current_time += timedelta(minutes=1)

    # 데이터프레임 저장
    df = pd.DataFrame(minute_data)
    df.to_csv("data/MINUTE_DATA.csv", index=False)
    print(f"✅ 생성 완료: 총 {len(df)}개 1분봉 데이터")

if __name__ == "__main__":
    create_minute_data()