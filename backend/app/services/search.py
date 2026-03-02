"""
搜索服务 - 向量语义搜索

使用 ChromaDB 存储和检索向量嵌入
"""
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from ..core.config import settings


class SearchService:
    """向量搜索服务"""
    
    def __init__(self):
        self._client = None
        self._collection = None
        self._embedding_function = None
    
    def _get_embedding_function(self):
        """获取嵌入模型"""
        if self._embedding_function is None:
            try:
                from chromadb.utils import embedding_functions
                
                # 使用 Sentence Transformers 嵌入模型
                self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.EMBEDDING_MODEL
                )
                logger.info(f"✅ 嵌入模型已加载：{settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"嵌入模型加载失败：{e}")
                raise
        return self._embedding_function
    
    def _get_client(self):
        """获取 ChromaDB 客户端"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                
                chroma_path = Path(settings.CHROMA_PERSIST_DIR)
                chroma_path.mkdir(parents=True, exist_ok=True)
                
                self._client = chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=Settings(anonymized_telemetry=False),
                )
                logger.info(f"✅ ChromaDB 已初始化：{chroma_path}")
            except ImportError:
                logger.error("未安装 chromadb，请运行：pip install chromadb")
                raise
        return self._client
    
    def _get_collection(self):
        """获取或创建集合"""
        if self._collection is None:
            client = self._get_client()
            embedding_fn = self._get_embedding_function()
            
            try:
                self._collection = client.get_collection(
                    name="course_subtitles",
                    embedding_function=embedding_fn,
                )
                logger.info("✅ 已加载 ChromaDB 集合")
            except Exception:
                # 集合不存在，创建它
                self._collection = client.create_collection(
                    name="course_subtitles",
                    embedding_function=embedding_fn,
                    metadata={"description": "课程视频字幕和总结的向量索引"},
                )
                logger.info("✅ 已创建 ChromaDB 集合")
        
        return self._collection
    
    async def add_embeddings(
        self,
        video_id: int,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ):
        """
        添加向量嵌入
        
        Args:
            video_id: 视频 ID
            texts: 文本列表（字幕片段或总结）
            metadatas: 元数据列表，每个包含：
                - type: subtitle/summary/knowledge_point
                - start: 开始时间（对于字幕）
                - end: 结束时间（对于字幕）
        """
        collection = self._get_collection()
        
        # 生成 IDs
        ids = [f"video_{video_id}_{i}" for i in range(len(texts))]
        
        # 添加视频 ID 到元数据
        for metadata in metadatas:
            metadata["video_id"] = str(video_id)
        
        # 异步添加到 ChromaDB
        await asyncio.to_thread(
            collection.add,
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )
        
        logger.info(f"✅ 已添加 {len(texts)} 个向量嵌入，视频 ID: {video_id}")
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        search_type: str = "all",
    ) -> List[Dict[str, Any]]:
        """
        语义搜索
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量
            search_type: all/subtitle/summary
        
        Returns:
            搜索结果列表
        """
        collection = self._get_collection()
        
        # 构建过滤条件
        where = None
        if search_type != "all":
            where = {"type": search_type}
        
        # 查询
        results = await asyncio.to_thread(
            collection.query,
            query_texts=[query],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        # 处理结果
        search_results = []
        
        if results and results["documents"] and results["documents"][0]:
            from ..db.base import async_session_maker
            from sqlalchemy import select
            from ..models.video import Video
            
            # 获取视频信息
            async with async_session_maker() as session:
                video_ids = set()
                for metadata_list in results["metadatas"][0]:
                    if metadata_list and "video_id" in metadata_list:
                        video_ids.add(int(metadata_list["video_id"]))
                
                video_map = {}
                result = await session.execute(
                    select(Video).where(Video.id.in_(video_ids))
                )
                for video in result.scalars().all():
                    video_map[video.id] = video
            
            # 构建搜索结果
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )):
                if metadata and "video_id" in metadata:
                    video_id = int(metadata["video_id"])
                    video = video_map.get(video_id)
                    
                    if video:
                        # 将距离转换为相似度分数（0-1）
                        score = 1.0 / (1.0 + distance) if distance else 1.0
                        
                        search_results.append({
                            "video_id": video_id,
                            "video_title": video.title or video.filename,
                            "video_filename": video.filename,
                            "text": doc,
                            "text_type": metadata.get("type", "subtitle"),
                            "timestamp": metadata.get("start"),
                            "score": round(score, 4),
                        })
        
        # 按分数排序
        search_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"🔍 搜索完成，查询：'{query}', 结果数：{len(search_results)}")
        
        return search_results
    
    async def get_suggestions(
        self,
        query: str,
        limit: int = 5,
    ) -> List[str]:
        """获取搜索建议（基于热门搜索或关键词）"""
        # 简单实现：返回空列表
        # 可以扩展为基于历史搜索或关键词提取
        return []
    
    async def delete_video_embeddings(self, video_id: int):
        """删除指定视频的所有向量嵌入"""
        collection = self._get_collection()
        
        # 查询该视频的所有嵌入 ID
        results = await asyncio.to_thread(
            collection.get,
            where={"video_id": str(video_id)},
            include=[],
        )
        
        if results and results["ids"]:
            await asyncio.to_thread(
                collection.delete,
                ids=results["ids"],
            )
            logger.info(f"✅ 已删除视频 {video_id} 的 {len(results['ids'])} 个向量嵌入")


# 全局实例
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """获取搜索服务实例"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
