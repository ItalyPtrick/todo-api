# ===== POST /todos/ =====
def test_create_todo(client):
    # 测试创建一个Todo任务
    response = client.post(
        "/todos/",
        json={
            "title": "学习 pytest",
            "priority": 2,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "学习 pytest"
    assert data["completed"] == False
    assert data["priority"] == 2
    assert "id" in data  # 确保返回了 id 字段
    assert "created_at" in data  # 确保返回了 created_at 字段


# ===== GET /todos/ =====
def test_get_todos_empty(client):
    # 测试获取任务列表，初始应该是空的
    response = client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_todos(client):
    """创建两条后能查到两条"""
    client.post("/todos/", json={"title": "任务一", "priority": 1})
    client.post("/todos/", json={"title": "任务二", "priority": 2})

    response = client.get("/todos/")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ===== GET /todos/{id} =====
def test_get_todo(client):
    """创建后能按 id 查到"""
    created = client.post("/todos/", json={"title": "单条测试", "priority": 1}).json()

    response = client.get(f"/todos/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "单条测试"


def test_get_todo_not_found(client):
    """查不存在的 id 应该 404"""
    response = client.get("/todos/999")
    assert response.status_code == 404


# ==== GET /todos/stats =====
def test_get_stats(client):
    """测试统计接口,创建3条任务，1条已完成，2条未完成"""
    client.post("/todos/", json={"title": "统计测试1", "priority": 1})
    client.post(
        "/todos/", json={"title": "统计测试2", "priority": 2, "completed": True}
    )
    client.post(
        "/todos/", json={"title": "统计测试3", "priority": 3, "completed": False}
    )

    response = client.get("/todos/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["completed"] == 1
    assert data["uncompleted"] == 2


# ===== PUT /todos/{id} =====
def test_update_todo(client):
    """更新标题和完成状态"""
    created = client.post("/todos/", json={"title": "旧标题", "priority": 1}).json()

    response = client.put(
        f"/todos/{created['id']}", json={"title": "新标题", "completed": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "新标题"
    assert data["completed"] == True


def test_update_todo_not_found(client):
    """更新不存在的 id 应该 404"""
    response = client.put("/todos/999", json={"title": "没有这条"})
    assert response.status_code == 404


# ===== DELETE /todos/{id} =====
def test_delete_todo(client):
    """删除再查应该404"""
    created = client.post("/todos/", json={"title": "要删除的", "priority": 1}).json()

    delete_response = client.delete(f"/todos/{created['id']}")
    assert delete_response.status_code == 204

    # 再查一次，应该 404
    get_response = client.get(f"/todos/{created['id']}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client):
    """删除不存在的 id 应该 404"""
    response = client.delete("/todos/999")
    assert response.status_code == 404
