import json
import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv("MECOM_HEAD_API", "http://localhost:8000")

st.set_page_config(page_title="MECOM 본사 통합관제", layout="wide")
st.title("MECOM 본사 통합관제")

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

ADMIN_USER = os.getenv("MECOM_ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("MECOM_ADMIN_PASS", "admin123")


def get_headers():
    headers = {"Content-Type": "application/json"}
    if st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"
    return headers


def api_get(path):
    try:
        return requests.get(f"{API_BASE}{path}", headers=get_headers(), timeout=5).json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path, json_data):
    try:
        return requests.post(f"{API_BASE}{path}", json=json_data, headers=get_headers(), timeout=5).json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_delete(path):
    try:
        return requests.delete(f"{API_BASE}{path}", headers=get_headers(), timeout=5).json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


if not st.session_state.auth_token:
    st.markdown("### 관리자 로그인")
    user = st.text_input("Username", value=ADMIN_USER)
    pw = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if user == ADMIN_USER and pw == ADMIN_PASS:
            st.session_state.auth_token = json.dumps({"user": user, "pass": pw})
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

with st.sidebar:
    st.markdown(f"**관리자:** {ADMIN_USER}")
    if st.button("Logout", use_container_width=True):
        st.session_state.auth_token = None
        st.rerun()

tab_sites, tab_alarms, tab_reports = st.tabs(["현장 관리", "알람 이력", "일일리포트"])

with tab_sites:
    col_list, col_register = st.columns([3, 2])
    with col_list:
        st.subheader("등록된 현장")
        sites = api_get("/sites")
        if sites:
            for site in sites:
                with st.container(border=True):
                    sc1, sc2, sc3 = st.columns([3, 1, 1])
                    with sc1:
                        st.markdown(f"**{site.get('name', site['id'])}** (`{site['id']}`)")
                        st.caption(f"API Key: {site.get('api_key', '(none)')} | Created: {site.get('created_at', '')}")
                    with sc2:
                        detail_key = f"detail_{site['id']}"
                        if st.button("상세", key=detail_key, use_container_width=True):
                            st.session_state.selected_site = site['id']
                    with sc3:
                        if st.button("삭제", key=f"del_{site['id']}", use_container_width=True):
                            result = api_delete(f"/api/sites/{site['id']}")
                            if result and result.get("success"):
                                st.success(f"Deleted {site['id']}")
                                st.rerun()
                            else:
                                st.error("Delete failed")
            if hasattr(st, 'selected_site') or 'selected_site' in st.session_state:
                sid = st.session_state.get('selected_site')
                if sid:
                    st.markdown("---")
                    st.markdown(f"### 현장 상세: {sid}")
                    logs = api_get(f"/api/realtime-log?site_id={sid}&limit=20")
                    if logs:
                        df = pd.DataFrame(logs)
                        st.dataframe(df.drop(columns=["id", "bits_json", "words_json"], errors="ignore"),
                                     use_container_width=True, hide_index=True)
                        if not df.empty and "words_json" in df.columns and df.iloc[0]["words_json"]:
                            words = json.loads(df.iloc[0]["words_json"])
                            labels = ["지중공급(1)", "지중환수(1)", "지중공급(2)", "지중환수(2)",
                                      "2차공급(1)", "2차환수(1)", "2차공급(2)", "2차환수(2)",
                                      "1동유량", "2동유량", "생산열량"]
                            vals = {labels[i]: words[i] for i in range(min(len(labels), len(words)))}
                            st.json(vals)
                    else:
                        st.info("No data yet")
        else:
            st.info("등록된 현장이 없습니다.")

    with col_register:
        st.subheader("현장 등록")
        with st.form("register_form"):
            sid = st.text_input("Site ID", placeholder="e.g. site_a")
            name = st.text_input("Site Name", placeholder="e.g. A현장")
            api_key = st.text_input("API Key", placeholder="optional")
            if st.form_submit_button("등록", use_container_width=True):
                if sid:
                    result = api_post(f"/api/register?site_id={sid}&name={name}&api_key={api_key}", {})
                    if result and result.get("success"):
                        st.success(f"Site '{sid}' registered")
                        st.rerun()
                    else:
                        st.error(result.get("detail", "Registration failed") if result else "API error")
                else:
                    st.warning("Site ID is required")

with tab_alarms:
    st.subheader("알람 이력")
    col_a1, col_a2 = st.columns([1, 3])
    with col_a1:
        sites_list = api_get("/sites")
        all_sites = [""] + [s["id"] for s in (sites_list or [])]
        selected_site = st.selectbox("현장 필터", all_sites, format_func=lambda x: "전체 현장" if x == "" else x)
    with col_a2:
        limit = st.number_input("조회 개수", min_value=10, max_value=200, value=50, step=10)
    params = f"?limit={limit}"
    if selected_site:
        params += f"&site_id={selected_site}"
    alarms = api_get(f"/api/alarms{params}")
    if alarms:
        df = pd.DataFrame(alarms)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("알람이 없습니다.")

with tab_reports:
    st.subheader("일일리포트")
    sites_list = api_get("/sites")
    all_sites = [""] + [s["id"] for s in (sites_list or [])]
    selected = st.selectbox("현장 선택", all_sites, key="rpt_site",
                            format_func=lambda x: "전체 현장" if x == "" else x)
    reports = api_get(f"/api/daily-reports?site_id={selected}&limit=20" if selected else "/api/daily-reports?limit=20")
    if reports:
        df = pd.DataFrame(reports)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("보고서가 없습니다.")
