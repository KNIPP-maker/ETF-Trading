from services.kiwoom_manager import KiwoomManager
import datetime

# 실거래/모의투자 스위치
IS_LIVE_TRADING = True  # 실거래 True, 모의투자 False

# 종목명-코드 매핑 (예시)
CODES = {
    "KODEX 레버리지": "122630",
    "KODEX 200선물인버스2X": "252670",
}

LOG_FILE = "order_log.txt"

def log_order(event):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now()} {event}\n")
    except Exception as e:
        print(f"[ERROR] 주문 로그 파일 저장 실패: {e}")

# 실제 주문 실행 함수
# action: "BUY" or "SELL"
def execute_trade(asset, action, amount=None):
    try:
        km = KiwoomManager()
        kiwoom = km.get_kiwoom()
        account_no = km.get_account_no()
        code = CODES.get(asset, None)
        if asset == "ALL" and action == "SELL":
            # 전량 청산: 보유 종목 모두 매도 (예시)
            for name, code in CODES.items():
                qty = 10  # TODO: 실제 잔고 조회 후 보유수량으로 변경
                _place_order(kiwoom, account_no, code, qty, "1")
            log_order("[ORDER] ALL SELL (전량 청산)")
            return
        if code is None:
            log_order(f"[ERROR] Unknown asset: {asset}")
            return
        qty = amount if amount else 10
        order_type = "2" if action == "BUY" else "1"
        _place_order(kiwoom, account_no, code, qty, order_type)
        log_order(f"[ORDER] {action} {qty} of {asset}")
    except Exception as e:
        log_order(f"[ERROR] 주문 실행 실패: {e}")

# 내부 주문 실행 및 로그 기록
def _place_order(kiwoom, account_no, code, qty, order_type):
    try:
        log_msg = f"[실거래] 주문 실행: {code} ({qty}주)" if IS_LIVE_TRADING else f"[모의투자] 주문 실행: {code} ({qty}주)"
        log_order(log_msg)
        if IS_LIVE_TRADING:
            kiwoom.SendOrder("order", "0101", account_no, int(order_type), code, qty, 0, "03", "")
    except Exception as e:
        log_order(f"[ERROR] _place_order 실패: {e}") 