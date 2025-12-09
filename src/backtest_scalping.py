import pandas as pd
import os

def run_scalping():
    if not os.path.exists("data/MINUTE_DATA.csv"):
        print("❌ 데이터가 없습니다. create_minute_data.py를 먼저 실행하세요.")
        return

    df = pd.read_csv("data/MINUTE_DATA.csv")

    # --- [SOLAB 스캘핑 환경] ---
    INITIAL_CAPITAL = 100_000_000
    LOAN_RATIO = 3.0
    
    # [법인 특권] 비용 거의 0
    COST_RATE = 0.0004  # 수수료+슬리피지 합쳐서 0.04% (보수적)
    
    # [스캘핑 파라미터]
    ENTRY_THRESHOLD = 0.15  # 괴리율 0.15만 벌어져도 덥썩 뭅니다
    EXIT_THRESHOLD = 0.02   # 거의 0에 수렴하면 바로 익절
    STOP_LOSS = -0.005      # -0.5%만 가도 칼손절 (회전율로 복구)

    cash = INITIAL_CAPITAL * LOAN_RATIO
    position = None
    entry_price = 0
    entry_idx = 0
    holding_qty = 0
    
    trades = []
    
    print(f"🚀 [초단타 스캘핑] 1분봉 백테스트 시작 (1개월)")
    print(f"💰 자금: {cash:,}원 | 목표: 티끌 모아 태산")

    for i in range(len(df)):
        row = df.iloc[i]
        basis = row['futures'] - row['kospi']
        lev_p = row['lev']
        inv_p = row['inv']
        
        action = None
        
        # 1. 포지션 없을 때 (진입 탐색)
        if position is None:
            if basis >= ENTRY_THRESHOLD:
                action = "BUY_LEV"
            elif basis <= -ENTRY_THRESHOLD:
                action = "BUY_INV"
        
        # 2. 포지션 있을 때 (청산 탐색)
        else:
            curr_p = lev_p if position == "LEV" else inv_p
            pnl_pct = (curr_p - entry_price) / entry_price
            
            # (A) 칼손절 (-0.5%)
            if pnl_pct <= STOP_LOSS:
                action = "SELL_STOP"
            
            # (B) 빠른 익절 (괴리율 해소 시)
            elif abs(basis) <= EXIT_THRESHOLD:
                action = "SELL_PROFIT"
                
            # (C) 장 마감 강제청산 (15:20분)
            time_str = str(row['timestamp'])
            if "15:20" in time_str or "15:21" in time_str:
                 action = "SELL_TIME"

        # --- 실행 로직 ---
        if action and "BUY" in action:
            target = lev_p if action == "BUY_LEV" else inv_p
            holding_qty = int(cash * 0.99 / target)
            entry_price = target
            entry_idx = i
            
            cost = (holding_qty * target) * COST_RATE
            cash -= (holding_qty * target + cost)
            
            position = "LEV" if action == "BUY_LEV" else "INV"
            
        elif action and "SELL" in action:
            target = lev_p if position == "LEV" else inv_p
            revenue = holding_qty * target
            cost = revenue * COST_RATE
            
            cash += (revenue - cost)
            
            profit = (target - entry_price) * holding_qty - cost*2
            duration = i - entry_idx # 보유 시간(분)
            
            icon = "✅" if profit > 0 else "⛔"
            trades.append(f"[{row['timestamp'][5:-3]}] {action} ({duration}분 보유) | 손익: {int(profit):,}원")
            
            position = None
            holding_qty = 0

    # 최종 정산
    loan_amt = INITIAL_CAPITAL * (LOAN_RATIO - 1)
    final_equity = cash - loan_amt
    roi = ((final_equity / INITIAL_CAPITAL) - 1) * 100

    print("\n===========================================")
    print(f"🏁 [스캘핑 결과 리포트]")
    print(f"▶ 순수 원금: {int(INITIAL_CAPITAL):,}원")
    print(f"▶ 최종 평가: {int(final_equity):,}원")
    print(f"▶ 수익률: {roi:.2f}% (월간)")
    print(f"▶ 총 매매 횟수: {len(trades)}회 (일평균 {len(trades)//20}회)")
    print("===========================================")
    print("\n[최근 거래 로그]")
    for t in trades[-5:]: print(t)

if __name__ == "__main__":
    run_scalping()