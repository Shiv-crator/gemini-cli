# api/models.py
# SQLAlchemy models for the "Supreme V1000 Infinite Registry" (practical registry + billing/tenant)
# This file defines Plan, Tenant, Usage, ModelArtifact, and a registry table that can be extended.

import uuid
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, BigInteger, Text, func, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Plan(Base):
    __tablename__ = "plans"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    monthly_price_cents = Column(Integer, nullable=False, default=0)   # cents
    monthly_quota_requests = Column(BigInteger, nullable=False, default=10000)
    created_at = Column(DateTime, server_default=func.now())


class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    plan = relationship("Plan")
    usages = relationship("Usage", back_populates="tenant")


class Usage(Base):
    __tablename__ = "usages"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    requests = Column(Integer, nullable=False, default=1)
    cost_cents = Column(Integer, nullable=False, default=0)

    tenant = relationship("Tenant", back_populates="usages")


class ModelArtifact(Base):
    """
    This is the model registry table for uploaded artifacts.
    'Supreme V1000 Infinite Registry' is a brand name — this table stores versioned model metadata.
    """
    __tablename__ = "model_artifacts"
    id = Column(Integer, primary_key=True)
    # UUID for the model version — use uuid.uuid4().hex or a proper UUID column if Postgres
    model_uuid = Column(String(64), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    name = Column(String(255), nullable=False)
    version = Column(String(64), nullable=False)
    framework = Column(String(64), nullable=True)   # torch / tf / onnx / triton
    type = Column(String(64), nullable=True)        # foundation / adapter / specialist
    metadata = Column(Text, nullable=True)          # JSON string of metadata (provenance, tags)
    storage_path = Column(String(1024), nullable=True) # where artifact is stored (S3/GCS/local)
    created_at = Column(DateTime, server_default=func.now())

    tenant = relationship("Tenant")

# Optional: a convenience registry view/table (supreme_registry) you can expand
class SupremeRegistry(Base):
    __tablename__ = "supreme_registry"
    id = Column(Integer, primary_key=True)
    model_uuid = Column(String(64), nullable=False)
    registry_name = Column(String(128), nullable=False, default="Supreme V1000")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Not required to relate directly; this is an extensible catalog table.
