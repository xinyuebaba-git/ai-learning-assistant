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
  description: string
  type: string
}

interface VideoPlayerProps {
  src: string
  poster?: string
  subtitles?: Subtitle[]
  knowledgePoints?: KnowledgePoint[]
}

export default function VideoPlayer({
  src,
  poster = '',
  subtitles = [],
  knowledgePoints = [],
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLDivElement>(null)
  const playerRef = useRef<any>(null)
  const [currentSubtitle, setCurrentSubtitle] = useState<string>('')
  const [showSubtitles, setShowSubtitles] = useState(true)

  useEffect(() => {
    if (!videoRef.current) return

    // 初始化 Video.js
    playerRef.current = videojs(videoRef.current, {
      autoplay: false,
      controls: true,
      responsive: true,
      fluid: true,
      poster,
      sources: [{
        src,
        type: 'video/mp4',
      }],
    })

    // 监听时间更新，显示对应字幕
    const handleTimeUpdate = () => {
      const currentTime = playerRef.current.currentTime()
      const subtitle = subtitles.find(
        (s) => currentTime >= s.start && currentTime <= s.end
      )
      setCurrentSubtitle(subtitle?.text || '')
    }

    playerRef.current.on('timeupdate', handleTimeUpdate)

    return () => {
      if (playerRef.current) {
        playerRef.current.off('timeupdate', handleTimeUpdate)
        playerRef.current.dispose()
      }
    }
  }, [src, poster, subtitles])

  // 跳转到知识点
  const jumpToKnowledgePoint = (timestamp: number) => {
    if (playerRef.current) {
      playerRef.current.currentTime(timestamp)
      playerRef.current.play()
    }
  }

  return (
    <div className="relative">
      {/* 视频播放器 */}
      <div data-vjs-player className="w-full">
        <div ref={videoRef} className="video-js vjs-default-skin" />
      </div>

      {/* 知识点标记（在进度条上方） */}
      {knowledgePoints.length > 0 && (
        <div className="absolute bottom-20 left-0 right-0 px-4 flex justify-between pointer-events-none">
          {knowledgePoints.map((kp, index) => (
            <div
              key={index}
              className="knowledge-point-marker pointer-events-auto"
              style={{
                left: `${(kp.timestamp / (playerRef.current?.duration() || 1)) * 100}%`,
              }}
              onClick={() => jumpToKnowledgePoint(kp.timestamp)}
              title={kp.title}
            />
          ))}
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
        className="absolute top-4 right-4 px-3 py-1 bg-black bg-opacity-50 text-white rounded text-sm hover:bg-opacity-75"
      >
        {showSubtitles ? '字幕：开' : '字幕：关'}
      </button>
    </div>
  )
}
