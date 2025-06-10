<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="sm:flex sm:items-center">
        <div class="sm:flex-auto">
          <h1 class="text-2xl font-semibold text-gray-900">Jobs</h1>
          <p class="mt-2 text-sm text-gray-700">
            Manage and monitor scraping jobs
          </p>
        </div>
        <div class="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            @click="showNewJobModal = true"
            type="button"
            class="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
          >
            New Job
          </button>
        </div>
      </div>

      <!-- Jobs List -->
      <div class="mt-8 flex flex-col">
        <div class="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div class="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table class="min-w-full divide-y divide-gray-300">
                <thead class="bg-gray-50">
                  <tr>
                    <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Type
                    </th>
                    <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Progress
                    </th>
                    <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Created
                    </th>
                    <th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Duration
                    </th>
                    <th scope="col" class="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span class="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 bg-white">
                  <tr v-for="job in jobs" :key="job._id || job.id">
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                      {{ job.type }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm">
                      <span
                        class="inline-flex rounded-full px-2 text-xs font-semibold leading-5"
                        :class="getStatusClass(job.status)"
                      >
                        {{ job.status }}
                      </span>
                    </td>
                    <td class="px-3 py-4 text-sm">
                      <div v-if="job.status === 'running' && job.total_steps > 0" class="w-48">
                        <div class="flex items-center">
                          <div class="flex-1">
                            <div class="bg-gray-200 rounded-full h-2">
                              <div 
                                class="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                                :style="`width: ${(job.current_step / job.total_steps) * 100}%`"
                              ></div>
                            </div>
                            <p class="text-xs text-gray-600 mt-1">
                              {{ job.current_step }} of {{ job.total_steps }} tasks
                              <span v-if="job.progress_message" class="text-gray-500">• {{ job.progress_message }}</span>
                            </p>
                          </div>
                        </div>
                      </div>
                      <span v-else-if="job.status === 'completed'" class="text-green-600">
                        ✓ Completed
                      </span>
                      <span v-else-if="job.status === 'failed'" class="text-red-600">
                        ✗ Failed
                      </span>
                      <span v-else class="text-gray-400">
                        Not started
                      </span>
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {{ formatDate(job.created_at) }}
                    </td>
                    <td class="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {{ getDuration(job) }}
                    </td>
                    <td class="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <button
                        @click="viewJob(job._id || job.id)"
                        class="text-indigo-600 hover:text-indigo-900 mr-4"
                      >
                        View
                      </button>
                      <button
                        v-if="job.status === 'pending' || job.status === 'running'"
                        @click="cancelJob(job._id || job.id)"
                        class="text-red-600 hover:text-red-900"
                      >
                        Cancel
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="loading" class="text-center py-8">
                Loading jobs...
              </div>
              <div v-if="!loading && jobs.length === 0" class="text-center py-8 text-gray-500">
                No jobs found
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- New Job Modal -->
    <NewJobModal v-model:show="showNewJobModal" @created="onJobCreated" />
    
    <!-- Job Preview Modal -->
    <JobPreviewModal 
      v-model:show="showPreviewModal" 
      :job-id="selectedJobId"
      @cancel="handleCancelFromPreview"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const jobs = ref([])
const loading = ref(false)
const showNewJobModal = ref(false)
const showPreviewModal = ref(false)
const selectedJobId = ref(null)
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
  if (!job.started_at) return '-'
  
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

const fetchJobs = async () => {
  loading.value = true
  try {
    jobs.value = await $fetch('http://localhost:8000/api/jobs')
  } catch (error) {
    console.error('Failed to fetch jobs:', error)
  } finally {
    loading.value = false
  }
}

const cancelJob = async (jobId) => {
  if (confirm('Are you sure you want to cancel this job?')) {
    try {
      await $fetch(`http://localhost:8000/api/jobs/${jobId}`, { method: 'DELETE' })
      await fetchJobs()
    } catch (error) {
      console.error('Failed to cancel job:', error)
      alert('Failed to cancel job. Please try again.')
    }
  }
}

const viewJob = (jobId) => {
  selectedJobId.value = jobId
  showPreviewModal.value = true
}

const handleCancelFromPreview = async (jobId) => {
  showPreviewModal.value = false
  await cancelJob(jobId)
}

const onJobCreated = () => {
  showNewJobModal.value = false
  fetchJobs()
}

onMounted(() => {
  fetchJobs()
  // Refresh jobs every 5 seconds
  refreshInterval = setInterval(fetchJobs, 5000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>