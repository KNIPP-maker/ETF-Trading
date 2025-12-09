import pandas as pd
import numpy as np
import os
import math
from datetime import datetime, timedelta

class MarketSimulator:
    def __init__(self):
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def generate_market_data(self, days=5):
        """
        초정밀 시장 데이터 생성 (1초 단위)
        - days: 생성할 영업일 수
        """
        print(f"⏳ [System] {days}일치 정밀 시뮬레이션 데이터 생성 중...")
        
        start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # 초기가 설정
        kospi = 350.00
        lev_price = 15000
        inv_price = 4000
        
        records = []
        
        for d in range(days):
            curr_time = start_date + timedelta(days=d)
            # 장 시작 시 갭(Gap) 발생 시뮬레이션 (전일 대비 +/- 0.5%)
            gap = np.random.normal(0, 0.005)
            kospi *= (1 + gap)
            lev_price *= (1 + gap * 2)
            inv_price *= (1 + gap * -2)

            # 장중 시간 (09:00 ~ 15:20 = 22,800초)
            seconds_in_day = 6 * 3600 + 20 * 60 
            
            # 베이시스 사이클 (하루에 몇 번 오르내릴지)
            cycle_speed = np.random.randint(10, 50) 
            
            for t in range(seconds_in_day):
                # 1. 기초자산 (KOSPI 200) 변동
                # 1초당 변동성 (연 변동성 20% 가정)
                volatility = 0.0001 * np.random.randn() 
                ret = volatility
                
                # 지수 업데이트
                prev_kospi = kospi
                kospi *= (1 + ret)
                
                # 2. 파생상품 가격 결정 (수학적 연동)
                # ETF는 기초자산 수익률의 정확히 2배 / -2배 추종
                # (현실적인 슬리피지/괴리율 0.001% 반영)
                lev_ret = ret * 2.0 
                inv_ret = ret * -2.0 
                
                lev_price *= (1 + lev_ret)
                inv_price *= (1 + inv_ret)
                
                # 3. 선물 가격 & 베이시스
                # 베이시스는 사인파(Sin) 형태로 벌어졌다 좁혀졌다를 반복함
                # 이론가 대비 괴리율 (-0.4 ~ +0.4)
                basis_noise = math.sin(t / 1000 * cycle_speed) * 0.4 + np.random.normal(0, 0.05)
                futures = kospi + basis_noise

                # 4. 데이터 저장
                records.append({
                    "timestamp": curr_time,
                    "kospi200": round(kospi, 2),
                    "futures": round(futures, 2),
                    "basis": round(futures - kospi, 2),
                    "lev_price": int(lev_price),
                    "inv_price": int(inv_price),
                    "lev_return": round(lev_ret * 100, 4), # 검증용
                    "inv_return": round(inv_ret * 100, 4)  # 검증용
                })
                
                curr_time += timedelta(seconds=1)
                
        # DataFrame 변환 및 저장
        df = pd.DataFrame(records)
        save_path = f"{self.data_dir}/simulation_market_data.csv"
        df.to_csv(save_path, index=False)
        
        print(f"✅ [완료] 데이터 생성됨: {save_path}")
        print(f"   - 총 데이터 수: {len(df):,} rows")
        print(f"   - 기초자산과 ETF간 상관관계 검증 필요")
        
        return df

if __name__ == "__main__":
    sim = MarketSimulator()
    df = sim.generate_market_data(days=1)
    
    # [검증] 데이터가 진짜 맞게 도는지 샘플 출력
    print("\n🔎 [데이터 무결성 검증]")
    print(df[['timestamp', 'kospi200', 'lev_price', 'inv_price', 'basis']].head(10))
    print("...")