import asyncio
from video_backend import get_backend_status
import json

async def test():
    status = await get_backend_status()
    print("Backend Status:")
    print(json.dumps(status, indent=2))

asyncio.run(test())
