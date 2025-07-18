<template>
  <section class="section">
    <div class="container">
      <div class="about-container">
        <div class="about-content">
          <h1 class="title">About Darwin ATLAS</h1>
          <p>
            Darwin ATLAS is a specialized version of ATLAS (Analysis and Testing of Language Models for Archival Systems) 
            designed specifically for exploring Charles Darwin's correspondence and writings. ATLAS is a test harness for the 
            evaluation of Large Language Model (LLM) Retrieval Augmented Generation (RAG) for Humanities & 
            Social Science (HASS) research. ATLAS is a deliverable of the 
            <a href="https://aiinfra.anu.edu.au" target="_blank" rel="noreferrer">AI as Infrastructure (AIINFRA)</a> project.
          </p>
          
          <p>
            Darwin ATLAS enables researchers to semantically search through Darwin's extensive correspondence, 
            using advanced filtering by time period and correspondence direction (letters sent by Darwin vs. received by Darwin). 
            This allows for nuanced exploration of the development of Darwin's ideas through his personal and professional networks.
          </p>

          <!-- Dynamically loaded license content -->
          <div v-if="licenseContent" v-html="licenseContent" class="license-content"></div>
          <div v-else-if="loading" class="loading">Loading license information...</div>
          <div v-else class="error">Unable to load license information.</div>

        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { marked } from 'marked'

const licenseContent = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    // Fetch LICENSE.md from the public directory or via API
    const response = await fetch('/LICENSE.md')
    if (response.ok) {
      const markdown = await response.text()
      // Convert markdown to HTML
      licenseContent.value = marked(markdown)
    } else {
      console.error('Failed to load LICENSE.md')
    }
  } catch (error) {
    console.error('Error loading LICENSE.md:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.about-container {
  display: flex;
  justify-content: center;
}

.about-content {
  width: 75%; /* Same width as the previous is-three-quarters column */
  max-width: 800px;
}

.title {
  color: black;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.license-content {
  margin-top: 2rem;
}

.license-content :deep(h2) {
  color: black;
  font-size: 1.5rem;
  font-weight: bold;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.license-content :deep(h3) {
  color: black;
  font-size: 1.25rem;
  font-weight: bold;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.license-content :deep(ul) {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
}

.license-content :deep(li) {
  margin-bottom: 0.5rem;
}

.license-content :deep(a) {
  color: #3273dc;
  text-decoration: none;
}

.license-content :deep(a:hover) {
  text-decoration: underline;
}

.loading, .error {
  margin-top: 2rem;
  padding: 1rem;
  text-align: center;
  color: #666;
}
</style>