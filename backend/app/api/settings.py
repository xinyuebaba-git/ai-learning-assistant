from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
from pathlib import Path

from ..db.base import get_db
from ..models.user import User
from ..api.auth import get_current_user_dependency


router = APIRouter()


class Settings(BaseModel):
    """系统设置"""
    asr_engine: str = "faster-whisper"
    asr_model: str = "medium"
    deepgram_api_key: Optional[str] = None
    llm_backend: str = "local"
    llm_model: str = "qwen3.5"
    ollama_base_url: str = "http://localhost:11434"
    deepseek_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    alibaba_api_key: Optional[str] = None
    alibaba_base_url: str = "https://coding.dashscope.aliyuncs.com/v1"
    max_segment_duration: float = 2.2
    max_segment_chars: int = 28
    
    class Config:
        from_attributes = True


CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "settings.json"


@router.get("", response_model=Settings)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """获取系统设置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Settings(**data)
        except Exception as e:
            print(f"读取配置失败：{e}")
    
    # 返回默认设置
    return Settings()


@router.post("", response_model=Settings)
async def save_settings(
    settings: Settings,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """保存系统设置"""
    # 确保配置目录存在
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存配置到文件
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False)
    
    return settings


@router.post("/test-ollama")
async def test_ollama_connection(
    settings: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """测试 Ollama 连接"""
    import httpx
    
    base_url = settings.get('ollama_base_url', 'http://localhost:11434')
    model = settings.get('llm_model', 'qwen2.5:7b')
    
    try:
        async with httpx.AsyncClient() as client:
            # 测试连接
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]
                
                # 检查指定模型是否存在
                model_exists = any(model in m for m in models)
                
                return {
                    "success": True,
                    "message": "Ollama 连接成功",
                    "models": models,
                    "model_exists": model_exists,
                }
            else:
                return {
                    "success": False,
                    "message": f"Ollama 响应异常：{response.status_code}",
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败：{str(e)}",
        }
