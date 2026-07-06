from unittest.mock import patch, AsyncMock

with patch('cognee.config.set_llm_api_key'), \
     patch('cognee.prune.prune_system', new_callable=AsyncMock), \
     patch('cognee.add', new_callable=AsyncMock), \
     patch('cognee.search', new_callable=AsyncMock, return_value=[]):
    import main
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    resp = client.post('/ingest', json={'content': 'abc', 'title': 'test'})
    print(resp.status_code)
    print(resp.text)
