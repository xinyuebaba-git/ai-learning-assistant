import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [searched, setSearched] = useState(false)

  const { data: searchResults, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: () => searchApi.search(query, 50),
    enabled: searched && query.trim().length > 0,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      setSearched(true)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">🔍 搜索视频内容</h1>

      {/* 搜索框 */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex space-x-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="输入关键词搜索字幕和总结内容..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-lg"
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 font-medium"
          >
            {isLoading ? '搜索中...' : '搜索'}
          </button>
        </div>
      </form>

      {/* 搜索结果 */}
      {searched && !isLoading && (!searchResults || searchResults.total === 0) && (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <span className="text-6xl">🔍</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">未找到相关结果</h3>
          <p className="mt-2 text-gray-600">尝试其他关键词或检查拼写</p>
        </div>
      )}

      {searchResults && searchResults.total > 0 && (
        <div>
          <div className="mb-4 text-gray-600">
            找到 <span className="font-semibold text-primary-600">{searchResults.total}</span> 个相关结果
          </div>

          <div className="space-y-4">
            {searchResults.results.map((result: any, index: number) => {
              const handleClick = (e: React.MouseEvent) => {
                if (result.timestamp) {
                  e.preventDefault()
                  // 跳转到视频页面并传递时间戳
                  window.location.href = `/videos/${result.video_id}?t=${result.timestamp}`
                }
              }
              
              return (
              <a
                key={index}
                href={`/videos/${result.video_id}`}
                onClick={handleClick}
                className="block bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 p-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">
                    {result.video_title}
                  </h3>
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded">
                    {result.text_type === 'subtitle' ? '字幕' : '总结'}
                  </span>
                </div>

                <div className="text-sm text-gray-600 mb-2 line-clamp-2">
                  {result.text}
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-2">
                    {result.timestamp && (
                      <span className="px-2 py-1 bg-primary-50 text-primary-700 rounded">
                        ⏱️ {Math.floor(result.timestamp / 60)}:{String(Math.floor(result.timestamp % 60)).padStart(2, '0')}
                      </span>
                    )}
                    <span>相关性：{(result.score * 100).toFixed(1)}%</span>
                  </div>
                  <span className="text-primary-600">点击查看 →</span>
                </div>
              </a>
              )
            })}
          </div>
        </div>
      )}

      {/* 搜索提示 */}
      {!searched && (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <span className="text-6xl">💡</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">语义搜索</h3>
          <p className="mt-2 text-gray-600">
            输入关键词，搜索视频字幕和总结内容
          </p>
          <div className="mt-4 flex justify-center space-x-2">
            <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
              人工智能
            </span>
            <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
              机器学习
            </span>
            <span className="px-3 py-1 bg-gray-100 rounded-full text-sm text-gray-600">
              深度学习
            </span>
          </div>
        </div>
      )}
    </div>
  )
}
