import { useEffect, useRef, useState } from 'react'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'

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
  console.log('🎥 [VideoPlayer] 组件渲染，src:', src)
  alert('🎥 VideoPlayer 渲染，src=' + src)
  console.log('🎥 [VideoPlayer] 参数:', { src, poster, subtitles: subtitles?.length, knowledgePoints: knowledgePoints?.length })
  const videoRef = useRef<HTMLVideoElement>(null)
  const playerRef = useRef<any>(null)
  const [currentSubtitle, setCurrentSubtitle] = useState<string>('')
  const [showSubtitles, setShowSubtitles] = useState(true)
  const [videoDuration, setVideoDuration] = useState<number>(0)
  const [error, setError] = useState<string>('')

  // 初始化 Video.js
  console.log('⚙️ [VideoPlayer] 开始初始化 Video.js')
  console.log('⚙️ [VideoPlayer] videoRef:', videoRef.current ? '存在' : '不存在')
  useEffect(() => {
    if (!videoRef.current) return

    // 清理旧实例
    if (playerRef.current) {
      playerRef.current.dispose()
      playerRef.current = null
    }

    try {
      // 初始化 Video.js
      playerRef.current = videojs(videoRef.current!, {
        autoplay: false,
        controls: true,
        responsive: true,
        fluid: true,
        poster,
        preload: 'auto',
        sources: [{
          src,
          type: 'video/mp4',
        }],
        html5: {
          hls: {
            enableLowInitialPlaylist: true,
            smoothQualityChange: true,
          },
        },
      })

      // 监听错误
      const handleError = () => {
        console.error('❌ [VideoPlayer] 视频播放错误')
        const error = playerRef.current.error()
        if (error) {
          setError(`视频加载失败：${error.message}`)
          console.error('Video.js error:', error)
        }
      }

      // 监听视频加载完成
      const handleLoadedMetadata = () => {
        const duration = playerRef.current.duration()
        setVideoDuration(duration)
        setError('')
        console.log('Video loaded, duration:', duration)
      }

      // 监听时间更新，显示对应字幕
      const handleTimeUpdate = () => {
        const currentTime = playerRef.current.currentTime()
        const subtitle = subtitles.find(
          (s) => currentTime >= s.start && currentTime <= s.end
        )
        setCurrentSubtitle(subtitle?.text || '')
      }

      playerRef.current.on('error', handleError)
      playerRef.current.on('loadedmetadata', handleLoadedMetadata)
      playerRef.current.on('timeupdate', handleTimeUpdate)

      return () => {
        if (playerRef.current) {
          playerRef.current.off('error', handleError)
          playerRef.current.off('loadedmetadata', handleLoadedMetadata)
          playerRef.current.off('timeupdate', handleTimeUpdate)
          playerRef.current.dispose()
          playerRef.current = null
        }
      }
    } catch (err) {
      console.error('Failed to initialize Video.js:', err)
      setError('播放器初始化失败')
    }
  }, [src, poster])

  // 跳转时间
  useEffect(() => {
    if (jumpToTime !== undefined && jumpToTime !== null && playerRef.current) {
      playerRef.current.currentTime(jumpToTime)
      playerRef.current.play().catch(err => {
        console.error('Failed to play after seek:', err)
      })
      if (onTimeJump) {
        onTimeJump()
      }
    }
  }, [jumpToTime, onTimeJump])

  // 跳转到知识点
  const jumpToKnowledgePoint = (timestamp: number) => {
    if (playerRef.current) {
      playerRef.current.currentTime(timestamp)
      playerRef.current.play().catch(err => {
        console.error('Failed to play after seek:', err)
      })
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

      {/* 视频播放器 */}
      <div ref={videoRef} className="w-full">
        <video
          className="video-js vjs-default-skin vjs-big-play-centered"
          preload="auto"
          poster={poster}
          controls
          playsInline
          data-setup='{}'
        >
          <source src={src} type="video/mp4" />
          <p className="vjs-no-js">
            要观看此视频，请启用 JavaScript 并考虑升级到支持 HTML5 视频的 Web 浏览器
          </p>
        </video>
      </div>

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
