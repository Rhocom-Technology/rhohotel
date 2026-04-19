<template>
 <div class="min-h-screen flex items-center justify-center" style="background-color: #f1f5f9;">
    <div class="w-full max-w-md px-4">
      <!-- Card -->
      <div class="bg-white rounded-2xl shadow-2xl overflow-hidden">
        <!-- Top accent bar -->
        <div class="h-1 w-full bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600"></div>

        <div class="p-8">
          <!-- Logo & Title -->
          <div class="mb-8">
            <div class="flex items-center gap-2 mb-3">
              <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span class="text-white font-bold text-sm">R</span>
              </div>
              <span class="text-gray-900 font-bold text-xl">Rho-HMS</span>
            </div>
            <h1 class="text-2xl font-bold text-gray-900">Welcome back</h1>
            <p class="text-gray-500 text-sm mt-1">Sign in to your hotel management account</p>
          </div>

          <!-- Success message -->
          <div
            v-if="success"
            class="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2"
          >
            <CheckCircle class="w-4 h-4 text-green-500 flex-shrink-0" />
            <p class="text-green-700 text-sm font-medium">Login successful! Redirecting...</p>
          </div>

          <!-- Error message -->
          <div
            v-if="error"
            class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2"
          >
            <XCircle class="w-4 h-4 text-red-500 flex-shrink-0" />
            <p class="text-red-700 text-sm font-medium">{{ error }}</p>
          </div>

          <div class="space-y-4">
            <!-- Email -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
              <div class="relative">
                <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  v-model="email"
                  type="email"
                  class="w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': error }"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <!-- Password -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
              <div class="relative">
                <Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  class="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  :class="{ 'border-red-300 focus:ring-red-500 focus:border-red-500': error }"
                  placeholder="••••••••"
                  @keyup.enter="login"
                />
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <Eye v-if="!showPassword" class="w-4 h-4" />
                  <EyeOff v-else class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Submit -->
            <button
              @click="login"
              :disabled="loginResource.loading || !email || !password"
              class="w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              style="background-color: #1a1f2e;"
            >
              <Loader2 v-if="loginResource.loading" class="w-4 h-4 animate-spin" />
              <span>{{ loginResource.loading ? 'Signing in...' : 'Sign in' }}</span>
            </button>
          </div>

          <!-- Footer -->
          <p class="text-center text-xs text-gray-400 mt-6">
            Rhocom Hotel Management System &copy; {{ new Date().getFullYear() }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import { createResource } from 'frappe-ui'
import { Eye, EyeOff, Mail, Lock, Loader2, CheckCircle, XCircle } from 'lucide-vue-next'

const email = ref('')
const password = ref('')
const error = ref('')
const success = ref(false)
const showPassword = ref(false)
const router = useRouter()
const session = useSessionStore()

const loginResource = createResource({
  url: 'login',
  onSuccess(data) {
    success.value = true
    error.value = ''
    session.user = email.value
    setTimeout(() => {
      router.push('/room-view')
    }, 800)
  },
  onError(err) {
    error.value = err.messages?.[0] || 'Invalid email or password. Please try again.'
    success.value = false
  },
})

function login() {
  if (!email.value || !password.value) return
  error.value = ''
  success.value = false
  loginResource.submit({
    usr: email.value,
    pwd: password.value,
  })
}
</script>