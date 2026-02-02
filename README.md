<p align="right">
  <a href="./README.zh-CN.md">中文</a> | English
</p>
# FW Lab - Firewall Lab Environment Manager 

A comprehensive lab environment management system for deploying and managing network topologies with firewalls, virtual machines, and containers.

![view](./view.png)
![shell view](./shell-view.png)

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

### 1️⃣ Configure DHCP server
sudo apt install -y dnsmasq

#### Edit the configuration file
sudo vim /etc/dnsmasq.d/mgmt.conf

#### Write in the following content
interface=br-mgmt
bind-interfaces
dhcp-range=192.168.168.50,192.168.168.200,12h
dhcp-option=3,192.168.168.1
dhcp-option=6,192.168.168.1

#### run
sudo systemctl restart dnsmasq

#### Verify if DHCP is working properly
sudo dnsmasq --test

#### the following content appears is OK
dnsmasq: syntax check OK.

---

### 2️⃣ Configuration Management Network

#### Please make sure the image is located in the /img directory.

```bash
sudo vim /tmp/br-mgmt.xml
# write in
<network>
  <name>br-mgmt</name>
  <forward mode="bridge"/>
  <bridge name="br-mgmt"/>
</network>
# load
sudo virsh net-define /tmp/br-mgmt.xml
sudo virsh net-start br-mgmt
sudo virsh net-autostart br-mgmt
```

Key network parameters (located in `ipam.py`):

* **ip address**：`192.168.168.0/24`
* **gateway**：`192.168.168.1`
* **DHCP range**：`192.168.168.50-200`
* **static ip address range**：`192.168.168.201-250`

---

### 3️⃣ start server

```bash
sudo bash start_all.sh
```

This will start:
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Frontend**: [http://localhost:5173](http://localhost:5173)

### 4️⃣ Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check available firewall images
curl http://localhost:8000/images
```

---

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

---

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

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

**Note**: This is a lab environment tool. Not recommended for production use without additional security hardening.
