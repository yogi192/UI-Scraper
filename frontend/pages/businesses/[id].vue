<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Back button -->
      <div class="mb-6">
        <NuxtLink
          to="/data"
          class="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-700"
        >
          <svg class="mr-1.5 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l2.293 2.293a1 1 0 010 1.414z" clip-rule="evenodd" />
          </svg>
          Back to Data Explorer
        </NuxtLink>
      </div>

      <div v-if="loading" class="text-center py-12">
        <div class="inline-flex items-center">
          <svg class="animate-spin h-8 w-8 mr-3 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Loading business details...
        </div>
      </div>

      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600">{{ error }}</p>
      </div>

      <div v-else-if="business" class="bg-white shadow overflow-hidden sm:rounded-lg">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">
            {{ business.name }}
          </h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">
            {{ business.category || 'Uncategorized' }}
          </p>
        </div>
        <div class="border-t border-gray-200 px-4 py-5 sm:px-6">
          <dl class="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <!-- Address -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Address</dt>
              <dd class="mt-1 text-sm text-gray-900">
                {{ business.address || 'Not available' }}
              </dd>
            </div>

            <!-- Phone -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Phone</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <a v-if="business.phone" :href="`tel:${business.phone}`" class="text-indigo-600 hover:text-indigo-500">
                  {{ business.phone }}
                </a>
                <span v-else>Not available</span>
              </dd>
            </div>

            <!-- Website -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Website</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <a v-if="business.website" :href="business.website" target="_blank" class="text-indigo-600 hover:text-indigo-500">
                  {{ business.website }}
                </a>
                <span v-else>Not available</span>
              </dd>
            </div>

            <!-- Email -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Email</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <a v-if="business.email" :href="`mailto:${business.email}`" class="text-indigo-600 hover:text-indigo-500">
                  {{ business.email }}
                </a>
                <span v-else>Not available</span>
              </dd>
            </div>

            <!-- Rating -->
            <div v-if="business.rating" class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Rating</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ business.rating }}</dd>
            </div>

            <!-- Hours -->
            <div v-if="business.hours && Object.keys(business.hours).length > 0" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Business Hours</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <ul class="space-y-1">
                  <li v-for="(hours, day) in business.hours" :key="day">
                    <span class="font-medium">{{ day }}:</span> {{ hours }}
                  </li>
                </ul>
              </dd>
            </div>

            <!-- Description -->
            <div v-if="business.description" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Description</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ business.description }}</dd>
            </div>

            <!-- Social Media -->
            <div v-if="business.social_media && Object.keys(business.social_media).length > 0" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Social Media</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <div class="flex space-x-4">
                  <a
                    v-for="(url, platform) in business.social_media"
                    :key="platform"
                    :href="url"
                    target="_blank"
                    class="text-indigo-600 hover:text-indigo-500 capitalize"
                  >
                    {{ platform }}
                  </a>
                </div>
              </dd>
            </div>

            <!-- Location -->
            <div v-if="business.location && business.location.lat && business.location.lng" class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Location</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <a
                  :href="`https://www.google.com/maps/search/?api=1&query=${business.location.lat},${business.location.lng}`"
                  target="_blank"
                  class="text-indigo-600 hover:text-indigo-500"
                >
                  View on Google Maps
                </a>
              </dd>
            </div>

            <!-- Source -->
            <div class="sm:col-span-2">
              <dt class="text-sm font-medium text-gray-500">Source</dt>
              <dd class="mt-1 text-sm text-gray-900">
                <a v-if="business.source_url" :href="business.source_url" target="_blank" class="text-indigo-600 hover:text-indigo-500">
                  {{ business.source_name || business.source_url }}
                </a>
                <span v-else>{{ business.source_name || 'Unknown' }}</span>
              </dd>
            </div>

            <!-- Dates -->
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Added</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(business.created_at) }}</dd>
            </div>
            <div class="sm:col-span-1">
              <dt class="text-sm font-medium text-gray-500">Last Updated</dt>
              <dd class="mt-1 text-sm text-gray-900">{{ formatDate(business.updated_at) }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const route = useRoute()
const business = ref(null)
const loading = ref(true)
const error = ref(null)

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

onMounted(async () => {
  try {
    business.value = await $fetch(`http://localhost:8000/api/businesses/${route.params.id}`)
  } catch (err) {
    error.value = err.data?.detail || 'Failed to load business details'
  } finally {
    loading.value = false
  }
})
</script>