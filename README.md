# gemini-cli - "Effectively Unlimited" Hybrid AI Platform (starter)

This repository contains starter code, infra templates and policy examples to build an autoscaling, hybrid, continuously‑updating AI platform with:
- Model registry + artifact upload
- Canary deploy and promotion workflows
- Inference API (FastAPI)
- Kubernetes deployment + HPA
- CI pipeline (GitHub Actions)
- Policy engine example (auto vs manual approvals)
- Hooks to hybrid / on‑prem nodes and multi‑region replication

NOTES:
- This is a blueprint + starter; for production you'll need cloud infra (S3 / GCS), GPUs, secret management and compliance reviews.
- This design intentionally prevents unchecked self‑permission escalation; permission changes are governed by policy rules and manual approvals for sensitive ops.

See files:
- api/main.py — FastAPI server + model registry API
- Dockerfile — container image
- k8s/deployment.yaml — Deployment and Service
- k8s/hpa.yaml — HorizontalPodAutoscaler example
- infra/terraform/main.tf — skeleton to create S3/GCS bucket, EKS/GKE cluster (fill with provider specifics)
- .github/workflows/ci.yml — CI for tests and model validation
- policy/policy.yaml — example rules for auto‑approval
- model_registry/schema.json — expected metadata for uploads

To get started:
1. Fill cloud provider infra in infra/terraform/
2. Build and push container, deploy K8s manifests
3. Configure object storage and point MODEL_STORE_URL env var
4. Use /upload_model to upload artifacts; system runs validations and canary deploys on success.

Security: Do not enable "auto‑grant" rules for critical permissions without human approval.