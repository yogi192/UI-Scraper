<template>
  <div
    class="w-2 h-2 rounded-full"
    :class="statusClass"
    :title="status"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusClass = computed(() => {
  const classes = {
    'pending': 'bg-yellow-400',
    'running': 'bg-blue-400 animate-pulse',
    'completed': 'bg-green-400',
    'failed': 'bg-red-400'
  }
  return classes[props.status] || 'bg-gray-400'
})
</script>