import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { videoApi } from '../api'
import dayjs from 'dayjs'

export default function FavoritesPage() {
  // 获取收藏列表（通过用户 API 或视频列表的过滤）
  // 这里简化处理，实际应该有一个专门的收藏列表 API
  const { data: videos, isLoading } = useQuery({
    queryKey: ['videos'],
    queryFn: () => videoApi.list({ limit: 100 }),
  })

  // 过滤出收藏的视频（需要后端支持收藏标记）
  const favoriteVideos = videos || []

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '--:--'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${String(secs).padStart(2, '0')}`
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">⭐ 我的收藏</h1>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      ) : favoriteVideos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {favoriteVideos.map((video: any) => (
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

                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>{formatDuration(video.duration)}</span>
                  <span className="text-yellow-600">⭐ 已收藏</span>
                </div>

                <div className="mt-3 text-xs text-gray-400">
                  收藏时间：{dayjs(video.created_at).format('YYYY-MM-DD')}
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <span className="text-6xl">⭐</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">暂无收藏</h3>
          <p className="mt-2 text-gray-600">去视频库添加你喜欢的课程吧</p>
          <Link
            to="/"
            className="mt-4 inline-block px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            浏览视频库
          </Link>
        </div>
      )}
    </div>
  )
}
