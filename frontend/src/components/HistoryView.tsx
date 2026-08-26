import React, { useState, useEffect } from 'react'
import { Loader2, GitCommit, Flame, GitBranch, ChevronDown, ChevronRight, Plus, Minus } from 'lucide-react'
import { getCommits, getCommitDetail, getHotspots, getTimeline, getCoChanges } from '../services/api'
import type { CommitSummary, CommitDetail, Hotspot, TimelineEntry, CoChange } from '../types/api'

interface HistoryViewProps {
  repoId: string
}

type SubTab = 'commits' | 'hotspots' | 'co-changes'

const HistoryView: React.FC<HistoryViewProps> = ({ repoId }) => {
  const [subTab, setSubTab] = useState<SubTab>('commits')
  const [loading, setLoading] = useState(true)

  // Commits state
  const [commits, setCommits] = useState<CommitSummary[]>([])
  const [totalCommits, setTotalCommits] = useState(0)
  const [page, setPage] = useState(1)
  const [expandedSha, setExpandedSha] = useState<string | null>(null)
  const [commitDetail, setCommitDetail] = useState<CommitDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  // Timeline
  const [timeline, setTimeline] = useState<TimelineEntry[]>([])

  // Hotspots
  const [hotspots, setHotspots] = useState<Hotspot[]>([])

  // Co-changes
  const [coChanges, setCoChanges] = useState<CoChange[]>([])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        if (subTab === 'commits') {
          const [commitsData, timelineData] = await Promise.all([
            getCommits(repoId, page),
            getTimeline(repoId),
          ])
          setCommits(commitsData.commits)
          setTotalCommits(commitsData.total)
          setTimeline(timelineData.timeline)
        } else if (subTab === 'hotspots') {
          const data = await getHotspots(repoId)
          setHotspots(data.hotspots)
        } else if (subTab === 'co-changes') {
          const data = await getCoChanges(repoId)
          setCoChanges(data.co_changes)
        }
      } catch {
        // No data
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [repoId, subTab, page])

  const handleExpandCommit = async (sha: string) => {
    if (expandedSha === sha) {
      setExpandedSha(null)
      setCommitDetail(null)
      return
    }
    setExpandedSha(sha)
    setLoadingDetail(true)
    try {
      const detail = await getCommitDetail(repoId, sha)
      setCommitDetail(detail)
    } catch {
      setCommitDetail(null)
    } finally {
      setLoadingDetail(false)
    }
  }

  const maxTimelineCount = Math.max(1, ...timeline.map(t => t.commit_count))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#8b949e]" size={24} />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Sub-tabs */}
      <div className="flex gap-1 bg-[#161b22] border border-[#30363d] rounded-lg p-1 w-fit">
        {([
          { key: 'commits', label: 'Commits', icon: GitCommit },
          { key: 'hotspots', label: 'Hotspots', icon: Flame },
          { key: 'co-changes', label: 'Co-Changes', icon: GitBranch },
        ] as const).map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSubTab(key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              subTab === key
                ? 'bg-[#21262d] text-[#e6edf3]'
                : 'text-[#8b949e] hover:text-[#e6edf3]'
            }`}
          >
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Commits Tab */}
      {subTab === 'commits' && (
        <div className="space-y-4">
          {/* Timeline Bar */}
          {timeline.length > 0 && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
              <h3 className="text-xs font-medium text-[#8b949e] mb-3">Commit Activity</h3>
              <div className="flex items-end gap-[2px] h-16">
                {timeline.map((t, i) => (
                  <div
                    key={i}
                    className="flex-1 bg-[#238636] rounded-t-sm hover:bg-[#2ea043] transition-colors cursor-default"
                    style={{ height: `${(t.commit_count / maxTimelineCount) * 100}%`, minHeight: '2px' }}
                    title={`${t.week}: ${t.commit_count} commits`}
                  />
                ))}
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[10px] text-[#6e7681]">{timeline[0]?.week}</span>
                <span className="text-[10px] text-[#6e7681]">{timeline[timeline.length - 1]?.week}</span>
              </div>
            </div>
          )}

          {/* Commit List */}
          {commits.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 bg-[#0d1117] border border-dashed border-[#30363d] rounded-lg">
              <GitCommit size={48} className="text-[#30363d] mb-4" />
              <p className="text-[#8b949e]">No commit history available.</p>
              <p className="text-xs text-[#6e7681] mt-1">Git history is only available for GitHub-cloned repositories.</p>
            </div>
          ) : (
            <div className="space-y-1">
              {commits.map(c => (
                <div key={c.sha} className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
                  <button
                    onClick={() => handleExpandCommit(c.sha)}
                    className="w-full text-left px-4 py-3 hover:bg-[#1c2128] transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-2 min-w-0">
                        {expandedSha === c.sha ? <ChevronDown size={14} className="text-[#8b949e] mt-0.5 flex-shrink-0" /> : <ChevronRight size={14} className="text-[#8b949e] mt-0.5 flex-shrink-0" />}
                        <div className="min-w-0">
                          <p className="text-sm text-[#e6edf3] truncate">{c.message.split('\n')[0]}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs font-mono text-[#58a6ff]">{c.sha.substring(0, 7)}</span>
                            <span className="text-xs text-[#8b949e]">{c.author_name}</span>
                            <span className="text-xs text-[#6e7681]">{new Date(c.authored_date).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0 text-xs">
                        <span className="text-[#3fb950]"><Plus size={10} className="inline" />{c.insertions}</span>
                        <span className="text-[#f85149]"><Minus size={10} className="inline" />{c.deletions}</span>
                        <span className="text-[#8b949e]">{c.files_changed} files</span>
                      </div>
                    </div>
                  </button>

                  {expandedSha === c.sha && (
                    <div className="border-t border-[#30363d] px-4 py-3 bg-[#0d1117]">
                      {loadingDetail ? (
                        <Loader2 className="animate-spin text-[#8b949e]" size={16} />
                      ) : commitDetail ? (
                        <div className="space-y-2">
                          {commitDetail.message.includes('\n') && (
                            <p className="text-xs text-[#8b949e] whitespace-pre-wrap mb-3">
                              {commitDetail.message.split('\n').slice(1).join('\n').trim()}
                            </p>
                          )}
                          {commitDetail.file_changes.map((fc, i) => (
                            <div key={i} className="flex items-center justify-between text-xs py-1">
                              <div className="flex items-center gap-2 min-w-0">
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                  fc.change_type === 'added' ? 'bg-green-900/30 text-green-400' :
                                  fc.change_type === 'deleted' ? 'bg-red-900/30 text-red-400' :
                                  fc.change_type === 'renamed' ? 'bg-purple-900/30 text-purple-400' :
                                  'bg-yellow-900/30 text-yellow-400'
                                }`}>
                                  {fc.change_type.charAt(0).toUpperCase()}
                                </span>
                                <span className="font-mono text-[#e6edf3] truncate">{fc.file_path}</span>
                              </div>
                              <div className="flex gap-2 flex-shrink-0">
                                <span className="text-[#3fb950]">+{fc.insertions}</span>
                                <span className="text-[#f85149]">-{fc.deletions}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-[#6e7681]">Failed to load details</p>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Pagination */}
              {totalCommits > 50 && (
                <div className="flex items-center justify-between pt-3">
                  <span className="text-xs text-[#8b949e]">
                    Showing {(page - 1) * 50 + 1}–{Math.min(page * 50, totalCommits)} of {totalCommits}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1 text-xs bg-[#21262d] border border-[#30363d] rounded text-[#e6edf3] disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setPage(p => p + 1)}
                      disabled={page * 50 >= totalCommits}
                      className="px-3 py-1 text-xs bg-[#21262d] border border-[#30363d] rounded text-[#e6edf3] disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Hotspots Tab */}
      {subTab === 'hotspots' && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-[#30363d]">
            <h3 className="text-sm font-medium text-[#e6edf3]">Most Frequently Changed Files</h3>
            <p className="text-xs text-[#8b949e] mt-1">Files ranked by number of commits that modified them</p>
          </div>
          {hotspots.length === 0 ? (
            <div className="p-8 text-center text-[#8b949e] text-sm">No hotspot data available.</div>
          ) : (
            <div className="divide-y divide-[#21262d]">
              {hotspots.slice(0, 30).map((h, i) => {
                const maxCount = hotspots[0]?.change_count || 1
                return (
                  <div key={i} className="px-4 py-2.5 flex items-center gap-3">
                    <span className="text-xs text-[#6e7681] w-6 text-right">{i + 1}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono text-[#e6edf3] truncate">{h.file_path}</p>
                      <div className="mt-1 h-1.5 bg-[#21262d] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-[#f85149] rounded-full"
                          style={{ width: `${(h.change_count / maxCount) * 100}%` }}
                        />
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-shrink-0 text-xs">
                      <span className="text-[#e6edf3] font-medium">{h.change_count}×</span>
                      <span className="text-[#3fb950]">+{h.total_insertions}</span>
                      <span className="text-[#f85149]">-{h.total_deletions}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Co-Changes Tab */}
      {subTab === 'co-changes' && (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-[#30363d]">
            <h3 className="text-sm font-medium text-[#e6edf3]">Files That Change Together</h3>
            <p className="text-xs text-[#8b949e] mt-1">File pairs frequently modified in the same commit</p>
          </div>
          {coChanges.length === 0 ? (
            <div className="p-8 text-center text-[#8b949e] text-sm">No co-change data available.</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#21262d]">
                  <th className="text-left text-xs text-[#8b949e] font-medium px-4 py-2">File A</th>
                  <th className="text-left text-xs text-[#8b949e] font-medium px-4 py-2">File B</th>
                  <th className="text-right text-xs text-[#8b949e] font-medium px-4 py-2">Co-Changes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#21262d]">
                {coChanges.slice(0, 30).map((cc, i) => (
                  <tr key={i} className="hover:bg-[#1c2128]">
                    <td className="px-4 py-2 text-xs font-mono text-[#e6edf3] truncate max-w-[200px]">{cc.file_a}</td>
                    <td className="px-4 py-2 text-xs font-mono text-[#e6edf3] truncate max-w-[200px]">{cc.file_b}</td>
                    <td className="px-4 py-2 text-xs text-[#58a6ff] text-right font-medium">{cc.co_change_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}

export default HistoryView
