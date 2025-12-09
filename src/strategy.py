import os
from dotenv import load_dotenv

# .env 로드
load_dotenv()

class Strategy:
    def __init__(self):
        # 1. 설정값 로드 (없으면 기본값 사용)
        self.target_disparity = float(os.getenv("TARGET_DISPARITY_THRESHOLD", -0.5)) # 진입 괴리율 (-0.5%)
        self.stop_loss_pct = float(os.getenv("STOP_LOSS_PERCENTAGE", 1.5))           # 손절 (-1.5%)
        self.take_profit_pct = float(os.getenv("TAKE_PROFIT_PERCENTAGE", 5.0))       # 익절 (+5.0%)
        
        # [옵션] 괴리율 해소 기준 (괴리율이 이 값보다 높아지면 정상화로 보고 청산)
        # 보통 0.0(이론가 도달)이나 -0.1(살짝 덜 먹더라도 확실한 청산) 정도로 잡습니다.
        self.exit_disparity = 0.0 

        print(f"✅ [전략] 초기화 완료")
        print(f"   - 매수 진입: 괴리율 {self.target_disparity}% 이하 (저평가)")
        print(f"   - 매도 청산: 괴리율 {self.exit_disparity}% 이상 (정상화) OR 손익 {self.stop_loss_pct}% 도달")

    def decide_action(self, market_data, current_position):
        """
        시장 데이터와 현재 잔고를 분석하여 매매 신호를 생성
        :param market_data: {price, inav, disparity_rate} 딕셔너리
        :param current_position: {qty, avg_price} (없으면 None 혹은 qty=0)
        :return: (action, reason) 튜플 -> action: "BUY", "SELL", "HOLD"
        """
        if not market_data:
            return "HOLD", "데이터 없음"

        # 데이터 추출
        current_price = market_data.get('price')
        disparity_rate = market_data.get('disparity_rate')
        
        # 현재 보유 상태 확인
        has_position = False
        avg_price = 0
        if current_position and current_position.get('qty', 0) > 0:
            has_position = True
            avg_price = current_position.get('avg_price', 0)

        # ----------------------------------------------------
        # 🟢 1. 매수(BUY) 로직: 포지션이 없을 때만 동작
        # ----------------------------------------------------
        if not has_position:
            # 설정한 타겟(-0.5%)보다 괴리율이 더 낮으면 (더 저평가되면) 진입
            if disparity_rate <= self.target_disparity:
                return "BUY", f"진입 포착 (괴리율 {disparity_rate}% <= {self.target_disparity}%)"
            else:
                return "HOLD", f"관망 중 (괴리율 {disparity_rate}%)"

        # ----------------------------------------------------
        # 🔴 2. 매도(SELL) 로직: 포지션이 있을 때만 동작
        # ----------------------------------------------------
        else:
            # 현재 수익률 계산 (Unrealized PnL)
            pnl_rate = 0.0
            if avg_price > 0:
                pnl_rate = ((current_price - avg_price) / avg_price) * 100

            # A. 손절 (Stop Loss) 체크 - 가장 최우선!
            if pnl_rate <= -self.stop_loss_pct:
                return "SELL", f"손절매 실행 (수익률 {pnl_rate:.2f}% <= -{self.stop_loss_pct}%)"

            # B. 익절 (Hard Take Profit) 체크 - 대박 수익 시 안전장치
            if pnl_rate >= self.take_profit_pct:
                return "SELL", f"목표 수익 달성 (수익률 {pnl_rate:.2f}% >= {self.take_profit_pct}%)"

            # C. 전략적 청산 (괴리율 정상화)
            # 괴리율이 0% 이상으로 올라오면 제값 받은 것이므로 팝니다.
            if disparity_rate >= self.exit_disparity:
                return "SELL", f"괴리율 정상화 (괴리율 {disparity_rate}% >= {self.exit_disparity}%)"

            # 아무 조건도 해당 안 되면 보유
            return "HOLD", f"보유 중 (수익률 {pnl_rate:.2f}%, 괴리율 {disparity_rate}%)"

# --- 테스트 코드 (파일 직접 실행 시) ---
if __name__ == "__main__":
    strategy = Strategy()
    
    print("\n--- [상황 1] 포지션 없음, 괴리율 -0.6% (진입 기회) ---")
    dummy_data = {"price": 10000, "inav": 10060, "disparity_rate": -0.6}
    action, reason = strategy.decide_action(dummy_data, None)
    print(f"결과: {action} ({reason})")

    print("\n--- [상황 2] 포지션 보유 중, 괴리율 -0.2% (아직 보유) ---")
    dummy_pos = {"qty": 10, "avg_price": 10000}
    dummy_data_2 = {"price": 10050, "inav": 10070, "disparity_rate": -0.2} # 수익중이지만 괴리 남음
    action, reason = strategy.decide_action(dummy_data_2, dummy_pos)
    print(f"결과: {action} ({reason})")

    print("\n--- [상황 3] 포지션 보유 중, 괴리율 +0.1% (정상화 -> 청산) ---")
    dummy_data_3 = {"price": 10100, "inav": 10090, "disparity_rate": 0.1}
    action, reason = strategy.decide_action(dummy_data_3, dummy_pos)
    print(f"결과: {action} ({reason})")
    
    print("\n--- [상황 4] 포지션 보유 중, 폭락 발생 (손절 테스트) ---")
    dummy_data_4 = {"price": 9800, "inav": 10000, "disparity_rate": -2.0} # 가격이 -2% 빠짐
    action, reason = strategy.decide_action(dummy_data_4, dummy_pos)
    print(f"결과: {action} ({reason})")