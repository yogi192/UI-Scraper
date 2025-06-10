<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-gray-900">AI Business Crawler</h1>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <NuxtLink to="/" class="nav-link">Dashboard</NuxtLink>
              <NuxtLink to="/data" class="nav-link">Data Explorer</NuxtLink>
              <NuxtLink to="/jobs" class="nav-link">Jobs</NuxtLink>
              <NuxtLink to="/settings" class="nav-link">Settings</NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </nav>
    <main>
      <slot />
    </main>
  </div>
</template>

<style scoped>
.nav-link {
  @apply border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium;
}
.nav-link.router-link-active {
  @apply border-indigo-500 text-gray-900;
}
</style>