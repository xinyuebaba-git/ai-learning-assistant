import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { videoApi } from '../api'
import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'

dayjs.extend(duration)

export default function VideoListPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')

  // 获取视频列表
  const { data: videos, isLoading, error, refetch } = useQuery({
    queryKey: ['videos', searchTerm],
    queryFn: async () => {
      try {
        const response = await videoApi.list({ search: searchTerm || undefined })
        console.log('视频列表响应:', response.data)
        return response.data
      } catch (err) {
        console.error('获取视频失败:', err)
        throw err
      }
    },
  })

  // 扫描视频
  const scanMutation = useMutation({
    mutationFn: () => videoApi.scan(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      alert('扫描完成！')
    },
  })

  // 处理视频
  const processMutation = useMutation({
    mutationFn: (videoId: number) => 
      fetch(`/api/videos/${videoId}/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      }).then(res => res.json()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] })
      alert('视频处理已启动！请稍后查看结果。')
    },
    onError: (error) => {
      alert('处理失败：' + error.message)
    },
  })

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '--:--'
    const duration = dayjs.duration(seconds, 'seconds')
    return duration.format('HH:mm:ss')
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      scanned: 'bg-gray-100 text-gray-800',
      subtitling: 'bg-blue-100 text-blue-800',
      subtitled: 'bg-green-100 text-green-800',
      summarizing: 'bg-yellow-100 text-yellow-800',
      summarized: 'bg-purple-100 text-purple-800',
      failed: 'bg-red-100 text-red-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      scanned: '已扫描',
      subtitling: '生成字幕中',
      subtitled: '字幕完成',
      summarizing: '生成总结中',
      summarized: '总结完成',
      failed: '处理失败',
    }
    return texts[status] || status
  }

  return (
    <div>
      {/* 页面头部 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">视频库</h1>
        <button
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
          className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
        >
          {scanMutation.isPending ? '扫描中...' : '📁 扫描新视频'}
        </button>
      </div>

      {/* 搜索框 */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="搜索视频..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <h3 className="text-red-800 font-semibold">❌ 加载失败</h3>
          <p className="text-red-600 text-sm mt-1">
            {error.message || '未知错误'}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            重试
          </button>
        </div>
      )}

      {/* 视频列表 */}
      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      ) : videos && videos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video: any) => (
            <Link
              key={video.id}
              to={`/videos/${video.id}`}
              className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 overflow-hidden"
            >
              {/* 视频缩略图占位 */}
              <div className="aspect-video bg-gray-200 flex items-center justify-center">
                <span className="text-4xl">🎬</span>
              </div>

              {/* 视频信息 */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 truncate mb-2" title={video.title || video.filename}>
                  {video.title || video.filename}
                </h3>

                <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
                  <span>{formatDuration(video.duration)}</span>
                  <span className={getStatusColor(video.status)}>
                    {getStatusText(video.status)}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                  <span>
                    {video.has_subtitle ? '✅ 字幕' : '⏳ 无字幕'}
                  </span>
                  <span>
                    {video.has_summary ? '✅ 总结' : '⏳ 无总结'}
                  </span>
                </div>

                {/* 处理按钮 */}
                {!video.has_subtitle && (
                  <button
                    onClick={(e) => {
                      e.preventDefault()
                      if (confirm(`开始处理视频 "${video.title || video.filename}"？\n\n将执行：\n1. ASR 语音识别生成字幕\n2. 大模型生成课程总结`)) {
                        processMutation.mutate(video.id)
                      }
                    }}
                    disabled={processMutation.isPending || video.status === 'subtitling' || video.status === 'summarizing'}
                    className="w-full mt-2 px-3 py-2 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processMutation.isPending ? '处理中...' : '🚀 开始处理'}
                  </button>
                )}

                <div className="mt-3 text-xs text-gray-400">
                  添加时间：{dayjs(video.created_at).format('YYYY-MM-DD HH:mm')}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <span className="text-6xl">📹</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">暂无视频</h3>
          <p className="mt-2 text-gray-600">点击"扫描新视频"按钮添加视频文件</p>
          <button
            onClick={() => scanMutation.mutate()}
            className="mt-4 px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            扫描视频
          </button>
        </div>
      )}
    </div>
  )
}
