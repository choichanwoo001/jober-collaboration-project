<template>
  <v-card class="login-form" elevation="0" color="transparent">
    <v-card-title class="text-h4 font-weight-bold text-center mb-6">
      로그인
    </v-card-title>
    
    <v-form @submit.prevent="handleLogin" v-model="isFormValid">
      <v-text-field
        v-model="email"
        label="이메일"
        type="email"
        variant="outlined"
        :rules="emailRules"
        required
        class="mb-4"
      />
      
      <v-text-field
        v-model="password"
        label="비밀번호"
        type="password"
        variant="outlined"
        :rules="passwordRules"
        required
        class="mb-6"
      />
      
      <v-btn
        type="submit"
        color="primary"
        size="large"
        block
        :loading="isLoading"
        :disabled="!isFormValid"
        class="mb-4"
      >
        로그인
      </v-btn>
    </v-form>

    <!-- 소셜 로그인 구분선 -->
    <v-divider class="my-4">
      <span class="text-caption text-medium-emphasis">또는</span>
    </v-divider>

    <!-- 카카오 로그인 버튼 -->
    <v-btn
      color="#FEE500"
      size="large"
      block
      :loading="isKakaoLoading"
      @click="handleKakaoLogin"
      class="mb-4 text-black"
      style="background-color: #FEE500 !important;"
    >
      <v-icon start>mdi-chat</v-icon>
      카카오로 로그인
    </v-btn>
    
    <!-- 에러 메시지 표시 -->
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ errorMessage }}
    </v-alert>
    
    <div class="text-center">
      <v-btn
        variant="text"
        color="primary"
        @click="$emit('switchForm', 'register')"
        class="mb-2 w-100"
      >
        회원가입
      </v-btn>
      <br>
      <v-btn
        variant="text"
        color="secondary"
        @click="$emit('switchForm', 'forgot')"
        class="w-100"
      >
        비밀번호 찾기
      </v-btn>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '@/api'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

interface Emits {
  (e: 'switchForm', form: string): void
  (e: 'loginSuccess'): void
}

const emit = defineEmits<Emits>()
const router = useRouter()
const userStore = useUserStore()

const email = ref('')
const password = ref('')
const isFormValid = ref(false)
const isLoading = ref(false)
const isKakaoLoading = ref(false)
const errorMessage = ref('')

const emailRules = [
  (v: string) => !!v || '이메일을 입력해주세요',
  (v: string) => /.+@.+\..+/.test(v) || '올바른 이메일 형식을 입력해주세요'
]

const passwordRules = [
  (v: string) => !!v || '비밀번호를 입력해주세요',
  (v: string) => v.length >= 6 || '비밀번호는 최소 6자 이상이어야 합니다'
]

const handleLogin = async () => {
  if (!isFormValid.value) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authApi.login(email.value, password.value)

    // 토큰 저장
    localStorage.setItem('accessToken', response.data.accessToken)
    localStorage.setItem('refreshToken', response.data.refreshToken)

    // 랜딩 페이지 showForm 비활성화
    emit('loginSuccess')

    // 전역 유저 상태 업데이트
    userStore.setUser({
      accountId: response.data.userId,
      role: response.data.role
    })

    // 로그인 성공 시 랜딩 페이지로 이동
    router.push('/')
  } catch (error: any) {
    console.error('로그인 실패:', error)
    errorMessage.value = error.response?.data?.message || '로그인에 실패했습니다.'
  } finally {
    isLoading.value = false
  }
}

const handleKakaoLogin = async () => {
  isKakaoLoading.value = true
  errorMessage.value = ''

  try {
    // 카카오 로그인 URL 조회
    const urlResponse = await authApi.getKakaoLoginUrl()
    const kakaoAuthUrl = urlResponse.data.url

    // 새 창에서 카카오 로그인 페이지 열기
    const kakaoWindow = window.open(
      kakaoAuthUrl,
      'kakaoLogin',
      'width=500,height=600,scrollbars=yes,resizable=yes'
    )

    // 메시지 이벤트 리스너 등록
    const messageListener = async (event: MessageEvent) => {
      if (event.origin !== window.location.origin) return

      if (event.data.type === 'KAKAO_LOGIN_SUCCESS') {
        kakaoWindow?.close()
        window.removeEventListener('message', messageListener)

        try {
          // 카카오 로그인 처리
          const response = await authApi.kakaoLogin(event.data.code)

          // 토큰 저장
          localStorage.setItem('accessToken', response.data.accessToken)
          localStorage.setItem('refreshToken', response.data.refreshToken)

          // 랜딩 페이지 showForm 비활성화
          emit('loginSuccess')

          // 전역 유저 상태 업데이트
          userStore.setUser({
            accountId: response.data.userId,
            role: response.data.role
          })

          // 로그인 성공 시 랜딩 페이지로 이동
          router.push('/')
        } catch (error: any) {
          console.error('카카오 로그인 처리 실패:', error)
          errorMessage.value = error.response?.data?.message || '카카오 로그인에 실패했습니다.'
        }
      } else if (event.data.type === 'KAKAO_LOGIN_ERROR') {
        kakaoWindow?.close()
        window.removeEventListener('message', messageListener)
        errorMessage.value = '카카오 로그인이 취소되었습니다.'
      }
    }

    window.addEventListener('message', messageListener)

    // 창이 닫혔는지 주기적으로 확인
    const checkClosed = setInterval(() => {
      if (kakaoWindow?.closed) {
        clearInterval(checkClosed)
        window.removeEventListener('message', messageListener)
        isKakaoLoading.value = false
      }
    }, 1000)

  } catch (error: any) {
    console.error('카카오 로그인 URL 조회 실패:', error)
    errorMessage.value = '카카오 로그인을 시작할 수 없습니다.'
  } finally {
    isKakaoLoading.value = false
  }
}
</script>

<style scoped>
.login-form {
  max-width: 400px;
  width: 100%;
}
</style>
