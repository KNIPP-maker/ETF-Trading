import aiohttp
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class KiwoomRESTClient:
    """
    [SOLAB] 키움증권 REST API 통신 모듈 (원본 복구 버전)
    """
    DOMAIN = "https://api.kiwoom.com"
    TOKEN_URL = "https://api.kiwoom.com/oauth2/token"

    def __init__(self, app_key=None, secret_key=None, account_no=None):
        self.app_key = app_key if app_key else os.getenv("KIWOOM_APP_KEY")
        self.secret_key = secret_key if secret_key else os.getenv("KIWOOM_SECRET_KEY")
        self.account_no = account_no if account_no else os.getenv("ACCOUNT_NO")
        
        self.access_token = None
        self.token_expiry = None
        self.session = None

        if not self.app_key or not self.secret_key:
            print("❌ [Client] 키 설정 오류: .env 파일을 확인하세요.")

    async def _ensure_token(self):
        # 토큰 유효성 체크
        if self.access_token and self.token_expiry and self.token_expiry > datetime.now():
            return

        if not self.session:
            self.session = aiohttp.ClientSession()

        headers = {"Content-Type": "application/json;charset=UTF-8"}
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.secret_key
        }

        try:
            async with self.session.post(self.TOKEN_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get("access_token") or data.get("token")
                    
                    if "expires_in" in data:
                        self.token_expiry = datetime.now() + timedelta(seconds=int(data["expires_in"]) - 60)
                    else:
                        self.token_expiry = datetime.now() + timedelta(hours=6)
                        
                    print(f"✅ [토큰발급] 성공! (만료: {self.token_expiry.strftime('%H:%M:%S')})")
                else:
                    print(f"❌ [토큰실패] {response.status}: {await response.text()}")
        except Exception as e:
            print(f"❌ [연결오류] {e}")

    async def get_current_price(self, code: str):
        """현재가 조회 (ka10004)"""
        await self._ensure_token()
        url = f"{self.DOMAIN}/api/dostk/mrkcond"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json;charset=UTF-8",
            "api-id": "ka10004"
        }
        try:
            async with self.session.post(url, headers=headers, json={"stk_cd": code}) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except: return None

    async def get_account_balance(self):
        """
        [원본] 잔고 조회 (ka01690 - 계좌자산/수익률)
        """
        await self._ensure_token()
        
        # 원래 쓰시던 URL (/api/dostk/acnt)로 복구
        url = f"{self.DOMAIN}/api/dostk/acnt"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json;charset=UTF-8",
            "api-id": "ka01690"
        }
        
        # 오늘 날짜
        today = datetime.now().strftime("%Y%m%d")
        
        payload = {
            "account_no": self.account_no,  # 혹은 acc_no 확인 필요 (보통 account_no)
            "qry_dt": today,
            "comp_yn": "N"
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"⚠️ 잔고조회 실패: {await response.text()}")
                    return None
        except: return None

    async def send_order(self, code, qty, order_type, price=0):
        """주문 전송 (kt10000)"""
        await self._ensure_token()
        url = f"{self.DOMAIN}/api/dostk/ordr"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "content-type": "application/json;charset=UTF-8",
            "api-id": "kt10000"
        }
        
        # 매수/매도 구분 (API 규격: 매도=1, 매수=2)
        ord_type = "1" if order_type == "sell" else "2"
        # 거래 구분 (시장가=03, 지정가=00)
        trade_type = "03" if price == 0 else "00"
        
        payload = {
            "account_no": self.account_no,
            "dmst_stex_tp": "SOR",
            "ord_type": ord_type,
            "stk_cd": code,
            "ord_qty": str(qty),
            "ord_price": str(price),
            "trade_type": trade_type,
            "cond_uv": ""
        }
        
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()
        except: return None
        
    async def close(self):
        if self.session: await self.session.close()