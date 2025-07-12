// Build information from environment variables
export const buildInfo = {
  buildTimestamp: import.meta.env.VITE_BUILD_TIMESTAMP || 'development',
  gitSha: import.meta.env.VITE_GIT_SHA || 'development',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
}

export const formatBuildDate = (timestamp) => {
  if (timestamp === 'development') return 'Development Build'
  try {
    return new Date(timestamp).toLocaleString()
  } catch {
    return timestamp
  }
}

export const formatGitSha = (sha) => {
  if (sha === 'development') return 'Development'
  return sha.substring(0, 7) // Show first 7 characters of SHA
}
