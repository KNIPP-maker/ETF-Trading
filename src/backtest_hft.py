import pandas as pd
import os

def run_hft_backtest():
    if not os.path.exists("data/HFT_DATA.csv"):
        print("❌ 데이터 없음")
        return

    df = pd.read_csv("data/HFT_DATA.csv")

    # [SOLAB 환경]
    INITIAL_CAPITAL = 100_000_000
    LOAN_RATIO = 3.0
    COST_RATE = 0.0004 # 수수료 거의 없음
    
    # [호가 스캘핑 파라미터]
    # 매수잔량이 매도잔량의 3배가 되면 '매수세 폭발'로 간주
    ENTRY_RATIO = 3.0 
    EXIT_RATIO = 1.2  # 매수세가 약해지면(1.2배 이하) 즉시 탈출
    STOP_LOSS = -0.003 # -0.3% 칼손절

    cash = INITIAL_CAPITAL * LOAN_RATIO
    position = None
    entry_price = 0
    holding_qty = 0
    trades = 0
    wins = 0
    
    print(f"🚀 [호가 스캘핑] 초단타 백테스트 시작 (총 {len(df)}초 데이터)")

    # 시뮬레이션 속도를 위해 10초 단위로 샘플링 (실전은 1초)
    # df = df.iloc[::10].reset_index(drop=True)

    for i in range(len(df)):
        row = df.iloc[i]
        bid = row['bid_qty']
        ask = row['ask_qty']
        
        # 호가 비율 (매수세 / 매도세)
        ratio = bid / ask if ask > 0 else 10
        price = row['lev_price'] # 레버리지 기준
        
        # 1. 진입 (매수세 폭발)
        if position is None:
            if ratio >= ENTRY_RATIO:
                position = "LEV"
                entry_price = price
                holding_qty = int(cash * 0.99 / price)
                cost = (holding_qty * price) * COST_RATE
                cash -= (holding_qty * price + cost)
                
        # 2. 청산 (매수세 소멸 or 손절)
        elif position == "LEV":
            pnl_pct = (price - entry_price) / entry_price
            
            # (A) 손절
            if pnl_pct <= STOP_LOSS:
                revenue = holding_qty * price
                cost = revenue * COST_RATE
                cash += (revenue - cost)
                position = None
                trades += 1
            
            # (B) 익절/청산 (매수세가 1.2배 이하로 떨어짐)
            elif ratio <= EXIT_RATIO:
                revenue = holding_qty * price
                cost = revenue * COST_RATE
                cash += (revenue - cost)
                
                if revenue - cost > holding_qty * entry_price:
                    wins += 1
                
                position = None
                trades += 1

    # 결과 정산
    final_equity = cash - (INITIAL_CAPITAL * (LOAN_RATIO - 1))
    roi = ((final_equity / INITIAL_CAPITAL) - 1) * 100

    print("\n===========================================")
    print(f"🏁 [HFT 결과] (무세금/초저수수료 효과)")
    print(f"▶ 순수 원금: {int(INITIAL_CAPITAL):,}원")
    print(f"▶ 최종 평가: {int(final_equity):,}원")
    print(f"▶ 수익률: {roi:.2f}%")
    print(f"▶ 총 매매: {trades}회 (승률: {wins/trades*100 if trades > 0 else 0:.1f}%)")
    print("===========================================")

if __name__ == "__main__":
    run_hft_backtest()