# Postman 테스트 가이드 - AOP & ArgumentResolver 검증

이 가이드는 수정한 AOP(`@RequireAuth`)와 ArgumentResolver(`@CurrentUser`)가 올바르게 동작하는지 확인하는 방법입니다.

## 📋 테스트 시나리오

### 1️⃣ 인증 없이 접근 시도 (AOP 검증)

**목적**: `@RequireAuth`가 붙은 API에 토큰 없이 접근하면 401 에러가 발생하는지 확인

#### 테스트 1-1: `/api/auth/me` (인증 필요)
```
Method: GET
URL: http://localhost:8080/api/auth/me
Headers: (없음)
```

**예상 결과**:
- Status: `401 Unauthorized`
- Body: `"Unauthorized"`

#### 테스트 1-2: `/api/mypage` (인증 필요)
```
Method: GET
URL: http://localhost:8080/api/mypage
Headers: (없음)
```

**예상 결과**:
- Status: `401 Unauthorized`
- Body: `"Unauthorized"`

#### 테스트 1-3: `/api/template/validate` (인증 필요)
```
Method: POST
URL: http://localhost:8080/api/template/validate
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "templateContent": "테스트 템플릿",
  "category": "테스트",
  "variableList": []
}
```

**예상 결과**:
- Status: `401 Unauthorized`
- Body: `"Unauthorized"`

---

### 2️⃣ 로그인하여 토큰 받기

**목적**: 테스트용 계정으로 로그인하여 JWT 토큰 획득

#### Step 1: 회원가입 (선택사항 - 계정이 없다면)
```
Method: POST
URL: http://localhost:8080/api/auth/signup
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "email": "test@example.com",
  "username": "testuser",
  "password": "test1234"
}
```

**예상 결과**:
- Status: `200 OK`
- Body: `{"message": "회원가입 성공", "username": "testuser"}`

#### Step 2: 로그인
```
Method: POST
URL: http://localhost:8080/api/auth/login
Headers:
  Content-Type: application/json
Body (raw JSON):
{
  "email": "test@example.com",
  "password": "test1234"
}
```

**예상 결과**:
- Status: `200 OK`
- Body:
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "userId": "1",
  "role": "USER",
  "userName": "testuser"
}
```

**⚠️ 중요**: 응답에서 `accessToken` 값을 복사해두세요!

---

### 3️⃣ 유효한 토큰으로 접근 (정상 동작 확인)

**목적**: `@CurrentUser`가 제대로 주입되고 API가 정상 동작하는지 확인

#### 테스트 3-1: `/api/auth/me` (ArgumentResolver 검증)
```
Method: GET
URL: http://localhost:8080/api/auth/me
Headers:
  Authorization: Bearer {여기에 accessToken 붙여넣기}
```

**예상 결과**:
- Status: `200 OK`
- Body: `{"userId": 1}`

**✅ 검증 포인트**:
- 401 에러가 나지 않음 → AOP가 인증을 통과
- userId가 정상 반환됨 → `@CurrentUser Account`가 제대로 주입됨

#### 테스트 3-2: `/api/mypage` (UserDto 변환 검증)
```
Method: GET
URL: http://localhost:8080/api/mypage
Headers:
  Authorization: Bearer {여기에 accessToken 붙여넣기}
```

**예상 결과**:
- Status: `200 OK`
- Body: 사용자 정보 (UserDto 형태)

**✅ 검증 포인트**:
- 401 에러가 나지 않음 → AOP 통과
- 사용자 정보가 정상 반환됨 → `@CurrentUser UserDto`가 제대로 주입되고 변환됨

#### 테스트 3-3: `/api/template/validate` (복합 검증)
```
Method: POST
URL: http://localhost:8080/api/template/validate
Headers:
  Authorization: Bearer {여기에 accessToken 붙여넣기}
  Content-Type: application/json
Body (raw JSON):
{
  "templateContent": "안녕하세요 {{고객명}}님, 주문이 완료되었습니다.",
  "category": "주문완료",
  "variableList": ["고객명"]
}
```

**예상 결과**:
- Status: `200 OK`
- Body: 템플릿 검증 결과

**✅ 검증 포인트**:
- 401 에러가 나지 않음 → AOP 통과
- 로그에 "사용자 {}({})가 템플릿 검증을 요청했습니다." 메시지 확인
  → `@CurrentUser UserDto`가 제대로 주입되어 로그에 사용자 정보가 출력됨

---

### 4️⃣ 잘못된 토큰으로 접근 (토큰 검증)

**목적**: 유효하지 않은 토큰으로 접근 시 401 에러 발생 확인

```
Method: GET
URL: http://localhost:8080/api/auth/me
Headers:
  Authorization: Bearer invalid_token_here
```

**예상 결과**:
- Status: `401 Unauthorized`
- Body: `"Unauthorized"` 또는 JWT 관련 에러

---

## 🔍 추가 확인 사항

### 서버 로그 확인

서버 콘솔에서 다음 로그를 확인하세요:

1. **AOP 동작 확인**:
   - `@RequireAuth`가 붙은 메서드 호출 시 인증 체크 로그는 없지만, 401 에러가 발생하면 AOP가 동작한 것

2. **ArgumentResolver 동작 확인**:
   - `/api/template/validate` 호출 시 로그에 다음 메시지 확인:
     ```
     사용자 testuser(test@example.com)가 템플릿 검증을 요청했습니다.
     ```
   - 이 메시지가 나오면 `@CurrentUser UserDto`가 제대로 주입된 것

---

## 📝 Postman Collection 예시

Postman에서 Collection을 만들어서 테스트하면 편리합니다:

### Collection 구조
```
📁 AOP & ArgumentResolver 테스트
  📁 1. 인증 없이 접근 (실패 예상)
    - GET /api/auth/me (no token)
    - GET /api/mypage (no token)
    - POST /api/template/validate (no token)
  
  📁 2. 로그인
    - POST /api/auth/signup
    - POST /api/auth/login
  
  📁 3. 유효한 토큰으로 접근 (성공 예상)
    - GET /api/auth/me (with token)
    - GET /api/mypage (with token)
    - POST /api/template/validate (with token)
  
  📁 4. 잘못된 토큰
    - GET /api/auth/me (invalid token)
```

### Environment Variables 설정

Postman Environment에 다음 변수 추가:
- `base_url`: `http://localhost:8080`
- `access_token`: (로그인 후 자동으로 설정)

---

## ✅ 최종 검증 체크리스트

- [ ] 인증 없이 `/api/auth/me` 호출 → 401 에러
- [ ] 인증 없이 `/api/mypage` 호출 → 401 에러
- [ ] 인증 없이 `/api/template/validate` 호출 → 401 에러
- [ ] 로그인 성공 → accessToken 받기
- [ ] 유효한 토큰으로 `/api/auth/me` 호출 → 200 OK, userId 반환
- [ ] 유효한 토큰으로 `/api/mypage` 호출 → 200 OK, 사용자 정보 반환
- [ ] 유효한 토큰으로 `/api/template/validate` 호출 → 200 OK, 로그에 사용자 정보 출력
- [ ] 잘못된 토큰으로 접근 → 401 에러

모든 체크리스트가 통과하면 **AOP와 ArgumentResolver가 올바르게 적용된 것**입니다! 🎉






