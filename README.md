# aiRouting KiCad Plugin (Draft)

목표: KiCad 액션 플러그인으로 “AI Assisted Routing” 패널을 제공하고, 선택된 넷/DRC 정보를 로컬 백엔드(REST)로 보내 Freerouting 기반 자동 라우팅 제안을 받아 적용하는 워크플로우를 만든다.

## 구성
- `kicad_plugin/ai_routing.py`: KiCad 파이썬 액션 플러그인 엔트리. 사이드 패널 UI(넷 리스트, DRC 요약, 요청/적용 버튼)와 로컬 REST 호출.
- `backend/main.py`: 로컬 FastAPI 서버. 입력 DSN/컨텍스트를 받아 Freerouting CLI/SES를 호출해 제안/패치를 생성 후 반환.

## 워크플로우(초안)
1) KiCad에서 “AI Routing” 액션 실행 → 사이드 패널 표시.
2) “Analyze Selected Nets” 클릭 → 현재 보드 DSN 임시 저장 → REST `/analyze` 호출.
3) 백엔드: Freerouting CLI로 대상 넷 부분 라우팅/검증 → SES/SCR 제안 + 요약 반환.
4) 패널에서 제안 리스트를 선택 후 “Apply” → SES를 KiCad에 재적용(초기엔 파일 재로딩; 차후 pcbnew API로 직접 반영).

## 실행 방법(초안)
```bash
# 백엔드 (FastAPI)
cd backend
python -m venv .venv && .venv\\Scripts\\activate
pip install fastapi uvicorn
python main.py  # uvicorn main:app --reload 와 동일

# KiCad 플러그인
# kicad_plugin 디렉터리를 KiCad 파이썬 플러그인 경로에 링크/복사
```

## TODO
- KiCad 사이드 패널 UI 구현 (PyQt/PyWx 대신 기본 wxPython 위젯 사용).
- 보드 DSN 임시 내보내기/불러오기 유틸.
- Freerouting CLI 호출 래퍼 + SES 적용 헬퍼.
- 추천/DRC 요약 응답 스키마 정의.
