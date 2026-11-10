from __future__ import annotations

"""8501 HTML 대시보드와 같은 정보 구조를 Streamlit 위젯으로 재현합니다."""

import base64
import csv
from html import escape
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ulfra_pjt.dashboard_chat import answer_question
from ulfra_pjt.dashboard_data import (
    find_region,
    get_snapshot,
    list_places,
    search_places,
)
from ulfra_pjt.queries import get_gu_list
from ulfra_pjt.scoring import CATEGORIES

DATA_CAPTION = "상가 데이터 기준: 2026-06 / 인구 데이터 기준: 2026-08"
ULSAN_CENTER = [35.5396, 129.3115]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAGE_OPTIONS = [
    ("🏠　홈", "home", "홈"),
    ("🗺️　지도탐색", "map", "지도"),
    ("📊　동네비교", "compare", "지역 비교"),
    ("🤖　데이터 챗봇", "chat", "데이터 챗봇"),
    ("🛠️　데이터점검", "data", "데이터 관제탑"),
]
PAGE_KEYS = {page_key for _, page_key, _ in PAGE_OPTIONS}
CATEGORY_COLORS = {
    "medical": "#e11d48",
    "food": "#f97316",
    "cafe": "#059669",
    "shop": "#2563eb",
}

PURE_DASHBOARD_CSS = """
<style>
.stApp {
    background: #f1f5f9;
    color: #0f172a;
    font-family: Pretendard, "Malgun Gothic", -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stHeader"] { display: none; }
[data-testid="stElementContainer"]:has(> [data-testid="stHtml"] > script) { display: none; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #eef2f7;
    min-width: 318px;
}
[data-testid="stSidebarContent"] {
    padding: 0 18px 20px 18px !important;
}
[data-testid="stSidebarHeader"] {
    position: absolute;
    top: 4px;
    right: 8px;
    height: 28px !important;
    width: 36px;
    z-index: 5;
    padding: 0 !important;
    background: transparent;
}
[data-testid="stLogoSpacer"] {
    display: none !important;
}
[data-testid="stSidebarUserContent"] {
    padding-top: 8px !important;
}
[data-testid="stSidebarNav"] {
    display: none;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    margin-bottom: 0;
}
.ulfra-side-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 11px;
    margin: 2px 0 15px 0;
}
.ulfra-brand-wrap {
    display: flex;
    align-items: center;
    gap: 11px;
    min-width: 0;
}
.ulfra-logo-mark {
    width: 40px;
    height: 40px;
    border-radius: 11px;
    background: #2f63e8;
    color: #ffffff;
    display: grid;
    place-items: center;
    font-weight: 950;
    font-size: 21px;
    box-shadow: 0 7px 15px rgba(47, 99, 232, .24);
    flex: 0 0 auto;
}
.ulfra-brand {
    min-width: 0;
    flex: 1 1 auto;
}
.ulfra-brand-title {
    color: #111827;
    font-size: 22px;
    line-height: 1;
    font-weight: 950;
    letter-spacing: .01em;
}
.ulfra-brand-subtitle {
    color: #94a3b8;
    font-size: 13px;
    line-height: 1.35;
    font-weight: 850;
    margin-top: 4px;
    white-space: nowrap;
}
.ulfra-door-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    height: 32px;
    padding: 0 11px;
    border: 1px solid #d8e1ee;
    border-radius: 9px;
    background: #f8fafc;
    color: #475569 !important;
    font-size: 13px;
    font-weight: 900;
    text-decoration: none !important;
    white-space: nowrap;
}
.ulfra-door-link:hover {
    background: #eef4ff;
    color: #2563eb !important;
}
.ulfra-page-nav {
    border-bottom: 1px solid #d8dee8;
    margin: 0 0 18px 0;
    padding-bottom: 18px;
}
.ulfra-page-nav-label {
    color: #64748b;
    font-size: 14px;
    line-height: 1.25;
    margin: 0 0 9px 0;
}
.ulfra-page-nav-link {
    min-height: 30px;
    border-radius: 7px;
    display: flex;
    align-items: center;
    padding: 0 10px;
    font-size: 15px;
    font-weight: 800;
    color: #64748b !important;
    text-decoration: none !important;
}
.ulfra-page-nav-link:hover {
    color: #2563eb !important;
    background: #eff6ff;
}
.ulfra-page-nav-active {
    background: #e6ebf3;
    color: #172033 !important;
}
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadio"]),
[data-testid="stSidebar"] [data-testid="stRadio"],
[data-testid="stSidebar"] [data-testid="stRadioGroup"],
[data-testid="stSidebar"] [data-testid="stRadioGroup"] > div {
    width: 100%;
}
[data-testid="stSidebar"] [role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 14px;
    width: 100%;
    align-items: stretch !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
    display: flex !important;
    align-items: center;
    gap: 8px;
    width: 100%;
    min-height: 52px;
    border-radius: 14px;
    padding: 0 16px;
    box-sizing: border-box;
    transition: background .15s ease, color .15s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #f4f8ff;
}
[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: #64748b;
    font-size: 18px;
    font-weight: 950;
}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #2563eb;
}
[data-testid="stSidebar"] [role="radiogroup"] input {
    accent-color: #ff405a;
    width: 16px;
    height: 16px;
}
.ulfra-sidebar-spacer {
    height: clamp(62px, 8vh, 88px);
}
.ulfra-metrics-card {
    border: 1px solid #dbe4ef;
    background: #f8fafc;
    border-radius: 15px;
    padding: 18px 15px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.85);
}
.ulfra-metrics-title {
    color: #94a3b8;
    font-size: 14px;
    font-weight: 950;
    letter-spacing: .04em;
    margin-bottom: 16px;
}
.ulfra-metric-row {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 14px;
    align-items: start;
    margin-top: 12px;
}
.ulfra-metric-label {
    color: #64748b;
    font-size: 15px;
    font-weight: 800;
}
.ulfra-metric-value {
    color: #0f172a;
    font-size: 16px;
    font-weight: 950;
    text-align: right;
    line-height: 1.2;
}
.ulfra-metric-value.blue {
    color: #2563eb;
}
.ulfra-metric-value.green {
    color: #059669;
}
.ulfra-side-footnote {
    color: #7b8ba4;
    font-size: 15px;
    line-height: 1.65;
    font-weight: 650;
    margin-top: 20px;
}
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.2rem;
    max-width: 1500px;
}
.ulfra-header {
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.09), transparent 58%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    border: 1px solid rgba(255,255,255,.85);
    border-radius: 22px;
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
    padding: 20px 24px;
    margin-bottom: 18px;
}
.ulfra-title {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
    color: #0f172a;
    font-size: 30px;
    line-height: 1.25;
    font-weight: 900;
}
.ulfra-desc {
    color: #64748b;
    font-size: 14px;
    line-height: 1.7;
    margin-top: 8px;
}
.ulfra-badge {
    display: inline-flex;
    align-items: center;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
    color: #2563eb;
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 800;
}
.ulfra-card {
    background: rgba(255,255,255,.86);
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    box-shadow: 0 8px 24px rgba(15,78,86,.06);
    padding: 18px;
}
.ulfra-kpi-label {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 900;
    text-transform: uppercase;
}
.ulfra-kpi-value {
    color: #0f172a;
    font-size: 30px;
    font-weight: 950;
    margin-top: 4px;
}
.ulfra-kpi-sub {
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    margin-top: 4px;
}
.ulfra-status {
    border: 1px solid #bbf7d0;
    background: #ecfdf5;
    color: #047857;
    border-radius: 12px;
    padding: 7px 10px;
    font-size: 12px;
    font-weight: 800;
}
.ulfra-home-stage {
    padding: 4px 4px 12px;
}
.ulfra-home-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 20px;
    margin: 4px 0 24px;
}
.ulfra-home-title-line {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.ulfra-home-title {
    color: #0f172a;
    font-size: 32px;
    line-height: 1.2;
    font-weight: 950;
}
.ulfra-home-desc {
    color: #64748b;
    font-size: 16px;
    line-height: 1.65;
    margin-top: 12px;
}
.ulfra-home-status {
    flex: 0 0 auto;
    border: 1px solid #bfdbfe;
    background: #eff6ff;
    color: #0f172a;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 15px;
    font-weight: 800;
}
.ulfra-home-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 20px;
}
.ulfra-home-card {
    min-height: 382px;
    border-radius: 22px;
    border: 1px solid #dbe4ef;
    box-shadow: 0 12px 30px rgba(15,23,42,.08);
    overflow: hidden;
    position: relative;
    display: flex;
    flex-direction: column;
    text-decoration: none !important;
}
.ulfra-card-arrow {
    position: absolute;
    top: 26px;
    right: 28px;
    color: #94a3b8;
    font-size: 32px;
    font-weight: 700;
}
.ulfra-home-card-title {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #0f172a;
    font-size: 30px;
    font-weight: 950;
    line-height: 1.2;
}
.ulfra-home-card-sub {
    color: #64748b;
    font-size: 17px;
    font-weight: 650;
    margin-top: 4px;
}
.ulfra-map-card {
    justify-content: flex-end;
    min-height: 382px;
    padding: 38px 34px;
    color: #ffffff;
    background:
        linear-gradient(to top, rgba(2,6,23,.82) 0%, rgba(15,23,42,.50) 36%, rgba(255,255,255,.22) 100%),
        linear-gradient(135deg, #18305a 0%, #1c6982 55%, #7c3aed 100%);
    background-size: cover;
    background-position: center;
}
.ulfra-map-card * {
    color: #ffffff !important;
}
.ulfra-map-kicker {
    position: absolute;
    top: 35px;
    left: 34px;
    border-radius: 999px;
    background: rgba(255,255,255,.28);
    backdrop-filter: blur(8px);
    padding: 8px 14px;
    font-size: 16px;
    font-weight: 900;
}
.ulfra-map-title {
    font-size: 38px;
    font-weight: 950;
    line-height: 1.1;
}
.ulfra-map-sub {
    margin-top: 8px;
    font-size: 18px;
    font-weight: 650;
    color: rgba(255,255,255,.86) !important;
}
.ulfra-map-cta {
    width: fit-content;
    margin-top: 22px;
    border-radius: 999px;
    background: #ffffff;
    color: #111827 !important;
    padding: 12px 28px;
    font-size: 18px;
    font-weight: 950;
    box-shadow: 0 8px 20px rgba(2,6,23,.22);
}
.ulfra-compare-card {
    background: #ffffff;
    padding: 34px;
}
.ulfra-bar-stage {
    flex: 1;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    gap: 68px;
    border-bottom: 1px solid #e2e8f0;
    margin: 38px 0 18px;
    min-height: 172px;
}
.ulfra-mini-bar-wrap {
    width: 70px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
}
.ulfra-mini-label {
    font-size: 15px;
    font-weight: 900;
}
.ulfra-mini-bar {
    width: 66px;
    border-radius: 8px 8px 0 0;
}
@keyframes ulfra-bar-rise-one {
    0%, 100% { height: 25px; }
    50% { height: 85px; }
}
@keyframes ulfra-bar-rise-two {
    0%, 100% { height: 40px; }
    50% { height: 95px; }
}
.ulfra-mini-bar-wrap:nth-child(1) .ulfra-mini-bar { animation: ulfra-bar-rise-one 3.2s ease-in-out infinite; }
.ulfra-mini-bar-wrap:nth-child(2) .ulfra-mini-bar { animation: ulfra-bar-rise-two 3.2s ease-in-out .6s infinite; }
.ulfra-mini-bar-wrap:nth-child(3) .ulfra-mini-bar { animation: ulfra-bar-rise-one 3.2s ease-in-out 1.2s infinite; }
@media (prefers-reduced-motion: reduce) {
    .ulfra-mini-bar { animation: none !important; }
}
.ulfra-card-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    color: #64748b;
    font-size: 16px;
    font-weight: 700;
}
.ulfra-card-bottom strong {
    color: #2563eb;
    font-weight: 950;
}
.ulfra-chat-card {
    background: linear-gradient(135deg, #312e81, #5b2d90);
    padding: 34px;
}
.ulfra-chat-card * {
    color: #ffffff;
}
.ulfra-chat-terminal {
    margin: 54px 0 48px;
    min-height: 126px;
    border-radius: 14px;
    background: rgba(15,23,42,.46);
    display: flex;
    align-items: center;
    padding: 0 28px;
    color: #00ff99 !important;
    font-family: Consolas, "Courier New", monospace;
    font-size: 19px;
    letter-spacing: .02em;
}
.ulfra-chat-terminal::after {
    content: "";
    display: inline-block;
    width: 2px;
    height: 32px;
    background: #00ff99;
    margin-left: auto;
}
.ulfra-data-card {
    background: #18181b;
    padding: 34px;
}
.ulfra-data-card * {
    color: #f8fafc;
}
.ulfra-online-pill {
    position: absolute;
    top: 32px;
    right: 34px;
    border: 1px solid rgba(34,197,94,.38);
    border-radius: 999px;
    background: rgba(22,163,74,.24);
    color: #4ade80 !important;
    padding: 6px 16px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 17px;
    font-weight: 800;
}
.ulfra-data-table {
    margin: 60px 0 44px;
    border-radius: 10px;
    background: #0d0d0f;
    padding: 14px 16px;
}
.ulfra-data-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid rgba(255,255,255,.12);
    padding: 8px 0;
    color: #a1a1aa;
    font-size: 16px;
}
.ulfra-data-row:last-child {
    border-bottom: 0;
}
.ulfra-data-row strong {
    color: #4ade80;
}
.ulfra-data-row.total strong {
    color: #ffffff;
    font-size: 18px;
}
@media (max-width: 1100px) {
    .ulfra-home-grid {
        grid-template-columns: 1fr;
    }
}
.ulfra-chat-wrap {
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.10), transparent 60%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 24px;
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
    padding: 18px;
}
.ulfra-chat-message {
    background: rgba(255,255,255,.86);
    border: 1px solid rgba(255,255,255,.95);
    border-radius: 18px;
    padding: 14px 16px;
    margin: 10px 0;
    color: #0f172a;
    line-height: 1.75;
}
.ulfra-chat-user {
    background: linear-gradient(135deg, #0d9488, #2563eb);
    color: #ffffff;
    margin-left: 12%;
}
/* 원본 HTML의 288px 사이드바와 24px 콘텐츠 간격을 기준으로 맞춥니다. */
[data-testid="stSidebar"] { min-width: 288px; width: 288px !important; max-width: 288px; }
[data-testid="stSidebarContent"] { padding: 16px 14px 24px !important; }
.block-container { max-width: none; padding: 24px 14px 32px 24px; }
[data-testid="stMain"]:has(.ulfra-header) .block-container { padding-top: 8px; }
[data-testid="stMain"]:has(.ulfra-home-card) .block-container { padding-top: 40px; }
.ulfra-side-head { margin-bottom: 28px; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 6px; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height: 44px;
    border-radius: 13px;
    padding: 0 14px;
}
[data-testid="stSidebar"] [role="radiogroup"] label p { font-size: 15px; font-weight: 700; }
[data-testid="stSidebar"] [role="radiogroup"] input { display: none; }
[data-testid="stSidebar"] [class*="st-key-pure_nav_"] button {
    min-height: 52px;
    justify-content: flex-start;
    padding: 0 20px;
    border: 0;
    border-radius: 13px;
    background: transparent;
    color: #64748b;
    font-size: 17px;
    font-weight: 700;
}
[data-testid="stSidebar"] [class*="st-key-pure_nav_"] { margin-bottom: -10px; }
[data-testid="stSidebar"] [class*="st-key-pure_nav_"] button > div {
    justify-content: flex-start !important;
    text-align: left;
}
[data-testid="stSidebar"] [class*="st-key-pure_nav_"] button p {
    font-size: 17px;
    font-weight: 700;
    color: inherit;
}
[data-testid="stSidebar"] [class*="st-key-pure_nav_"] button:hover {
    background: #f1f5f9;
    color: #0f172a;
}
.ulfra-sidebar-spacer { height: 56px; }
.ulfra-metrics-card { padding: 14px 15px; }
.ulfra-metrics-title { font-size: 12px; margin-bottom: 10px; }
.ulfra-metric-row { margin-top: 7px; }
.ulfra-metric-label { font-size: 12px; }
.ulfra-metric-value { font-size: 14px; }
.ulfra-side-footnote { font-size: 13px; line-height: 1.5; margin-top: 31px; }
.ulfra-header {
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.09), transparent 58%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    border: 1px solid rgba(255,255,255,.85);
    border-radius: 22px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
}
.ulfra-title { font-size: 28px; }
.ulfra-desc { font-size: 15px; margin-top: 6px; }
.ulfra-home-stage { padding: 0; }
.ulfra-home-head { margin: -16px 0 14px; }
.ulfra-home-title { font-size: 32px; }
.ulfra-home-desc { font-size: 13px; margin-top: 4px; }
.ulfra-home-status { padding: 7px 11px; font-size: 12px; margin-top: 7px; }
.ulfra-home-card { height: 270px; min-height: 270px; border-radius: 24px; }
.stHorizontalBlock:has(.st-key-pure_home_map) { margin-bottom: 4px; }
.stHorizontalBlock:has(.st-key-pure_home_map),
.stHorizontalBlock:has(.st-key-pure_home_chat) { gap: 20px !important; }
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"] { position: relative; }
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"] > [class*="st-key-pure_home_open_"] {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    z-index: 3;
}
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"] > [class*="st-key-pure_home_open_"] [data-testid="stButton"],
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"] > [class*="st-key-pure_home_open_"] button {
    width: 100%;
    height: 100%;
}
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"] > [class*="st-key-pure_home_open_"] button {
    opacity: 0;
    cursor: pointer;
}
[data-testid="stVerticalBlock"][class*="st-key-pure_home_"]:focus-within { outline: 3px solid #2563eb; border-radius: 24px; }
.ulfra-map-card { padding: 38px; }
.ulfra-compare-card, .ulfra-chat-card, .ulfra-data-card { padding: 34px; }
.ulfra-home-card-title { font-size: 30px; }
.ulfra-home-card-sub { font-size: 13px; }
.ulfra-map-title { font-size: 38px; }
.ulfra-map-sub, .ulfra-card-bottom { font-size: 13px; }
.ulfra-map-cta { font-size: 14px; padding: 10px 22px; }
.ulfra-map-title, .ulfra-map-sub, .ulfra-map-cta { transform: translateY(10px); }
.ulfra-bar-stage { min-height: 100px; margin: 14px 0 8px; gap: 40px; }
.ulfra-chat-terminal { min-height: 110px; margin: 0 0 8px; font-size: 15px; }
.ulfra-data-card { overflow-y: auto; }
.ulfra-data-card .ulfra-home-card-title { max-width: 210px; }
.ulfra-data-table { margin: 12px 0 12px; }
.ulfra-data-row { font-size: 13px; }
.ulfra-compare-panel {
    min-height: 500px;
    padding: 26px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,.9);
    background: linear-gradient(135deg, #f0fdf4, #e0f2fe 65%, #f8fafc);
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
    overflow: hidden;
}
.st-key-pure_compare_header {
    padding: 20px 24px 28px;
    border-radius: 22px;
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.09), transparent 58%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    border: 1px solid rgba(255,255,255,.85);
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
}
.st-key-pure_compare_header .ulfra-header { padding: 0; border: 0; margin: 0; box-shadow: none; background: transparent; }
.st-key-pure_compare_header [data-testid="stVerticalBlock"] { gap: 8px; }
.st-key-pure_compare_header [data-testid="stHorizontalBlock"] { max-width: 430px; gap: 20px !important; }
.st-key-pure_compare_header [data-testid="stSelectbox"] label { display: none; }
.st-key-pure_compare_header [data-testid="stSelectbox"] [data-baseweb="select"] { background: white; border-radius: 10px; }
.st-key-pure_map_header {
    padding: 20px 24px 24px;
    border-radius: 22px;
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.09), transparent 58%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    border: 1px solid rgba(255,255,255,.85);
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
}
.st-key-pure_map_header .ulfra-header { padding: 0; border: 0; margin: 0; box-shadow: none; background: transparent; }
.st-key-pure_map_header [data-testid="stVerticalBlock"] { gap: 8px; }
.st-key-pure_map_header [data-testid="stHorizontalBlock"] { gap: 12px !important; }
.st-key-pure_map_header [data-testid="stSelectbox"] label { display: none; }
.st-key-pure_map_header [data-testid="stSelectbox"] [data-baseweb="select"] { background: white; border-radius: 10px; }
.st-key-pure_map_header [data-testid="stPills"] label { display: none; }
.st-key-pure_map_header .st-key-pure_map_district { margin-left: auto; }
.st-key-pure_map_header [role="radiogroup"] { margin: 10px 0 0 auto; }
.st-key-pure_map_header [role="radiogroup"] button[data-selected="true"] {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}
.st-key-pure_map_left {
    padding: 12px;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    background: #ffffff;
    box-shadow: 0 8px 24px rgba(15,23,42,.05);
}
.st-key-pure_map_panel {
    position: relative;
    min-height: 500px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    border-radius: 22px;
    background: #ffffff;
    box-shadow: 0 8px 24px rgba(15,23,42,.05);
}
.ulfra-map-score-badge {
    position: absolute;
    top: 24px;
    right: 24px;
    color: #2563eb;
    background: #eff6ff;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 16px;
    font-weight: 900;
}
.st-key-pure_map_panel [data-testid="stElementContainer"]:has(.ulfra-map-score-badge) {
    position: static;
    height: 0;
}
.st-key-pure_map_left [data-testid="stForm"] { border: 0; padding: 0; }
.st-key-pure_map_left [data-testid="stForm"] [data-testid="stBaseButton-secondaryFormSubmit"] { margin-top: 0; }
.st-key-pure_map_left [data-testid="stVerticalBlock"] { gap: 8px; }
.st-key-pure_map_left [data-testid="stSelectbox"] label { display: none; }
.st-key-pure_map_panel [data-testid="stMetric"] { margin: 10px 0 14px; }
.st-key-pure_map_panel h3 { margin: 10px 0; font-size: 27px; }
.ulfra-compare-panel h2 { margin: 0; font-size: 22px; color: #0f172a; }
.ulfra-compare-panel > p { margin: 2px 0 12px; color: #64748b; font-size: 14px; }
.ulfra-compare-legend { display: flex; justify-content: flex-end; gap: 14px; font-size: 13px; color: #334155; }
.ulfra-compare-row { margin: 16px 0 22px; }
.ulfra-compare-row-head { display: flex; justify-content: space-between; gap: 12px; color: #334155; font-size: 14px; }
.ulfra-compare-row-head strong { white-space: nowrap; }
.ulfra-compare-track { height: 12px; margin: 5px 0; border-radius: 999px; background: #e2e8f0; overflow: hidden; }
.ulfra-compare-track span { display: block; height: 100%; border-radius: inherit; background: #3b82f6; }
.ulfra-compare-track.pink span { background: #fb7185; }
.ulfra-compare-row small { color: #64748b; font-size: 13px; }
.ulfra-compare-summary { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 18px 0; }
.ulfra-compare-summary > div { display: flex; flex-direction: column; gap: 2px; padding: 16px; border-radius: 18px; background: rgba(255,255,255,.8); }
.ulfra-compare-summary b { font-size: 17px; }
.ulfra-compare-summary strong { color: #2563eb; font-size: 24px; }
.ulfra-compare-summary strong.pink { color: #f43f5e; }
.ulfra-compare-summary span { color: #64748b; font-size: 14px; }
.ulfra-compare-explain { padding: 16px; border-radius: 16px; background: #0f172a; color: #e2e8f0; font-size: 13px; line-height: 1.55; }
.ulfra-compare-explain b { color: #34d399; font-size: 15px; }
.ulfra-compare-explain p { margin: 8px 0 0; }
.ulfra-compare-panel .ulfra-compare-limit { margin-top: 14px; line-height: 1.55; }
.st-key-pure_chat_header { position: relative; }
.st-key-pure_chat_header [class*="st-key-pure_chat_reset"] {
    position: absolute;
    top: 25px;
    right: 24px;
    width: 160px;
    z-index: 2;
}
.st-key-pure_chat_header [class*="st-key-pure_chat_reset"] button {
    width: 100%;
    border-radius: 11px;
    background: rgba(255,255,255,.8);
}
.st-key-pure_data_header { position: relative; }
.st-key-pure_data_header [class*="st-key-pure_data_refresh"] {
    position: absolute;
    top: 38px;
    right: 24px;
    width: 145px;
    z-index: 2;
}
.st-key-pure_data_header [class*="st-key-pure_data_refresh"] button { width: 100%; }
.st-key-pure_data_header .ulfra-status { margin-right: 150px; }
.st-key-pure_data_metrics .ulfra-card { height: 154px; overflow: hidden; }
.st-key-pure_data_metrics [data-testid="stColumn"]:nth-child(2) .ulfra-kpi-value {
    font-size: 26px;
    line-height: 1.15;
}
.st-key-pure_data_table_card {
    margin-top: 18px;
    padding: 16px 24px 24px;
    min-height: 375px;
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 22px;
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.06), transparent 58%),
        linear-gradient(135deg, #ffffff, #f0fdfa);
    box-shadow: 0 8px 24px rgba(15,78,86,.06);
}
.st-key-pure_data_table_card h4 { margin: 0; font-size: 22px; }
.st-key-pure_data_table_card [data-testid="stDownloadButton"] { margin-left: auto; }
.st-key-pure_data_table_card [data-testid="stDownloadButton"] button {
    border: 0;
    background: transparent;
    box-shadow: none;
    color: #64748b;
}
.st-key-pure_chat_console {
    min-height: 545px;
    padding: 24px;
    border: 1px solid rgba(255,255,255,.9);
    border-radius: 24px;
    background: radial-gradient(circle at 90% 10%, rgba(16,185,129,.10), transparent 60%),
        linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 52%, #f8fafc 100%);
    box-shadow: 0 8px 24px rgba(15,78,86,.08);
    display: flex;
    flex-direction: column;
}
.st-key-pure_chat_console p,
.st-key-pure_chat_console label { color: #334155; }
.st-key-pure_chat_console [data-testid="stChatMessage"] {
    max-width: 89%;
    background: rgba(255,255,255,.92);
    border: 1px solid rgba(255,255,255,.95);
    color: #0f172a;
    border-radius: 18px;
    margin: 10px 0;
    box-shadow: 0 8px 20px rgba(15,23,42,.05);
}
.st-key-pure_chat_console [data-testid^="stChatMessageAvatar"] { display: none; }
.st-key-pure_chat_console [data-testid="stChatMessageContent"] { font-size: 16px; line-height: 1.6; }
.st-key-pure_chat_console [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: #e0f2fe;
    border-color: #bae6fd;
    margin-left: auto;
}
.st-key-pure_chat_console [class*="st-key-pure_chat_"] button {
    border-radius: 999px;
    background: rgba(255,255,255,.82);
    color: #334155;
    font-size: 14px;
    min-height: 32px;
    height: 32px;
}
.st-key-pure_chat_console [data-testid="stChatInput"] { margin-top: 20px; }
.st-key-pure_chat_console > [data-testid="stElementContainer"]:has([data-testid="stChatInput"]) { margin-top: auto; }
.st-key-pure_chat_console [data-testid="stChatInput"] > div {
    background: transparent;
    border: 0;
    box-shadow: none;
    padding: 0;
}
.st-key-pure_chat_console [data-testid="stChatInput"] > div > div:first-child {
    width: calc(100% - 120px);
    min-height: 48px;
    margin-top: 10px;
    padding: 8px 15px;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
    background: #ffffff;
}
.st-key-pure_chat_console [data-testid="stChatInput"] div:has(> [data-testid="stChatInputSubmitButton"]) {
    position: absolute;
    right: 0;
    top: 10px;
    width: 107px;
    height: 48px;
}
.st-key-pure_chat_console [data-testid="stChatInputSubmitButton"] {
    width: 100%;
    height: 100%;
    border-radius: 16px;
    background: linear-gradient(110deg, #0d9488, #2563eb);
    color: #ffffff;
    opacity: 1;
}
.st-key-pure_chat_console [data-testid="stChatInputSubmitButton"] svg { display: none; }
.st-key-pure_chat_console [data-testid="stChatInputSubmitButton"]::after {
    content: "전송 ➔";
    font-size: 16px;
    font-weight: 800;
}
@media (max-width: 900px) {
    .ulfra-home-grid { grid-template-columns: 1fr; }
    .ulfra-home-card { min-height: 300px; }
}
</style>
"""


@st.cache_data(show_spinner=False)
def load_app_snapshot() -> dict[str, Any]:
    """전체 행정동 공급점수 스냅샷을 읽습니다."""
    return get_snapshot()


@st.cache_data(show_spinner=False)
def load_gu_options() -> list[str]:
    """기존 테스트와 화면 필터가 함께 쓰는 구·군 목록을 읽습니다."""
    return ["전체"] + get_gu_list()


@st.cache_data(show_spinner=False)
def load_intro_background_data_uri() -> str:
    """프로젝트에 포함된 태화강 배경 이미지를 인트로에 사용합니다."""
    image_path = PROJECT_ROOT / "assets" / "intro-background.jpg"
    try:
        image_data = image_path.read_bytes()
    except OSError:
        return ""
    return "data:image/jpeg;base64," + base64.b64encode(image_data).decode("ascii")


@st.cache_data(show_spinner=False)
def load_places_page(region_id: str, category: str, offset: int, limit: int) -> dict[str, Any]:
    """HTML 대시보드의 시설 페이지 데이터를 읽습니다."""
    return list_places(region_id, category=category, offset=offset, limit=limit)


@st.cache_data(show_spinner=False)
def load_place_search(
    query: str,
    district: str | None,
    region_id: str | None,
) -> dict[str, Any]:
    """HTML 대시보드의 상호명 검색과 같은 검색 결과를 읽습니다."""
    return search_places(query=query, district=district, region_id=region_id, limit=100)


def format_number(value: float) -> str:
    return f"{int(value):,}"


def format_score(value: float) -> str:
    return f"{float(value):.1f}"


def region_label(region: dict[str, Any]) -> str:
    return f"{region['gu_name']} {region['dong_name']}"


def category_label(snapshot: dict[str, Any], key: str) -> str:
    return snapshot.get("categories", {}).get(key, {}).get("label", CATEGORIES[key]["label"])


def make_region_options(regions: list[dict[str, Any]], district: str) -> dict[str, str]:
    filtered = [
        region
        for region in regions
        if district == "전체" or region["gu_name"] == district
    ]
    return {region_label(region): region["region_id"] for region in filtered}


def region_rank_frame(snapshot: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for region in sorted(snapshot["regions"], key=lambda item: item["rank"]):
        row = {
            "구·군": region["gu_name"],
            "행정동명": region["dong_name"],
            "총 인프라 수": int(region["total_places"]),
        }
        for key in CATEGORIES:
            row[category_label(snapshot, key)] = int(region["categories"][key]["count"])
        row["공급점수 / 순위"] = f"{format_score(region['score'])} / {region['rank']}위"
        rows.append(row)
    return pd.DataFrame(rows)


def export_region_csv(snapshot: dict[str, Any]) -> str:
    """HTML 화면의 CSV와 같은 집계·점수 항목을 내려받기용으로 만듭니다."""
    metadata = snapshot["metadata"]
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "행정동코드", "구군", "행정동", "인구", "전체시설", "공급점수", "순위",
        *[
            f"{rule['label']} {metric}"
            for rule in CATEGORIES.values()
            for metric in ("시설수", "천명당", "점수")
        ],
        "상가기준월", "인구기준월", "산식버전", "스냅샷ID",
    ])
    for region in snapshot["regions"]:
        values = [
            region["region_id"], region["gu_name"], region["dong_name"],
            region["total_pop"], region["total_places"], region["score"], region["rank"],
            *[
                region["categories"][key][metric]
                for key in CATEGORIES
                for metric in ("count", "per_1000", "score")
            ],
            metadata["commercial_reference"], metadata["population_reference"],
            metadata["score_version"], metadata["snapshot_id"],
        ]
        # 스프레드시트에서 원천 문자열이 수식으로 실행되지 않도록 보호합니다.
        writer.writerow([
            "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@")) else value
            for value in values
        ])
    return "\ufeff" + output.getvalue()


def render_header(title: str, badge: str, description: str, status: str) -> None:
    st.markdown(
        f"""
        <div class="ulfra-header">
            <div style="display:flex; justify-content:space-between; gap:16px; align-items:flex-start; flex-wrap:wrap;">
                <div>
                    <div class="ulfra-title"><span>{title}</span><span class="ulfra-badge">{badge}</span></div>
                    <div class="ulfra-desc">{description}</div>
                </div>
                <div class="ulfra-status">{status}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str, color: str = "#0f172a") -> None:
    st.markdown(
        f"""
        <div class="ulfra-card">
            <div class="ulfra-kpi-label">{label}</div>
            <div class="ulfra-kpi-value" style="color:{color};">{value}</div>
            <div class="ulfra-kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_requested_page_key() -> str | None:
    page_key = st.query_params.get("page")
    if isinstance(page_key, list):
        page_key = page_key[0] if page_key else ""
    page_key = str(page_key or "").strip().lower()
    return page_key if page_key in PAGE_KEYS else None


def render_streamlit_intro() -> None:
    background_uri = load_intro_background_data_uri()
    background_image = (
        f"linear-gradient(rgba(15,23,42,.22), rgba(15,23,42,.42)), url('{background_uri}')"
        if background_uri
        else "linear-gradient(135deg, #164e63 0%, #1e3a8a 44%, #0f172a 100%)"
    )
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {{
            display: none !important;
        }}
        .block-container {{
            padding: 0 !important;
            max-width: none !important;
        }}
        .ulfra-intro-screen {{
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            cursor: pointer;
            text-align: center;
            color: #ffffff;
            text-decoration: none;
            background-color: #1e293b;
            background-image: {background_image};
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        .ulfra-intro-screen,
        .ulfra-intro-screen:visited,
        .ulfra-intro-screen:hover,
        .ulfra-intro-screen *,
        .ulfra-intro-screen:hover * {{
            color: #ffffff !important;
            text-decoration: none !important;
        }}
        .ulfra-intro-screen::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(to top, rgba(2,6,23,.64), rgba(15,23,42,0) 52%, rgba(15,23,42,.25));
            pointer-events: none;
        }}
        .ulfra-intro-content {{
            position: relative;
            z-index: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 0 24px;
            text-shadow: 0 8px 20px rgba(0,0,0,.58);
        }}
        .ulfra-intro-kicker {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 22px;
            margin-bottom: 34px;
            border: 1px solid rgba(255,255,255,.42);
            border-radius: 999px;
            background: rgba(255,255,255,.24);
            backdrop-filter: blur(12px);
            box-shadow: 0 18px 48px rgba(15,23,42,.26);
            font-size: 18px;
            font-weight: 850;
        }}
        .ulfra-intro-title {{
            margin: 0;
            font-size: clamp(88px, 12vw, 152px) !important;
            line-height: .86 !important;
            font-weight: 950 !important;
            letter-spacing: 0 !important;
        }}
        .ulfra-intro-subtitle {{
            margin: 32px 0 42px;
            font-size: clamp(30px, 3.4vw, 44px) !important;
            line-height: 1.25 !important;
            font-weight: 720 !important;
        }}
        .ulfra-intro-cta {{
            display: inline-flex;
            align-items: center;
            gap: 14px;
            padding: 16px 38px;
            border: 1px solid rgba(255,255,255,.52);
            border-radius: 999px;
            background: rgba(255,255,255,.28);
            backdrop-filter: blur(16px);
            box-shadow: 0 18px 48px rgba(15,23,42,.28);
            font-size: 22px;
            font-weight: 900;
            animation: ulfraIntroPulse 1.8s ease-in-out infinite;
        }}
        .ulfra-intro-caption {{
            position: absolute;
            left: 0;
            right: 0;
            bottom: 34px;
            z-index: 1;
            color: rgba(255,255,255,.82);
            font-size: 17px;
            font-weight: 750;
            letter-spacing: .01em;
            text-shadow: 0 5px 16px rgba(0,0,0,.52);
        }}
        @keyframes ulfraIntroPulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.025); }}
        }}
        @media (max-width: 720px) {{
            .ulfra-intro-kicker {{ font-size: 14px; margin-bottom: 26px; }}
            .ulfra-intro-cta {{ font-size: 17px; padding: 14px 24px; }}
            .ulfra-intro-caption {{ font-size: 13px; bottom: 22px; padding: 0 20px; }}
        }}
        </style>
        <a class="ulfra-intro-screen" href="/?page=home" target="_self" title="화면 아무 곳이나 클릭하여 홈 대시보드로 이동">
            <div class="ulfra-intro-content">
                <div class="ulfra-intro-kicker"><span>🌊</span><span>태화강을 품은 스마트 생활인프라 대시보드</span></div>
                <h1 class="ulfra-intro-title">ULFRA</h1>
                <div class="ulfra-intro-subtitle">울산의 생활을 다시 그리다</div>
                <div class="ulfra-intro-cta"><span>👉</span><span>화면 아무 곳이나 클릭하여 시작하기</span><span>➔</span></div>
            </div>
            <div class="ulfra-intro-caption">울산 태화강 &amp; 시티 전경 · Click anywhere to enter Home Dashboard</div>
        </a>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(snapshot: dict[str, Any], current_page_key: str) -> str:
    metadata = snapshot["metadata"]
    quality = snapshot["quality"]
    page_by_key = {page_key: page for _, page_key, page in PAGE_OPTIONS}
    with st.sidebar:
        st.markdown(
            """
            <div class="ulfra-side-head">
                <div class="ulfra-brand-wrap">
                    <div class="ulfra-logo-mark">U</div>
                    <div class="ulfra-brand">
                        <div class="ulfra-brand-title">ULFRA</div>
                        <div class="ulfra-brand-subtitle">울산 생활인프라 2.0</div>
                    </div>
                </div>
                <a class="ulfra-door-link" href="/" target="_self">🚪 대문</a>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.html(
            f'<style>.st-key-pure_nav_{current_page_key} button{{'
            'background:#eff6ff!important;color:#2563eb!important;font-weight:800!important;'
            '}</style>'
        )
        for label, page_key, _ in PAGE_OPTIONS:
            if st.button(label, key=f"pure_nav_{page_key}", width="stretch"):
                st.query_params["page"] = page_key
                st.rerun()
        st.markdown('<div class="ulfra-sidebar-spacer"></div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="ulfra-metrics-card">
                <div class="ulfra-metrics-title">ULSAN METRICS</div>
                <div class="ulfra-metric-row">
                    <div class="ulfra-metric-label">조사 대상 행정동</div>
                    <div class="ulfra-metric-value">{metadata['region_count']}개 읍면동<br>({metadata['district_count']}개 구·군)</div>
                </div>
                <div class="ulfra-metric-row">
                    <div class="ulfra-metric-label">인프라 총 데이터</div>
                    <div class="ulfra-metric-value blue">{format_number(quality['total_places'])}건</div>
                </div>
                <div class="ulfra-metric-row">
                    <div class="ulfra-metric-label">공공데이터 기준</div>
                    <div class="ulfra-metric-value green">상가 {metadata['commercial_reference']} /<br>인구 {metadata['population_reference']}</div>
                </div>
            </div>
            <div class="ulfra-side-footnote">
                시설 공급의 상대 비교입니다. 상권정보에 수록되지 않은 공공시설 등은 평가에 포함되지 않습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
    return page_by_key[current_page_key]


def render_home(snapshot: dict[str, Any]) -> None:
    metadata = snapshot["metadata"]
    quality = snapshot["quality"]
    regions = snapshot["regions"]
    top_regions = sorted(regions, key=lambda item: item["rank"])[:3]
    bar_colors = ["#3b82f6", "#f87171", "#4ade80"]
    bar_heights = [84, 66, 52]
    bars_html = "\n".join(
        f"""
        <div class="ulfra-mini-bar-wrap">
            <div class="ulfra-mini-label" style="color:{bar_colors[index]};">{escape(region['dong_name'])}</div>
            <div class="ulfra-mini-bar" style="height:{bar_heights[index]}px; background:{bar_colors[index]};"></div>
        </div>
        """
        for index, region in enumerate(top_regions)
    )
    query_ms = float(metadata.get("query_ms", 0))

    st.html(
        f"""
        <div class="ulfra-home-head">
            <div>
                <div class="ulfra-home-title-line">
                    <div class="ulfra-home-title">생활인프라 대시보드</div>
                    <span class="ulfra-badge">실제 자료 연동</span>
                </div>
                <div class="ulfra-home-desc">원하는 위젯을 클릭하여 상세 분석 화면으로 바로 진입하세요.</div>
            </div>
            <div class="ulfra-home-status">자료 연결 · {metadata['score_version']}</div>
        </div>
        """,
    )
    cards = [
        (
            "map",
            (
                '<div class="ulfra-home-card ulfra-map-card"><div class="ulfra-card-arrow">↗</div>'
                '<div class="ulfra-map-kicker">GIS SPATIAL</div>'
                '<div class="ulfra-map-title">🗺️ 지도 탐색</div>'
                '<div class="ulfra-map-sub">읍면동 공급점수와 실제 시설 위치를 함께 확인하세요.</div>'
                '<div class="ulfra-map-cta">시설 지도 열기 ➜</div></div>'
            ),
        ),
        (
            "compare",
            (
                '<div class="ulfra-home-card ulfra-compare-card"><div class="ulfra-card-arrow">↗</div>'
                '<div class="ulfra-home-card-title"><span>📊</span><span>동네 비교</span></div>'
                '<div class="ulfra-home-card-sub">울산 동네 미리보기</div>'
                f'<div class="ulfra-bar-stage">{bars_html}</div>'
                '<div class="ulfra-card-bottom"><span>같은 기준으로 두 읍면동 비교하기</span>'
                '<strong>비교 분석기 열기 ➜</strong></div></div>'
            ),
        ),
        (
            "chat",
            (
                '<div class="ulfra-home-card ulfra-chat-card"><div class="ulfra-card-arrow">↗</div>'
                '<div class="ulfra-home-card-title"><span>🤖</span><span>데이터 챗봇</span></div>'
                '<div class="ulfra-home-card-sub">프로젝트 자료에 근거한 동네 비교와 후보 탐색</div>'
                f'<div class="ulfra-chat-terminal">울산 {metadata["region_count"]}개 동네 분석 중...</div>'
                '<div class="ulfra-card-bottom"><span>“삼산동과 옥동의 카페·병의원 공급점수를 비교해줘”</span>'
                '<strong style="color:#fff;">대화창 열기 ➜</strong></div></div>'
            ),
        ),
        (
            "data",
            (
                '<div class="ulfra-home-card ulfra-data-card"><div class="ulfra-card-arrow">↗</div>'
                '<div class="ulfra-online-pill">● Status: Online</div>'
                '<div class="ulfra-home-card-title"><span>🛠️</span><span>데이터 관제탑</span></div>'
                '<div class="ulfra-data-table">'
                f'<div class="ulfra-data-row"><span>[DB] 프로젝트 SQLite</span><strong>조회 {query_ms:.2f} ms</strong></div>'
                f'<div class="ulfra-data-row"><span>[SOURCE] 상가 / 인구 기준월</span><strong>{metadata["commercial_reference"]} / {metadata["population_reference"]}</strong></div>'
                f'<div class="ulfra-data-row"><span>[MAP] 시설 좌표</span><strong>{format_number(quality["valid_coordinates"])}개 범위 확인</strong></div>'
                f'<div class="ulfra-data-row total"><span>시설 레코드</span><strong>{format_number(quality["total_places"])}</strong></div>'
                '</div><div class="ulfra-card-bottom"><span>업종·지역 연결과 좌표 범위 점검 결과 확인</span>'
                '<strong style="color:#fff;">전체 DB 점검 ➜</strong></div></div>'
            ),
        ),
    ]
    for row in (cards[:2], cards[2:]):
        columns = st.columns(2, gap="medium")
        for column, (page_key, markup) in zip(columns, row):
            with column, st.container(key=f"pure_home_{page_key}"):
                st.html(markup)
                if st.button(f"{page_key} 화면 열기", key=f"pure_home_open_{page_key}"):
                    st.query_params["page"] = page_key
                    st.rerun()


def build_offline_map(
    regions: list[dict[str, Any]],
    selected_region_id: str,
    category_pages: list[tuple[str, dict[str, Any]]],
    search_result: dict[str, Any] | None,
    center: list[float],
    focused: bool,
) -> go.Figure:
    """외부 지도 타일 없이 DB 좌표를 확대·선택 가능한 도표로 표시합니다."""
    figure = go.Figure()
    visible_regions = [
        region for region in regions
        if region.get("latitude") is not None and region.get("longitude") is not None
    ]
    figure.add_trace(go.Scatter(
        x=[region["longitude"] for region in visible_regions],
        y=[region["latitude"] for region in visible_regions],
        mode="markers",
        name="행정동",
        marker={
            "size": [15 if region["region_id"] == selected_region_id else 9 for region in visible_regions],
            "color": ["#7c3aed" if region["region_id"] == selected_region_id else "#475569" for region in visible_regions],
            "line": {"color": "#ffffff", "width": 1},
        },
        text=[f"{escape(region_label(region))} · {format_score(region['score'])}점" for region in visible_regions],
        customdata=[["region", region["region_id"]] for region in visible_regions],
        hovertemplate="%{text}<extra></extra>",
    ))
    for key, page in category_pages:
        places = [place for place in page["items"] if place.get("coordinate_valid")]
        figure.add_trace(go.Scatter(
            x=[place["longitude"] for place in places],
            y=[place["latitude"] for place in places],
            mode="markers",
            name=CATEGORIES[key]["label"],
            marker={"size": 6, "color": CATEGORY_COLORS[key], "opacity": 0.8},
            text=[escape(place["name"]) for place in places],
            hovertemplate="%{text}<extra></extra>",
        ))
    if search_result:
        places = search_result["items"]
        figure.add_trace(go.Scatter(
            x=[place["longitude"] for place in places],
            y=[place["latitude"] for place in places],
            mode="markers",
            name="검색 결과",
            marker={"size": 12, "color": "#f59e0b", "symbol": "star"},
            text=[escape(place["name"]) for place in places],
            hovertemplate="%{text}<extra></extra>",
        ))
    coordinates = [(region["longitude"], region["latitude"]) for region in visible_regions]
    if focused or not coordinates:
        longitude_range = [center[1] - 0.035, center[1] + 0.035]
        latitude_range = [center[0] - 0.025, center[0] + 0.025]
    else:
        longitude_range = [min(x for x, _ in coordinates) - 0.025, max(x for x, _ in coordinates) + 0.025]
        latitude_range = [min(y for _, y in coordinates) - 0.025, max(y for _, y in coordinates) + 0.025]
    figure.update_layout(
        height=280, margin={"l": 8, "r": 8, "t": 8, "b": 8},
        paper_bgcolor="#eff6ff", plot_bgcolor="#eff6ff",
        legend={"orientation": "h", "y": 1.02, "x": 0},
        dragmode="pan", clickmode="event+select",
        xaxis={"range": longitude_range, "title": "경도", "showgrid": True, "gridcolor": "#dbeafe"},
        yaxis={"range": latitude_range, "title": "위도", "showgrid": True, "gridcolor": "#dbeafe"},
    )
    return figure


def render_map_facility_list(
    regions: list[dict[str, Any]],
    selected_region_id: str,
    list_category: str,
    search_result: dict[str, Any] | None,
    search_query: str,
) -> None:
    if search_result:
        table_rows = search_result["items"]
        st.caption(f"검색 {format_number(search_result['total'])}개 중 {len(table_rows)}개 표시 · 검색 결과의 별표가 지도에 표시됩니다.")
        next_offset = None
    else:
        offset = st.session_state["pure_map_offset"]
        page = load_places_page(selected_region_id, list_category, offset, 200)
        table_rows = page["items"]
        next_offset = page["next_offset"]
        first_row = offset + 1 if table_rows else 0
        st.caption(f"전체 {format_number(page['total'])}개 중 {first_row:,}–{offset + len(table_rows):,}개 표시 · 이름순")

    if table_rows:
        table = pd.DataFrame([
            {
                "상호명": place["name"],
                "지점명": place.get("branch_name") or "",
                "업종": place.get("sub_name") or "",
                **({"지역": f"{place['gu_name']} {place['dong_name']}"} if search_result else {}),
                "주소": place.get("address") or "",
            }
            for place in table_rows
        ])
        selection = st.dataframe(
            table, hide_index=True, height=260, width="stretch",
            on_select="rerun", selection_mode="single-row",
            key=f"pure_map_table_{selected_region_id}_{list_category}_{st.session_state['pure_map_offset']}_{search_query}",
        )
        if selection.selection.rows:
            place = table_rows[selection.selection.rows[0]]
            place_region_id = next(
                (
                    region["region_id"] for region in regions
                    if region["gu_name"] == place.get("gu_name")
                    and region["dong_name"] == place.get("dong_name")
                ),
                selected_region_id,
            )
            if (
                place.get("latitude") is not None
                and place.get("longitude") is not None
                and (
                    st.session_state.get("pure_map_focused_place_id") != place["place_id"]
                    or selected_region_id != place_region_id
                )
            ):
                st.session_state["pure_map_selected_region_id"] = place_region_id
                st.session_state["pure_map_focused_place_id"] = place["place_id"]
                st.session_state["pure_map_focus"] = {
                    "place_id": place["place_id"],
                    "region_id": place_region_id,
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                }
                st.rerun()
    else:
        st.warning("조건에 맞는 시설이 없습니다.")

    if not search_result:
        previous, following = st.columns(2)
        if previous.button("← 이전 200개", disabled=st.session_state["pure_map_offset"] == 0):
            st.session_state["pure_map_offset"] = max(0, st.session_state["pure_map_offset"] - 200)
            st.rerun()
        if following.button("다음 200개 →", disabled=next_offset is None):
            st.session_state["pure_map_offset"] = next_offset
            st.rerun()


def render_map(snapshot: dict[str, Any]) -> None:
    metadata = snapshot["metadata"]
    regions = snapshot["regions"]
    available_districts = {region["gu_name"] for region in regions}
    districts = ["전체", *(name for name in ("남구", "중구", "동구", "북구", "울주군") if name in available_districts)]

    with st.container(key="pure_map_header"):
        render_header(
            "🗺️ 지도탐색",
            "공간 분석 뷰",
            "구·군, 동네, 업종을 선택하면 실제 시설 위치와 공급점수가 함께 바뀝니다.",
            "",
        )
        control_a, control_b = st.columns([8, 1], gap="small")
        with control_a:
            district = st.pills(
                "구·군", districts, selection_mode="single", default="전체", required=True,
                format_func=lambda value: "전체 (울산)" if value == "전체" else value,
                key="pure_map_district", width="content", wrap=False,
                label_visibility="collapsed",
            )
        region_options = make_region_options(regions, district)
        current_id = st.session_state.get("pure_map_selected_region_id")
        first_region = min(
            (region for region in regions if district == "전체" or region["gu_name"] == district),
            key=lambda region: region["rank"],
        )
        default_label = next(
            (label for label, region_id in region_options.items() if region_id == current_id),
            region_label(first_region),
        )
        with control_b:
            selected_label = st.selectbox(
                "행정동", list(region_options), index=list(region_options).index(default_label),
                key=f"pure_map_region_{district}_{current_id}",
            )
    selected_region_id = region_options[selected_label]
    if st.session_state.get("pure_map_selected_region_id") != selected_region_id:
        st.session_state["pure_map_selected_region_id"] = selected_region_id
        st.session_state["pure_map_focus"] = None
        st.session_state["pure_map_focused_place_id"] = None
    selected_region = find_region(snapshot, selected_region_id)
    map_col, panel_col = st.columns([1.5, 1], gap="small")
    with map_col:
        left_panel = st.container(key="pure_map_left")
    with left_panel:
        selected_categories = st.pills(
            "시설 레이어",
            list(CATEGORIES),
            selection_mode="multi",
            default=[],
            format_func=lambda key: category_label(snapshot, key),
            help="선택한 업종의 시설 점을 업종별 최대 200개씩 표시합니다.",
            width="stretch",
            wrap=False,
        ) or []
        with st.form("pure_map_search_form"):
            search_col, submit_col, clear_col = st.columns([3, 1, 1])
            with search_col:
                search_text = st.text_input(
                    "상호명 일부 검색", placeholder="상호명 일부 검색", max_chars=100,
                    label_visibility="collapsed",
                )
            with submit_col:
                searched = st.form_submit_button("검색")
            with clear_col:
                cleared = st.form_submit_button("지우기")
    if searched or cleared:
        new_query = "" if cleared else search_text.strip()
        if new_query != st.session_state.get("pure_map_search_query", ""):
            st.session_state["pure_map_focus"] = None
            st.session_state["pure_map_focused_place_id"] = None
        st.session_state["pure_map_search_query"] = new_query
    search_query = st.session_state.get("pure_map_search_query", "")
    list_category = st.session_state.get("pure_map_list_category", "all")
    page_scope = (selected_region_id, list_category, search_query)
    if st.session_state.get("pure_map_page_scope") != page_scope:
        st.session_state["pure_map_page_scope"] = page_scope
        st.session_state["pure_map_offset"] = 0

    search_result = (
        load_place_search(
            search_query,
            None if district == "전체" else district,
            None if district == "전체" else selected_region_id,
        )
        if search_query else None
    )

    category_pages = [
        (key, load_places_page(selected_region_id, key, 0, 200))
        for key in selected_categories
    ]
    all_visible_places = [
        place
        for _, page in category_pages
        for place in page["items"]
        if place.get("coordinate_valid")
    ]
    focus = st.session_state.get("pure_map_focus")
    center = (
        [focus["latitude"], focus["longitude"]]
        if focus and focus["region_id"] == selected_region_id
        else [selected_region["latitude"], selected_region["longitude"]]
        if selected_region.get("latitude") is not None
        else ULSAN_CENTER
    )
    visible_regions = [
        region for region in regions
        if district == "전체" or region["gu_name"] == district
    ]
    offline_map = build_offline_map(
        visible_regions, selected_region_id, category_pages, search_result, center, bool(focus),
    )
    with left_panel:
        map_state = st.plotly_chart(
            offline_map, width="stretch", on_select="rerun", selection_mode="points",
            config={"scrollZoom": True, "displaylogo": False},
            key=f"pure_map_{district}_{selected_region_id}_{'_'.join(selected_categories)}_{search_query}_{focus['place_id'] if focus else ''}",
        )
        points = map_state["selection"]["points"] if map_state else []
        if points:
            selected_point = points[0].get("customdata", [])
            if len(selected_point) == 2 and selected_point[0] == "region":
                clicked_region_id = selected_point[1]
                if clicked_region_id != selected_region_id:
                    st.session_state["pure_map_selected_region_id"] = clicked_region_id
                    st.session_state["pure_map_focus"] = None
                    st.rerun()
        st.caption("로컬 좌표 지도 · 지명·도로 배경 없이 위치와 거리 관계를 표시합니다.")
        st.caption(
            f"{selected_label} · 선택 레이어 시설 점 {format_number(len(all_visible_places))}개 · 업종별 최대 200개"
        )
        facility_list_container = st.expander("시설 목록 펼치기", expanded=bool(search_result))

    with panel_col, st.container(key="pure_map_panel"):
        st.caption("SELECTED SPOT")
        st.html(
            f'<div class="ulfra-map-score-badge">{format_score(selected_region["score"])}점 · '
            f'{selected_region["rank"]}위</div>'
        )
        st.markdown(f"### {selected_label}")
        st.caption("생활인프라 공급점수 · 울산 55개 읍면동 상대 비교")
        for key in CATEGORIES:
            metric = selected_region["categories"][key]
            st.progress(min(float(metric["score"]) / 100, 1.0), text=f"{category_label(snapshot, key)} {format_score(metric['score'])}점")
            st.caption(f"{format_number(metric['count'])}개 · 인구 천 명당 {metric['per_1000']:.2f}개")
        st.caption(
            f"인구 {format_number(selected_region['total_pop'])}명 · "
            f"전체 시설 {format_number(selected_region['total_places'])}개 · "
            f"상가 {metadata['commercial_reference']} / 인구 {metadata['population_reference']}"
        )
        if st.button("이 동네 비교하기 →", key="pure_map_to_compare", width="stretch"):
            st.session_state["pure_compare_a_id"] = selected_region_id
            st.query_params["page"] = "compare"
            st.rerun()
        st.info(metadata["map_note"])

    with facility_list_container:
        st.selectbox(
            "시설 목록 업종", ["all", *list(CATEGORIES)],
            format_func=lambda key: "전체 업종" if key == "all" else category_label(snapshot, key),
            key="pure_map_list_category",
        )
        render_map_facility_list(
            regions, selected_region_id, list_category, search_result, search_query,
        )
    st.caption(metadata["limitation"])


def render_compare(snapshot: dict[str, Any]) -> None:
    metadata = snapshot["metadata"]
    regions = snapshot["regions"]
    region_options = {region_label(region): region["region_id"] for region in regions}
    labels = list(region_options)

    with st.container(key="pure_compare_header"):
        render_header(
            "📊 동네비교",
            "1:1 다이내믹 비교",
            "두 동네를 나란히 두고 핵심 생활인프라 밸런스를 즉시 비교 분석합니다.",
            "",
        )
        col_a, col_b = st.columns(2)
        with col_a:
            selected_a = st.session_state.get("pure_compare_a_id")
            default_a = next(
                (i for i, label in enumerate(labels) if region_options[label] == selected_a),
                next((i for i, label in enumerate(labels) if "삼산동" in label), 0),
            )
            label_a = st.selectbox("A 기준 지역", labels, index=default_a)
        with col_b:
            default_b = next((i for i, label in enumerate(labels) if "옥동" in label), min(1, len(labels) - 1))
            label_b = st.selectbox("B 비교 지역", labels, index=default_b)

    region_a = find_region(snapshot, region_options[label_a])
    region_b = find_region(snapshot, region_options[label_b])
    st.session_state["pure_compare_a_id"] = region_a["region_id"]

    names = {
        "medical": "의료 및 병의원",
        "food": "외식 및 식음 인프라",
        "cafe": "카페",
        "shop": "쇼핑·생활소매",
    }
    comparison_rows = []
    for key in CATEGORIES:
        a = region_a["categories"][key]
        b = region_b["categories"][key]
        comparison_rows.append(
            f'<div class="ulfra-compare-row">'
            f'<div class="ulfra-compare-row-head"><b>{escape(names.get(key, category_label(snapshot, key)))}</b>'
            f'<strong>{format_score(a["score"])}점 vs {format_score(b["score"])}점</strong></div>'
            f'<div class="ulfra-compare-track"><span style="width:{min(100, a["score"])}%"></span></div>'
            f'<div class="ulfra-compare-track pink"><span style="width:{min(100, b["score"])}%"></span></div>'
            f'<small>{escape(category_label(snapshot, key))} · A {format_number(a["count"])}개 / 천 명당 {a["per_1000"]:.2f}개'
            f' · B {format_number(b["count"])}개 / 천 명당 {b["per_1000"]:.2f}개</small>'
            '</div>'
        )
    strongest_a = max(CATEGORIES, key=lambda key: region_a["categories"][key]["score"])
    weakest_a = min(CATEGORIES, key=lambda key: region_a["categories"][key]["score"])
    strongest_b = max(CATEGORIES, key=lambda key: region_b["categories"][key]["score"])
    weakest_b = min(CATEGORIES, key=lambda key: region_b["categories"][key]["score"])

    chart_col, comment_col = st.columns(2, gap="small")
    with chart_col:
        st.html(
            '<div class="ulfra-compare-panel">'
            '<h2>카테고리별 인프라 점수 비교</h2>'
            '<p>시설 수 50% + 인구 천 명당 시설 수 50% · 울산 전체 평균순위 환산</p>'
            f'<div class="ulfra-compare-legend"><span>🔵 {escape(label_a)}</span><span>🔴 {escape(label_b)}</span></div>'
            + ''.join(comparison_rows)
            + '</div>'
        )
    with comment_col:
        st.html(
            '<div class="ulfra-compare-panel">'
            '<h2>생활인프라 공급점수</h2>'
            '<div class="ulfra-compare-summary">'
            f'<div><b>{escape(label_a)}</b><strong>{format_score(region_a["score"])}점</strong>'
            f'<span>울산 {region_a["rank"]}위 / 55개</span><span>인구 {format_number(region_a["total_pop"])}명</span>'
            f'<span>전체 시설 {format_number(region_a["total_places"])}개</span></div>'
            f'<div><b>{escape(label_b)}</b><strong class="pink">{format_score(region_b["score"])}점</strong>'
            f'<span>울산 {region_b["rank"]}위 / 55개</span><span>인구 {format_number(region_b["total_pop"])}명</span>'
            f'<span>전체 시설 {format_number(region_b["total_places"])}개</span></div>'
            '</div>'
            '<div class="ulfra-compare-explain"><b>계산 근거와 해석</b>'
            f'<p>A · {escape(label_a)}: 공급점수 최고는 {escape(category_label(snapshot, strongest_a))} '
            f'{format_score(region_a["categories"][strongest_a]["score"])}점, 최저는 '
            f'{escape(category_label(snapshot, weakest_a))} {format_score(region_a["categories"][weakest_a]["score"])}점입니다. '
            f'학원 {format_number(region_a["academy_places"])}개, 의원 {format_number(region_a["clinic_places"])}개.</p>'
            f'<p>B · {escape(label_b)}: 공급점수 최고는 {escape(category_label(snapshot, strongest_b))} '
            f'{format_score(region_b["categories"][strongest_b]["score"])}점, 최저는 '
            f'{escape(category_label(snapshot, weakest_b))} {format_score(region_b["categories"][weakest_b]["score"])}점입니다. '
            f'학원 {format_number(region_b["academy_places"])}개, 의원 {format_number(region_b["clinic_places"])}개.</p>'
            '</div>'
            f'<p class="ulfra-compare-limit">{escape(metadata["limitation"])}</p>'
            '</div>'
        )
        if st.button("데이터 챗봇에 두 동네 차이 묻기 →", key="pure_compare_to_chat", width="stretch"):
            st.session_state["pure_chat_region_ids"] = [region_a["region_id"], region_b["region_id"]]
            st.query_params["page"] = "chat"
            st.rerun()


def render_chat(snapshot: dict[str, Any]) -> None:
    regions = snapshot["regions"]
    region_options = {region_label(region): region["region_id"] for region in regions}

    with st.container(key="pure_chat_header"):
        render_header(
            "🤖 데이터 챗봇",
            "DB 근거 응답",
            "선택한 동네와 질문에 명시한 행정동의 실제 자료로 답합니다. 학군·보행·시설 품질은 평가하지 않습니다.",
            "",
        )
        if st.button("↻ 새로운 챗", key="pure_chat_reset"):
            st.session_state.pure_chat_history = st.session_state.pure_chat_history[:1]
            st.rerun()

    if "pure_chat_history" not in st.session_state:
        st.session_state.pure_chat_history = [
            {
                "role": "assistant",
                "content": "울산 55개 읍면동, 54,737개 시설을 조회했습니다. 생활인프라 공급점수, 두 동네 비교, 업종별 후보, 시설 주소를 질문하세요. DB 근거로 응답합니다.",
            }
        ]

    region_ids = [
        region_id for region_id in st.session_state.get("pure_chat_region_ids", [])
        if region_id in region_options.values()
    ] or [next(
        (region_id for label, region_id in region_options.items() if "삼산동" in label),
        next(iter(region_options.values())),
    )]

    with st.container(key="pure_chat_console"):
        quick_prompts = [
            ("☕ 20대 카페/외식 핫플", "20대 청년층이 살기 좋은 동네로 카페와 음식점, 편의점이 밀집한 곳 추천해줘"),
            ("👶 30대 영유아 가정 추천", "30대 영유아 자녀가 있는 가정인데, 소아과 병의원과 마트·편의점이 많은 동네 추천해줘"),
            ("📚 40대 학군/학원가 추천", "40대 학령기 자녀를 위한 학원 입시 교육 시설이 많은 동네 추천해줘"),
            ("🏥 60대 의료/생활 중심지", "60대 은퇴 후 거주하기 좋게 병의원과 약국, 편의시설이 잘 갖춰진 동네 추천해줘"),
        ]
        queued_prompt = None
        quick_cols = st.columns([0.6, 1.6, 1.75, 1.85, 1.7], gap="small")
        with quick_cols[0]:
            st.caption("추천 질문:")
        for column, (label, question) in zip(quick_cols[1:], quick_prompts[:3]):
            with column:
                if st.button(label, key=f"pure_chat_{label}", width="stretch"):
                    queued_prompt = question
        second_prompt_col, _ = st.columns([1.2, 4])
        with second_prompt_col:
            label, question = quick_prompts[3]
            if st.button(label, key=f"pure_chat_{label}", width="stretch"):
                queued_prompt = question

        for message in st.session_state.pure_chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("note"):
                    st.caption(message["note"])
                if message.get("evidence"):
                    with st.expander("DB 계산 근거 확인"):
                        st.markdown(message["evidence"])

        chat_input = st.chat_input("예: '삼산동과 달동의 생활인프라 차이점은?' 질문을 입력하세요...")
    user_prompt = chat_input or queued_prompt
    if user_prompt:
        history = [
            {
                "role": message["role"],
                "content": message["content"],
                "region_ids": region_ids,
                "service_groups": [],
            }
            for message in st.session_state.pure_chat_history[-12:]
        ]
        st.session_state.pure_chat_history.append({"role": "user", "content": user_prompt})
        with st.spinner("DB 인프라 통계를 분석 중입니다..."):
            result = answer_question(
                snapshot=snapshot,
                question=user_prompt,
                region_ids=region_ids or list(region_options.values())[:1],
                chat_history=history,
            )
        reply = result.get("answer", "데이터를 조회할 수 없습니다.")
        st.session_state.pure_chat_history.append(
            {
                "role": "assistant",
                "content": reply,
                "note": result.get("note"),
                "evidence": result.get("evidence"),
            }
        )
        st.session_state.pure_chat_history = st.session_state.pure_chat_history[-30:]
        st.rerun()


def render_data(snapshot: dict[str, Any]) -> None:
    metadata = snapshot["metadata"]
    quality = snapshot["quality"]
    coverage = quality["valid_coordinates"] / quality["total_places"] * 100

    with st.container(key="pure_data_header"):
        render_header(
            "🛠️ 데이터 관제탑",
            "System Online",
            f"{metadata['region_count']}개 읍면동 · {format_number(quality['total_places'])}개 시설의 조회 결과입니다.",
            "SQLite 읽기 전용",
        )
        if st.button("자료 다시 불러오기", key="pure_data_refresh"):
            load_app_snapshot.clear()
            load_places_page.clear()
            load_place_search.clear()
            st.rerun()

    with st.container(key="pure_data_metrics"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("전체 시설 레코드", format_number(quality["total_places"]), f"상가정보 {metadata['commercial_reference']}", "#0f172a")
        with col2:
            metric_card("관측 읍면동", f"{metadata['region_count']}개 / {metadata['district_count']}개 구·군", f"인구 {format_number(metadata['total_population'])}명", "#0f172a")
        with col3:
            metric_card("DB 조회·집계 시간", f"{metadata['query_ms']} ms", "현재 스냅샷 최초 집계 시간", "#059669")
        with col4:
            metric_card("좌표 범위 통과율", f"{coverage:.2f}%", "위치 정확도·영업 여부는 미검증", "#2563eb")

    with st.container(key="pure_data_table_card"):
        title_col, hint_col = st.columns([3, 2])
        with title_col:
            st.markdown("#### 행정동별 인프라 집계 현황 데이터셋")
        with hint_col:
            st.caption("프로젝트 SQLite 조회 스냅샷 · 행을 선택하면 지도로 이동")
        frame = region_rank_frame(snapshot)
        table_state = st.dataframe(
            frame, hide_index=True, height=184, width="stretch",
            on_select="rerun", selection_mode="single-row", key="pure_data_table",
        )
        if table_state.selection.rows:
            row_index = table_state.selection.rows[0]
            selected_region = sorted(snapshot["regions"], key=lambda item: item["rank"])[row_index]
            if st.session_state.get("pure_data_last_region") != selected_region["region_id"]:
                st.session_state["pure_data_last_region"] = selected_region["region_id"]
                st.session_state["pure_map_selected_region_id"] = selected_region["region_id"]
                st.session_state["pure_map_district"] = selected_region["gu_name"]
                st.query_params["page"] = "map"
                st.rerun()
        stamp_col, export_col = st.columns([3, 2])
        with stamp_col:
            st.caption(f"{metadata['score_version']} · {metadata['loaded_at']} 조회")
        with export_col:
            st.download_button(
                "전체 집계·점수 CSV 다운로드 →",
                data=export_region_csv(snapshot),
                file_name="ulfra-supply-v0.1.csv",
                mime="text/csv; charset=utf-8",
                key="pure_data_export",
            )
        st.caption(
            f"지역 연결 누락 {quality['unmapped_regions']}개 · "
            f"업종 연결 누락 {quality['unmapped_categories']}개. {metadata['quality_note']}"
        )


def render_pure_streamlit_app() -> None:
    """순수 Streamlit 대시보드 메인 렌더러"""
    st.markdown(PURE_DASHBOARD_CSS, unsafe_allow_html=True)
    current_page_key = get_requested_page_key()
    if current_page_key is None:
        render_streamlit_intro()
        return

    if st.session_state.get("pure_last_page_key") != current_page_key:
        st.session_state["pure_last_page_key"] = current_page_key
        st.html(
            f"<script>/* {current_page_key} */ (() => {{const resetPageScroll = () => "
            "document.querySelector('[data-testid=\"stMain\"]')?.scrollTo(0, 0);"
            "requestAnimationFrame(resetPageScroll);"
            "setTimeout(resetPageScroll, 250);"
            "setTimeout(resetPageScroll, 900);})();</script>",
            unsafe_allow_javascript=True,
        )

    snapshot = load_app_snapshot()
    page = render_sidebar(snapshot, current_page_key)

    if page == "홈":
        render_home(snapshot)
    elif page == "지도":
        render_map(snapshot)
    elif page == "지역 비교":
        render_compare(snapshot)
    elif page == "데이터 챗봇":
        render_chat(snapshot)
    else:
        render_data(snapshot)

    st.caption(DATA_CAPTION)
