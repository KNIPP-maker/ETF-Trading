import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 윈도우 비동기 에러 방지
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ---------------------------------------------------------
# [1] 환경변수 로드 진단 (가장 중요)
# ---------------------------------------------------------
# 현재 파일(src/debug_connection.py) 기준으로 .env 위치 찾기
# 경로: 현재파일 -> 상위폴더(src) -> 상위폴더(프로젝트 루트) -> .env
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / '.env'

print(f"📂 프로젝트 루트: {project_root}")
print(f"📄 .env 파일 경로: {env_path}")

# 강제로 경로 지정해서 로드
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print("✅ .env 파일을 발견하고 로드했습니다.")
else:
    print("❌ [치명적 오류] .env 파일을 찾을 수 없습니다!")
    print("   -> 파일 이름이 '.env'가 맞는지(확장자 없음), 프로젝트 루트에 있는지 확인하세요.")

# 키 값 로드 확인
APP_KEY = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")

print("-" * 40)
if APP_KEY:
    print(f"🔑 APP_KEY 로드됨: {APP_KEY[:5]}..." + "*"*10)
else:
    print("❌ APP_KEY가 None입니다. .env 파일 안에 'KIWOOM_APP_KEY=' 부분이 있는지 확인하세요.")

if SECRET_KEY:
    print(f"🔑 SECRET_KEY 로드됨: {SECRET_KEY[:5]}..." + "*"*10)
else:
    print("❌ SECRET_KEY가 None입니다. .env 파일 내용을 확인하세요.")
print("-" * 40)

# 키가 없으면 여기서 중단
if not APP_KEY or not SECRET_KEY:
    print("⛔ 키 값이 없어서 서버 접속을 시도하지 않습니다.")
    sys.exit()

# ---------------------------------------------------------
# [2] 서버 접속 테스트
# ---------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.kiwoom_client import KiwoomRESTClient

async def debug_system():
    print("\n📡 키움증권 서버 접속 시도...")
    kiwoom = KiwoomRESTClient()
    
    try:
        # 토큰 발급
        await kiwoom._ensure_token()
        
        if kiwoom.access_token:
            print(f"✅ [성공] 토큰 발급 완료! (길이: {len(kiwoom.access_token)})")
            
            # 잔고 조회
            print("💰 잔고 조회 시도...")
            balance = await kiwoom.get_account_balance()
            if balance:
                print(f"   📄 응답: {str(balance)[:100]}...")
            else:
                print("   ❌ 잔고 응답 없음")
        else:
            print("❌ 토큰 발급 실패 (키 값은 있지만 서버 거부)")
            
    except Exception as e:
        print(f"⚠️ 오류 발생: {e}")
    finally:
        await kiwoom.close()
        print("============== [진단 종료] ==============")

if __name__ == "__main__":
    try:
        asyncio.run(debug_system())
    except KeyboardInterrupt:
        pass