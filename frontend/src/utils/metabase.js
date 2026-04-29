export const getMetabaseUrl = () => {
  const configuredUrl = import.meta.env.VITE_METABASE_URL?.trim()
  if (configuredUrl) {
    return configuredUrl.replace(/\/$/, '')
  }

  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:3001`
  }

  return 'http://localhost:3001'
}
