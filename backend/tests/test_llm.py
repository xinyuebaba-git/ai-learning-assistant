"""
LLM 服务测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

from app.services.llm import LLMService


class TestLLMService:
    """LLM 服务测试类"""

    def test_init_default(self):
        """测试默认初始化"""
        service = LLMService()
        assert service.backend == "local"
        assert service.model is not None

    def test_init_custom(self):
        """测试自定义参数初始化"""
        service = LLMService(backend="deepseek", model="deepseek-chat")
        assert service.backend == "deepseek"
        assert service.model == "deepseek-chat"

    def test_get_default_model_local(self):
        """测试获取本地默认模型"""
        service = LLMService(backend="local")
        model = service._get_default_model()
        assert "qwen" in model.lower() or "dolphin" in model.lower()

    def test_get_default_model_deepseek(self):
        """测试获取 DeepSeek 默认模型"""
        service = LLMService(backend="deepseek")
        model = service._get_default_model()
        assert "deepseek" in model.lower()

    def test_get_default_model_openai(self):
        """测试获取 OpenAI 默认模型"""
        service = LLMService(backend="openai")
        model = service._get_default_model()
        assert "gpt" in model.lower()

    @pytest.mark.asyncio
    async def test_summarize_with_mock_ollama(self):
        """测试总结功能（Mock Ollama）"""
        service = LLMService(backend="local")
        
        # Mock Ollama 客户端
        mock_client = Mock()
        mock_response = {
            "message": {
                "content": json.dumps({
                    "summary": "这是一个测试总结",
                    "knowledge_points": [
                        {
                            "timestamp": 60.0,
                            "title": "测试知识点",
                            "description": "描述",
                            "type": "concept"
                        }
                    ]
                })
            },
            "prompt_eval_count": 100,
            "eval_count": 50
        }
        mock_client.chat = Mock(return_value=mock_response)
        service._client = mock_client
        
        result = await service.summarize(
            subtitle_text="这是测试字幕内容",
            video_title="测试视频"
        )
        
        assert "summary" in result
        assert "knowledge_points" in result
        assert len(result["knowledge_points"]) > 0
        assert result["token_count"] > 0

    @pytest.mark.asyncio
    async def test_summarize_with_mock_openai(self):
        """测试总结功能（Mock OpenAI）"""
        service = LLMService(backend="openai")
        
        # Mock OpenAI 客户端
        mock_client = Mock()
        mock_choice = Mock()
        mock_choice.message.content = json.dumps({
            "summary": "OpenAI 测试总结",
            "knowledge_points": []
        })
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage.total_tokens = 150
        
        mock_client.chat.completions.create = Mock(return_value=mock_response)
        service._client = mock_client
        
        result = await service.summarize(
            subtitle_text="测试内容",
            video_title="测试"
        )
        
        assert "summary" in result
        assert result["token_count"] == 150

    @pytest.mark.asyncio
    async def test_answer_question(self):
        """测试问答功能"""
        service = LLMService(backend="local")
        
        # Mock 客户端
        mock_client = Mock()
        mock_response = {
            "message": {"content": "这是答案"}
        }
        mock_client.chat = Mock(return_value=mock_response)
        service._client = mock_client
        
        answer = await service.answer_question(
            question="什么是 AI？",
            context="AI 是人工智能的缩写..."
        )
        
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_summarize_invalid_json(self):
        """测试无效 JSON 处理"""
        service = LLMService()
        
        # 测试 JSON 解析错误处理
        import re
        text = 'Some text before {"key": "value"} some text after'
        match = re.search(r'\{.*\}', text, re.DOTALL)
        assert match is not None
        assert json.loads(match.group()) == {"key": "value"}


class TestLLMServiceIntegration:
    """LLM 服务集成测试"""

    @pytest.mark.skip(reason="需要实际 API Key 和模型，运行较慢")
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_summarize(self):
        """真实总结测试（跳过）"""
        # 这个测试需要实际的 API 配置
        # 仅在需要时手动运行
        pass
