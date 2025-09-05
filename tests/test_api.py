import pytest
from httpx import AsyncClient
from main import app as fastapi_app

BASE_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_read_root():
    """测试根路径 / 是否返回成功。"""
    async with AsyncClient(app=fastapi_app, base_url=BASE_URL) as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "欢迎来到费曼学生Agent API。请访问 /docs 查看API文档。"}

@pytest.mark.asyncio
async def test_read_docs():
    """测试API文档路径 /docs 是否返回成功。"""
    async with AsyncClient(app=fastapi_app, base_url=BASE_URL) as ac:
        response = await ac.get("/docs")
    assert response.status_code == 200

# 可以在这里添加更多对 /chat 端点的集成测试
# 例如，模拟一个请求，并检查响应的结构是否正确
# from main import ChatResponse

# @pytest.mark.asyncio
# async def test_chat_endpoint_structure():
#     """测试 /chat 端点的基本响应结构。"""
#     test_payload = {
#         "topic": "test",
#         "explanation": "This is a test.",
#         "session_id": "test_session_123",
#         "short_term_memory": []
#     }
#     async with AsyncClient(app=fastapi_app, base_url=BASE_URL) as ac:
#         response = await ac.post("/chat", json=test_payload)
    
#     # 我们不关心内容，只关心它是否成功并返回了正确的结构
#     assert response.status_code == 200
#     
#     # 验证响应是否可以被解析为ChatResponse模型
#     try:
#         ChatResponse.model_validate(response.json())
#     except Exception as e:
#         pytest.fail(f"响应未能通过ChatResponse模型验证: {e}") 