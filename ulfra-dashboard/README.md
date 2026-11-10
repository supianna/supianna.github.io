# ULFRA 울산 생활인프라 대시보드

울산 행정동별 인구와 생활인프라 공급을 비교한 팀 프로젝트의 로컬 실행용 포트폴리오 사본입니다. 원본 팀 프로젝트는 [Team2_Pjt_Ulfra](https://github.com/heromi01/Team2_Pjt_Ulfra)에 있습니다.

## 실행

Python 3.12와 `uv`가 필요합니다. 최초 의존성 설치에는 패키지 다운로드가 필요할 수 있습니다. 설치 후 대시보드 기능은 프로젝트에 포함된 SQLite DB만 사용합니다.

```powershell
cd ulfra-dashboard
uv sync
uv run streamlit run src/ulfra_pjt/main.py
```

터미널에 표시되는 `http://localhost:...` 주소를 브라우저에서 엽니다.

## 포함된 기능

- 울산 55개 읍면동의 생활인프라 공급점수 비교
- 로컬 좌표 도표에서 행정동 선택, 시설 위치 탐색 및 상호명 검색
- 지역 간 비교, 집계표와 CSV 다운로드
- 프로젝트 DB 계산 결과를 설명하는 데이터 챗봇

지도는 외부 지도 타일 없이 좌표와 격자로 표시합니다. 도로와 행정동 경계는 표시하지 않습니다. 데이터 챗봇은 외부 AI 모델을 호출하지 않습니다. 인구와 상가 자료는 원본 프로젝트의 2026년 8월·6월 기준 스냅샷이며 실시간 정보가 아닙니다.

GitHub Pages에서는 Python 서버를 실행할 수 없으므로 이 폴더의 Streamlit 앱은 로컬에서 실행합니다. `supianna.github.io`의 Projects 카드는 프로젝트 소개와 소스 안내용입니다.
