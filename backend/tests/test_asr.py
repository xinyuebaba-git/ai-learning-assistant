"""
ASR 服务测试
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.services.asr import ASRService, SubtitleEntry


class TestASRService:
    """ASR 服务测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        service = ASRService()
        assert service.engine == "faster-whisper"
        assert service.model == "medium"

    def test_init_custom(self):
        """测试自定义参数初始化"""
        service = ASRService(engine="whisper", model="small")
        assert service.engine == "whisper"
        assert service.model == "small"

    def test_subtitle_entry_creation(self):
        """测试字幕条目创建"""
        entry = SubtitleEntry(
            index=0,
            start=1.5,
            end=3.0,
            text="Hello World"
        )
        assert entry.index == 0
        assert entry.start == 1.5
        assert entry.end == 3.0
        assert entry.text == "Hello World"

    def test_format_timestamp(self):
        """测试时间戳格式化"""
        service = ASRService()
        
        # 测试各种时间格式
        assert service._format_timestamp(0.0) == "00:00:00,000"
        assert service._format_timestamp(1.5) == "00:00:01,500"
        assert service._format_timestamp(61.234) == "00:01:01,234"
        assert service._format_timestamp(3661.999) == "01:01:01,999"

    def test_save_srt(self, tmp_path):
        """测试 SRT 文件保存"""
        service = ASRService()
        output_path = tmp_path / "test.srt"
        
        entries = [
            SubtitleEntry(0, 0.0, 2.0, "First subtitle"),
            SubtitleEntry(1, 2.5, 4.5, "Second subtitle"),
        ]
        
        service.save_srt(entries, str(output_path))
        
        # 验证文件存在
        assert output_path.exists()
        
        # 验证内容
        content = output_path.read_text(encoding="utf-8")
        assert "1" in content
        assert "00:00:00,000 --> 00:00:02,000" in content
        assert "First subtitle" in content
        assert "2" in content
        assert "Second subtitle" in content

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self):
        """测试文件不存在的情况"""
        service = ASRService()
        
        with pytest.raises(FileNotFoundError):
            await service.transcribe("/nonexistent/video.mp4")

    @pytest.mark.asyncio
    async def test_transcribe_with_mock(self):
        """测试转录功能（使用 mock）"""
        service = ASRService()
        
        # Mock faster-whisper 模型
        mock_model = Mock()
        mock_info = Mock(duration=10.0)
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Test transcription"
        
        mock_model.transcribe.return_value = (
            iter([mock_segment]),
            mock_info
        )
        
        service._model_instance = mock_model
        
        # 创建临时文件
        with patch("pathlib.Path.exists", return_value=True):
            entries = await service.transcribe("/fake/video.mp4")
        
        assert len(entries) == 1
        assert entries[0].text == "Test transcription"
        assert entries[0].start == 0.0
        assert entries[0].end == 2.0


class TestASRServiceIntegration:
    """ASR 服务集成测试（需要实际模型）"""

    @pytest.mark.skip(reason="需要实际模型文件，运行较慢")
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_transcription(self):
        """真实转录测试（跳过）"""
        # 这个测试需要实际的模型文件和视频文件
        # 仅在需要时手动运行
        pass
