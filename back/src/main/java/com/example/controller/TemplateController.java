package com.example.controller;

import com.example.dto.FastAPIResponseDto;
import com.example.dto.TemplateRequestDto;
import com.example.dto.TemplateValidationRequestDto;
import com.example.dto.TemplateValidationResponseDto;
import com.example.dto.UserDto;
import com.example.dto.TemplateSaveRequestDto;
import com.example.dto.TemplateSaveResponseDto;
import com.example.service.TemplateService;
import com.example.common.annotation.RequireAuth;
import com.example.common.annotation.CurrentUser;
import com.example.exception.template.TemplateException;
import com.example.exception.user.UserException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@Slf4j
public class TemplateController {

    private final TemplateService templateService;


    /**
     * 템플릿을 검증합니다. (POST /api/template/validate)
     */
    @RequireAuth
    @PostMapping("/template/validate")
    public ResponseEntity<TemplateValidationResponseDto> validateTemplate(
            @Valid @RequestBody TemplateValidationRequestDto requestDto,
            @CurrentUser UserDto currentUser
    ) {
        try {
            log.info("템플릿 검증 요청 받음");
            log.info("요청 데이터 - 템플릿 내용: {}, 변수 개수: {}, 카테고리: {}", 
                    requestDto.getTemplateContent() != null ? requestDto.getTemplateContent().substring(0, Math.min(50, requestDto.getTemplateContent().length())) : "null",
                    requestDto.getVariableList() != null ? requestDto.getVariableList().size() : "null",
                    requestDto.getCategory());
            
            log.info("사용자 {}({})가 템플릿 검증을 요청했습니다.", currentUser.getUserName(), currentUser.getEmail());
            
            TemplateValidationResponseDto response = templateService.validateTemplate(requestDto, currentUser);
            log.info("템플릿 검증 완료");
            return ResponseEntity.ok(response);
        } catch (TemplateException | UserException e) {
            throw e;
        } catch (Exception e) {
            log.error("템플릿 검증 중 오류 발생", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(TemplateValidationResponseDto.failure("템플릿 검증 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 템플릿 신규 생성 (POST /api/template/create)
     * 생성하기 직후 1차 저장용
     */
    @RequireAuth
    @PostMapping("/template/create")
    public ResponseEntity<TemplateSaveResponseDto> createTemplate(
            @Valid @RequestBody TemplateSaveRequestDto requestDto,
            @CurrentUser UserDto currentUser
    ) {
        try {
            log.info("템플릿 신규 생성 요청 - 사용자: {}({}), 카테고리: {}, 제목: {}",
                    currentUser.getUserName(),
                    currentUser.getEmail(),
                    requestDto.getCategory(),
                    requestDto.getTemplateTitle());

            TemplateSaveResponseDto response = templateService.upsertTemplate(requestDto, currentUser);

            if (response.isSuccess()) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
            }
        } catch (TemplateException | UserException e) {
            throw e;
        } catch (Exception e) {
            log.error("템플릿 생성 중 오류 발생", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(TemplateSaveResponseDto.failure("템플릿 생성 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * 템플릿 업데이트 (POST /api/template/save)
     * templateId 필수, 기존 템플릿만 업데이트 가능
     */
    @RequireAuth
    @PostMapping("/template/save")
    public ResponseEntity<TemplateSaveResponseDto> saveTemplate(
            @Valid @RequestBody TemplateSaveRequestDto requestDto,
            @CurrentUser UserDto currentUser
    ) {
        try {
            log.info("템플릿 업데이트 요청 - 사용자: {}({}), 카테고리: {}, 제목: {}",
                    currentUser.getUserName(),
                    currentUser.getEmail(),
                    requestDto.getCategory(),
                    requestDto.getTemplateTitle());

            TemplateSaveResponseDto response = templateService.upsertTemplate(requestDto, currentUser);

            if (response.isSuccess()) {
                return ResponseEntity.ok(response);
            } else {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(response);
            }
        } catch (TemplateException | UserException e) {
            throw e;
        } catch (Exception e) {
            log.error("템플릿 업데이트 중 오류 발생", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(TemplateSaveResponseDto.failure("템플릿 업데이트 중 오류가 발생했습니다: " + e.getMessage()));
        }
    }

    /**
     * AI를 사용하여 템플릿을 수정합니다. (POST /api/template/modify)
     */
    @RequireAuth
    @PostMapping("/template/modify")
    public ResponseEntity<FastAPIResponseDto> modifyTemplate(
            @Valid @RequestBody TemplateRequestDto requestDto
    ) {
        try {
            log.info("템플릿 수정 요청 시작 - 템플릿 내용: {}, 제목: {}, 사용자 메시지: {}",
                    requestDto.getTemplateContent() != null ? requestDto.getTemplateContent().substring(0, Math.min(50, requestDto.getTemplateContent().length())) : "null",
                    requestDto.getTemplateTitle(),
                    requestDto.getUserMessage());
            log.info("요청 데이터 전체: {}", requestDto);

            FastAPIResponseDto response = templateService.modifyTemplateWithAi(requestDto);
            log.info("템플릿 수정 성공 - 응답: {}", response);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("템플릿 수정 중 오류 발생", e);
            log.error("오류 상세 정보 - 메시지: {}, 원인: {}", e.getMessage(), e.getCause());

            // 실패 시 원본 템플릿을 반환
            FastAPIResponseDto errorResponse = new FastAPIResponseDto();
            errorResponse.setTemplateText(requestDto.getTemplateContent());
            errorResponse.setTemplateTitle(requestDto.getTemplateTitle());
            errorResponse.setGenerationMethod("error");
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}
