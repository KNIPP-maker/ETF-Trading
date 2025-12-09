import asyncio
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.kiwoom_client import KiwoomRESTClient

load_dotenv()

# 데이터 저장 폴더 생성
if not os.path.exists("data"):
    os.makedirs("data")

async def collect_market_data():
    kiwoom = KiwoomRESTClient()
    print("=============================================")
    print("📥 [데이터 수집기] 과거 차트 데이터 다운로드")
    print("=============================================")
    
    # 수집할 종목 목록
    targets = [
        {"name": "KODEX_레버리지", "code": "122630"},
        {"name": "KODEX_인버스2X", "code": "252670"},
        # {"name": "KOSPI_200", "code": "201"} # 지수 데이터 필요시 주석 해제
    ]

    try:
        await kiwoom._ensure_token()
    except Exception:
        print("❌ 키움 API 연결 실패. API 승인 상태를 확인하세요.")
        return

    for target in targets:
        name = target['name']
        code = target['code']
        print(f"\n📊 [{name}] ({code}) 데이터 수집 중...")
        
        all_data = []
        
        # 최근 100일치 데이터를 요청 (반복문으로 더 가져올 수 있음)
        # 키움 REST API는 한 번에 주는 개수 제한이 있으므로, Paging 처리가 필요할 수 있음
        # 여기서는 테스트를 위해 1회 호출
        raw_data = await kiwoom.get_chart_data(code, period_type="D")
        
        # (기존 코드의 for loop 내부 수정)
        
        # ka10005 응답 구조에 맞춘 파싱
        # 보통 'output' 리스트에 데이터가 들어옵니다.
        if raw_data and 'output' in raw_data:
            items = raw_data['output']
            print(f"   -> {len(items)}개 봉 데이터 수신")
            
            for item in items:
                # API 필드명 매핑 (문서 기준)
                # stck_bsop_date: 일자, stck_clpr: 종가, stck_oprc: 시가 ...
                all_data.append({
                    "date": item.get("stck_bsop_date", item.get("dt", "")),
                    "open": int(item.get("stck_oprc", item.get("open", 0))),
                    "high": int(item.get("stck_hgpr", item.get("high", 0))),
                    "low": int(item.get("stck_lwpr", item.get("low", 0))),
                    "close": int(item.get("stck_clpr", item.get("close", 0))),
                    "volume": int(item.get("acml_vol", item.get("vol", 0)))
                })
        else:
            print(f"   ⚠️ 데이터 수신 실패: {raw_data}") # 에러 메시지 상세 출력
            continue

        # 데이터프레임 변환 및 저장
        if all_data:
            df = pd.DataFrame(all_data)
            # 날짜순 정렬 (과거 -> 현재)
            df = df.sort_values("date").reset_index(drop=True)
            
            filename = f"data/{name}_daily.csv"
            df.to_csv(filename, index=False)
            print(f"   ✅ 저장 완료: {filename}")
        else:
            print("   ❌ 저장할 데이터가 없습니다.")
        
        # API 과부하 방지 대기
        await asyncio.sleep(1)

    print("\n🎉 모든 데이터 수집이 완료되었습니다.")

if __name__ == "__main__":
    try:
        asyncio.run(collect_market_data())
    except KeyboardInterrupt:
        print("수집 중단")