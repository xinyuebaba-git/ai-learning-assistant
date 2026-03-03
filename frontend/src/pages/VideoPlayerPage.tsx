import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { videoApi, noteApi } from '../api'
import VideoPlayer from '../components/VideoPlayer'

export default function VideoPlayerPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showNotes, setShowNotes] = useState(false)
  const [newNote, setNewNote] = useState('')

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

  // 获取总结
  const { data: summaryData } = useQuery({
    queryKey: ['summary', id],
    queryFn: () => videoApi.getSummary(Number(id)),
    enabled: !!video?.has_summary,
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

  if (videoLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!video) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">视频不存在</h2>
        <button
          onClick={() => navigate('/')}
          className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
        >
          返回首页
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 返回按钮 */}
      <button
        onClick={() => navigate('/')}
        className="text-primary-600 hover:text-primary-700 flex items-center space-x-2"
      >
        <span>←</span>
        <span>返回视频库</span>
      </button>

      {/* 视频播放器 */}
      <div className="bg-black rounded-lg overflow-hidden shadow-lg">
        <VideoPlayer
          src={`http://localhost:8000/api/videos/${video.id}/stream`}
          poster=""
          subtitles={subtitleData?.subtitles || []}
          knowledgePoints={summaryData?.knowledge_points || []}
        />
      </div>

      {/* 视频信息 */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {video.title || video.filename}
            </h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span>时长：{Math.floor((video.duration || 0) / 60)} 分钟</span>
              <span>状态：{video.status}</span>
            </div>
          </div>
          <button
            onClick={() => toggleFavoriteMutation.mutate()}
            className={`px-4 py-2 rounded-md ${
              toggleFavoriteMutation.isSuccess
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            ⭐ 收藏
          </button>
        </div>

        {/* 标签页 */}
        <div className="border-b mb-4">
          <div className="flex space-x-4">
            <button
              onClick={() => setShowNotes(false)}
              className={`pb-2 px-1 ${
                !showNotes
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-600'
              }`}
            >
              课程总结
            </button>
            <button
              onClick={() => setShowNotes(true)}
              className={`pb-2 px-1 ${
                showNotes
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-600'
              }`}
            >
              我的笔记 ({notes?.length || 0})
            </button>
          </div>
        </div>

        {/* 内容区域 */}
        {showNotes ? (
          /* 笔记区域 */
          <div className="space-y-4">
            {/* 添加笔记 */}
            <div className="flex space-x-2">
              <input
                type="text"
                value={newNote}
                onChange={(e) => setNewNote(e.target.value)}
                placeholder="添加笔记..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                onClick={() => createNoteMutation.mutate(newNote)}
                disabled={!newNote.trim() || createNoteMutation.isPending}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
              >
                添加
              </button>
            </div>

            {/* 笔记列表 */}
            {notes && notes.length > 0 ? (
              <div className="space-y-3">
                {notes.map((note: any) => (
                  <div key={note.id} className="p-4 bg-gray-50 rounded-md">
                    <div className="text-sm text-gray-600 mb-1">
                      {note.timestamp && (
                        <span className="mr-2">⏱️ {Math.floor(note.timestamp / 60)}:{String(Math.floor(note.timestamp % 60)).padStart(2, '0')}</span>
                      )}
                      <span>{new Date(note.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-gray-900">{note.content}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">暂无笔记</p>
            )}
          </div>
        ) : (
          /* 总结区域 */
          <div>
            {summaryData ? (
              <>
                <div className="prose max-w-none mb-6">
                  <h3 className="text-lg font-semibold mb-3">📝 课程总结</h3>
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {summaryData.content}
                  </p>
                </div>

                {summaryData.knowledge_points && summaryData.knowledge_points.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">🎯 知识点</h3>
                    <div className="space-y-2">
                      {summaryData.knowledge_points.map((kp: any, index: number) => (
                        <div key={index} className="p-3 bg-blue-50 rounded-md">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-gray-900">{kp.title}</span>
                            <span className="text-sm text-primary-600">
                              {Math.floor(kp.timestamp / 60)}:{String(Math.floor(kp.timestamp % 60)).padStart(2, '0')}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{kp.description}</p>
                          <span className="inline-block mt-1 px-2 py-0.5 bg-white text-xs rounded">
                            {kp.type}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="text-gray-500 text-center py-8">
                {video.has_summary ? '总结加载中...' : '暂无总结，请先处理视频'}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
