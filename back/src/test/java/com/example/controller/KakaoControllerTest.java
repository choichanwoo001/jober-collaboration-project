package com.example.controller;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.ActiveProfiles;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class KakaoControllerTest {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void 카카오_로그인_URL_조회_성공() {
        // When
        ResponseEntity<Map> response = restTemplate.getForEntity(
                "http://localhost:" + port + "/api/auth/kakao/url", Map.class);
        
        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsKey("url");
        assertThat(response.getBody().get("url").toString()).contains("kauth.kakao.com");
    }

    @Test
    void 카카오_로그인_실패_인가코드_누락() {
        // When
        ResponseEntity<Map> response = restTemplate.postForEntity(
                "http://localhost:" + port + "/api/auth/kakao/login", null, Map.class);
        
        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
    }

    @Test
    void 카카오_콜백_에러() {
        // When
        ResponseEntity<Map> response = restTemplate.getForEntity(
                "http://localhost:" + port + "/api/auth/kakao/callback?error=access_denied", Map.class);
        
        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).containsKey("error");
        assertThat(response.getBody().get("error").toString()).contains("카카오 인증 실패");
    }
}