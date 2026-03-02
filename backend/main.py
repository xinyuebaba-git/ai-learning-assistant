from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import asyncio

from app.core.config import settings as app_settings
from app.db import init_db, close_db
from app.api import auth, videos, search, notes, settings as settings_router


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    
    app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        description="AI 课程学习辅助系统 - 基于 subgen 核心能力",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境需要限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
    app.include_router(videos.router, prefix="/api/videos", tags=["视频管理"])
    app.include_router(search.router, prefix="/api/search", tags=["搜索"])
    app.include_router(notes.router, prefix="/api/notes", tags=["笔记"])
    app.include_router(settings_router.router, prefix="/api/settings", tags=["系统设置"])
    
    # 生命周期事件
    @app.on_event("startup")
    async def startup():
        logger.info(f"🚀 启动 {app_settings.APP_NAME} v{app_settings.APP_VERSION}")
        logger.info(f"📁 数据目录：{app_settings.DATA_DIR}")
        logger.info(f"🧠 LLM 后端：{app_settings.DEFAULT_LLM_BACKEND}")
        logger.info(f"🎤 ASR 引擎：{app_settings.ASR_ENGINE}")
        
        # 初始化数据库
        await init_db()
        logger.info("✅ 数据库初始化完成")
    
    @app.on_event("shutdown")
    async def shutdown():
        logger.info("👋 正在关闭应用...")
        await close_db()
        logger.info("✅ 应用已关闭")
    
    @app.get("/")
    async def root():
        return {
            "name": app_settings.APP_NAME,
            "version": app_settings.APP_VERSION,
            "docs": "/docs",
            "status": "running",
        }
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=app_settings.HOST,
        port=app_settings.PORT,
        reload=app_settings.DEBUG,
    )
