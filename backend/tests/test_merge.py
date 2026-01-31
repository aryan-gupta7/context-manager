import pytest
from unittest.mock import patch, AsyncMock
import json
from services.llm_service import llm_service

@pytest.mark.asyncio
async def test_merge_flow(client):
    # 1. Create Target Node
    t_resp = await client.post("/api/v1/nodes", json={"title": "Target"})
    target_id = t_resp.json()["node_id"]

    # 2. Create Source Node (child of target)
    s_resp = await client.post("/api/v1/nodes", json={"title": "Source", "parent_id": target_id})
    source_id = s_resp.json()["node_id"]

    # 3. Mock LLM merge response
    mock_merge_data = {
        "updated_target_summary": {"FACTS": ["Merged Fact"]},
        "conflicts": []
    }
    
    with patch.object(llm_service, "merge", new_callable=AsyncMock) as mock_merge:
        mock_merge.return_value = json.dumps(mock_merge_data)
        
        # 4. Call Merge
        response = await client.post("/api/v1/nodes/merge", json={
            "source_node_id": source_id,
            "target_node_id": target_id
        })
        
        if response.status_code != 200:
            print(f"Merge Failed: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["source_node_status"] == "frozen"
        assert data["updated_summary"]["FACTS"] == ["Merged Fact"]
        
        # Verify Source is frozen logic (via API check helper?)
        # Currently no get_node API, but we can try to send message to frozen node
        msg_resp = await client.post(f"/api/v1/nodes/{source_id}/messages", json={"content": "test"})
        assert msg_resp.status_code == 400 # Node is not active
