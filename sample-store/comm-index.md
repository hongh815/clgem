# clgem Project Index — Weather Dashboard

## Task Registry
| Id | Title | Status | Role | Report | Review Verdict |
| --- | --- | --- | --- | --- | --- |
| T1 | WeatherAPIClient | done | Implementer/sonnet | [T1.md](comm-reports/T1.md) | PASS |
| T2 | CacheStore | done | Implementer/sonnet | [T2.md](comm-reports/T2.md) | PASS |
| T3 | DashboardUI | done | Implementer/sonnet | [T3.md](comm-reports/T3.md) | CONDITIONAL |

## Key Decisions
- D1: 캐시 계층은 Redis — CacheStore가 WeatherAPIClient 응답 보관 → [details](comm-summary.md#d1)
- D2: UI는 React — DashboardUI가 ConfigLoader 사용 → [details](comm-summary.md#d2)
- D3: API 재시도 정책 — WeatherAPIClient 지수 백오프 → [details](comm-summary.md#d3)

## Questions
### Resolved
- OQ1: 캐시를 인메모리로 할까 Redis로 할까? → Redis (D1, 다중 인스턴스 공유)
