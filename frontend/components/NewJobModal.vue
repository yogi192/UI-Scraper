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
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
              <div>
                <h3 class="text-lg font-medium leading-6 text-gray-900">
                  Create New Job
                </h3>
                <div class="mt-4">
                  <label class="block text-sm font-medium text-gray-700">
                    Job Type
                  </label>
                  <select
                    v-model="jobType"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option value="website">Website Scraping</option>
                    <option value="search">Search Scraping</option>
                    <option value="pipeline">Full Pipeline</option>
                  </select>
                </div>

                <!-- Website URLs input -->
                <div v-if="jobType === 'website'" class="mt-4">
                  <label class="block text-sm font-medium text-gray-700">
                    Website URLs (one per line)
                  </label>
                  <textarea
                    v-model="websiteUrls"
                    rows="4"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="https://example.com&#10;https://another-site.com"
                  />
                </div>

                <!-- Search terms input -->
                <div v-if="jobType === 'search' || jobType === 'pipeline'" class="mt-4">
                  <label class="block text-sm font-medium text-gray-700">
                    Search Terms (one per line)
                  </label>
                  <textarea
                    v-model="searchTerms"
                    rows="4"
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="restaurants santo domingo&#10;hotels punta cana"
                  />
                </div>
              </div>

              <div class="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                <button
                  type="button"
                  class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 sm:col-start-2"
                  @click="createJob"
                  :disabled="loading"
                >
                  {{ loading ? 'Creating...' : 'Create Job' }}
                </button>
                <button
                  type="button"
                  class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                  @click="$emit('update:show', false)"
                >
                  Cancel
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
import { ref } from 'vue'
import {
  Dialog,
  DialogPanel,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'

const props = defineProps({
  show: Boolean
})

const emit = defineEmits(['update:show', 'created'])

const jobType = ref('website')
const websiteUrls = ref('')
const searchTerms = ref('')
const loading = ref(false)

const createJob = async () => {
  loading.value = true
  
  try {
    let parameters = {}
    
    if (jobType.value === 'website') {
      const urls = websiteUrls.value.split('\n').filter(url => url.trim())
      if (urls.length === 0) {
        alert('Please enter at least one URL')
        return
      }
      parameters.urls = urls
    } else if (jobType.value === 'search' || jobType.value === 'pipeline') {
      const terms = searchTerms.value.split('\n').filter(term => term.trim())
      if (terms.length === 0) {
        alert('Please enter at least one search term')
        return
      }
      parameters.terms = terms
    }
    
    await $fetch('http://localhost:8000/api/jobs', {
      method: 'POST',
      body: {
        type: jobType.value,
        parameters
      }
    })
    
    // Reset form
    websiteUrls.value = ''
    searchTerms.value = ''
    
    emit('created')
  } catch (error) {
    console.error('Failed to create job:', error)
    alert('Failed to create job. Please try again.')
  } finally {
    loading.value = false
  }
}
</script>