<p align="right">
  <a href="./README.zh-CN.md">中文</a> | English
</p>
# FW Lab - Firewall Lab Environment Manager 

A comprehensive lab environment management system for deploying and managing network topologies with firewalls, virtual machines, and containers.

## 🚀 Features

- **Topology Management**: Design and save network topologies with a visual interface
- **Multi-Resource Support**: Deploy VMs, containers, and network bridges
- **Firewall Integration**: Support for various firewall images and configurations
- **Resource Management**: Monitor CPU and memory usage across deployed resources
- **Interactive Terminals**: 
  - WebShell for container access
  - VM serial console for virtual machine management
- **Lifecycle Control**: Start, stop, restart individual nodes or entire tasks
- **IPAM**: Automated IP address management for management networks

## 🏗️ Architecture

```
fw-lab-v1/
├── backend/           # FastAPI backend service
│   ├── main.py       # API endpoints
│   ├── orchestrator.py # Resource deployment logic
│   ├── ipam.py       # IP address management
│   ├── models.py     # Database models
│   ├── db.py         # Database configuration
│   ├── webshell.py   # Container terminal
│   └── vmshell.py    # VM serial console
└── frontend/         # Vue.js frontend
    ├── src/
    │   ├── App.vue
    │   ├── components/
    │   └── api.js
    └── index.html

```

## 📋 Prerequisites

- Linux host (tested on Ubuntu)
- Docker and Docker Compose
- KVM/QEMU with libvirt
- Python 3.10+
- Node.js 16+ (for frontend development)

### System Requirements

- **Bridge Interface**: `br-mgmt` configured on `192.168.168.0/24`
- **Permissions**: User must have access to Docker and libvirt
- **Resources**: Adequate CPU and memory for VM deployments

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fw-lab-v1
```

### 2. Configure Management Network

The system uses a management bridge `br-mgmt` on `192.168.168.0/24`. Configure this on your host:

```bash
# Example using netplan (adjust for your system)
# Edit /etc/netplan/01-network-config.yaml
```

Key network settings (configured in `ipam.py`):
- **Network**: `192.168.168.0/24`
- **Gateway**: `192.168.168.1`
- **DHCP Range**: `192.168.168.50-200`
- **Static Range**: `192.168.168.201-250`

### 3. Start Services

```bash
sudo bash start_all.sh
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check available firewall images
curl http://localhost:8000/images
```

## 📖 API Documentation

### Task Management

#### List Tasks
```http
GET /tasks
```

#### Create Task
```http
POST /tasks/{task_name}
```

#### Get Task Details
```http
GET /tasks/{task_name}
```

#### Delete Task
```http
DELETE /tasks/{task_name}
```

### Topology Management

#### Save Topology
```http
POST /tasks/{task_name}/topology
Content-Type: application/json

{
  "nodes": [...],
  "links": [...]
}
```

#### Get Topology
```http
GET /tasks/{task_name}/topology
```

### Deployment

#### Deploy Environment
```http
POST /tasks/{task_name}/deploy
```

#### Destroy Environment
```http
POST /tasks/{task_name}/destroy
```

#### Get Status
```http
GET /tasks/{task_name}/status
```

### Power Management

#### Shutdown All
```http
POST /tasks/{task_name}/shutdown
```

#### Startup All
```http
POST /tasks/{task_name}/startup
```

#### Node Operations
```http
POST /tasks/{task_name}/nodes/{node_id}/shutdown
POST /tasks/{task_name}/nodes/{node_id}/startup
POST /tasks/{task_name}/nodes/{node_id}/restart
GET /tasks/{task_name}/nodes/{node_id}/state
```

### Terminal Access

#### Container WebShell
```javascript
ws://localhost:8000/ws/{container_name}
```

#### VM Serial Console
```javascript
ws://localhost:8000/vmws/{vm_name}
```

#### Check VM Console Status
```http
GET /vms/{vm_name}/console
```

### System Information

#### Get Available Resources
```http
GET /system/resources
```

Response:
```json
{
  "ok": true,
  "resources": {
    "cpu": {
      "total": 16,
      "available": 14,
      "used_by_vms": 4,
      "unit": "核"
    },
    "memory": {
      "total": 32768,
      "available": 28672,
      "used_by_vms": 8192,
      "unit": "MB"
    }
  }
}
```

#### List Firewall Images
```http
GET /images
```

## 🎮 Usage Examples

### 1. Create and Deploy a Lab

```bash
# Create a new task
curl -X POST http://localhost:8000/tasks/lab1

# Save topology (from frontend or API)
curl -X POST http://localhost:8000/tasks/lab1/topology \
  -H "Content-Type: application/json" \
  -d @topology.json

# Deploy the environment
curl -X POST http://localhost:8000/tasks/lab1/deploy

# Check deployment status
curl http://localhost:8000/tasks/lab1/status
```

### 2. Manage Running Lab

```bash
# Shutdown all nodes
curl -X POST http://localhost:8000/tasks/lab1/shutdown

# Start specific node
curl -X POST http://localhost:8000/tasks/lab1/nodes/fw1/startup

# Check node state
curl http://localhost:8000/tasks/lab1/nodes/fw1/state
```

### 3. Clean Up

```bash
# Destroy environment (keeps topology)
curl -X POST http://localhost:8000/tasks/lab1/destroy

# Delete task completely
curl -X DELETE http://localhost:8000/tasks/lab1
```

## 🔐 Terminal Features

### Container WebShell

- Full TTY support with PTY
- Real-time interaction
- Terminal resizing support
- UTF-8 character handling
- Color support (xterm-256color)

### VM Serial Console

- Direct serial port access via `virsh console`
- Force disconnect other sessions
- UTF-8 stream decoding
- Handle incomplete multi-byte characters
- Terminal resize support

## 🗄️ Database Schema

The system uses SQLite with three main tables:

### Tasks
- `name` (PK): Task identifier
- `status`: new | deployed | stopped | shutdown
- `created_at`: Creation timestamp

### Topology
- `task` (PK): Associated task name
- `json`: Topology configuration (JSON string)

### DeployedResource
- `id` (PK): Unique resource identifier
- `task`: Associated task name
- `resource_type`: vm | container | bridge
- `resource_name`: Resource identifier
- `extra_info`: Additional metadata (JSON)

## 🔧 Configuration

### IPAM Settings (`ipam.py`)

```python
MGMT_BRIDGE = "br-mgmt"
MGMT_NETWORK = "192.168.168.0/24"
MGMT_GATEWAY = "192.168.168.1"
MGMT_DHCP_START = "192.168.168.50"
MGMT_DHCP_END = "192.168.168.200"
STATIC_IP_START = 201
STATIC_IP_END = 250
```

### System Reservations

```python
system_reserved_cpu = 2      # Cores reserved for host
system_reserved_mem = 2048   # MB reserved for host
```

## 🐛 Troubleshooting

### VM Console Not Connecting

1. Verify VM has serial device configured:
```bash
virsh dumpxml {vm_name} | grep -E "<serial|<console"
```

2. Ensure VM is running:
```bash
virsh domstate {vm_name}
```

3. Check if another console session is active (use `--force` flag)

### Container Shell Issues

1. Verify container is running:
```bash
docker ps | grep {container_name}
```

2. Check if `/bin/bash` exists in container

### Network Issues

1. Verify bridge interface:
```bash
ip link show br-mgmt
```

2. Check IP allocation:
```bash
curl http://localhost:8000/tasks/{task}/status
```

## 📝 Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database Management

The database is automatically created on first run. To reset:

```bash
rm backend/data.db
# Restart backend - tables will be recreated
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

[Specify your license here]

## 👥 Authors

[Your name/team here]

## 🙏 Acknowledgments

- FastAPI for the robust backend framework
- Vue.js for the reactive frontend
- xterm.js for terminal emulation
- libvirt/KVM for virtualization

---

**Note**: This is a lab environment tool. Not recommended for production use without additional security hardening.
