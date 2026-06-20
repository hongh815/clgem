# clgem Project Summary — Weather Dashboard (rollup)

## Project Goal (condensed)
외부 날씨 API를 호출·캐시하여 실시간 대시보드로 보여주는 웹앱. 핵심 컴포넌트:
WeatherAPIClient, CacheStore, DashboardUI, ConfigLoader.

## Completed Work
- T1: WeatherAPIClient — OpenWeather API 호출, 재시도 포함. → comm-reports/T1.md
- T2: CacheStore — Redis 기반 캐시, WeatherAPIClient 응답 보관. → comm-reports/T2.md
- T3: DashboardUI — React 컴포넌트, WeatherAPIClient와 CacheStore를 사용. → comm-reports/T3.md

## Architectural Decisions (full rationale)

### D1
- **Title**: 캐시 계층은 Redis
- **Decision**: CacheStore는 Redis에 WeatherAPIClient 응답을 5분 TTL로 저장한다.
- **Rationale**: 같은 도시 반복 조회 시 API 호출 비용·레이트리밋을 줄이기 위함. 인메모리 대신 Redis로 다중 인스턴스 공유.
- **Impact**: CacheStore, WeatherAPIClient

### D2
- **Title**: UI는 React
- **Decision**: DashboardUI는 React로 구현하고 ConfigLoader에서 API 키를 읽는다.
- **Rationale**: 컴포넌트 재사용과 상태 관리 용이.
- **Impact**: DashboardUI, ConfigLoader

### D3
- **Title**: API 재시도 정책
- **Decision**: WeatherAPIClient는 실패 시 3회 지수 백오프 재시도.
- **Rationale**: 외부 API의 일시적 오류에 대한 복원력.
- **Impact**: WeatherAPIClient

## Known Risks & Deferred Items
- RISK: OpenWeather API 레이트리밋 — CacheStore로 완화.
- DEFERRED: 다국어 지원.

## Leader Profile
- 판단 원칙: 외부 의존(API)에는 항상 캐시+재시도를 둔다.
