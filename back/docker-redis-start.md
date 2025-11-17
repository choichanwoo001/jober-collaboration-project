# 로컬 Redis 실행 가이드 (Docker 사용)

## Docker가 설치되어 있다면

### 1. Redis 컨테이너 실행
```bash
docker run -d --name redis-local -p 6379:6379 redis:latest
```

### 2. 실행 확인
```bash
docker ps
# redis-local 컨테이너가 실행 중이면 OK
```

### 3. application-local.yml 수정
```yaml
spring:
  data:
    redis:
      host: localhost  # 158.179.169.48 → localhost로 변경
      port: 6379
      password:  # 비밀번호 없음
```

### 4. 서버 실행
이제 서버가 정상 실행됩니다!

---

## Docker가 없다면

### Windows: Docker Desktop 설치
1. https://www.docker.com/products/docker-desktop/ 다운로드
2. 설치 후 재시작
3. 위의 명령어 실행

### 또는 기존 서버 Redis 사용
application-local.yml에서 그대로 두면 됩니다 (네트워크만 연결되면 됨)





