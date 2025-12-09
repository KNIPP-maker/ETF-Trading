import pandas as pd
from services.strategy_engine import StrategyEngine

def run_test():
    # 1. 데이터 로드
    df = pd.read_csv("data/simulation_market_data.csv")
    print(f"📂 데이터 로드 완료: {len(df)}건")

    # 2. 전략 엔진 초기화 (자본금 2억)
    engine = StrategyEngine(initial_balance=200_000_000)
    
    print("\n🚀 [전략 검증 시작] --------------------------------")
    
    # 3. 틱 단위 시뮬레이션
    trade_count = 0
    
    # 너무 많으니 앞부분 1000개만 테스트하거나, 주요 변곡점만 출력
    for i, row in df.iterrows():
        market_data = {
            'basis': row['basis'],
            'lev_price': row['lev_price'],
            'inv_price': row['inv_price']
        }
        
        # 엔진에 데이터 주입 -> 주문 결정
        order = engine.decide_action(market_data)
        
        if order:
            trade_count += 1
            timestamp = row['timestamp'].split(' ')[1] # 시간만
            print(f"[{timestamp}] Basis:{row['basis']:.2f} | {order['msg']}")
            print(f"   ㄴ 주문: {order['name']} {order['qty']:,}주 ({order['action']})")
            
            # 엔진 내부 상태 강제 동기화 (스위칭 시)
            if "SWITCH" in order['action']:
                # 스위칭은 매도->매수 2단계가 한 번에 일어난 것임
                # 엔진 내부 _update_balance가 호출되었지만, 포지션 명확화를 위해
                new_pos = "LONG" if order['name'] == "레버리지" else "SHORT"
                engine.set_position_state(new_pos)
            elif order['action'] == "BUY":
                new_pos = "LONG" if order['name'] == "레버리지" else "SHORT"
                engine.set_position_state(new_pos)

    print("--------------------------------------------------")
    print(f"🏁 테스트 종료. 총 거래 신호: {trade_count}회")

if __name__ == "__main__":
    run_test()