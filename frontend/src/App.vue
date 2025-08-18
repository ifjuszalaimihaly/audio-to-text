<template>
  <div class="p-4 max-w-md mx-auto">
    <h1 class="text-2xl font-bold mb-4">Sermon Transcription</h1>
    <form @submit.prevent="submitForm" class="space-y-4">
      <input type="file" @change="handleFile" accept="audio/*" required class="block w-full" />
      <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">Upload and Process</button>
    </form>

    <div v-if="loading" class="mt-4 text-gray-500">Processing...</div>

    <div v-if="result" class="mt-6">
      <h2 class="text-xl font-semibold mb-2">Raw Transcript:</h2>
      <p class="whitespace-pre-line bg-gray-100 p-3 rounded">{{ result.raw_transcript }}</p>

      <h2 class="text-xl font-semibold mt-4 mb-2">Corrected Transcript:</h2>
      <p class="whitespace-pre-line bg-green-100 p-3 rounded">{{ result.corrected_transcript }}</p>
    </div>

    <div v-if="error" class="text-red-600 mt-4">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const file = ref(null)
const result = ref(null)
const loading = ref(false)
const error = ref(null)

function handleFile(event) {
  file.value = event.target.files[0]
}

async function submitForm() {
  if (!file.value) return
  loading.value = true
  error.value = null
  result.value = null

  const formData = new FormData()
  formData.append('file', file.value)

  try {
    const response = await axios.post('http://localhost:8000/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'An error occurred during upload.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
body {
  font-family: sans-serif;
}
</style>
