from fastapi import FastAPI

app = FastAPI(
    title="AI Engineering Workspace",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"status": "running"}