import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

REPORT_DIR = "../report"

st.set_page_config(page_title="ETF AutoTrader Dashboard", layout="wide")
st.title("ETF AutoTrader 거래 리포트 대시보드")

# 파일 경로
json_path = os.path.join(REPORT_DIR, "trade_report.json")
csv_path = os.path.join(REPORT_DIR, "trade_report.csv")
balance_img = os.path.join(REPORT_DIR, "balance_curve.png")
return_img = os.path.join(REPORT_DIR, "return_curve.png")

# 데이터 로드
if os.path.exists(json_path):
    with open(json_path, encoding="utf-8") as f:
        trade_data = json.load(f)
    df = pd.DataFrame(trade_data)
    df["time"] = pd.to_datetime(df["time"])
else:
    st.warning("리포트 파일이 없습니다. 먼저 generate_report()를 실행하세요.")
    st.stop()

# 요약 통계
st.subheader("거래 요약 통계")
col1, col2, col3 = st.columns(3)
col1.metric("총 거래 횟수", len(df))
col2.metric("최종 잔고", f"{df['balance'].iloc[-1]:,.0f}")
col3.metric("최종 누적 수익률(%)", f"{df['return(%)'].iloc[-1]:.2f}")

# 거래 내역 테이블
st.subheader("거래 내역")
st.dataframe(df[["time", "event", "price", "balance", "return(%)"]], use_container_width=True)

# 그래프 시각화
st.subheader("잔고/수익률 변화 그래프")
g1, g2 = st.columns(2)
with g1:
    st.image(balance_img, caption="누적 잔고 변화", use_column_width=True)
with g2:
    st.image(return_img, caption="누적 수익률 변화", use_column_width=True)

# CSV 다운로드
st.subheader("리포트 파일 다운로드")
with open(csv_path, "rb") as f:
    st.download_button("CSV 다운로드", f, file_name="trade_report.csv")
with open(json_path, "rb") as f:
    st.download_button("JSON 다운로드", f, file_name="trade_report.json") 