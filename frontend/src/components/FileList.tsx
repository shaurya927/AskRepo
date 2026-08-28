import React from 'react'
import type { RepositoryFile } from '../types/api'
import { getLanguageColor } from '../utils/languages'
import { formatBytes, formatNumber, truncatePath } from '../utils/format'
import { FileCode, FileText } from 'lucide-react'

interface FileListProps {
  files: RepositoryFile[]
  onLanguageFilter?: (lang: string | null) => void
}

const FileList: React.FC<FileListProps> = ({ files }) => {
  return (
    <div className="w-full overflow-x-auto border border-gray-200 dark:border-[#27272a] rounded-lg">
      <table className="w-full text-left text-sm whitespace-nowrap">
        <thead className="bg-gray-50 dark:bg-[#111111] text-gray-500 dark:text-[#8b949e]">
          <tr>
            <th className="px-4 py-3 font-medium">Path</th>
            <th className="px-4 py-3 font-medium">Language</th>
            <th className="px-4 py-3 font-medium text-right">Lines</th>
            <th className="px-4 py-3 font-medium text-right">Size</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-[#27272a]">
          {files.map((file) => (
            <tr key={file.id} className="hover:bg-gray-50 dark:hover:bg-[#18181b] transition-colors">
              <td className="px-4 py-3">
                <div className="flex items-center gap-2 text-gray-900 dark:text-[#e6edf3]">
                  {file.language ? (
                    <FileCode size={16} className="text-gray-400 dark:text-[#8b949e]" />
                  ) : (
                    <FileText size={16} className="text-gray-400 dark:text-[#8b949e]" />
                  )}
                  <span className="font-mono text-xs" title={file.path}>{truncatePath(file.path, 60)}</span>
                </div>
              </td>
              <td className="px-4 py-3">
                {file.language ? (
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getLanguageColor(file.language) }}
                    />
                    <span className="text-gray-700 dark:text-[#8b949e]">{file.language}</span>
                  </div>
                ) : (
                  <span className="text-gray-400 dark:text-[#6e7681]">-</span>
                )}
              </td>
              <td className="px-4 py-3 text-right text-gray-600 dark:text-[#8b949e]">
                {formatNumber(file.line_count)}
              </td>
              <td className="px-4 py-3 text-right text-gray-600 dark:text-[#8b949e]">
                {formatBytes(file.size)}
              </td>
            </tr>
          ))}
          {files.length === 0 && (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-500 dark:text-[#8b949e]">
                No files found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default FileList
