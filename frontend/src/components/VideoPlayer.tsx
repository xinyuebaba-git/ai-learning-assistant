import { useState, useRef, useEffect } from 'react'

interface Subtitle {
  index: number
  start: number
  end: number
  text: string
}

interface KnowledgePoint {
  timestamp: number
  title: string
  description?: string
  type?: string
}

interface VideoPlayerProps {
  src: string
  poster?: string
  subtitles?: Subtitle[]
  knowledgePoints?: KnowledgePoint[]
  jumpToTime?: number | null
  onTimeJump?: () => void
}

export default function VideoPlayer({
  src,
  poster = '',
  subtitles = [],
  knowledgePoints = [],
  jumpToTime,
  onTimeJump,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [currentSubtitle, setCurrentSubtitle] = useState<string>('')
  const [showSubtitles, setShowSubtitles] = useState(true)
  const [videoDuration, setVideoDuration] = useState<number>(0)
  const [error, setError] = useState<string>('')

  // 监听视频事件
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    // 监听错误
    const handleError = () => {
      if (video.error) {
        const errorMessages: Record<number, string> = {
          1: 'MEDIA_ERR_ABORTED',
          2: 'MEDIA_ERR_NETWORK',
          3: 'MEDIA_ERR_DECODE',
          4: 'MEDIA_ERR_SRC_NOT_SUPPORTED',
        }
        setError(`视频加载失败：${errorMessages[video.error.code] || video.error.message}`)
      }
    }

    // 监听视频加载完成
    const handleLoadedMetadata = () => {
      const duration = video.duration
      if (duration && isFinite(duration) && duration > 0) {
        setVideoDuration(duration)
        setError('')
      }
    }

    // 监听时间更新，显示对应字幕
    const handleTimeUpdate = () => {
      const subtitle = subtitles.find(
        (s) => video.currentTime >= s.start && video.currentTime <= s.end
      )
      setCurrentSubtitle(subtitle?.text || '')
    }

    video.addEventListener('error', handleError)
    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('timeupdate', handleTimeUpdate)

    return () => {
      video.removeEventListener('error', handleError)
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('timeupdate', handleTimeUpdate)
    }
  }, [src, subtitles])

  // 跳转到指定时间
  useEffect(() => {
    if (jumpToTime !== null && jumpToTime !== undefined && videoRef.current) {
      console.log('📍 VideoPlayer 执行跳转:', jumpToTime)
      videoRef.current.currentTime = jumpToTime
      videoRef.current.play().catch(err => {
        console.error('Play after seek failed:', err)
      })
      // 通知父组件已完成跳转
      if (onTimeJump) {
        onTimeJump()
      }
    }
  }, [jumpToTime, onTimeJump])

  // 跳转到知识点
  const jumpToKnowledgePoint = (timestamp: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp
      videoRef.current.play().catch(err => console.error('Play after seek failed:', err))
    }
  }

  return (
    <div className="relative">
      {/* 错误提示 */}
      {error && (
        <div className="absolute top-0 left-0 right-0 bg-red-600 text-white text-center py-2 z-10">
          ⚠️ {error}
        </div>
      )}
      
      {/* 原生 HTML5 视频播放器 */}
      <video
        ref={videoRef}
        className="w-full rounded-lg bg-black"
        controls
        preload="metadata"
        poster={poster}
        playsInline
      >
        <source src={src} type="video/mp4" />
        您的浏览器不支持 HTML5 视频
      </video>

      {/* 知识点标记（在进度条上方） */}
      {knowledgePoints.length > 0 && videoDuration > 0 && (
        <div className="absolute bottom-20 left-0 right-0 px-4 flex justify-between pointer-events-none">
          {knowledgePoints.map((kp, index) => {
            const position = (kp.timestamp / videoDuration) * 100
            return (
              <div
                key={index}
                className="knowledge-point-marker pointer-events-auto cursor-pointer"
                style={{
                  position: 'absolute',
                  left: `${Math.min(position, 95)}%`,
                  bottom: '8px',
                }}
                onClick={() => jumpToKnowledgePoint(kp.timestamp)}
                title={`${kp.title}\n${Math.floor(kp.timestamp / 60)}:${String(Math.floor(kp.timestamp % 60)).padStart(2, '0')}`}
              >
                <div className="w-3 h-3 bg-primary-500 rounded-full hover:bg-primary-600 hover:scale-125 transition-transform" />
              </div>
            )
          })}
        </div>
      )}

      {/* 字幕显示 */}
      {showSubtitles && currentSubtitle && (
        <div className="absolute bottom-16 left-0 right-0 px-8">
          <div className="bg-black bg-opacity-75 text-white text-center py-2 px-4 rounded">
            {currentSubtitle}
          </div>
        </div>
      )}

      {/* 字幕开关按钮 */}
      <button
        onClick={() => setShowSubtitles(!showSubtitles)}
        className="absolute top-4 right-4 px-3 py-1 bg-black bg-opacity-50 text-white rounded text-sm hover:bg-opacity-75 z-10"
      >
        {showSubtitles ? '字幕：开' : '字幕：关'}
      </button>
    </div>
  )
}
