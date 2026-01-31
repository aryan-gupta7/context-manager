import pytest
from unittest.mock import MagicMock, AsyncMock
from services.llm_service import llm_service
from config import settings

@pytest.mark.asyncio
async def test_routing():
    # Mock _get_client
    llm_service._get_client = MagicMock()
    mock_client = MagicMock()
    # Mock async behavior for chat called in executor
    # Since call wraps it in run_in_executor, we need to mock chat to return dict
    mock_client.chat.return_value = {"message": {"content": "mock response"}}
    llm_service._get_client.return_value = mock_client
    
    # Test chat (should use main-reasoner)
    await llm_service.chat("sys", "user")
    llm_service._get_client.assert_called_with(settings.MODEL_MAIN_REASONER)
    
    # Test graph (should use graph-builder)
    await llm_service.extract_graph("sys", "user")
    llm_service._get_client.assert_called_with(settings.MODEL_GRAPH_BUILDER)

@pytest.mark.asyncio
async def test_exploration_fallback():
    # Force NotImplementedError or Exception in exploration path
    # But wait, exploration_chat calls exploration first.
    # The implementation raises NotImplementedError immediately in try block.
    
    # Mock chat to return success so fallback works
    llm_service.chat = AsyncMock(return_value="Fallback Response")
    
    resp, source = await llm_service.exploration_chat("sys", "user")
    assert resp == "Fallback Response"
    assert source == "exploration"
