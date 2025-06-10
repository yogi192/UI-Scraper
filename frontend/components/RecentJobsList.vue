<template>
  <div class="flow-root">
    <ul role="list" class="-my-5 divide-y divide-gray-200">
      <li v-for="job in jobs" :key="job._id" class="py-4">
        <div class="flex items-center space-x-4">
          <div class="flex-shrink-0">
            <JobStatusIcon :status="job.status" />
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">
              {{ job.type }} Job
            </p>
            <p class="text-sm text-gray-500 truncate">
              {{ formatDate(job.created_at) }}
            </p>
          </div>
          <div>
            <NuxtLink
              :to="`/jobs/${job._id}`"
              class="inline-flex items-center shadow-sm px-2.5 py-0.5 border border-gray-300 text-sm leading-5 font-medium rounded-full text-gray-700 bg-white hover:bg-gray-50"
            >
              View
            </NuxtLink>
          </div>
        </div>
      </li>
    </ul>
    <div v-if="jobs.length === 0" class="text-center py-4 text-gray-500">
      No recent jobs
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  jobs: {
    type: Array,
    default: () => []
  }
})

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}
</script>