<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-2xl font-semibold text-gray-900">Settings</h1>
      
      <div class="mt-6 max-w-3xl">
        <div class="bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">
              Google Gemini API Key
            </h3>
            <div class="mt-2 max-w-xl text-sm text-gray-500">
              <p>
                Enter your Google Gemini 2.5 API key to enable AI-powered data extraction.
              </p>
            </div>
            <form @submit.prevent="saveSettings" class="mt-5">
              <div class="w-full">
                <label for="api-key" class="sr-only">API Key</label>
                <input
                  v-model="apiKey"
                  type="password"
                  name="api-key"
                  id="api-key"
                  class="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  :placeholder="hasApiKey ? '••••••••••••••••••••••••' : 'Enter your API key'"
                />
              </div>
              <div class="mt-3 flex gap-3">
                <button
                  type="submit"
                  :disabled="saving"
                  class="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {{ saving ? 'Saving...' : 'Save API Key' }}
                </button>
                <button
                  v-if="hasApiKey"
                  type="button"
                  @click="testApiKey"
                  :disabled="testing"
                  class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50"
                >
                  {{ testing ? 'Testing...' : 'Test Current Key' }}
                </button>
              </div>
            </form>
            
            <div v-if="message" class="mt-4">
              <div
                class="rounded-md p-4"
                :class="messageType === 'success' ? 'bg-green-50' : 'bg-red-50'"
              >
                <div class="flex">
                  <div class="flex-shrink-0">
                    <svg
                      v-if="messageType === 'success'"
                      class="h-5 w-5 text-green-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <svg
                      v-else
                      class="h-5 w-5 text-red-400"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                  </div>
                  <div class="ml-3">
                    <p
                      class="text-sm font-medium"
                      :class="messageType === 'success' ? 'text-green-800' : 'text-red-800'"
                    >
                      {{ message }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 bg-white shadow sm:rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <h3 class="text-lg leading-6 font-medium text-gray-900">
              API Documentation
            </h3>
            <div class="mt-2 text-sm text-gray-500">
              <p>
                To get a Google Gemini API key:
              </p>
              <ol class="mt-2 list-decimal list-inside space-y-1">
                <li>Visit <a href="https://makersuite.google.com/app/apikey" target="_blank" class="text-indigo-600 hover:text-indigo-500">Google AI Studio</a></li>
                <li>Sign in with your Google account</li>
                <li>Click "Create API Key"</li>
                <li>Copy the generated key and paste it above</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const apiKey = ref('')
const hasApiKey = ref(false)
const saving = ref(false)
const testing = ref(false)
const message = ref('')
const messageType = ref('success')

const checkApiKey = async () => {
  try {
    const { has_google_api_key } = await $fetch('http://localhost:8000/api/settings')
    hasApiKey.value = has_google_api_key
  } catch (error) {
    console.error('Failed to check API key status:', error)
  }
}

const saveSettings = async () => {
  if (!apiKey.value && !hasApiKey.value) {
    message.value = 'Please enter an API key'
    messageType.value = 'error'
    return
  }
  
  saving.value = true
  message.value = ''
  
  try {
    await $fetch('http://localhost:8000/api/settings', {
      method: 'PUT',
      body: {
        google_api_key: apiKey.value
      }
    })
    
    message.value = 'API key saved successfully'
    messageType.value = 'success'
    hasApiKey.value = true
    apiKey.value = ''
    
    // Clear message after 3 seconds
    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (error) {
    console.error('Settings error:', error)
    if (error.data?.detail) {
      message.value = error.data.detail
    } else {
      message.value = 'Failed to save API key. Please try again.'
    }
    messageType.value = 'error'
  } finally {
    saving.value = false
  }
}

const testApiKey = async () => {
  testing.value = true
  message.value = ''
  
  try {
    // Try to create a simple job to test the API key
    const response = await $fetch('http://localhost:8000/api/jobs', {
      method: 'POST',
      body: {
        job_type: 'test',
        urls: ['https://example.com']
      }
    })
    
    message.value = 'API key is valid and working!'
    messageType.value = 'success'
    
    // Clear message after 3 seconds
    setTimeout(() => {
      message.value = ''
    }, 3000)
  } catch (error) {
    console.error('API key test error:', error)
    if (error.data?.detail && error.data.detail.includes('API key')) {
      message.value = 'API key is invalid or expired. Please update it.'
    } else {
      message.value = 'Failed to test API key. Please try again.'
    }
    messageType.value = 'error'
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  checkApiKey()
})
</script>