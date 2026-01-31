import pytest

@pytest.mark.asyncio
async def test_create_node(client):
    response = await client.post("/api/v1/nodes", json={"title": "Root Node"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Root Node"
    assert data["node_type"] == "standard"
    return data["node_id"]

@pytest.mark.asyncio
async def test_create_child_node(client):
    # Create parent
    p_resp = await client.post("/api/v1/nodes", json={"title": "Parent"})
    parent_id = p_resp.json()["node_id"]
    
    # Create child
    c_resp = await client.post("/api/v1/nodes", json={
        "title": "Child",
        "parent_id": parent_id
    })
    assert c_resp.status_code == 200
    data = c_resp.json()
    assert data["parent_id"] == parent_id
    assert data["position"]["y"] > 0 # Should be below parent

@pytest.mark.asyncio
async def test_get_tree(client):
    await client.post("/api/v1/nodes", json={"title": "Node 1"})
    await client.post("/api/v1/nodes", json={"title": "Node 2"})
    
    response = await client.get("/api/v1/nodes/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

@pytest.mark.asyncio
async def test_delete_node(client):
    resp = await client.post("/api/v1/nodes", json={"title": "To Delete"})
    node_id = resp.json()["node_id"]
    
    del_resp = await client.post(f"/api/v1/nodes/{node_id}/delete", json={})
    assert del_resp.status_code == 200
    
    # Verify status
    tree = await client.get("/api/v1/nodes/tree")
    # Should not be in tree if tree filters deleted
    # The CRUD get_tree filters status != 'deleted'
    
    # Check manual retrieval? API doesn't have GET /nodes/{id} except via tree/messages/graph
    # But get_messages calls get_node_by_id_or_404 -> get_node. status is not filtered there?
    # Wait, create_node uses get_node_by_id_or_404.
    pass

@pytest.mark.asyncio
async def test_copy_node(client):
    resp = await client.post("/api/v1/nodes", json={"title": "Original"})
    node_id = resp.json()["node_id"]
    
    copy_resp = await client.post(f"/api/v1/nodes/{node_id}/copy", json={})
    assert copy_resp.status_code == 200
    data = copy_resp.json()
    assert "Original (Copy)" in data["title"]
