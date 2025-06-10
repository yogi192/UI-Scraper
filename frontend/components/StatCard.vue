<template>
  <div class="bg-white overflow-hidden shadow rounded-lg">
    <div class="px-4 py-5 sm:p-6">
      <div class="flex items-center">
        <div class="flex-shrink-0">
          <div :class="`rounded-md p-3 bg-${color}-100`">
            <component :is="iconComponent" :class="`h-6 w-6 text-${color}-600`" />
          </div>
        </div>
        <div class="ml-5 w-0 flex-1">
          <dt class="text-sm font-medium text-gray-500 truncate">
            {{ name }}
          </dt>
          <dd class="mt-1 text-3xl font-semibold text-gray-900">
            {{ value }}
          </dd>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  BuildingOfficeIcon,
  BriefcaseIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  name: String,
  value: String,
  icon: String,
  color: {
    type: String,
    default: 'blue'
  }
})

const iconComponent = computed(() => {
  const icons = {
    'building': BuildingOfficeIcon,
    'briefcase': BriefcaseIcon,
    'check-circle': CheckCircleIcon,
    'x-circle': XCircleIcon
  }
  return icons[props.icon] || BuildingOfficeIcon
})
</script>