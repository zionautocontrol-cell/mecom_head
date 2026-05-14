import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="MECOM 본사 통합관제", layout="wide")
st.title("🏢 MECOM 본사 통합관제")

tab1, tab2, tab3 = st.tabs(["📡 현장 목록", "⚠️ 알람 이력", "📊 현장 상세"])

with tab1:
    st.subheader("등록된 현장")
    try:
        sites = requests.get(f"{API_BASE}/sites", timeout=5).json()
        if sites:
            df = pd.DataFrame(sites)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("등록된 현장이 없습니다.")
    except Exception as e:
        st.error(f"서버 연결 실패: {e}")

with tab2:
    st.subheader("알람 이력")
    try:
        alarms = requests.get(f"{API_BASE}/api/alarms", timeout=5).json()
        if alarms:
            df = pd.DataFrame(alarms)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("알람이 없습니다.")
    except Exception as e:
        st.error(f"서버 연결 실패: {e}")

with tab3:
    st.subheader("현장 상세 조회")
    try:
        sites = requests.get(f"{API_BASE}/sites", timeout=5).json()
        site_ids = [s["id"] for s in sites] if sites else []
        if site_ids:
            selected = st.selectbox("현장 선택", site_ids)
            if st.button("실시간 데이터 조회"):
                logs = requests.get(f"{API_BASE}/api/realtime-log", params={"site_id": selected, "limit": 10}, timeout=5).json()
                if logs:
                    df = pd.DataFrame(logs)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("데이터가 없습니다.")
    except Exception as e:
        st.error(f"서버 연결 실패: {e}")
