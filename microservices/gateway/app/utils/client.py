import httpx

async def call_service(method: str, url: str, **kwargs):
    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, **kwargs)
        return response.json()
