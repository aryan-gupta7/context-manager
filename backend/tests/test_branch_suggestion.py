import pytest
import json

@pytest.mark.asyncio
async def test_send_message_with_branch_suggestion(client):
    """Test that send_message returns branch suggestion field in response."""
    # Create a node first
    node_resp = await client.post("/api/v1/nodes", json={"title": "Test Node"})
    node_id = node_resp.json()["node_id"]
    
    # Send a message - the branch_suggestion field should be present
    # (it will be null unless the LLM judge is available and triggers)
    msg_resp = await client.post(f"/api/v1/nodes/{node_id}/messages", json={
        "content": "What are the trade-offs between these approaches?"
    })
    
    assert msg_resp.status_code == 200
    data = msg_resp.json()
    
    # Verify response structure includes branch_suggestion field
    assert "branch_suggestion" in data
    # branch_suggestion may be null if judge doesn't suggest branching or isn't available


@pytest.mark.asyncio
async def test_auto_branch_creates_nodes(client):
    """Test that auto-branch endpoint creates multiple child nodes."""
    # Create parent node
    parent_resp = await client.post("/api/v1/nodes", json={"title": "Parent Node"})
    parent_id = parent_resp.json()["node_id"]
    
    # Call auto-branch
    branches = [
        {"title": "Branch A", "focus": "Explore option A in detail"},
        {"title": "Branch B", "focus": "Explore option B in detail"}
    ]
    
    branch_resp = await client.post(f"/api/v1/nodes/{parent_id}/auto-branch", json={
        "branches": branches
    })
    
    assert branch_resp.status_code == 200
    data = branch_resp.json()
    
    assert data["parent_node_id"] == parent_id
    assert len(data["created_nodes"]) == 2
    
    # Verify each created node
    for i, node in enumerate(data["created_nodes"]):
        assert node["title"] == branches[i]["title"]
        assert node["parent_id"] == parent_id
        assert node["status"] == "active"


@pytest.mark.asyncio
async def test_auto_branch_fails_on_frozen_node(client):
    """Test that auto-branch fails on non-active nodes."""
    # Create and delete a node (making it non-active)
    node_resp = await client.post("/api/v1/nodes", json={"title": "To Delete"})
    node_id = node_resp.json()["node_id"]
    
    # Delete the node
    await client.post(f"/api/v1/nodes/{node_id}/delete", json={})
    
    # Try to auto-branch
    branch_resp = await client.post(f"/api/v1/nodes/{node_id}/auto-branch", json={
        "branches": [{"title": "Branch A", "focus": "Test"}]
    })
    
    assert branch_resp.status_code == 400


@pytest.mark.asyncio 
async def test_auto_branch_empty_branches(client):
    """Test auto-branch with empty branches list."""
    node_resp = await client.post("/api/v1/nodes", json={"title": "Parent"})
    node_id = node_resp.json()["node_id"]
    
    branch_resp = await client.post(f"/api/v1/nodes/{node_id}/auto-branch", json={
        "branches": []
    })
    
    assert branch_resp.status_code == 200
    data = branch_resp.json()
    assert len(data["created_nodes"]) == 0
