// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt'
  ],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL || 'http://backend:8000'
    }
  },
  ssr: true,
  nitro: {
    devProxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        ws: true
      }
    }
  }
})