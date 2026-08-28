import React, { useRef, useState } from 'react'
import { Upload, Loader2, FileArchive } from 'lucide-react'
import { formatBytes } from '../utils/format'

interface ZipUploadProps {
  onSubmit: (file: File) => void
  isLoading: boolean
  maxSizeMB?: number
}

const ZipUpload: React.FC<ZipUploadProps> = ({ onSubmit, isLoading, maxSizeMB = 50 }) => {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const validateFile = (selectedFile: File) => {
    if (!selectedFile.name.endsWith('.zip')) {
      setError('Only .zip files are allowed.')
      return false
    }
    if (selectedFile.size > maxSizeMB * 1024 * 1024) {
      setError(`File size exceeds ${maxSizeMB}MB limit.`)
      return false
    }
    setError(null)
    return true
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected && validateFile(selected)) {
      setFile(selected)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const selected = e.dataTransfer.files?.[0]
    if (selected && validateFile(selected)) {
      setFile(selected)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (file) {
      onSubmit(file)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-xl mx-auto space-y-4">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-[#58a6ff] bg-[#58a6ff]/10'
            : error
            ? 'border-[#f85149] bg-transparent'
            : 'border-gray-300 dark:border-[#27272a] hover:border-gray-400 dark:hover:border-[#8b949e]'
        }`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          accept=".zip"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
          disabled={isLoading}
        />
        
        {file ? (
          <div className="flex flex-col items-center text-gray-900 dark:text-[#e6edf3]">
            <FileArchive size={32} className="mb-2 text-[#58a6ff]" />
            <p className="font-medium">{file.name}</p>
            <p className="text-sm text-gray-500 dark:text-[#8b949e]">{formatBytes(file.size)}</p>
          </div>
        ) : (
          <div className="flex flex-col items-center text-gray-600 dark:text-[#8b949e]">
            <Upload size={32} className="mb-2" />
            <p className="font-medium">Click or drag ZIP file here</p>
            <p className="text-sm mt-1">Max size: {maxSizeMB} MB</p>
          </div>
        )}
      </div>
      
      {error && <p className="text-center text-sm text-[#f85149]">{error}</p>}
      
      <div className="flex justify-center">
        <button
          type="submit"
          disabled={isLoading || !file}
          className="px-6 py-2 rounded-md bg-gray-900 hover:bg-gray-800 dark:bg-[#e6edf3] dark:hover:bg-white text-white dark:text-black font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center min-w-[120px] transition-colors"
        >
          {isLoading ? <Loader2 size={20} className="animate-spin" /> : 'Analyze ZIP'}
        </button>
      </div>
    </form>
  )
}

export default ZipUpload
