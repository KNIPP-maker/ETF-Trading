from pykiwoom.kiwoom import Kiwoom

# KOSPI200 선물/현물, 외국인 수급, ETF 가격을 TR로 받아오는 함수
# kiwoom: 로그인된 Kiwoom 객체를 인자로 받음

def fetch_market_data(kiwoom):
    try:
        # KOSPI200 현물 (지수)
        kiwoom.SetInputValue("업종코드", "201")  # 201: KOSPI200
        spot_df = kiwoom.BlockRequest("OPT50001", 업종코드="201", output="업종현재가", next=0)
        spot = float(spot_df["현재가"].iloc[0])
    except Exception as e:
        print(f"[ERROR] KOSPI200 현물 데이터 수신 실패: {e}")
        spot = None

    try:
        # KOSPI200 선물
        kiwoom.SetInputValue("종목코드", "101S3000")  # 101S3000: 최근월 KOSPI200 선물
        fut_df = kiwoom.BlockRequest("OPT50028", 종목코드="101S3000", output="선물현재가", next=0)
        futures = float(fut_df["현재가"].iloc[0])
    except Exception as e:
        print(f"[ERROR] KOSPI200 선물 데이터 수신 실패: {e}")
        futures = None

    try:
        # 외국인 수급
        kiwoom.SetInputValue("종목코드", "201")
        flow_df = kiwoom.BlockRequest("OPT90003", 종목코드="201", output="외인기관종목별동향", next=0)
        foreign_net = int(flow_df["외국계순매수"].iloc[0])
    except Exception as e:
        print(f"[ERROR] 외국인 수급 데이터 수신 실패: {e}")
        foreign_net = None

    try:
        # ETF 가격 (KODEX 레버리지, 122630)
        kiwoom.SetInputValue("종목코드", "122630")
        etf_df = kiwoom.BlockRequest("OPT10001", 종목코드="122630", output="주식기본정보", next=0)
        etf_price = float(etf_df["현재가"].iloc[0])
    except Exception as e:
        print(f"[ERROR] ETF 가격 데이터 수신 실패: {e}")
        etf_price = None

    return {
        "futures": futures,
        "spot": spot,
        "foreign_net": foreign_net,
        "etf_price": etf_price
    } 