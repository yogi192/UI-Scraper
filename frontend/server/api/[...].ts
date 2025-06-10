export default defineEventHandler(async (event) => {
  const apiBase = process.env.API_BASE_URL || 'http://backend:8000'
  const path = event.node.req.url || ''
  
  // Forward the request to the backend
  const response = await $fetch(`${apiBase}${path}`, {
    method: event.node.req.method,
    headers: event.node.req.headers as any,
    body: event.node.req.method !== 'GET' ? await readBody(event) : undefined,
  }).catch((error) => {
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.statusMessage || 'Backend API Error'
    })
  })
  
  return response
})