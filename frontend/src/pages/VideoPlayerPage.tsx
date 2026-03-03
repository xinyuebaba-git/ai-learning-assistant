import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { videoApi, noteApi } from '../api'
import VideoPlayer from '../components/VideoPlayer'

export default function VideoPlayerPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'summary' | 'notes'>('summary')
  const [newNote, setNewNote] = useState('')
  const [jumpToTime, setJumpToTime] = useState<number | null>(null)

  // 获取视频详情
  const { data: video, isLoading: videoLoading } = useQuery({
    queryKey: ['video', id],
    queryFn: () => videoApi.get(Number(id)),
    enabled: !!id,
  })

  // 获取字幕
  const { data: subtitleData } = useQuery({
    queryKey: ['subtitle', id],
    queryFn: () => videoApi.getSubtitle(Number(id)),
    enabled: !!video?.has_subtitle,
  })

  // 获取总结（总是尝试获取，由 API 决定是否返回 404）
  const { data: summaryData, error: summaryError } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => videoApi.getSummary(Number(id)),
    retry: false, // 失败不重试
  })

  // 获取笔记
  const { data: notes } = useQuery({
    queryKey: ['notes', id],
    queryFn: () => noteApi.list(Number(id)),
  })

  // 创建笔记
  const createNoteMutation = useMutation({
    mutationFn: (content: string) =>
      noteApi.create({ video_id: Number(id), content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes', id] })
      setNewNote('')
    },
  })

  // 收藏切换
  const toggleFavoriteMutation = useMutation({
    mutationFn: () => videoApi.toggleFavorite(Number(id)),
  })

  // 跳转到指定时间
  const handleJumpToTime = (time: number) => {
    setJumpToTime(time)
  }

  if (videoLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    )
  }

  if (!video) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">视频不存在</h2>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            返回首页
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-[1800px] mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-primary-600 hover:text-primary-700 flex items-center space-x-2"
            >
              <span>←</span>
              <span>返回视频库</span>
            </button>
            <h1 className="text-lg font-semibold text-gray-900 truncate max-w-2xl">
              {video.title || video.filename}
            </h1>
            <button
              onClick={() => toggleFavoriteMutation.mutate()}
              className={`px-4 py-2 rounded-md text-sm ${
                toggleFavoriteMutation.isSuccess
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              ⭐ 收藏
            </button>
          </div>
        </div>
      </div>

      {/* 主要内容区 - 左右分栏 */}
      <div className="max-w-[1800px] mx-auto p-4">
        <div className="flex gap-4">
          {/* 左侧：视频播放器 */}
          <div className="flex-1 min-w-0">
            <div className="bg-black rounded-lg overflow-hidden shadow-lg sticky top-4">
              <VideoPlayer
                src={`/api/videos/${video.id}/stream`}
                poster=""
                subtitles={subtitleData?.subtitles || []}
                knowledgePoints={summaryData?.knowledge_points || []}
                jumpToTime={jumpToTime}
                onTimeJump={() => setJumpToTime(null)}
                withAuth={true}
              />
            </div>

            {/* 视频信息 */}
            <div className="bg-white rounded-lg shadow-sm p-4 mt-4">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>时长：{Math.floor((video.duration || 0) / 60)}:{String(Math.floor((video.duration || 0) % 60)).padStart(2, '0')}</span>
                <span>状态：
                  <span className={`ml-1 px-2 py-0.5 rounded text-xs ${
                    video.status === 'SUMMARIZED' ? 'bg-green-100 text-green-800' :
                    video.status === 'SUBTITLED' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {video.status === 'SUMMARIZED' ? '已完成' :
                     video.status === 'SUBTITLED' ? '字幕完成' :
                     video.status}
                  </span>
                </span>
                <span className="text-xs text-gray-500">
                  添加时间：{new Date(video.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          {/* 右侧：总结/知识点/笔记 */}
          <div className="w-96 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm sticky top-4 max-h-[calc(100vh-2rem)] overflow-hidden flex flex-col">
              {/* 标签页 */}
              <div className="flex border-b">
                <button
                  onClick={() => setActiveTab('summary')}
                  className={`flex-1 py-3 text-sm font-medium ${
                    activeTab === 'summary'
                      ? 'border-b-2 border-primary-600 text-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📝 课程总结
                </button>
                <button
                  onClick={() => setActiveTab('notes')}
                  className={`flex-1 py-3 text-sm font-medium ${
                    activeTab === 'notes'
                      ? 'border-b-2 border-primary-600 text-primary-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  📔 我的笔记 ({notes?.length || 0})
                </button>
              </div>

              {/* 内容区域 */}
              <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'summary' ? (
                  /* 总结 */
                  <div className="space-y-4">
                    {summaryData ? (
                      <>
                        {summaryData.content && (
                          <div>
                            <h3 className="text-sm font-semibold text-gray-700 mb-2">📝 课程总结</h3>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 p-3 rounded-md">
                              {summaryData.content}
                            </div>
                          </div>
                        )}

                        {summaryData.knowledge_points && summaryData.knowledge_points.length > 0 && (
                          <div>
                            <h3 className="text-sm font-semibold text-gray-700 mb-3">🎯 知识点列表 ({summaryData.knowledge_points.length})</h3>
                            <div className="space-y-2">
                              {summaryData.knowledge_points.map((kp: any, index: number) => (
                                <div
                                  key={index}
                                  onClick={() => handleJumpToTime(kp.timestamp)}
                                  className="p-3 bg-blue-50 rounded-md cursor-pointer hover:bg-blue-100 transition-colors border border-blue-100"
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-medium text-gray-900">{kp.title}</span>
                                    <span className="text-xs text-primary-600 bg-white px-2 py-0.5 rounded font-mono">
                                      {Math.floor(kp.timestamp / 60)}:{String(Math.floor(kp.timestamp % 60)).padStart(2, '0')}
                                    </span>
                                  </div>
                                  {kp.description && (
                                    <p className="text-xs text-gray-600 mt-1">{kp.description}</p>
                                  )}
                                  {kp.type && (
                                    <span className="inline-block mt-2 px-2 py-0.5 bg-white text-xs rounded text-gray-600 border border-gray-200">
                                      {kp.type === 'concept' ? '📖 概念' :
                                       kp.type === 'formula' ? '📐 公式' :
                                       kp.type === 'example' ? '💡 示例' :
                                       kp.type === 'key_point' ? '⭐ 重点' : kp.type}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {!summaryData.content && (!summaryData.knowledge_points || summaryData.knowledge_points.length === 0) && (
                          <div className="text-center py-8">
                            <div className="text-4xl mb-2">📝</div>
                            <p className="text-gray-500 text-sm">总结内容为空</p>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-2">📝</div>
                        <p className="text-gray-500 text-sm">
                          {video.has_summary ? '总结加载中...' : '暂无总结'}
                        </p>
                        {summaryError && (
                          <p className="text-gray-400 text-xs mt-2">
                            {(summaryError as any)?.response?.status === 404 
                              ? '该视频尚未生成总结'
                              : '加载失败，请稍后重试'}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  /* 笔记 */
                  <div className="space-y-4">
                    {/* 添加笔记 */}
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="添加笔记..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                      <button
                        onClick={() => createNoteMutation.mutate(newNote)}
                        disabled={!newNote.trim() || createNoteMutation.isPending}
                        className="w-full px-4 py-2 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 disabled:opacity-50"
                      >
                        添加笔记
                      </button>
                    </div>

                    {/* 笔记列表 */}
                    {notes && notes.length > 0 ? (
                      <div className="space-y-3">
                        {notes.map((note: any) => (
                          <div key={note.id} className="p-3 bg-gray-50 rounded-md">
                            <div className="flex items-center justify-between mb-2">
                              {note.timestamp ? (
                                <span className="text-xs text-primary-600 bg-white px-2 py-0.5 rounded">
                                  ⏱️ {Math.floor(note.timestamp / 60)}:{String(Math.floor(note.timestamp % 60)).padStart(2, '0')}
                                </span>
                              ) : (
                                <span className="text-xs text-gray-400">无时间戳</span>
                              )}
                              <span className="text-xs text-gray-500">
                                {new Date(note.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <p className="text-sm text-gray-900">{note.content}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-2">📔</div>
                        <p className="text-gray-500 text-sm">暂无笔记</p>
                        <p className="text-gray-400 text-xs mt-1">点击上方输入框添加第一条笔记</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
