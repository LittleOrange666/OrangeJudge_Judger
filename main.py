import fastapi
import uvicorn
import asyncio
from pydantic import BaseModel

app = fastapi.FastAPI()


class TestRequest(BaseModel):
    pass


@app.post("/test")
async def test(request: TestRequest):
    await asyncio.sleep(100)
    return {"result": "ok"}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
