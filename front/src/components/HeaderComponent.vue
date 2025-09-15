<script setup lang="ts">
  import "../assets/styles/btn.css"

  import { useUserStore } from '@/stores/user' // Pinia/Vuex 스토어 import
  import { useRoute, useRouter } from "vue-router"
  import { computed } from "vue"
  import { authApi } from '@/api'

  const headerMenu = [
    { id: 1, text: "마이페이지", path: "/mypage" },
    { id: 2, text: "템플릿 작성하기", path: "/template/create" }
  ]

  const userStore = useUserStore()
  const route = useRoute()
  const router = useRouter()

  // 로그아웃 처리
  const handleLogout = async () => {
    try {
      const accessToken = localStorage.getItem('accessToken')
      const refreshToken = localStorage.getItem('refreshToken')

      // 백엔드에 로그아웃 요청
      if (accessToken) {
        await authApi.logout(accessToken, refreshToken)
      }
    } catch (error) {
      console.error('로그아웃 API 호출 실패:', error)
    } finally {
      // 로컬 스토리지 클리어
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')

      // 유저 스토어 클리어
      userStore.clearUser()

      // 랜딩 페이지로 이동
      router.push('/')
    }
  }

  // 로그인, 마이페이지 진입 시 헤더 버튼 핸들링
  const visibleMenu = computed(() => {
    // 1번 버튼 = 마이페이지
    // 2번 버튼 = 템플릿 작성하기

    // 비 로그인 유저 = null
    if(!userStore.isLoggedIn)
    return null

    // 마이페이지 진입 = 2
    else if(route.path.startsWith("/mypage"))
      return headerMenu.filter(item => item.id === 2)

    // 템플릿페이지 진입 = 1
    else if(route.path.startsWith("/template"))
      return headerMenu.filter(item => item.id === 1)

    // 랜딩 페이지
    else
      return headerMenu
  })
</script>

<template>
  <header class="header">
    <div class="header-container">
      <!-- 로고 -->
      <router-link to="/" class="logo">
        <div class="logo-icon">🤖</div>
        <span class="logo-text">AI Template</span>
      </router-link>

      <div class="header_menu">
        <router-link
          v-for="item in visibleMenu"
          :key="item.id"
          :to="item.path"
          class="btn btn-gradation"
          tabindex="0"
        >
          {{ item.text }}
        </router-link>

        <!-- 로그아웃 버튼 (로그인된 경우에만 표시) -->
        <button
          v-if="userStore.isLoggedIn"
          @click="handleLogout"
          class="btn btn-logout"
          tabindex="0"
        >
          로그아웃
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  background: linear-gradient(135deg, #1976d2 0%, #8E24AA 100%);
  padding: 0.6vw 0;
  box-shadow: 0 0.2rem 0.6rem rgba(25, 118, 210, 0.3);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%, rgba(255, 255, 255, 0.1) 100%);
  pointer-events: none;
}

.header a{
  text-decoration: none;
}

.header-container {
  max-width: 60rem;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.2rem;
  position: relative;
  z-index: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.logo-icon {
  font-size: 2rem;
  filter: drop-shadow(0 0.1rem 0.2rem rgba(0, 0, 0, 0.1));
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 0.05rem 0.1rem rgba(0, 0, 0, 0.3);
}

.header_menu{
  display: flex;
  gap: 10px;
  align-items: center;
}

.btn-logout {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
}
</style>
