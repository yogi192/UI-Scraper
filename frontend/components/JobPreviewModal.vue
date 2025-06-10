<template>
  <TransitionRoot as="template" :show="show">
    <Dialog as="div" class="relative z-10" @close="$emit('update:show', false)">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 translate-y-0 sm:scale-100"
            leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl">
              <div class="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                <div class="sm:flex sm:items-start">
                  <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
                    <DialogTitle as="h3" class="text-lg font-semibold leading-6 text-gray-900 flex items-center justify-between">
                      <span>Job Preview: {{ job?.type || 'Loading...' }}</span>
                      <span
                        v-if="job"
                        class="inline-flex rounded-full px-2 py-1 text-xs font-semibold"
                        :class="getStatusClass(job.status)"
                      >
                        {{ job.status }}
                      </span>
                    </DialogTitle>
                    
                    <div v-if="job" class="mt-4">
                      <!-- Progress Bar -->
                      <div v-if="job.status === 'running' && job.total_steps > 0" class="mb-6">
                        <div class="flex justify-between text-sm text-gray-600 mb-2">
                          <span>Progress</span>
                          <span>{{ job.current_step }} of {{ job.total_steps }} tasks</span>
                        </div>
                        <div class="bg-gray-200 rounded-full h-3">
                          <div 
                            class="bg-indigo-600 h-3 rounded-full transition-all duration-300"
                            :style="`width: ${(job.current_step / job.total_steps) * 100}%`"
                          ></div>
                        </div>
                        <p v-if="job.progress_message" class="text-sm text-gray-600 mt-2">
                          {{ job.progress_message }}
                        </p>
                      </div>

                      <!-- Live Output -->
                      <div class="space-y-4">
                        <div>
                          <h4 class="text-sm font-medium text-gray-900 mb-2">Parameters</h4>
                          <pre class="bg-gray-50 p-3 rounded-md text-xs overflow-x-auto">{{ JSON.stringify(job.parameters, null, 2) }}</pre>
                        </div>

                        <!-- Live Logs -->
                        <div v-if="job.status === 'running' || job.logs">
                          <h4 class="text-sm font-medium text-gray-900 mb-2">Live Output</h4>
                          <div class="bg-gray-900 text-green-400 p-4 rounded-md font-mono text-xs h-64 overflow-y-auto" ref="logsContainer">
                            <div v-if="logs.length === 0" class="text-gray-500">
                              Waiting for output...
                            </div>
                            <div v-for="(log, index) in logs" :key="index" class="mb-1">
                              <span class="text-gray-500">[{{ formatTime(log.timestamp) }}]</span> {{ log.message }}
                            </div>
                            <div v-if="job.status === 'running'" class="inline-block">
                              <span class="animate-pulse">▊</span>
                            </div>
                          </div>
                        </div>

                        <!-- Result Preview -->
                        <div v-if="job.result && job.status === 'completed'">
                          <h4 class="text-sm font-medium text-gray-900 mb-2">Result</h4>
                          <pre class="bg-gray-50 p-3 rounded-md text-xs overflow-x-auto max-h-64">{{ JSON.stringify(job.result, null, 2) }}</pre>
                        </div>

                        <!-- Error -->
                        <div v-if="job.error && job.status === 'failed'">
                          <h4 class="text-sm font-medium text-red-900 mb-2">Error</h4>
                          <div class="bg-red-50 border border-red-200 p-3 rounded-md text-sm text-red-700">
                            {{ job.error }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                <button
                  v-if="job?.status === 'running' || job?.status === 'pending'"
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 sm:ml-3 sm:w-auto"
                  @click="$emit('cancel', job._id || job.id)"
                >
                  Cancel Job
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                  @click="$emit('update:show', false)"
                >
                  Close
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionChild, TransitionRoot } from '@headlessui/vue'

const props = defineProps({
  show: Boolean,
  jobId: String
})

const emit = defineEmits(['update:show', 'cancel'])

const job = ref(null)
const logs = ref([])
const logsContainer = ref(null)
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

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

const fetchJob = async () => {
  if (!props.jobId) return
  
  try {
    const response = await $fetch(`http://localhost:8000/api/jobs/${props.jobId}`)
    job.value = response
    
    // Update logs from backend
    if (response.logs && response.logs.length > 0) {
      logs.value = response.logs
      
      // Auto-scroll to bottom
      await nextTick()
      if (logsContainer.value) {
        logsContainer.value.scrollTop = logsContainer.value.scrollHeight
      }
    }
    
    // Stop refreshing if job is completed or failed
    if (response.status === 'completed' || response.status === 'failed') {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }
  } catch (error) {
    console.error('Failed to fetch job:', error)
  }
}

watch(() => props.show, async (newVal) => {
  if (newVal && props.jobId) {
    logs.value = []
    await fetchJob()
    // Refresh every 2 seconds
    refreshInterval = setInterval(fetchJob, 2000)
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>