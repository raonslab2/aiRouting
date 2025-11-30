# aiRouting KiCad Plugin (Draft)

목표: KiCad 액션 플러그인으로 “AI Assisted Routing” 패널을 제공하고, 선택 넷/DRC 정보를 로컬 백엔드(REST)로 보내 Freerouting 기반 자동 라우팅 제안을 받아 적용하는 워크플로우를 만든다.

## 구성
- `kicad_plugin/ai_routing.py`: KiCad 파이썬 액션 플러그인 엔트리. 사이드 패널 UI(넷 필터, 버튼, 로그)와 로컬 REST 호출.
- `backend/main.py`: 로컬 FastAPI 서버. DSN 입력을 받아 Freerouting CLI/SES를 호출해 제안/패치를 생성 후 반환.

## 주요 설정
- 백엔드: 환경 변수 `FREEROUTING_JAR`를 freerouting-executable.jar 경로로 설정해야 실제 라우팅 실행. 미설정 시 에러 반환.
- 플러그인: 백엔드 URL을 패널에서 입력 가능(기본 `http://127.0.0.1:8000`). “Use Selected Nets”로 현재 보드에서 선택된 넷을 자동 입력.

## 워크플로우(초안)
1) KiCad에서 “AI Routing” 액션 실행 → 사이드 패널 표시.
2) Target nets 입력 또는 “Use Selected Nets” 클릭 후 “Analyze”.
3) 플러그인이 보드를 DSN으로 임시 내보내고 `/analyze` 호출.
4) 백엔드: Freerouting CLI로 라우팅/검증 → SES/log 경로 반환(현재는 경로만 반환, 적용은 추후).
5) 응답을 패널 로그에 표시. (차후 SES 재적용/직접 반영 추가 예정)

## 실행 방법(초안)
```bash
# 백엔드 (FastAPI)
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install fastapi uvicorn requests
set FREEROUTING_JAR=path\to\freerouting-executable.jar
uvicorn main:app --reload

# KiCad 플러그인
# kicad_plugin 디렉터리를 KiCad 파이썬 플러그인 경로에 링크/복사
```

## TODO
- SES 제안/적용 흐름 구현(초기엔 파일 재적용, 이후 pcbnew API 직접 삽입).
- Freerouting CLI 파라미터 튜닝(타겟 넷만 라우팅, 제안/설명 반환).
- DRC/룰 요약 및 “Fix it” 제안 추가.
