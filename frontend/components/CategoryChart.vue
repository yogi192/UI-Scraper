<template>
  <div class="space-y-3">
    <div v-for="category in categories" :key="category.name" class="relative">
      <div class="flex justify-between items-center mb-1">
        <span class="text-sm font-medium text-gray-600">{{ category.name }}</span>
        <span class="text-sm text-gray-500">{{ category.count }}</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all duration-500"
          :style="`width: ${getPercentage(category.count)}%`"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  categories: {
    type: Array,
    default: () => []
  }
})

const maxCount = computed(() => {
  return Math.max(...props.categories.map(c => c.count), 1)
})

const getPercentage = (count) => {
  return Math.round((count / maxCount.value) * 100)
}
</script>