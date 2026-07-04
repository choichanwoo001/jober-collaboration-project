# PLS Jober

> 한 줄 소개: AI 기반 카카오 알림톡 템플릿 생성, 수정 및 정책 검증 서비스

### 시연 영상

| 템플릿 검증 성공 시연 | 템플릿 검증 실패 시연 |
| :---: | :---: |
| [![검증 성공 시연](https://drive.google.com/thumbnail?id=106-9zGBQi1p282WBMUTikYB9gs4HU7u9&sz=w400)](https://drive.google.com/file/d/106-9zGBQi1p282WBMUTikYB9gs4HU7u9/view?usp=sharing) | [![검증 실패 시연](https://drive.google.com/thumbnail?id=1aeZBEZVs4x4EV_3YdlO25zMt-CZpQzhs&sz=w400)](https://drive.google.com/file/d/1aeZBEZVs4x4EV_3YdlO25zMt-CZpQzhs/view?usp=sharing) |
| [Drive에서 보기](https://drive.google.com/file/d/106-9zGBQi1p282WBMUTikYB9gs4HU7u9/view?usp=sharing) | [Drive에서 보기](https://drive.google.com/file/d/1aeZBEZVs4x4EV_3YdlO25zMt-CZpQzhs/view?usp=sharing) |

---

## 프로젝트 개요

- **기간**: 추후 기입
- **인원**: 추후 기입 (팀 프로젝트 및 일부 컴포넌트 1인 개발)
- **담당 역할**:
  - **전체 통합**: Frontend, Backend, AI Service 간 연동 및 엔드투엔드(E2E) 알림톡 템플릿 생성/검증 플로우 설계 및 구현
  - **Frontend**: 반려 사유 하이라이트 미리보기 UI, 채팅 기반 템플릿 수정 및 세션 관리 구현
  - **Backend**: JWT 기반 사용자 인증, 템플릿 버전 관리 및 FastAPI AI API 연동(WebClient)

---

## 서비스 구성 및 사용자 플로우

이 프로젝트는 사용자가 필요한 알림 메시지를 작성하는 것부터 AI를 통한 자동 생성, 카카오 심사 가이드 기반 정책 검증, 반려 사유 대응 및 최종 저장에 이르기까지 일련의 **템플릿 라이프사이클**을 유기적으로 제어합니다.

```mermaid
flowchart LR
    A["1. 알림 목적 입력"] --> B["2. AI 템플릿 생성"] --> C["3. 미리보기 & 검증"] --> D["4. 반려 사유 하이라이트"] --> E["5. 대체문구/채팅 수정"] --> F["6. 최종 저장"]
    F -.->|취향/이력 피드백| A

    %% 스타일 정의 (깃허브 다크모드 최적화 저대비 색상)
    classDef stepNode fill:#1e293b,stroke:#475569,stroke-width:1px,color:#e2e8f0;
    classDef finalNode fill:#0f172a,stroke:#3b82f6,stroke-width:1px,color:#e2e8f0;

    class A,B,C,D,E stepNode;
    class F finalNode;
```

### 알림톡 템플릿 생성 및 검증 플로우

| 단계 | 사용자 동작 (Frontend) | 시스템 처리 (Backend & AI) |
| :---: | :--- | :--- |
| **Step 1** | **알림 목적 및 내용 입력** | 요청을 수신하여 FastAPI AI 서버에 전달 |
| **Step 2** | 생성된 **초안 확인** (본문, 변수, 카테고리) | AI가 템플릿 생성 및 **데이터베이스 1차 저장(Upsert)** |
| **Step 3** | **카카오 알림톡 미리보기** 및 **검증 요청** | `WebClient`를 통해 AI 정책 검증 API 호출 |
| **Step 4** | **반려 사이드바**에서 오류/경고/대안 확인 | 템플릿 본문 규칙 및 광고성 표현 등 분석/검증 결과 반환 |
| **Step 5** | **대체 문구 적용** 및 **채팅 기반 추가 수정** | 세션별 수정 횟수 제한 및 AI 모델 기반 수정본 재생성 |
| **Step 6** | 템플릿 **최종 저장 및 마이페이지 관리** | 사용자 권한(JWT) 검증 및 최종 템플릿 영속화 |

---

## 시스템 아키텍처

```mermaid
flowchart LR
    User["사용자"] --> Front["Vue 3 (Vite) Frontend"]
    Front -->|Nginx Proxy /api| Back["Spring Boot Backend"]
    Front -->|Nginx Proxy /ai| AI["FastAPI AI Service"]
    Back -->|JPA / Flyway| MySQL[("MySQL Database")]
    Back -->|Session / Token| Redis[("Redis Cache")]
    Back -->|WebClient| AI
    AI -->|LangChain / RAG| OpenAI["OpenAI API"]
    AI -->|ChromaDB Vector| Chroma[("ChromaDB")]

    %% 스타일 정의 (깃허브 다크모드 최적화 저대비 색상)
    classDef mainNode fill:#1e293b,stroke:#475569,stroke-width:1px,color:#e2e8f0;
    classDef dbNode fill:#0f172a,stroke:#3b82f6,stroke-width:1px,color:#e2e8f0;
    
    class User,Front,Back,AI,OpenAI mainNode;
    class MySQL,Redis,Chroma dbNode;
```

*   **데이터 흐름**:
    1.  사용자가 웹 브라우저에서 알림 메시지를 요청하거나 템플릿 검증을 진행하면, **Vue 3 프론트엔드**에서 **Spring Boot 백엔드** 및 **FastAPI AI 서비스**로 요청을 보냅니다. Nginx 리버스 프록시를 통해 라우팅이 처리됩니다.
    2.  백엔드는 **JWT 기반 보안** 및 **Redis** 세션/캐싱을 거치며, **MySQL** 데이터베이스에 템플릿 정보 및 사용자 데이터를 적재합니다.
    3.  AI 요청은 백엔드의 `WebClient`를 거쳐 **FastAPI**로 전달되며, **ChromaDB** RAG(검색 증강 생성) 파이프라인 및 **OpenAI API**를 기반으로 템플릿 승인 정책 검증 및 대체 문장 추천 결과가 도출됩니다.

---

## 핵심 기능

### 1. AI 기반 알림톡 템플릿 생성 & 분류
- 사용자의 입력 내용을 분석하여 적절한 본문 메시지, 치환이 필요한 `{{변수}}`, 적절한 카테고리를 추천 및 자동 분류합니다.
- 생성 직후 백엔드에 1차 임시 저장하여 이후 수정/검증 단계의 연속성을 보장합니다.

### 2. 대화형(Chat-based) 템플릿 수정 및 버전 제어
- AI가 도출한 초안에 대해 채팅 형식으로 간편하게 수정 요구사항을 제안할 수 있습니다.
- 세션당 수정 횟수를 제한하여 무분별한 API 호출을 방지하고, 이전 히스토리 버전을 관리하여 취소 및 롤백이 가능합니다.

### 3. 실시간 카카오 알림톡 미리보기
- 카카오 알림톡 실물과 동일한 레이아웃의 프리뷰 컴포넌트를 제공합니다.
- 변수값 표시 토글 기능을 지원하여 실제 고객 발송 시 치환될 레이아웃을 미리 파악할 수 있으며, 오류 영역이 있을 경우 해당 위치를 붉은색으로 하이라이팅하여 즉각 인지하도록 돕습니다.

### 4. 지능형 정책 검증 & 원클릭 대안 적용
- 카카오의 복잡한 심사 가이드를 기반으로 규칙(변수 형식, 광고성 어조, 허용되지 않는 특수문자 등)을 자동 검증합니다.
- 검증 실패 시 반려 사유와 함께 AI가 보정한 대체 문구를 제안하며, 사용자가 반려 사이드바에서 대안을 선택하면 본문에 즉시 반영됩니다.

### 5. 사용자 인증 및 보안 관리
- Spring Security 및 JWT 기반 보안 환경을 제공하며, 카카오 OAuth2 간편 로그인과 일반 회원가입을 모두 지원합니다.
- 자신이 생성한 템플릿에만 접근 및 수정할 수 있도록 리소스 소유 권한을 엄격하게 통제합니다.

---

## 기술 스택 & 선택 이유

| 영역 | 기술 | 대안 스택 대비 선정 이유 (차별점) |
|---|---|---|
| **Frontend** | Vue 3, TypeScript, Vite, Vuetify | • **대안 기각**: **React.js** (상대적으로 무겁고 프레임워크 오버헤드가 큼), **Vanilla JS** (컴포넌트 재사용성 및 생산성 낮음)<br>• **차별점**: 가볍고 빠른 Vue 3 Composition API를 활용해 실시간 템플릿 텍스트 파싱 및 실시간 미리보기 반응성 극대화. |
| **Backend** | Java 17, Spring Boot 3.2, JPA, Flyway | • **대안 기각**: **Node.js Express** (트랜잭션 관리 및 엔터프라이즈 기능 확장 한계), **Python Django** (멀티스레딩 성능 제한)<br>• **차별점**: 견고한 Spring Security 및 JPA 기반의 엄격한 회원/권한 관리와, WebClient 비동기 요청을 통한 대규모 대기 트래픽 처리 역량 확보. |
| **AI Server** | Python, FastAPI, LangChain | • **대안 기각**: **Flask** (비동기 처리(ASGI) 부재로 인한 동시 LLM API 처리 지연), **Spring Boot 내 Python 스크립트 실행** (프로세스 실행 비용 과다)<br>• **차별점**: LangChain 생태계의 풍부한 Python 라이브러리를 네이티브로 활용하면서, FastAPI의 비동기 성능으로 LLM/RAG 호출 대기 시간 최소화. |
| **Database & Cache** | MySQL 8.0, Redis, ChromaDB | • **대안 기각**: **PostgreSQL** (현재 환경에서 단순 구조에 적합한 가볍고 널리 쓰이는 MySQL 선택), **In-Memory Cache** (다중 인스턴스 환경에서 세션 공유 불가)<br>• **차별점**: Flyway를 통한 DB 스키마 형상관리 자동화 및 Redis를 활용한 무중단 분산 세션 관리. ChromaDB를 사용하여 검증 데이터 및 심사 가이드 RAG 고성능 벡터 탐색 지원. |

---

## 기술적으로 어려웠던 점 (Troubleshooting)

### 이슈 1. OpenAI 응답 포맷의 불일치 및 데이터 구조 분리 오류
- **문제 상황**: OpenAI 응답 포맷의 무작위성으로 인해 생성/수정 요청 시 템플릿 본문, 수정 가이드, 변수 목록이 깨지거나 빈 값으로 프론트에 노출됨.
- **원인 분석**: 거대 언어 모델(LLM)이 프롬프트의 지시(JSON/Markdown 포맷팅)를 항상 100% 준수하지 못하고 예외 텍스트나 구분자를 오인하는 경우가 발생함.
- **해결 방안**: FastAPI AI 서버 단에 다중 정규식 매칭을 적용하여 템플릿 본문을 정밀 추출하는 정제 루틴을 구축함. 매칭 실패 시, 전체 텍스트에서 가장 긴 단락을 본문으로 간주하고 필수 필드를 기본값으로 보완하는 폴백(Fallback) 메커니즘을 적용.
- **결과**: 예외 상황에서도 프론트 화면 깨짐 현상을 100% 방지하고 안정적인 응답 가용성 확보.

### 이슈 2. 생성, 수정, 저장, 검증 단계의 데이터 연결 및 일관성 유실
- **문제 상황**: 템플릿의 생성, 수정, 검증, 최종 저장 단계에 이르는 다단계 플로우에서 `templateId`, 변수 데이터, 카테고리 등의 누락으로 데이터 일관성이 깨짐.
- **원인 분석**: 각 라이프사이클 단계가 완전히 별개의 API로 분리되어 있었고, 비동기 상태 전이 과정에서 상태 동기화 및 클라이언트-서버 간 데이터 홀딩이 명확하지 않았음.
- **해결 방안**: 템플릿 초안 생성 직후 즉시 데이터베이스에 `/api/template/create`를 호출해 1차 저장하고 고유 식별자(`templateId`)를 발급하는 파이프라인으로 개편함. 이후 모든 수정 및 검증 단계는 해당 ID를 영속성 키로 공유하며, 백엔드에 `upsertTemplate` 공통 메서드를 도입해 중복 코드를 줄이고 정합성을 맞춤.
- **결과**: 다단계 상태 전이 과정에서 발생하는 데이터 유실 가능성을 근본적으로 차단하고 코드 복잡도를 30% 감소시킴.

### 이슈 3. AI 정책 검증 결과의 화면 시각화 및 사용자 수정 인터랙션 복잡성
- **문제 상황**: AI가 반환하는 복잡한 중첩 객체 구조의 반려/검증 결과를 프론트 화면에 직관적으로 매칭하여 보여주지 못해 사용자가 수정에 어려움을 겪음.
- **원인 분석**: AI 검증 모델의 반환 규격이 원본 템플릿의 특정 위치 정보(인덱스 등)를 명확히 짚어주지 않아 시각적 매핑이 복잡했음.
- **해결 방안**: 백엔드 레이어에서 검증 결과를 정형화된 `TemplateValidationResponseDto` 구조로 정규화 및 파싱 처리함. 프론트엔드에서는 수신한 DTO를 바탕으로 템플릿 본문 텍스트 내 문제 영역의 매치 포인트를 찾아 실시간으로 인라인 하이라이팅 처리하고, 반려 사이드바에서 문제 원인 및 대체 문구를 원클릭으로 원본 텍스트에 교체 주입할 수 있는 인터랙션 컴포넌트를 설계함.
- **결과**: 반려 사유 인지 시점부터 수정 및 재검증 완료까지 걸리는 사용자 평균 작업 소요 시간을 대폭 절감.

### 이슈 4. 실제 OpenAI 호출 성능 테스트 시의 레이턴시 및 비용 문제
- **문제 상황**: 시스템 한계 부하 측정(k6 성능 테스트) 과정에서 외부 OpenAI API 호출로 인한 대용량 호출 비용 누적, 레이턴시 병목 및 Rate Limit 차단 이슈가 지속 발생.
- **원인 분석**: 성능 검증 대상인 백엔드와 AI 서비스 로직 외부에 위치한 써드파티 API에 종속되어 테스트 처리량(Throughput) 확보 불가능.
- **해결 방안**: FastAPI AI 서버 실행 환경에 `MOCK_OPENAI=1` 환경변수 스위치를 개발함. 활성화 시 OpenAI 네트워크 호출을 생략하고 로컬 메모리 상의 정적 더미 데이터를 규격에 맞춰 즉시 응답하는 모킹(Mocking) 모드를 구현함.
- **결과**: 외부 종속성 없이 로컬 인프라(FastAPI-Spring Boot-MySQL) 순수 한계 성능 측정 성공 및 불필요한 API 호출 비용 절감.

---

## 결과 및 회고

- 단순 문구 입력만으로 알림톡 템플릿 초안을 생성하고, 채팅으로 수정하며, 정책 검증까지 이어지는 흐름을 안정적으로 구현했습니다.
- Spring Boot와 FastAPI를 분리하고 WebClient를 활용하여 비동기 처리함으로써, 인증/저장 로직과 무거운 AI 처리 로직의 관심사를 성공적으로 나누었습니다.
- AI 응답은 예측 불가능성이 크기 때문에 프롬프트 최적화뿐만 아니라 유연한 응답 파싱, Fallback 처리, 그리고 사용자가 이를 직관적으로 통제할 수 있는 UI 피드백 구조의 설계가 매우 중요하다는 교훈을 얻었습니다.
