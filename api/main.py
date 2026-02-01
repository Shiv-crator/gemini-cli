from fastapi import FastAPI, HTTPException, UploadFile, File, Header, BackgroundTasks
from pydantic import BaseModel
from uuid import uuid4
import os, shutil, json, subprocess, datetime

app = FastAPI(title="Gemini‑CLI Starter Registry & Orchestrator")

MODEL_STORE = os.getenv("MODEL_STORE_URL", "/models")  # e.g., s3://bucket/path or local dir
METADATA_DB = os.getenv("METADATA_DB", "metadata.db")  # placeholder for real DB (Postgres)

# ----- Metadata schema -----
class ModelMetadata(BaseModel):
    name: str
    version: str
    framework: str  # e.g., torch, tf
    type: str  # foundation, specialized, adapter
    tags: dict = {}
    provenance: dict = {}  # dataset ids, licenses, uploader

# simple in-memory store for demo (replace with Postgres)
REGISTRY = {}

def persist_metadata(model_id, metadata):
    REGISTRY[model_id] = {
        "metadata": metadata,
        "status": "uploaded",
        "created_at": datetime.datetime.utcnow().isoformat()
    }

# ----- Upload endpoint -----
@app.post("/upload_model")
async def upload_model(metadata: str = Header(...), file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload a model artifact (tarball / zip). Header 'metadata' must contain JSON matching model_registry/schema.json
    """
    try:
        meta = ModelMetadata.parse_raw(metadata)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid metadata: {e}")

    model_id = str(uuid4())
    dest_dir = os.path.join(MODEL_STORE, model_id)
    os.makedirs(dest_dir, exist_ok=True)
    file_path = os.path.join(dest_dir, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    persist_metadata(model_id, meta.dict())

    # Background validation + canary deploy
    if background_tasks is not None:
        background_tasks.add_task(run_validation_and_canary, model_id, file_path)
    else:
        run_validation_and_canary(model_id, file_path)

    return {"model_id": model_id, "status": "upload_received"}

def run_validation_and_canary(model_id, file_path):
    # 1) Run validation tests (signature compatibility, simple smoke test)
    # 2) If passes -> create canary deployment (call orchestrator)
    # 3) Monitor canary metrics and promote or rollback
    # NOTE: Replace with real validation infra (unit tests, dataset checks, license checks)
    print(f"[validator] Running validation for {model_id} on {file_path} ham")
    # dummy pass
    passed = True
    if passed:
        REGISTRY[model_id]["status"] = "validated"
        # instruct orchestrator (could be message queue)
        orchestrator_create_canary(model_id)
    else:
        REGISTRY[model_id]["status"] = "validation_failed"

def orchestrator_create_canary(model_id):
    # This would enqueue deployment to Kubernetes cluster as new canary
    print(f"[orchestrator] Creating canary for {model_id}")
    REGISTRY[model_id]["status"] = "canary_deployed"

# ----- Promote / Rollback endpoints (protected) -----
@app.post("/promote_model/{model_id}")
def promote_model(model_id: str, approver: str = Header(None)):
    # Check policy: is manual approval required?
    # For demo: require approver header
    if not approver:
        raise HTTPException(403, "Approver header required")
    info = REGISTRY.get(model_id)
    if not info:
        raise HTTPException(404, "model not found")
    info["status"] = "promoted"
    return {"model_id": model_id, "status": "promoted"}

@app.get("/models/{model_id}")
def get_model(model_id: str):
    info = REGISTRY.get(model_id)
    if not info:
        raise HTTPException(404, "model not found")
    return info

# ----- Simple predict endpoint (routes to best model) -----
@app.post("/predict")
def predict(payload: dict):
    # In real system: router selects model based on tenant, tags, version matrix
    # Here return a dummy response
    return {"result": "ok", "payload": payload}