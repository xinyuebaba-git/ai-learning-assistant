"""
搜索服务测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.search import SearchService


class TestSearchService:
    """搜索服务测试类"""

    def test_init(self):
        """测试初始化"""
        service = SearchService()
        assert service._client is None
        assert service._collection is None

    def test_get_embedding_function(self):
        """测试获取嵌入函数（mock）"""
        service = SearchService()
        
        # Mock chromadb
        with patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction") as mock_fn:
            mock_fn.return_value = Mock()
            fn = service._get_embedding_function()
            assert fn is not None

    def test_get_client(self):
        """测试获取客户端（mock）"""
        service = SearchService()
        
        with patch("chromadb.PersistentClient") as mock_client:
            client = service._get_client()
            assert client is not None

    @pytest.mark.asyncio
    async def test_add_embeddings(self):
        """测试添加向量嵌入"""
        service = SearchService()
        
        # Mock collection
        mock_collection = Mock()
        mock_collection.add = Mock()
        service._collection = mock_collection
        
        texts = ["文本 1", "文本 2"]
        metadatas = [
            {"type": "subtitle", "start": 0.0, "end": 2.0},
            {"type": "subtitle", "start": 2.5, "end": 4.5}
        ]
        
        await service.add_embeddings(
            video_id=1,
            texts=texts,
            metadatas=metadatas
        )
        
        # 验证调用
        assert mock_collection.add.called
        call_args = mock_collection.add.call_args
        assert len(call_args[1]["ids"]) == 2
        assert call_args[1]["documents"] == texts

    @pytest.mark.asyncio
    async def test_search(self):
        """测试搜索功能"""
        service = SearchService()
        
        # Mock collection
        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            "documents": [["匹配文本"]],
            "metadatas": [[{"video_id": "1", "type": "subtitle", "start": 10.0}]],
            "distances": [[0.5]]
        })
        service._collection = mock_collection
        
        # Mock video query
        with patch("app.services.search.async_session_maker") as mock_session:
            mock_video = Mock()
            mock_video.id = 1
            mock_video.title = "测试视频"
            mock_video.filename = "test.mp4"
            
            mock_result = Mock()
            mock_result.scalars.return_value.all.return_value = [mock_video]
            
            mock_session.return_value.__aenter__.return_value.execute.return_value = mock_result
            
            results = await service.search(query="测试", limit=10)
            
            assert len(results) > 0
            assert results[0]["video_id"] == 1
            assert results[0]["text"] == "匹配文本"
            assert results[0]["score"] > 0

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """测试无结果搜索"""
        service = SearchService()
        
        # Mock collection 返回空结果
        mock_collection = Mock()
        mock_collection.query = Mock(return_value={
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        })
        service._collection = mock_collection
        
        results = await service.search(query="无匹配内容", limit=10)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_delete_video_embeddings(self):
        """测试删除视频嵌入"""
        service = SearchService()
        
        # Mock collection
        mock_collection = Mock()
        mock_collection.get = Mock(return_value={"ids": ["video_1_0", "video_1_1"]})
        mock_collection.delete = Mock()
        service._collection = mock_collection
        
        await service.delete_video_embeddings(video_id=1)
        
        assert mock_collection.delete.called

    @pytest.mark.asyncio
    async def test_get_suggestions(self):
        """测试搜索建议"""
        service = SearchService()
        
        suggestions = await service.get_suggestions(query="测试", limit=5)
        assert isinstance(suggestions, list)


class TestSearchServiceIntegration:
    """搜索服务集成测试"""

    @pytest.mark.skip(reason="需要 ChromaDB 和嵌入模型，运行较慢")
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_search(self):
        """真实搜索测试（跳过）"""
        # 这个测试需要实际的 ChromaDB 和模型
        # 仅在需要时手动运行
        pass
