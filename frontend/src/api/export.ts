import client from './client'

export const exportApi = {
  download: async (resource: string): Promise<Blob> => {
    const response = await client.get(`/api/v1/export/${resource}`, {
      responseType: 'blob',
    })
    return response.data
  },
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}

export default exportApi
