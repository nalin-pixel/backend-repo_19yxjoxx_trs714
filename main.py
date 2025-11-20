import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# Models
# ----------------------
class CreateWorkspace(BaseModel):
    name: str

class CreatePage(BaseModel):
    workspace_id: str
    title: Optional[str] = "Untitled"

class CreateBlock(BaseModel):
    page_id: str
    type: str = "text"  # text | todo
    content: str = ""
    checked: Optional[bool] = False
    position: int = 0

class UpdatePage(BaseModel):
    title: Optional[str] = None

class UpdateBlock(BaseModel):
    content: Optional[str] = None
    checked: Optional[bool] = None
    position: Optional[int] = None

# ----------------------
# Helpers
# ----------------------

def serialize(doc: Dict[str, Any]):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


def ensure_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


# ----------------------
# Health
# ----------------------
@app.get("/")
def read_root():
    return {"message": "Notion-like Backend Ready"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ----------------------
# Workspace Endpoints
# ----------------------
@app.post("/api/workspaces")
def create_workspace(payload: CreateWorkspace):
    workspace_id = create_document("workspace", payload.model_dump())
    return {"_id": workspace_id, **payload.model_dump()}


@app.get("/api/workspaces")
def list_workspaces():
    items = get_documents("workspace")
    return [serialize(it) for it in items]


# ----------------------
# Page Endpoints
# ----------------------
@app.post("/api/pages")
def create_page(payload: CreatePage):
    # ensure workspace exists
    ws = db["workspace"].find_one({"_id": ensure_object_id(payload.workspace_id)})
    if ws is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

    page_id = create_document("page", payload.model_dump())
    return {"_id": page_id, **payload.model_dump()}


@app.get("/api/pages")
def list_pages(workspace_id: Optional[str] = None):
    filt = {"workspace_id": workspace_id} if workspace_id else {}
    items = get_documents("page", filt)
    return [serialize(it) for it in items]


@app.patch("/api/pages/{page_id}")
def update_page(page_id: str, payload: UpdatePage):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        return {"_id": page_id}
    res = db["page"].update_one({"_id": ensure_object_id(page_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    doc = db["page"].find_one({"_id": ensure_object_id(page_id)})
    return serialize(doc)


@app.delete("/api/pages/{page_id}")
def delete_page(page_id: str):
    oid = ensure_object_id(page_id)
    res = db["page"].delete_one({"_id": oid})
    # cascade delete blocks
    db["block"].delete_many({"page_id": page_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"deleted": True}


# ----------------------
# Block Endpoints
# ----------------------
@app.post("/api/blocks")
def create_block(payload: CreateBlock):
    # ensure page exists
    pg = db["page"].find_one({"_id": ensure_object_id(payload.page_id)})
    if pg is None:
        raise HTTPException(status_code=404, detail="Page not found")

    block_id = create_document("block", payload.model_dump())
    return {"_id": block_id, **payload.model_dump()}


@app.get("/api/blocks")
def list_blocks(page_id: str):
    items = get_documents("block", {"page_id": page_id})
    items.sort(key=lambda x: x.get("position", 0))
    return [serialize(it) for it in items]


@app.patch("/api/blocks/{block_id}")
def update_block(block_id: str, payload: UpdateBlock):
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update:
        return {"_id": block_id}
    res = db["block"].update_one({"_id": ensure_object_id(block_id)}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Block not found")
    doc = db["block"].find_one({"_id": ensure_object_id(block_id)})
    return serialize(doc)


@app.delete("/api/blocks/{block_id}")
def delete_block(block_id: str):
    res = db["block"].delete_one({"_id": ensure_object_id(block_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Block not found")
    return {"deleted": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
