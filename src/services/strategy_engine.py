class StrategyEngine:
    def __init__(self, initial_balance=200_000_000):
        # 자산 상태
        self.balance = initial_balance  # 현금 잔고
        self.position = "NEUTRAL"       # 현재 포지션: NEUTRAL, LONG, SHORT
        self.holding_qty = 0            # 보유 수량
        self.avg_price = 0              # 평단가
        
        # 전략 파라미터 (괴리율 기준)
        self.THRESHOLD_S = 0.30  # S급 (100% 투입)
        self.THRESHOLD_A = 0.20  # A급 (50% 투입)
        self.THRESHOLD_B = 0.10  # B급 (10% 투입)
        self.EXIT_RANGE = 0.05   # 청산 범위 (±0.05 이내면 익절)

    def decide_action(self, market_data):
        """
        시장 데이터를 받아 [주문 명령]을 반환합니다.
        Return: { 'action': 'BUY/SELL', 'target': 'LEV/INV', 'qty': 0, 'desc': '...' }
        """
        basis = market_data['basis']
        lev_price = market_data['lev_price']
        inv_price = market_data['inv_price']
        
        # 1. 신호 강도(Grade) 판정
        grade = "NONE"
        direction = "NONE" # UP(레버리지), DOWN(인버스)
        
        if basis >= self.THRESHOLD_S:
            grade = "S"; direction = "UP"
        elif basis >= self.THRESHOLD_A:
            grade = "A"; direction = "UP"
        elif basis >= self.THRESHOLD_B:
            grade = "B"; direction = "UP"
            
        elif basis <= -self.THRESHOLD_S:
            grade = "S"; direction = "DOWN"
        elif basis <= -self.THRESHOLD_A:
            grade = "A"; direction = "DOWN"
        elif basis <= -self.THRESHOLD_B:
            grade = "B"; direction = "DOWN"
            
        elif abs(basis) < self.EXIT_RANGE:
            grade = "EXIT"

        # 2. 포지션 대응 로직 (상태 머신)
        order = None
        
        # [Case 1] 청산 신호 (EXIT)
        if grade == "EXIT" and self.position != "NEUTRAL":
            order = self._create_order("SELL", self.position, self.holding_qty, "괴리율 정상화(익절)")
            self._update_balance("SELL", 0, self.holding_qty, lev_price if self.position=="LONG" else inv_price)

        # [Case 2] 상승 신호 (UP) -> 레버리지 진입
        elif direction == "UP":
            if self.position == "SHORT": # 인버스 들고 있으면? -> 스위칭!
                # 1. 인버스 전량 매도
                self._update_balance("SELL", 0, self.holding_qty, inv_price)
                # 2. 레버리지 매수 (스위칭)
                invest_amt = self._calc_invest_amount(grade)
                qty = int(invest_amt / lev_price)
                if qty > 0:
                    order = self._create_order("SWITCH_BUY", "LONG", qty, f"스위칭: 인버스매도->레버리지매수({grade}급)")
                    self._update_balance("BUY", invest_amt, qty, lev_price)
            
            elif self.position == "NEUTRAL": # 무포지션 -> 신규 진입
                invest_amt = self._calc_invest_amount(grade)
                qty = int(invest_amt / lev_price)
                if qty > 0:
                    order = self._create_order("BUY", "LONG", qty, f"신규진입: 레버리지({grade}급)")
                    self._update_balance("BUY", invest_amt, qty, lev_price)

        # [Case 3] 하락 신호 (DOWN) -> 인버스 진입
        elif direction == "DOWN":
            if self.position == "LONG": # 레버리지 들고 있으면? -> 스위칭!
                self._update_balance("SELL", 0, self.holding_qty, lev_price)
                
                invest_amt = self._calc_invest_amount(grade)
                qty = int(invest_amt / inv_price)
                if qty > 0:
                    order = self._create_order("SWITCH_BUY", "SHORT", qty, f"스위칭: 레버리지매도->인버스매수({grade}급)")
                    self._update_balance("BUY", invest_amt, qty, inv_price)
                    
            elif self.position == "NEUTRAL":
                invest_amt = self._calc_invest_amount(grade)
                qty = int(invest_amt / inv_price)
                if qty > 0:
                    order = self._create_order("BUY", "SHORT", qty, f"신규진입: 인버스({grade}급)")
                    self._update_balance("BUY", invest_amt, qty, inv_price)
        
        return order

    def _calc_invest_amount(self, grade):
        """등급별 투입 금액 계산"""
        if grade == "S": return self.balance * 0.99 # 풀매수 (수수료 여유 1%)
        if grade == "A": return self.balance * 0.50 # 절반
        if grade == "B": return self.balance * 0.10 # 정찰병
        return 0

    def _create_order(self, action, target_pos, qty, msg):
        target_code = "122630" if target_pos == "LONG" else "252670" # 레버리지/인버스 코드
        return {
            "action": action,
            "code": target_code,
            "name": "레버리지" if target_pos == "LONG" else "인버스",
            "qty": qty,
            "msg": msg
        }

    def _update_balance(self, action, amount, qty, price):
        """내부 장부 업데이트 (시뮬레이션용)"""
        if action == "BUY":
            self.balance -= (qty * price)
            self.holding_qty = qty
            self.avg_price = price
            self.position = "LONG" if amount > 0 else "SHORT" # 로직상 단순화 (실제로는 호출부에서 제어)
            # 여기서는 편의상 호출 흐름에 따라 포지션이 결정된다고 가정
            
        elif action == "SELL":
            self.balance += (qty * price)
            self.holding_qty = 0
            self.avg_price = 0
            self.position = "NEUTRAL"
            
    # 외부에서 포지션을 강제 설정할 때 (스위칭 로직 보정용)
    def set_position_state(self, pos):
        self.position = pos