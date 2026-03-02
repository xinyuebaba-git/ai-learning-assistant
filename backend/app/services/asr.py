"""
ASR 服务 - 复用 subgen 核心功能

负责调用 Whisper/Faster-Whisper 进行语音识别
"""
import asyncio
from pathlib import Path
from typing import Callable, Optional, List
from loguru import logger

from ..core.config import settings


class SubtitleEntry:
    """字幕条目"""
    def __init__(self, index: int, start: float, end: float, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text


class ASRService:
    """ASR 语音识别服务"""
    
    def __init__(
        self,
        engine: str = None,
        model: str = None,
    ):
        self.engine = engine or settings.ASR_ENGINE
        self.model = model or settings.ASR_MODEL
        self._model_instance = None
    
    def load_model(self):
        """加载 ASR 模型"""
        if self._model_instance is not None:
            return
        
        logger.info(f"加载 ASR 模型：engine={self.engine}, model={self.model}")
        
        if self.engine == "faster-whisper":
            try:
                from faster_whisper import WhisperModel
                self._model_instance = WhisperModel(
                    self.model,
                    device="cpu",  # 或 "cuda"
                    compute_type="int8",
                )
                logger.info("✅ Faster-Whisper 模型加载完成")
            except ImportError:
                logger.error("未安装 faster-whisper，请运行：pip install faster-whisper")
                raise
        elif self.engine == "whisper":
            try:
                import whisper
                self._model_instance = whisper.load_model(self.model)
                logger.info("✅ Whisper 模型加载完成")
            except ImportError:
                logger.error("未安装 whisper，请运行：pip install openai-whisper")
                raise
        else:
            raise ValueError(f"不支持的 ASR 引擎：{self.engine}")
    
    async def transcribe(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[SubtitleEntry]:
        """
        转录视频音频为字幕
        
        Args:
            video_path: 视频文件路径
            progress_callback: 进度回调函数 (0.0-1.0)
        
        Returns:
            字幕条目列表
        """
        if self._model_instance is None:
            self.load_model()
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在：{video_path}")
        
        logger.info(f"开始转录：{video_path.name}")
        
        return await asyncio.to_thread(
            self._transcribe_sync,
            str(video_path),
            progress_callback
        )
    
    def _transcribe_sync(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[SubtitleEntry]:
        """同步转录实现"""
        entries = []
        
        if self.engine == "faster-whisper":
            # 使用 faster-whisper
            segments, info = self._model_instance.transcribe(
                video_path,
                language=None,  # 自动检测
                vad_filter=True,  # 语音活动检测
            )
            
            for segment in segments:
                entry = SubtitleEntry(
                    index=len(entries),
                    start=segment.start,
                    end=segment.end,
                    text=segment.text.strip(),
                )
                entries.append(entry)
                
                if progress_callback:
                    progress_callback(segment.end / info.duration if info.duration > 0 else 0)
        
        elif self.engine == "whisper":
            # 使用 whisper
            result = self._model_instance.transcribe(video_path)
            
            for i, segment in enumerate(result["segments"]):
                entry = SubtitleEntry(
                    index=i,
                    start=segment["start"],
                    end=segment["end"],
                    text=segment["text"].strip(),
                )
                entries.append(entry)
                
                if progress_callback:
                    progress_callback(segment["end"] / result.get("duration", 1))
        
        elif self.engine == "deepgram":
            # 使用 Deepgram API
            entries = self._transcribe_with_deepgram(video_path, progress_callback)
        
        logger.info(f"转录完成，生成 {len(entries)} 条字幕")
        return entries
    
    def _transcribe_with_deepgram(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> List[SubtitleEntry]:
        """使用 Deepgram API 进行转录"""
        import urllib.request as urlrequest
        import urllib.error as urlerror
        import urllib.parse as urlparse
        import json
        from pathlib import Path
        from ..core.config import settings
        
        # 获取 API Key
        api_key = settings.DEEPGRAM_API_KEY
        if not api_key:
            raise RuntimeError("Deepgram API Key 未配置，请在设置页面或环境变量中配置 DEEPGRAM_API_KEY")
        
        model_name = getattr(settings, 'DEEPGRAM_MODEL', 'nova-3')
        
        # 读取音频文件
        video_path = Path(video_path)
        audio_bytes = video_path.read_bytes()
        
        # 构建请求参数
        params = {
            "model": model_name or "nova-3",
            "smart_format": "true",
            "punctuate": "true",
            "utterances": "true",
            "diarize": "false",
            "language": "zh-CN",  # 默认中文，可改为自动检测
        }
        
        url = "https://api.deepgram.com/v1/listen?" + urlparse.urlencode(params)
        
        # 构建请求
        req = urlrequest.Request(
            url,
            data=audio_bytes,
            headers={
                "Authorization": f"Token {api_key.strip()}",
                "Content-Type": "application/octet-stream",
                "Accept": "application/json",
            },
            method="POST",
        )
        
        if progress_callback:
            progress_callback(0.0)
        
        try:
            # 发送请求
            with urlrequest.urlopen(req, timeout=600) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        except urlerror.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            raise RuntimeError(f"Deepgram 请求失败：HTTP {exc.code} {body[:240]}") from exc
        except Exception as exc:
            raise RuntimeError(f"Deepgram 请求失败：{exc}") from exc
        
        # 解析结果
        channels = payload.get("results", {}).get("channels", [])
        alt = {}
        if channels and isinstance(channels[0], dict):
            alts = channels[0].get("alternatives", [])
            if alts and isinstance(alts[0], dict):
                alt = alts[0]
        
        # 获取字幕条目
        entries = []
        words_raw = alt.get("words", []) if isinstance(alt, dict) else []
        
        # 将单词组合成字幕片段（简单实现，按时间分组）
        current_start = None
        current_end = None
        current_text = []
        
        for i, w in enumerate(words_raw if isinstance(words_raw, list) else []):
            if not isinstance(w, dict):
                continue
            
            start = w.get("start", 0)
            end = w.get("end", 0)
            word = w.get("word", "")
            
            if current_start is None:
                current_start = start
                current_end = end
                current_text = [word]
            else:
                # 如果间隔小于 0.5 秒，合并到当前片段
                if start - current_end < 0.5:
                    current_text.append(word)
                    current_end = end
                else:
                    # 保存当前片段
                    if current_text:
                        entries.append(SubtitleEntry(
                            index=len(entries),
                            start=current_start,
                            end=current_end,
                            text=" ".join(current_text).strip(),
                        ))
                    # 开始新片段
                    current_start = start
                    current_end = end
                    current_text = [word]
        
        # 保存最后一个片段
        if current_text:
            entries.append(SubtitleEntry(
                index=len(entries),
                start=current_start,
                end=current_end,
                text=" ".join(current_text).strip(),
            ))
        
        if progress_callback:
            progress_callback(1.0)
        
        return entries
    
    def save_srt(self, entries: List[SubtitleEntry], output_path: str):
        """保存为 SRT 格式"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(f"{entry.index + 1}\n")
                f.write(self._format_timestamp(entry.start) + " --> " + self._format_timestamp(entry.end) + "\n")
                f.write(entry.text + "\n\n")
        
        logger.info(f"SRT 字幕已保存：{output_path}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """将秒数转换为 SRT 时间戳格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# 全局实例
_asr_service: Optional[ASRService] = None


def get_asr_service() -> ASRService:
    """获取 ASR 服务实例"""
    global _asr_service
    if _asr_service is None:
        _asr_service = ASRService()
    return _asr_service
