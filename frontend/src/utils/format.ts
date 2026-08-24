export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

export const formatNumber = (n: number): string => {
  return new Intl.NumberFormat('en-US').format(n)
}

export const formatDate = (iso: string): string => {
  const date = new Date(iso)
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export const truncatePath = (path: string, maxLen: number = 50): string => {
  if (path.length <= maxLen) return path
  const parts = path.split('/')
  const file = parts.pop() || ''
  const dir = parts.join('/')
  
  if (dir.length + file.length + 4 <= maxLen) {
    return path
  }
  
  const remainLen = maxLen - file.length - 4
  if (remainLen <= 0) {
    return '.../' + file
  }
  
  return dir.substring(0, remainLen) + '.../' + file
}
