from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import Base, engine, SessionLocal
from models import Task, Topology, DeployedResource
import orchestrator
import webshell
import vmshell
import json

Base.metadata.create_all(engine)

app = FastAPI(title="FW Lab API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 任务管理 ==========

@app.get("/tasks")
def list_tasks():
    """获取所有任务"""
    db = SessionLocal()
    try:
        tasks = db.query(Task).all()
        result = []
        for t in tasks:
            # 获取任务的资源数量
            resource_count = db.query(DeployedResource).filter_by(task=t.name).count()
            result.append({
                "name": t.name,
                "status": t.status,
                "resource_count": resource_count,
                "created_at": str(t.created_at) if t.created_at else None
            })
        return {"ok": True, "tasks": result}
    finally:
        db.close()


@app.post("/tasks/{task}")
def create_task(task: str):
    """创建新任务"""
    db = SessionLocal()
    try:
        existing = db.query(Task).filter_by(name=task).first()
        if existing:
            return {"ok": True, "task": task, "message": "任务已存在"}

        db.add(Task(name=task, status="new"))
        db.commit()
        return {"ok": True, "task": task, "message": "任务创建成功"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.delete("/tasks/{task}")
def delete_task(task: str):
    """删除任务及其所有资源"""
    db = SessionLocal()
    try:
        # 先销毁资源
        destroy_result = orchestrator.destroy(task, db)

        # 删除拓扑
        topo = db.query(Topology).filter_by(task=task).first()
        if topo:
            db.delete(topo)

        # 删除任务
        task_obj = db.query(Task).filter_by(name=task).first()
        if task_obj:
            db.delete(task_obj)

        db.commit()

        return {
            "ok": True,
            "message": "任务删除成功",
            "destroy_result": destroy_result
        }
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.get("/tasks/{task}")
def get_task(task: str):
    """获取任务详情"""
    db = SessionLocal()
    try:
        task_obj = db.query(Task).filter_by(name=task).first()
        if not task_obj:
            return {"ok": False, "error": "任务不存在"}

        # 获取拓扑
        topo = db.query(Topology).filter_by(task=task).first()

        # 获取资源状态
        status_result = orchestrator.get_status(task, db)

        return {
            "ok": True,
            "task": {
                "name": task_obj.name,
                "status": task_obj.status,
                "created_at": str(task_obj.created_at) if task_obj.created_at else None
            },
            "has_topology": topo is not None,
            "resource_status": status_result.get("status") if status_result.get("ok") else None
        }
    finally:
        db.close()


# ========== 拓扑管理 ==========

@app.post("/tasks/{task}/topology")
async def save_topology(task: str, request: Request):
    """保存拓扑配置"""
    db = SessionLocal()
    try:
        # 确保任务存在
        task_obj = db.query(Task).filter_by(name=task).first()
        if not task_obj:
            db.add(Task(name=task, status="new"))

        topo = await request.json()
        db.merge(Topology(task=task, json=json.dumps(topo)))
        db.commit()
        return {"ok": True, "task": task, "message": "拓扑保存成功"}
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.get("/tasks/{task}/topology")
def get_topology(task: str):
    """获取拓扑配置"""
    db = SessionLocal()
    try:
        topo = db.query(Topology).filter_by(task=task).first()
        if topo:
            return {"ok": True, "topology": json.loads(topo.json)}
        return {"ok": False, "error": "拓扑不存在"}
    finally:
        db.close()


# ========== 部署管理 ==========

@app.post("/tasks/{task}/deploy")
def deploy_task(task: str):
    """部署环境"""
    db = SessionLocal()
    try:
        topo = db.query(Topology).filter_by(task=task).first()
        if not topo:
            return {"ok": False, "error": "请先保存拓扑配置"}

        result = orchestrator.deploy(task, topo.json, db)

        if result.get("ok"):
            # 更新任务状态
            task_obj = db.query(Task).filter_by(name=task).first()
            if task_obj:
                task_obj.status = "deployed"
                db.commit()

        return result
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.post("/tasks/{task}/destroy")
def destroy_task(task: str):
    """销毁环境(保留拓扑)"""
    db = SessionLocal()
    try:
        result = orchestrator.destroy(task, db)

        if result.get("ok"):
            # 更新任务状态
            task_obj = db.query(Task).filter_by(name=task).first()
            if task_obj:
                task_obj.status = "stopped"
                db.commit()

        return result
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.get("/tasks/{task}/status")
def get_task_status(task: str):
    """获取任务资源状态"""
    db = SessionLocal()
    try:
        return orchestrator.get_status(task, db)
    finally:
        db.close()


# ========== 开关机管理 ==========

@app.post("/tasks/{task}/shutdown")
def shutdown_task(task: str):
    """关闭任务中所有机器"""
    db = SessionLocal()
    try:
        result = orchestrator.shutdown_all(task, db)

        if result.get("ok"):
            # 更新任务状态为 shutdown
            task_obj = db.query(Task).filter_by(name=task).first()
            if task_obj:
                task_obj.status = "shutdown"
                db.commit()

        return result
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.post("/tasks/{task}/startup")
def startup_task(task: str):
    """启动任务中所有机器"""
    db = SessionLocal()
    try:
        result = orchestrator.startup_all(task, db)

        if result.get("ok"):
            # 更新任务状态
            task_obj = db.query(Task).filter_by(name=task).first()
            if task_obj:
                task_obj.status = "deployed"
                db.commit()

        return result
    except Exception as e:
        db.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


# ========== 单个设备操作 ==========

@app.post("/tasks/{task}/nodes/{node_id}/shutdown")
def shutdown_node(task: str, node_id: str):
    """关闭单个设备"""
    db = SessionLocal()
    try:
        result = orchestrator.shutdown_node(task, node_id, db)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.post("/tasks/{task}/nodes/{node_id}/startup")
def startup_node(task: str, node_id: str):
    """启动单个设备"""
    db = SessionLocal()
    try:
        result = orchestrator.startup_node(task, node_id, db)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.post("/tasks/{task}/nodes/{node_id}/restart")
def restart_node(task: str, node_id: str):
    """重启单个设备"""
    db = SessionLocal()
    try:
        result = orchestrator.restart_node(task, node_id, db)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@app.get("/tasks/{task}/nodes/{node_id}/state")
def get_node_state(task: str, node_id: str):
    """获取单个设备状态"""
    db = SessionLocal()
    try:
        result = orchestrator.get_node_state(task, node_id, db)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


# ========== 防火墙镜像 ==========

@app.get("/images")
def list_images():
    """获取可用的防火墙镜像列表"""
    images = orchestrator.list_fw_images()
    return {"ok": True, "images": images}


# ========== 系统资源信息 ==========

@app.get("/system/resources")
def get_system_resources():
    """获取系统可用的 CPU 和内存资源"""
    import os
    import subprocess

    try:
        # 获取 CPU 核心数
        total_cpu = os.cpu_count() or 1

        # 获取内存信息 (MB)
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()

        total_mem = 0
        available_mem = 0
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                total_mem = int(line.split()[1]) // 1024  # KB to MB
            elif line.startswith('MemAvailable:'):
                available_mem = int(line.split()[1]) // 1024  # KB to MB

        # 获取已被 VM 使用的资源
        used_cpu = 0
        used_mem = 0
        try:
            result = subprocess.run(
                ["virsh", "list", "--name"],
                capture_output=True, text=True
            )
            running_vms = [vm.strip() for vm in result.stdout.strip().split('\n') if vm.strip()]

            for vm in running_vms:
                # 获取 VM 的 CPU
                result = subprocess.run(
                    ["virsh", "vcpucount", vm, "--current"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    used_cpu += int(result.stdout.strip())

                # 获取 VM 的内存
                result = subprocess.run(
                    ["virsh", "dominfo", vm],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Used memory' in line or 'Max memory' in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                mem_kb = int(parts[-2])
                                used_mem += mem_kb // 1024
                                break
        except Exception as e:
            print(f"[WARN] Failed to get VM resource usage: {e}")

        # 计算可用资源
        system_reserved_cpu = 2
        system_reserved_mem = 2048

        available_cpu = max(1, total_cpu - system_reserved_cpu)
        available_mem_for_vm = max(1024, available_mem - system_reserved_mem)

        return {
            "ok": True,
            "resources": {
                "cpu": {
                    "total": total_cpu,
                    "available": available_cpu,
                    "used_by_vms": used_cpu,
                    "unit": "核"
                },
                "memory": {
                    "total": total_mem,
                    "available": available_mem_for_vm,
                    "used_by_vms": used_mem,
                    "unit": "MB"
                }
            }
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ========== WebShell (容器) ==========

@app.websocket("/ws/{container}")
async def websocket_shell(ws: WebSocket, container: str):
    """WebSocket Shell连接 - 容器"""
    await webshell.shell(ws, container)


# ========== VMShell (虚拟机串口控制台) ==========

@app.websocket("/vmws/{vm_name}")
async def websocket_vm_shell(ws: WebSocket, vm_name: str):
    """WebSocket Shell连接 - VM 串口控制台"""
    await vmshell.vm_shell(ws, vm_name)


@app.get("/vms/{vm_name}/console")
async def get_vm_console_info(vm_name: str):
    """获取 VM 控制台状态"""
    return await vmshell.check_vm_console(vm_name)


# ========== 健康检查 ==========

@app.get("/health")
def health_check():
    """健康检查"""
    return {"ok": True, "status": "running"}
