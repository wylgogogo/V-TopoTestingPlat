from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from db import Base

class Task(Base):
    __tablename__ = "tasks"
    name = Column(String, primary_key=True)
    status = Column(String, default="new")  # new, deployed, stopped
    created_at = Column(DateTime, server_default=func.now())

class Topology(Base):
    __tablename__ = "topology"
    task = Column(String, primary_key=True)
    json = Column(Text)

class DeployedResource(Base):
    """跟踪已部署的资源，便于清理"""
    __tablename__ = "deployed_resources"
    id = Column(String, primary_key=True)  # 资源唯一ID
    task = Column(String, index=True)       # 所属任务
    resource_type = Column(String)          # vm, container, bridge
    resource_name = Column(String)          # 资源名称
    extra_info = Column(Text, nullable=True)  # 额外信息(JSON)