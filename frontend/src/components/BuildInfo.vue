<template>
  <div class="build-info" :class="{ 'build-info-inline': inline }">
    <div class="build-info-item">
      <span class="build-label">Build:</span>
      <span class="build-value">{{ formattedTimestamp }}</span>
    </div>
    <div class="build-info-item">
      <span class="build-label">Git:</span>
      <span class="build-value">{{ formattedSha }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { buildInfo, formatBuildDate, formatGitSha } from '../utils/buildInfo'

const props = defineProps({
  inline: {
    type: Boolean,
    default: false
  }
})

const formattedTimestamp = computed(() => formatBuildDate(buildInfo.buildTimestamp))
const formattedSha = computed(() => formatGitSha(buildInfo.gitSha))
</script>

<style scoped>
.build-info {
  font-size: 0.85rem;
  color: var(--text-color);
  opacity: 0.8;
  padding: 0.5rem;
  border-radius: 6px;
  background: var(--bg-color);
}

.build-info-inline {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.build-info-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.build-label {
  font-weight: 500;
}

.build-value {
  font-family: monospace;
}
</style>
