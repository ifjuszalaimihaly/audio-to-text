<template>
  <div class="container py-4" style="max-width: 720px;">
    <h1 class="h3 fw-bold mb-4">Sermon Transcription</h1>

    <form @submit.prevent="submitForm" class="mb-4">
      <div class="mb-3">
        <input
          type="file"
          class="form-control"
          @change="handleFile"
          accept="audio/*"
          required
        />
      </div>
      <button type="submit" class="btn btn-primary">Upload and Process</button>
    </form>

    <div v-if="loading" class="mt-3 text-muted d-flex align-items-center gap-2">
      <div class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></div>
      <span>Processing...</span>
    </div>

    <div v-if="result" class="mt-4">
      <h2 class="h5 fw-semibold mb-2">Raw Transcript:</h2>
      <p class="bg-light p-3 rounded border" style="white-space: pre-line;">
        {{ result.raw_transcript }}
      </p>

      <h2 class="h5 fw-semibold mt-4 mb-2">Corrected Transcript:</h2>
      <p class="p-3 rounded border bg-success-subtle" style="white-space: pre-line;">
        {{ result.corrected_transcript }}
      </p>

      <h2 class="h5 fw-semibold mt-4 mb-2">Bible Reference</h2>
      <p class="p-3 rounded border bg-success-subtle" style="white-space: pre-line;">
        {{ result.bible_reference }}
      </p>
    </div>

    <div v-if="error" class="alert alert-danger mt-4 mb-0" role="alert">
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
/* no custom styles needed; Bootstrap handles most UI.
   we keep white-space handling inline on the <p> elements */
</style>
