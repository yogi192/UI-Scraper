<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-2xl font-semibold text-gray-900">Dashboard</h1>
      
      <!-- Stats Grid -->
      <div class="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          v-for="stat in stats"
          :key="stat.name"
          :name="stat.name"
          :value="stat.value"
          :icon="stat.icon"
          :color="stat.color"
        />
      </div>

      <!-- Categories Chart -->
      <div class="mt-8 bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">
            Top Business Categories
          </h3>
          <div class="mt-4">
            <CategoryChart :categories="categories" />
          </div>
        </div>
      </div>

      <!-- Recent Jobs -->
      <div class="mt-8 bg-white overflow-hidden shadow rounded-lg">
        <div class="px-4 py-5 sm:p-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">
            Recent Jobs
          </h3>
          <div class="mt-4">
            <RecentJobsList :jobs="recentJobs" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stats = ref([
  { name: 'Total Businesses', value: '0', icon: 'building', color: 'blue' },
  { name: 'Total Jobs', value: '0', icon: 'briefcase', color: 'green' },
  { name: 'Completed Jobs', value: '0', icon: 'check-circle', color: 'green' },
  { name: 'Failed Jobs', value: '0', icon: 'x-circle', color: 'red' }
])

const categories = ref([])
const recentJobs = ref([])

onMounted(async () => {
  try {
    const data = await $fetch('http://localhost:8000/api/dashboard/stats')
    
    if (data && data.stats) {
      // Update stats
      stats.value[0].value = data.stats.total_businesses.toLocaleString()
      stats.value[1].value = data.stats.total_jobs.toLocaleString()
      stats.value[2].value = data.stats.completed_jobs.toLocaleString()
      stats.value[3].value = data.stats.failed_jobs.toLocaleString()
      
      // Update categories and jobs
      categories.value = data.categories || []
      recentJobs.value = data.recent_jobs || []
    }
  } catch (error) {
    console.error('Failed to fetch dashboard stats:', error)
  }
})
</script>