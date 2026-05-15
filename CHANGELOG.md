# MECOM Head Office 변경 이력

## 2026-05-15 — v1.0 (최초 릴리스)

### 구현 내용
1. **API 인증 시스템**
   - `MECOM_TRUSTED_KEYS` 환경변수로 현장별 API key 설정 (예: `site_a=key1,site_b=key2`)
   - 모든 데이터 수집 엔드포인트에서 `X-Site-ID`, `X-API-Key` 헤더 검증
   - 인증키 미설정 시 열린 모드로 동작 (하위호환)

2. **현장 관리 API 확장**
   - `GET /sites/{site_id}` — 현장 상세 조회
   - `PUT /api/sites/{site_id}` — 현장 정보 수정
   - `DELETE /api/sites/{site_id}` — 현장 삭제
   - `GET /api/daily-reports` — 일일리포트 목록 조회
   - `GET /api/health` — 서버 상태 + 현장 수 확인

3. **관리자 대시보드 (dashboard.py)**
   - 로그인 페이지 (`admin` / `admin123`, 환경변수로 변경 가능)
   - 현장 관리 탭: 등록, 삭제, 상세 조회, 실시간 데이터 확인
   - 알람 이력 탭: 현장별 필터, 조회 개수 설정
   - 일일리포트 탭: 보고서 목록 조회

4. **설정 환경변수화**
   - `MECOM_HEAD_HOST`, `MECOM_HEAD_PORT`, `MECOM_ADMIN_USER`, `MECOM_ADMIN_PASS`
