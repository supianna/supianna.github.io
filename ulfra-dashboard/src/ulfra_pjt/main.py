"""로컬 SQLite만 사용하는 ULFRA 포트폴리오 대시보드."""

import streamlit as st

from ulfra_pjt.ui.pure_streamlit import render_pure_streamlit_app


def main() -> None:
    st.set_page_config(page_title="ULFRA | 울산 생활인프라", page_icon="🗺️", layout="wide")
    render_pure_streamlit_app()


if __name__ == "__main__":
    main()
