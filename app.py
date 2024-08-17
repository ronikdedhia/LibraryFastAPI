from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str = None

items = []

@app.get("/")
async def root():
    return {"message": "FastAPI is properly installed and running!"}

@app.get("/items")
async def get_items():
    return {"items": items}

@app.post("/items")
async def create_item(item: Item):
    items.append(item)
    return {"message": "Item created successfully", "item": item}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    if 0 <= item_id < len(items):
        return {"item": items[item_id]}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)