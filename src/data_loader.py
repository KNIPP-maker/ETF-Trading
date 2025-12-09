import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class DataLoader:
    def __init__(self):
        self.app_key = os.getenv("KIWOOM_APP_KEY")
        self.secret_key = os.getenv("KIWOOM_SECRET_KEY")
        self.base_url = "https://api.kiwoom.com"
        self.access_token = None

    def get_access_token(self):
        if self.access_token: return self.access_token
        
        url = f"{self.base_url}/oauth2/token"
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        data = {
            'grant_type': 'client_credentials', 
            'appkey': self.app_key, 
            'secretkey': self.secret_key
        }
        
        try:
            res = requests.post(url, headers=headers, json=data)
            if res.status_code == 200:
                self.access_token = res.json().get('token')
                # print("✅ [시스템] 토큰 발급 완료")
                return self.access_token
        except Exception as e:
            print(f"❌ [에러] 토큰 발급 실패: {e}")
        return None

    def get_etf_data(self, stock_code):
        """ 
        [하이브리드 데이터 조회]
        1. 호가 데이터 (ka10004) -> 매수/매도 잔량 확인용
        2. ETF 데이터 (ka40004) -> iNAV 확인용 (보조)
        """
        token = self.get_access_token()
        if not token: return None

        # ---------------------------------------------------------
        # 1. 호가 데이터 조회 (ka10004) - 필수
        # ---------------------------------------------------------
        url_orderbook = f"{self.base_url}/api/dostk/mrkcond"
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'ka10004',
            'custtype': 'P',
        }
        
        result_data = {
            "code": stock_code,
            "price": 0,
            "inav": 0,
            "disparity_rate": 0.0,
            "orderbook": {"asks": [], "bids": []}
        }

        try:
            res = requests.post(url_orderbook, headers=headers, json={"stk_cd": stock_code})
            if res.status_code == 200:
                output = res.json().get('output', {})
                
                # 현재가
                try:
                    result_data['price'] = abs(float(output.get('stck_prpr', output.get('sel_fpr_bid', 0))))
                except: pass

                # 호가 파싱
                asks = []
                for i in range(5, 0, -1):
                    p = output.get(f"sel_{i}th_pre_bid", "0")
                    v = output.get(f"sel_{i}th_pre_req", "0")
                    asks.append({"price": int(p) if p else 0, "vol": int(v) if v else 0})
                
                bids = []
                for i in range(1, 6):
                    p = output.get(f"buy_{i}th_pre_bid", "0")
                    v = output.get(f"buy_{i}th_pre_req", "0")
                    bids.append({"price": int(p) if p else 0, "vol": int(v) if v else 0})
                
                result_data['orderbook']['asks'] = asks
                result_data['orderbook']['bids'] = bids

        except Exception as e:
            print(f"❌ 호가 조회 에러: {e}")

        # ---------------------------------------------------------
        # 2. iNAV 데이터 조회 (ka40004) - 선택 (느리면 제거 가능)
        # ---------------------------------------------------------
        # ※ 매번 호출하면 느릴 수 있으므로 1초에 한번만 호출하는 등의 최적화가 필요할 수 있음.
        # 일단은 정확한 데이터를 위해 호출함.
        
        url_etf = f"{self.base_url}/api/dostk/etf"
        headers['api-id'] = 'ka40004'
        params_etf = {
            "txon_type": "0", "navpre": "0", "mngmcomp": "3020", 
            "txon_yn": "0", "trace_idex": "0", "stex_tp": "1"
        }

        try:
            res = requests.post(url_etf, headers=headers, json=params_etf)
            if res.status_code == 200:
                etf_list = res.json().get('etfall_mrpr', [])
                if not etf_list: etf_list = res.json().get('output', [])
                
                for item in etf_list:
                    if item.get('stk_cd', '').strip() == stock_code:
                        result_data['inav'] = float(item.get('nav', 0))
                        break
        except: pass

        # 괴리율 계산 (데이터가 둘 다 있을 때만)
        if result_data['price'] > 0 and result_data['inav'] > 0:
            result_data['disparity_rate'] = ((result_data['price'] - result_data['inav']) / result_data['inav']) * 100

        return result_data

if __name__ == "__main__":
    loader = DataLoader()
    print(loader.get_etf_data("122630"))