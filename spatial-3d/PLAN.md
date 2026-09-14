# [계획서 & 설계 문서] Spatial-3D: 모던 3D 스페이셜 오비탈 인터페이스

> **목적**: 기존 메인 블로그에 영향을 주지 않는 독립된 3D 인터랙티브 프리뷰 환경 구축  
> **접속 경로**: `https://supianna.github.io/spatial-3d/` (로컬: `spatial-3d/index.html`)

---

## 1. 핵심 비주얼 디테일 & 기술 스택

### 1) Three.js 기반 화이트/글래스 3D 오비탈 오브젝트
- 가볍고 최적화된 WebGL 렌더러(Three.js r128 CDN)를 적용하여 로딩 부담과 눈의 피로를 최소화.
- **Physical Glass Material**: 반투명 글래스 질감(Transmission, Roughness, IOR, Metalness)을 갖춘 미니멀한 화이트/오팔 톤 3D 구체.
- **3D Orbital Rings**: 구체 주위를 서로 다른 각도로 교차하며 자전하는 초박형 3D 궤도 링.

### 2) 마우스 커서 반응형 3D 마이크로 틸트 (Micro Tilt)
- 마우스 커서 위치(`mouseX`, `mouseY`)를 실시간 추적하여 카메라와 오브젝트 각도를 부드러운 감속(Lerp)으로 미세 틸트.
- 시선에 따라 3D 조명(Point Light, Ambient Light)과 바닥 섀도우가 실시간으로 반응하여 우아한 입체감 형성.

### 3) Framer Motion 스타일의 부드러운 화면 전환 (Fluid Morphing)
- 탭(Home, About, Projects, Guestbook) 전환 시 3D 구체가 줌인/줌아웃 및 회전 궤적을 그리며 유기적으로 전환.
- 콘텐츠 패널이 물방울이 합쳐지고 나뉘듯 부드러운 스프링 이징(`cubic-bezier`) 곡선으로 전환.

### 4) 최신 [About Me] 콘텐츠 온전한 탑재
- **슬로건**: *"아이디어를 코드로 즉시 증명하는 바이브 코더"*
- **3대 철학 노드**:
  1. `ORBIT 01 · WORKFLOW`: AI-Native Workflow
  2. `ORBIT 02 · PRACTICAL`: Practical Automation
  3. `ORBIT 03 · PHILOSOPHY`: Vibe Coding Explorer
- **기술 스택**: `Language: Python`, `Environment: Google Colab, VS Code (uv)`, `Ecosystem: Antigravity, AI Platforms`

---

## 2. 파일 구조
- `spatial-3d/PLAN.md`: 본 설계 및 계획 문서
- `spatial-3d/index.html`: 독립 실행형 3D 스페이셜 오비탈 웹 애플리케이션

