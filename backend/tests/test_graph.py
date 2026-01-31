import pytest
from unittest.mock import patch, AsyncMock
import json
from services.llm_service import llm_service

@pytest.mark.asyncio
async def test_summarize_and_graph(client):
    # Create Node
    resp = await client.post("/api/v1/nodes", json={"title": "Graph Node"})
    node_id = resp.json()["node_id"]
    
    # Mock LLM calls
    mock_summary = {"FACTS": ["Fact 1"]}
    mock_graph = {
        "entities": ["A", "B"],
        "relations": [
            {"from_entity": "A", "to_entity": "B", "relation_type": "USES", "confidence": 0.9}
        ]
    }
    
    with patch.object(llm_service, "summarize", new_callable=AsyncMock) as mock_sum, \
         patch.object(llm_service, "extract_graph", new_callable=AsyncMock) as mock_graph_call:
        
        mock_sum.return_value = json.dumps(mock_summary)
        mock_graph_call.return_value = json.dumps(mock_graph)
        
        sum_resp = await client.post(f"/api/v1/nodes/{node_id}/summarize")
        if sum_resp.status_code != 200:
            print(f"Summarize Failed: {sum_resp.text}")
        assert sum_resp.status_code == 200
        data = sum_resp.json()
        
        assert data["graph_extraction_status"] == "success"
        
        # Verify Graph API
        g_resp = await client.get(f"/api/v1/nodes/{node_id}/graph")
        g_data = g_resp.json()
        assert len(g_data["entities"]) == 2
        assert len(g_data["relations"]) == 1
        assert g_data["relations"][0]["from_entity"] == "A"
