<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Back button -->
      <div class="mb-6">
        <NuxtLink
          to="/jobs"
          class="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          <svg class="mr-1.5 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l2.293 2.293a1 1 0 010 1.414z" clip-rule="evenodd" />
          </svg>
          Back to Jobs
        </NuxtLink>
      </div>

      <div v-if="loading" class="text-center py-12">
        Loading job details...
      </div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600">{{ error }}</p>
      </div>

      <div v-else-if="job" class="bg-white shadow overflow-hidden sm:rounded-lg">
        <div class="px-4 py-5 sm:px-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg leading-6 font-medium text-gray-900">
                {{ job.type }} Job
              </h3>
              <p class="mt-1 max-w-2xl text-sm text-gray-500">
                ID: {{ job._id }}
              </p>
            </div>
            <span
              class="inline-flex rounded-full px-3 py-1 text-sm font-semibold"
              :class="getStatusClass(job.status)"
            >
              {{ job.status }}
            </span>
          </div>
        </div>
        <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <!-- Created -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Created</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(job.created_at) }}</dd>
            </div>

            <!-- Started -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Started</dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ job.started_at ? formatDate(job.started_at) : 'Not started' }}
              </dd>
            </div>

            <!-- Completed -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Completed</dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ job.completed_at ? formatDate(job.completed_at) : 'Not completed' }}
              </dd>
            </div>

            <!-- Duration -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Duration</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ getDuration(job) }}</dd>
            </div>

            <!-- Parameters -->
            <div class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Parameters</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <pre class="bg-gray-50 p-3 rounded-md overflow-x-auto">{{ JSON.stringify(job.parameters, null, 2) }}</pre>
              </dd>
            </div>

            <!-- Progress -->
            <div v-if="job.status === 'running' || job.total_steps > 0" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Progress</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <div v-if="job.total_steps > 0" class="mb-4">
                  <div class="bg-gray-200 rounded-full h-3">
                    <div 
                      class="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                      :style="`width: ${(job.current_step / job.total_steps) * 100}%`"
                    ></div>
                  </div>
                  <p class="text-sm text-gray-600 mt-2">
                    {{ job.current_step }} of {{ job.total_steps }} tasks completed
                    <span v-if="job.progress_message" class="text-gray-500">• {{ job.progress_message }}</span>
                  </p>
                </div>
                <div v-if="job.progress" class="space-y-2">
                  <div v-for="(value, key) in job.progress" :key="key">
                    <span class="font-medium">{{ key }}:</span> {{ value }}
                  </div>
                </div>
              </dd>
            </div>

            <!-- Result -->
            <div v-if="job.result" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Result</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <pre class="bg-gray-50 p-3 rounded-md overflow-x-auto max-h-96">{{ JSON.stringify(job.result, null, 2) }}</pre>
              </dd>
            </div>

            <!-- Error -->
            <div v-if="job.error" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Error</dt>
              <dd class="mt-1 text-sm text-red-600">{{ job.error }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const route = useRoute()
const job = ref(null)
const loading = ref(true)
const error = ref(null)
let refreshInterval = null

const getStatusClass = (status) => {
  const classes = {
    'pending': 'bg-yellow-100 text-yellow-800',
    'running': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800'
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

const formatDate = (dateString) => {
  // Handle UTC time and convert to local time
  const date = new Date(dateString)
  // If the date string doesn't include timezone info, assume it's UTC
  if (!dateString.includes('Z') && !dateString.includes('+') && !dateString.includes('-')) {
    // Add Z to indicate UTC
    const utcDate = new Date(dateString + 'Z')
    return utcDate.toLocaleString()
  }
  return date.toLocaleString()
}

const getDuration = (job) => {
  if (!job.started_at) return 'Not started'
  
  const start = new Date(job.started_at)
  const end = job.completed_at ? new Date(job.completed_at) : new Date()
  const duration = end - start
  
  const minutes = Math.floor(duration / 60000)
  const seconds = Math.floor((duration % 60000) / 1000)
  
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`
  }
  return `${seconds}s`
}

const fetchJob = async () => {
  try {
    job.value = await $fetch(`http://localhost:8000/api/jobs/${route.params.id}`)
    
    // Stop refreshing if job is completed or failed
    if (job.value.status === 'completed' || job.value.status === 'failed') {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }
  } catch (err) {
    error.value = err.data?.detail || 'Failed to load job details'
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchJob()
  // Refresh job details every 2 seconds if still running
  refreshInterval = setInterval(fetchJob, 2000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>