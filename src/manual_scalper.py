import asyncio
import os
import sys
import keyboard # 키보드 입력 감지
import json
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.kiwoom_client import KiwoomRESTClient

load_dotenv()

# ==========================================
# ⚙️ [설정] 스캘핑 타겟 및 수량
# ==========================================
TARGET_CODE = "122630"  # KODEX 레버리지 (기본값)
ORDER_QTY   = 100       # 한 번 누를 때마다 100주
# ==========================================

class LightningTrigger:
    def __init__(self):
        self.kiwoom = KiwoomRESTClient()
        self.loop = None
        self.running = True
        
        # 미리 만들어둔 주문 패킷 (속도 최적화)
        self.buy_payload = None
        self.sell_payload = None

    async def initialize(self):
        print("🔌 키움 서버 연결 중...")
        await self.kiwoom._ensure_token()
        
        # [핵심] 주문 데이터를 미리 조립해둡니다 (누를 때 계산 안 함)
        # 매수 패킷
        self.buy_payload = {
            "account_no": self.kiwoom.account_no,
            "ord_type": "1", # 신규매수
            "stk_cd": TARGET_CODE,
            "ord_qty": str(ORDER_QTY),
            "ord_price": "0",    # 시장가
            "trade_type": "03"   # 시장가
        }
        
        # 매도 패킷
        self.sell_payload = {
            "account_no": self.kiwoom.account_no,
            "ord_type": "2", # 신규매도
            "stk_cd": TARGET_CODE,
            "ord_qty": str(ORDER_QTY),
            "ord_price": "0",
            "trade_type": "03"
        }
        
        print(f"✅ [준비 완료] 타겟: {TARGET_CODE} | 수량: {ORDER_QTY}주")
        print("----------------------------------------------------")
        print("⌨️  [F1] 키: 시장가 매수 (Buy)")
        print("⌨️  [F2] 키: 시장가 매도 (Sell)")
        print("⌨️  [F4] 키: 타겟 변경 (레버리지 <-> 인버스)")
        print("⌨️  [ESC] 키: 프로그램 종료")
        print("----------------------------------------------------")

    async def send_fast_order(self, type_name, payload):
        """
        초고속 주문 전송 (응답 대기 최소화)
        """
        # 로깅조차 사치일 수 있지만 확인용으로 출력
        print(f"🚀 [{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] {type_name} 주문 발사!!")
        
        url = f"{self.kiwoom.DOMAIN}/api/dostk/ordr"
        headers = {
            "Authorization": f"Bearer {self.kiwoom.access_token}",
            "content-type": "application/json;charset=UTF-8",
            "api-id": "ka10000"
        }

        # aiohttp로 비동기 전송
        try:
            async with self.kiwoom.session.post(url, headers=headers, json=payload) as response:
                # 응답을 기다리긴 하지만, 이미 주문은 서버로 떠났음
                if response.status != 200:
                    text = await response.text()
                    print(f"❌ 주문 실패: {text}")
                else:
                    # 성공 시 별도 로그 없이 쾌적하게 유지 (원하면 추가 가능)
                    pass
        except Exception as e:
            print(f"❌ 전송 오류: {e}")

    def switch_target(self):
        global TARGET_CODE
        if TARGET_CODE == "122630": # 레버리지면
            TARGET_CODE = "252670"  # 인버스로
            name = "KODEX 인버스2X"
        else:
            TARGET_CODE = "122630"
            name = "KODEX 레버리지"
            
        # 패킷 재생성
        self.buy_payload["stk_cd"] = TARGET_CODE
        self.sell_payload["stk_cd"] = TARGET_CODE
        print(f"\n🔄 [타겟 변경] 현재 타겟: {name} ({TARGET_CODE})")

    async def run(self):
        # ClientSession을 여기서 열고 계속 유지 (Keep-Alive)
        async with aiohttp.ClientSession() as session:
            self.kiwoom.session = session # 세션 주입
            await self.initialize()

            while self.running:
                # 0.01초 간격으로 키 입력 감지 (CPU 점유율 방지)
                try:
                    if keyboard.is_pressed('F1'):
                        # 중복 입력 방지 (떼질 때까지 대기하거나 쿨타임 필요하면 추가)
                        await self.send_fast_order("매수", self.buy_payload)
                        await asyncio.sleep(0.2) # 연타 방지 0.2초 쿨타임

                    elif keyboard.is_pressed('F2'):
                        await self.send_fast_order("매도", self.sell_payload)
                        await asyncio.sleep(0.2)

                    elif keyboard.is_pressed('F4'):
                        self.switch_target()
                        await asyncio.sleep(0.3)

                    elif keyboard.is_pressed('esc'):
                        print("시스템을 종료합니다.")
                        self.running = False
                        
                    await asyncio.sleep(0.01) # 루프 속도 조절
                    
                except Exception as e:
                    print(f"Error: {e}")
                    break

if __name__ == "__main__":
    import aiohttp # 로컬 임포트
    
    # 윈도우의 경우 이벤트 루프 정책 설정 필요할 수 있음
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    trigger = LightningTrigger()
    try:
        asyncio.run(trigger.run())
    except KeyboardInterrupt:
        pass