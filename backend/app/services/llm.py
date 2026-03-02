"""
LLM 服务 - 大模型调用

支持本地 Ollama 和云端 API (DeepSeek/OpenAI)
负责内容总结和知识点提取
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from ..core.config import settings


class LLMService:
    """大模型服务"""
    
    def __init__(
        self,
        backend: str = None,
        model: str = None,
    ):
        self.backend = backend or settings.DEFAULT_LLM_BACKEND
        self.model = model or self._get_default_model()
        self._client = None
    
    def _get_default_model(self) -> str:
        """根据后端获取默认模型"""
        if self.backend == "local":
            return settings.OLLAMA_MODEL
        elif self.backend == "deepseek":
            return settings.DEEPSEEK_MODEL
        elif self.backend == "openai":
            return settings.OPENAI_MODEL
        elif self.backend == "alibaba":
            return settings.ALIBABA_MODEL
        else:
            return settings.OLLAMA_MODEL
    
    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            if self.backend == "local":
                try:
                    import ollama
                    self._client = ollama.Client(host=settings.OLLAMA_BASE_URL)
                    logger.info(f"✅ Ollama 客户端已连接：{settings.OLLAMA_BASE_URL}")
                except ImportError:
                    logger.error("未安装 ollama，请运行：pip install ollama")
                    raise
            else:
                try:
                    from openai import OpenAI
                    
                    if self.backend == "deepseek":
                        api_key = settings.DEEPSEEK_API_KEY
                        base_url = settings.DEEPSEEK_BASE_URL
                    elif self.backend == "openai":
                        api_key = settings.OPENAI_API_KEY
                        base_url = settings.OPENAI_BASE_URL
                    elif self.backend == "alibaba":
                        api_key = settings.ALIBABA_API_KEY
                        base_url = settings.ALIBABA_BASE_URL
                    else:
                        raise ValueError(f"未知的 LLM 后端：{self.backend}")
                    
                    if not api_key:
                        raise ValueError(f"{self.backend.upper()} API Key 未配置")
                    
                    self._client = OpenAI(api_key=api_key, base_url=base_url)
                    logger.info(f"✅ {self.backend.upper()} 客户端已初始化：{base_url}")
                except ImportError:
                    logger.error("未安装 openai，请运行：pip install openai")
                    raise
        
        return self._client
    
    async def summarize(
        self,
        subtitle_text: str,
        video_title: str = "",
    ) -> Dict[str, Any]:
        """
        生成视频内容总结
        
        Args:
            subtitle_text: 字幕文本
            video_title: 视频标题
        
        Returns:
            {
                "summary": str,  # 完整总结
                "knowledge_points": List[Dict],  # 知识点列表
                "token_count": int,  # 消耗的 token 数
            }
        """
        client = self._get_client()
        
        # 构建提示词
        system_prompt = """你是一个专业的课程内容分析助手。你的任务是：
1. 总结视频的核心内容（300-500 字）
2. 提取关键知识点，包括知识点名称、描述、对应的时间点
3. 知识点类型包括：concept(概念), formula(公式), example(示例), key_point(重点)

请以 JSON 格式返回，结构如下：
{
    "summary": "完整的课程总结...",
    "knowledge_points": [
        {
            "timestamp": 120.5,
            "title": "知识点名称",
            "description": "详细描述",
            "type": "concept"
        }
    ]
}

注意：
- 知识点的时间点需要根据字幕内容推断
- 只返回 JSON，不要有其他内容
- 知识点数量控制在 10-20 个之间"""

        user_prompt = f"""视频标题：{video_title}

字幕内容：
{subtitle_text[:15000]}  # 限制长度避免超出上下文

请分析并总结这个视频的内容。"""

        logger.info(f"开始生成总结，模型：{self.model}, backend: {self.backend}")
        
        if self.backend == "local":
            # Ollama 调用
            response = await asyncio.to_thread(
                client.chat,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                format="json",  # JSON 模式
            )
            result_text = response["message"]["content"]
            token_count = response.get("prompt_eval_count", 0) + response.get("eval_count", 0)
        else:
            # OpenAI / DeepSeek 调用
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            result_text = response.choices[0].message.content
            token_count = response.usage.total_tokens
        
        # 解析 JSON
        try:
            result = json.loads(result_text)
            logger.info(f"✅ 总结生成完成，知识点数量：{len(result.get('knowledge_points', []))}")
            
            return {
                "summary": result.get("summary", ""),
                "knowledge_points": result.get("knowledge_points", []),
                "token_count": token_count,
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{e}")
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "summary": result.get("summary", ""),
                    "knowledge_points": result.get("knowledge_points", []),
                    "token_count": token_count,
                }
            raise
    
    async def answer_question(
        self,
        question: str,
        context: str,
    ) -> str:
        """
        基于上下文回答问题
        
        Args:
            question: 用户问题
            context: 相关上下文（字幕片段或总结）
        
        Returns:
            回答文本
        """
        client = self._get_client()
        
        system_prompt = """你是一个学习助手。根据提供的课程内容上下文，回答用户的问题。
- 回答要准确、简洁
- 如果上下文中没有相关信息，请说明
- 可以适当引用上下文中的内容"""

        user_prompt = f"""上下文：
{context}

问题：{question}

请回答："""

        if self.backend == "local":
            response = await asyncio.to_thread(
                client.chat,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response["message"]["content"]
        else:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return response.choices[0].message.content


# 全局实例
_llm_service: Optional[LLMService] = None


def get_llm_service(backend: str = None, model: str = None) -> LLMService:
    """获取 LLM 服务实例"""
    global _llm_service
    if _llm_service is None or backend is not None:
        _llm_service = LLMService(backend=backend, model=model)
    return _llm_service
