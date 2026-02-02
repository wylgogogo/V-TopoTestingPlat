<p align="right">
  中文 | <a href="./README.md">English</a>
</p>

# FW Lab - 虚拟化拓扑测试平台

一个用于 **部署与管理网络拓扑实验环境** 的综合平台，支持防火墙、虚拟机以及容器等多种资源类型。

---

## 🚀 功能特性

* **拓扑管理**：通过可视化界面设计并保存网络拓扑
* **多资源支持**：统一编排虚拟机、容器与网络桥接
* **防火墙集成**：支持多种防火墙镜像与配置方式
* **资源管理**：实时监控已部署资源的 CPU 与内存使用情况
* **交互式终端**：

  * Container WebShell（容器 Web 终端）
  * VM 串口控制台（虚拟机管理）
* **生命周期控制**：支持节点或任务级别的启动 / 停止 / 重启
* **IPAM**：自动化管理管理网段的 IP 地址分配

---

## 🏗️ 系统架构

```
fw-lab-v1/
├── backend/              # 后端服务（FastAPI）
│   ├── main.py           # API 接口入口
│   ├── orchestrator.py   # 资源部署与编排逻辑
│   ├── ipam.py           # IP 地址管理
│   ├── models.py         # 数据库模型
│   ├── db.py             # 数据库配置
│   ├── webshell.py       # 容器 Web 终端
│   └── vmshell.py        # 虚拟机串口控制台
└── frontend/             # 前端（Vue.js）
    ├── src/
    │   ├── App.vue
    │   ├── components/
    │   └── api.js
    └── index.html

```

---

## 📋 环境依赖

* Linux 主机（已在 Ubuntu 上测试）
* KVM / QEMU + libvirt
* Python 3.10+
* Node.js 16+（前端开发）

### 系统要求

* **管理网桥**：`br-mgmt`（`192.168.168.0/24`）
* **权限要求**：当前用户需具备 Docker 与 libvirt 访问权限
* **硬件资源**：需具备足够的 CPU / 内存以支持虚拟机运行

---

## 🔧 安装部署

### 1️⃣ 克隆仓库

```bash
git clone <repository-url>
cd fw-lab-v1
```

---

### 2️⃣ 配置管理网络

系统使用管理网桥 `br-mgmt`（`192.168.168.0/24`），请在宿主机上完成配置。

关键网络参数（位于 `ipam.py`）：

* **网络地址**：`192.168.168.0/24`
* **网关**：`192.168.168.1`
* **DHCP 范围**：`192.168.168.50-200`
* **静态地址范围**：`192.168.168.201-250`

---

### 3️⃣ 启动服务

```bash
sudo bash start_all.sh
```

启动后可访问：

* **后端 API**：[http://localhost:8000](http://localhost:8000)
* **前端界面**：[http://localhost:3000](http://localhost:3000)

---

### 4️⃣ 验证服务状态

```bash
curl http://localhost:8000/health
curl http://localhost:8000/images
```

---

## 📖 API 接口说明

### 任务管理

* `GET /tasks`：获取任务列表
* `POST /tasks/{task_name}`：创建任务
* `GET /tasks/{task_name}`：获取任务详情
* `DELETE /tasks/{task_name}`：删除任务

---

### 拓扑管理

* `POST /tasks/{task_name}/topology`：保存拓扑
* `GET /tasks/{task_name}/topology`：获取拓扑

---

### 环境部署

* `POST /tasks/{task_name}/deploy`：部署实验环境
* `POST /tasks/{task_name}/destroy`：销毁环境
* `GET /tasks/{task_name}/status`：查看状态

---

### 电源管理

* `POST /tasks/{task_name}/shutdown`：关闭全部节点
* `POST /tasks/{task_name}/startup`：启动全部节点

节点级操作：

* `shutdown / startup / restart`
* `GET /tasks/{task_name}/nodes/{node_id}/state`

---

### 终端访问

* **容器 WebShell**：`ws://localhost:8000/ws/{container_name}`
* **虚拟机串口**：`ws://localhost:8000/vmws/{vm_name}`

---

## 🎮 使用示例

```bash
# 创建任务
curl -X POST http://localhost:8000/tasks/lab1

# 部署环境
curl -X POST http://localhost:8000/tasks/lab1/deploy

# 查看状态
curl http://localhost:8000/tasks/lab1/status
```

---

## 🗄️ 数据库结构

* **Tasks**：实验任务
* **Topology**：拓扑定义（JSON）
* **DeployedResource**：已部署资源信息

---

## 🔧 配置说明

### IPAM（`ipam.py`）

```python
MGMT_BRIDGE = "br-mgmt"
MGMT_NETWORK = "192.168.168.0/24"
MGMT_GATEWAY = "192.168.168.1"
MGMT_DHCP_START = "192.168.168.50"
MGMT_DHCP_END = "192.168.168.200"
STATIC_IP_START = 201
STATIC_IP_END = 250
```

---

## 🐛 常见问题排查

* **虚拟机串口无法连接**：确认 VM 串口配置及运行状态
* **容器 Shell 异常**：确认容器运行状态及 shell 类型
* **网络异常**：检查 `br-mgmt` 网桥及 IP 分配情况

---

## 🧑‍💻 开发说明

### 后端

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
npm run dev
```

---

## 🤝 参与贡献

欢迎提交 Issue 与 Pull Request，共同完善项目。

---

## 📄 License

待补充

---

> ⚠️ 本项目为实验/测试用途工具，未进行生产级安全加固，请谨慎用于生产环境。
