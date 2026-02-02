import subprocess
import json
import shutil
import os
import tempfile
from ipam import MGMT_BRIDGE, get_mgmt_config

# 默认防火墙镜像路径
DEFAULT_FW_IMAGE = "/img/USG-FW-CMCC-VFEA-542-x86-9st.qcow2"

# Docker 管理网络名称
DOCKER_MGMT_NET = "mgmt-net"


def check_dependencies():
    """检查系统依赖"""
    deps = {
        'virsh': shutil.which('virsh'),
        'virt-install': shutil.which('virt-install'),
        'docker': shutil.which('docker'),
        'ip': shutil.which('ip'),
    }
    missing = [k for k, v in deps.items() if v is None]
    return deps, missing


def sh(cmd, check=False):
    """执行shell命令"""
    print(f"[CMD] {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"[STDOUT] {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"[STDERR] {result.stderr.strip()}")

    if check and result.returncode != 0:
        raise Exception(f"Command failed: {cmd}\nStderr: {result.stderr}")
    return result


def create_bridge(br_name):
    """创建 Linux bridge"""
    sh(f"ip link add {br_name} type bridge 2>/dev/null || true")
    sh(f"ip link set {br_name} up")
    return br_name


def delete_bridge(br_name):
    """删除 Linux bridge"""
    sh(f"ip link set {br_name} down 2>/dev/null || true")
    sh(f"ip link del {br_name} 2>/dev/null || true")


def register_libvirt_network(net_name, br_name):
    """将 bridge 注册为 libvirt 网络"""
    xml_lines = [
        "<network>",
        f"  <name>{net_name}</name>",
        '  <forward mode="bridge"/>',
        f'  <bridge name="{br_name}"/>',
        "</network>"
    ]
    xml_content = "\n".join(xml_lines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
        f.write(xml_content)
        xml_path = f.name

    try:
        sh(f"virsh net-destroy {net_name} 2>/dev/null || true")
        sh(f"virsh net-undefine {net_name} 2>/dev/null || true")
        sh(f"virsh net-define {xml_path}", check=True)
        sh(f"virsh net-start {net_name}", check=True)
    finally:
        os.unlink(xml_path)

    return net_name


def unregister_libvirt_network(net_name):
    """从 libvirt 注销网络"""
    sh(f"virsh net-destroy {net_name} 2>/dev/null || true")
    sh(f"virsh net-undefine {net_name} 2>/dev/null || true")


def ensure_docker_mgmt_network():
    """确保 Docker 管理网络存在"""
    result = sh(f"docker network ls --format '{{{{.Name}}}}' | grep -x '{DOCKER_MGMT_NET}'")
    if result.returncode == 0 and DOCKER_MGMT_NET in result.stdout:
        print(f"[INFO] Docker network {DOCKER_MGMT_NET} already exists")
        return DOCKER_MGMT_NET

    mgmt = get_mgmt_config()
    sh(f"docker network create -d macvlan "
       f"--subnet={mgmt['network']} "
       f"--gateway={mgmt['gateway']} "
       f"-o parent={MGMT_BRIDGE} "
       f"{DOCKER_MGMT_NET}", check=True)

    print(f"[INFO] Created Docker network {DOCKER_MGMT_NET}")
    return DOCKER_MGMT_NET


def create_docker_macvlan_network(net_name, br_name):
    """创建连接到指定 bridge 的 macvlan Docker 网络"""
    result = sh(f"docker network ls --format '{{{{.Name}}}}' | grep -x '{net_name}'")
    if result.returncode == 0 and net_name in result.stdout:
        print(f"[INFO] Docker network {net_name} already exists")
        return net_name

    sh(f"docker network create -d macvlan -o parent={br_name} {net_name}", check=True)
    print(f"[INFO] Created Docker macvlan network {net_name} on {br_name}")
    return net_name


def delete_docker_network(net_name):
    """删除 Docker 网络"""
    sh(f"docker network rm {net_name} 2>/dev/null || true")


def get_node_port_connections(node_id, edges, edge_net_map=None):
    """
    获取节点的端口连接信息

    Args:
        node_id: 节点 ID
        edges: 边列表
        edge_net_map: 可选，edge_id -> net_info 的映射，用于获取最新的网络信息
    """
    connections = {}
    for edge in edges:
        source_node = edge.get("sourceNode") or edge.get("source")
        target_node = edge.get("targetNode") or edge.get("target")
        source_port = edge.get("sourcePort") or edge.get("data", {}).get("sourcePort", "eth0")
        target_port = edge.get("targetPort") or edge.get("data", {}).get("targetPort", "eth0")

        # 优先从 edge_net_map 获取网络信息（更准确）
        edge_id = edge.get("id")
        if edge_net_map and edge_id in edge_net_map:
            net_info = edge_net_map[edge_id]
        else:
            net_info = edge.get("_net_info", {})

        if source_node == node_id:
            connections[source_port] = net_info
        elif target_node == node_id:
            connections[target_port] = net_info

    return connections


def get_existing_resources(task, db_session):
    """获取已部署的资源"""
    if not db_session:
        return {}, {}

    from models import DeployedResource
    resources = db_session.query(DeployedResource).filter_by(task=task).all()

    existing_nodes = {}  # node_id -> resource info
    existing_networks = {}  # edge_id -> {bridge, libvirt_net, docker_net}

    for res in resources:
        extra = json.loads(res.extra_info) if res.extra_info else {}

        if res.resource_type == "vm":
            existing_nodes[extra.get("node_id")] = {
                "type": "vm",
                "name": res.resource_name,
                "extra": extra
            }
        elif res.resource_type == "container":
            existing_nodes[extra.get("node_id")] = {
                "type": "container",
                "name": res.resource_name,
                "extra": extra
            }
        elif res.resource_type == "bridge":
            edge_id = extra.get("edge_id")
            if edge_id:
                if edge_id not in existing_networks:
                    existing_networks[edge_id] = {"edge_id": edge_id}
                existing_networks[edge_id]["bridge"] = res.resource_name
        elif res.resource_type == "libvirt_net":
            bridge = extra.get("bridge")
            for eid, nets in existing_networks.items():
                if nets.get("bridge") == bridge:
                    existing_networks[eid]["libvirt_net"] = res.resource_name
                    break
        elif res.resource_type == "docker_net":
            bridge = extra.get("bridge")
            for eid, nets in existing_networks.items():
                if nets.get("bridge") == bridge:
                    existing_networks[eid]["docker_net"] = res.resource_name
                    break

    return existing_nodes, existing_networks


def get_vm_interfaces(vm_name):
    """
    获取 VM 的所有网络接口信息
    返回: list of {interface, type, source, model, mac}
    """
    result = sh(f"virsh domiflist {vm_name}")
    if result.returncode != 0:
        return []

    interfaces = []
    lines = result.stdout.strip().split('\n')

    # 跳过标题行
    for line in lines[2:]:  # 第一行是标题，第二行是分隔线
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 5:
            interfaces.append({
                'interface': parts[0],
                'type': parts[1],
                'source': parts[2],
                'model': parts[3],
                'mac': parts[4]
            })

    return interfaces


def detach_vm_interface_by_mac(vm_name, mac, persistent=True):
    """
    通过 MAC 地址移除 VM 网络接口

    Args:
        vm_name: VM 名称
        mac: MAC 地址
        persistent: 是否持久化（重启后仍然生效）
    """
    # 检查 VM 状态
    result = sh(f"virsh domstate {vm_name}")
    is_running = 'running' in result.stdout.lower()

    if is_running:
        # 运行中的 VM：先尝试热拔
        if persistent:
            # --config 确保重启后也生效
            sh(f"virsh detach-interface {vm_name} --mac {mac} --config")
        # 热拔（可能失败，特别是对于不支持 ACPI 的 VM）
        result = sh(f"virsh detach-interface {vm_name} --mac {mac} --live")
        if result.returncode != 0:
            print(f"[WARN] 热拔网卡失败 (MAC: {mac})，将在 VM 重启后生效")
    else:
        # 关闭状态：直接修改配置
        sh(f"virsh detach-interface {vm_name} --mac {mac} --config")


def attach_vm_interface(vm_name, network, persistent=True):
    """
    添加 VM 网络接口

    Args:
        vm_name: VM 名称
        network: libvirt 网络名称
        persistent: 是否持久化

    Returns:
        新添加接口的 MAC 地址，失败返回 None
    """
    # 检查 VM 状态
    result = sh(f"virsh domstate {vm_name}")
    is_running = 'running' in result.stdout.lower()

    # 获取添加前的接口列表
    before_ifaces = get_vm_interfaces(vm_name)
    before_macs = {iface['mac'] for iface in before_ifaces}

    if is_running:
        if persistent:
            sh(f"virsh attach-interface {vm_name} network {network} --model virtio --config")
        result = sh(f"virsh attach-interface {vm_name} network {network} --model virtio --live")
        if result.returncode != 0:
            print(f"[WARN] 热添加网卡失败，将在 VM 重启后生效")
    else:
        sh(f"virsh attach-interface {vm_name} network {network} --model virtio --config")

    # 获取添加后的接口列表，找出新添加的 MAC
    after_ifaces = get_vm_interfaces(vm_name)
    for iface in after_ifaces:
        if iface['mac'] not in before_macs:
            return iface['mac']

    return None


def rebuild_vm_with_new_networks(vm_name, node_id, task, image, ports_with_networks, cpu_cores=2, memory_mb=4096,
                                 db_session=None):
    """
    重建 VM 以应用网络变更
    这是最可靠的方式，但会导致 VM 重启

    Args:
        vm_name: VM 名称
        node_id: 节点 ID
        task: 任务名称
        image: 镜像路径
        ports_with_networks: dict, port_name -> libvirt_network_name (eth0 除外，eth0 是管理口)
        cpu_cores: CPU 核心数
        memory_mb: 内存大小 (MB)

    Returns:
        deployed_resources list
    """
    deployed_resources = []

    # 验证配置范围
    cpu_cores = max(1, min(cpu_cores, 32))
    memory_mb = max(512, min(memory_mb, 131072))

    # 1. 关闭并删除 VM（保留磁盘）
    print(f"[REBUILD] Destroying old VM: {vm_name}")
    sh(f"virsh destroy {vm_name} 2>/dev/null || true")
    sh(f"virsh undefine {vm_name} 2>/dev/null || true")

    # 2. 构建网络参数
    # eth0 是管理口
    nets = f"--network network={MGMT_BRIDGE},model=virtio "

    # 按端口顺序添加网络（eth1, eth2, eth3...）
    port_names = sorted(ports_with_networks.keys(), key=lambda x: int(x.replace('eth', '')))
    for port in port_names:
        net = ports_with_networks[port]
        if net:
            nets += f"--network network={net},model=virtio "

    # 3. 重新创建 VM
    print(f"[REBUILD] Creating new VM: {vm_name} with CPU={cpu_cores}, Memory={memory_mb}MB, ports: {port_names}")
    cmd = f"""virt-install --name {vm_name} \
        --memory {memory_mb} --vcpus {cpu_cores} \
        --disk path={image},format=qcow2 \
        --import --noautoconsole --os-variant generic \
        --graphics vnc,listen=127.0.0.1 \
        --serial pty \
        --console pty,target_type=serial \
        {nets}"""

    result = sh(cmd)
    if result.returncode != 0:
        raise Exception(f"VM 重建失败: {result.stderr}")

    deployed_resources.append({
        "type": "vm",
        "name": vm_name,
        "node_id": node_id,
        "image": image,
        "cpu": cpu_cores,
        "memory": memory_mb,
        "ports": ports_with_networks
    })

    return deployed_resources


def deploy(task, topo_json, db_session=None):
    """部署拓扑环境（支持增量更新）"""
    deps, missing = check_dependencies()
    if missing:
        return {
            "ok": False,
            "error": f"缺少系统命令: {', '.join(missing)}",
            "dependencies": deps
        }

    topo = json.loads(topo_json)
    print(f"[DEPLOY] Task: {task}")

    # 获取已存在的资源
    existing_nodes, existing_networks = get_existing_resources(task, db_session)
    print(f"[DEPLOY] Existing nodes: {list(existing_nodes.keys())}")
    print(f"[DEPLOY] Existing networks: {list(existing_networks.keys())}")

    deployed_resources = []
    edges = topo.get("edges", [])
    nodes = topo.get("nodes", [])

    current_node_ids = {n["id"] for n in nodes}
    current_edge_ids = {e["id"] for e in edges}

    # 记录需要重建的 VM（因为网络变更）
    vms_need_rebuild = {}

    # 用于跟踪所有边的网络信息（包括已存在的和新创建的）
    edge_net_map = {}

    try:
        ensure_docker_mgmt_network()

        # ========== 1. 处理网络 ==========
        for edge in edges:
            edge_id = edge["id"]
            source_node = edge.get("sourceNode") or edge.get("source")
            target_node = edge.get("targetNode") or edge.get("target")
            source_port = edge.get("sourcePort") or edge.get("data", {}).get("sourcePort", "eth0")
            target_port = edge.get("targetPort") or edge.get("data", {}).get("targetPort", "eth0")

            if edge_id in existing_networks:
                print(f"[DEPLOY] Network {edge_id} exists, skipping")
                edge["_net_info"] = existing_networks[edge_id]
                edge_net_map[edge_id] = existing_networks[edge_id]
                continue

            br_name = f"br-{task[:3]}{edge_id[:5]}"[:15]
            net_name = f"{task}-{edge_id[:8]}"[:20]
            docker_net = f"dn-{task[:3]}{edge_id[:5]}"[:15]

            print(f"[DEPLOY] Creating network: {source_node}:{source_port} <-> {target_node}:{target_port}")

            create_bridge(br_name)
            deployed_resources.append({"type": "bridge", "name": br_name, "edge_id": edge_id})

            register_libvirt_network(net_name, br_name)
            deployed_resources.append({"type": "libvirt_net", "name": net_name, "bridge": br_name})

            create_docker_macvlan_network(docker_net, br_name)
            deployed_resources.append({"type": "docker_net", "name": docker_net, "bridge": br_name})

            net_info = {
                "bridge": br_name,
                "libvirt_net": net_name,
                "docker_net": docker_net,
                "edge_id": edge_id
            }
            edge["_net_info"] = net_info
            edge_net_map[edge_id] = net_info

        # ========== 2. 处理防火墙 VM ==========
        for node in nodes:
            if node["type"] != "fw":
                continue

            node_id = node["id"]
            vm_name = f"{task}_{node_id}"

            port_connections = get_node_port_connections(node_id, edges, edge_net_map)
            node_ports = node.get("data", {}).get("ports", ["eth0", "eth1", "eth2", "eth3"])
            image = node.get("data", {}).get("image", DEFAULT_FW_IMAGE)

            # 计算当前需要的端口网络配置（排除 eth0 管理口）
            current_ports_config = {}
            standalone_networks = {}

            for port in node_ports:
                if port == "eth0":
                    continue  # eth0 是管理口

                if port in port_connections:
                    # 有连线的端口
                    current_ports_config[port] = port_connections[port].get("libvirt_net")
                else:
                    # 没有连线的端口，需要创建独立网络
                    standalone_br = f"br-{task[:3]}{node_id}{port}"[:15]
                    standalone_net = f"{task}-{node_id}-{port}"[:20]

                    # 检查是否已存在
                    result = sh(f"virsh net-list --all --name | grep -x '{standalone_net}'")
                    if result.returncode != 0 or standalone_net not in result.stdout:
                        print(f"[DEPLOY] Creating standalone network for {vm_name}:{port}")
                        create_bridge(standalone_br)
                        deployed_resources.append({
                            "type": "bridge",
                            "name": standalone_br,
                            "node_id": node_id,
                            "port": port,
                            "standalone": True
                        })

                        register_libvirt_network(standalone_net, standalone_br)
                        deployed_resources.append({
                            "type": "libvirt_net",
                            "name": standalone_net,
                            "bridge": standalone_br,
                            "node_id": node_id,
                            "port": port,
                            "standalone": True
                        })

                    current_ports_config[port] = standalone_net
                    standalone_networks[port] = standalone_net

            # 检查 VM 是否已存在
            if node_id in existing_nodes and existing_nodes[node_id]["type"] == "vm":
                print(f"[DEPLOY] VM {vm_name} exists, checking config changes")

                existing_ports = existing_nodes[node_id]["extra"].get("ports", {})
                existing_cpu = existing_nodes[node_id]["extra"].get("cpu", 2)
                existing_memory = existing_nodes[node_id]["extra"].get("memory", 4096)

                # 获取当前配置
                cpu_cores = node.get("data", {}).get("cpu", 2)
                memory_mb = node.get("data", {}).get("memory", 4096)
                cpu_cores = max(1, min(cpu_cores, 32))
                memory_mb = max(512, min(memory_mb, 131072))

                # 比较配置是否有变化
                config_changed = False

                # 检查 CPU 是否变化
                if existing_cpu != cpu_cores:
                    config_changed = True
                    print(f"[DEPLOY] CPU changed: {existing_cpu} -> {cpu_cores}")

                # 检查内存是否变化
                if existing_memory != memory_mb:
                    config_changed = True
                    print(f"[DEPLOY] Memory changed: {existing_memory} -> {memory_mb}")

                # 检查端口数量是否变化
                existing_port_set = set(existing_ports.keys())
                current_port_set = set(current_ports_config.keys())

                if existing_port_set != current_port_set:
                    config_changed = True
                    print(f"[DEPLOY] Port set changed: {existing_port_set} -> {current_port_set}")
                else:
                    # 检查网络配置是否变化
                    for port in current_port_set:
                        if existing_ports.get(port) != current_ports_config.get(port):
                            config_changed = True
                            print(
                                f"[DEPLOY] Port {port} network changed: {existing_ports.get(port)} -> {current_ports_config.get(port)}")
                            break

                if config_changed:
                    print(f"[DEPLOY] VM {vm_name} needs rebuild due to config changes")
                    # 标记需要重建
                    vms_need_rebuild[node_id] = {
                        "vm_name": vm_name,
                        "image": image,
                        "ports_config": current_ports_config,
                        "cpu": cpu_cores,
                        "memory": memory_mb
                    }
                else:
                    print(f"[DEPLOY] VM {vm_name} config unchanged, skipping")

                # 更新数据库中的端口信息
                if db_session:
                    from models import DeployedResource
                    res = db_session.query(DeployedResource).filter_by(
                        task=task, resource_name=vm_name
                    ).first()
                    if res:
                        extra = json.loads(res.extra_info) if res.extra_info else {}
                        extra["ports"] = current_ports_config
                        extra["standalone_networks"] = standalone_networks
                        res.extra_info = json.dumps(extra)

                continue

            # 新建 VM
            print(f"[DEPLOY] Creating FW: {vm_name}")

            if not os.path.exists(image):
                raise Exception(f"镜像不存在: {image}")

            # 获取 CPU 和内存配置
            cpu_cores = node.get("data", {}).get("cpu", 2)
            memory_mb = node.get("data", {}).get("memory", 4096)

            # 验证配置范围
            cpu_cores = max(1, min(cpu_cores, 32))  # 1-32 核
            memory_mb = max(512, min(memory_mb, 131072))  # 512MB - 128GB

            print(f"[DEPLOY] VM config: CPU={cpu_cores} cores, Memory={memory_mb} MB")

            # 管理网络（eth0）
            nets = f"--network network={MGMT_BRIDGE},model=virtio "

            # 按端口顺序添加网络
            for port in sorted(current_ports_config.keys(), key=lambda x: int(x.replace('eth', ''))):
                net = current_ports_config[port]
                if net:
                    nets += f"--network network={net},model=virtio "

            cmd = f"""virt-install --name {vm_name} \
                --memory {memory_mb} --vcpus {cpu_cores} \
                --disk path={image},format=qcow2 \
                --import --noautoconsole --os-variant generic \
                --graphics vnc,listen=127.0.0.1 \
                --serial pty \
                --console pty,target_type=serial \
                {nets}"""

            sh(cmd)

            deployed_resources.append({
                "type": "vm",
                "name": vm_name,
                "node_id": node_id,
                "image": image,
                "cpu": cpu_cores,
                "memory": memory_mb,
                "ports": current_ports_config,
                "standalone_networks": standalone_networks
            })

        # ========== 2.5 重建需要更新网络的 VM ==========
        for node_id, rebuild_info in vms_need_rebuild.items():
            vm_name = rebuild_info["vm_name"]
            image = rebuild_info["image"]
            ports_config = rebuild_info["ports_config"]
            cpu_cores = rebuild_info.get("cpu", 2)
            memory_mb = rebuild_info.get("memory", 4096)

            print(f"[DEPLOY] Rebuilding VM {vm_name}")

            # 删除旧的数据库记录
            if db_session:
                from models import DeployedResource
                db_session.query(DeployedResource).filter_by(
                    task=task, resource_name=vm_name
                ).delete()

            # 重建 VM
            rebuild_resources = rebuild_vm_with_new_networks(
                vm_name, node_id, task, image, ports_config,
                cpu_cores=cpu_cores, memory_mb=memory_mb, db_session=db_session
            )
            deployed_resources.extend(rebuild_resources)

        # ========== 3. 处理 PC 容器 ==========
        pc_info = []
        for node in nodes:
            if node["type"] != "pc":
                continue

            node_id = node["id"]
            container_name = f"{task}_{node_id}"

            port_connections = get_node_port_connections(node_id, edges, edge_net_map)
            node_ports = node.get("data", {}).get("ports", ["eth0", "eth1"])

            if node_id in existing_nodes and existing_nodes[node_id]["type"] == "container":
                print(f"[DEPLOY] Container {container_name} exists, checking network changes")
                print(f"[DEPLOY] PC {node_id} ports: {node_ports}")
                print(f"[DEPLOY] PC {node_id} port_connections: {port_connections}")

                existing_nets = set(existing_nodes[node_id]["extra"].get("connected_nets", []))
                print(f"[DEPLOY] PC {node_id} existing_nets: {existing_nets}")

                # 当前需要的网络
                current_nets = set()
                for port_name in node_ports:
                    if port_name == "eth0":
                        continue  # eth0 是管理口

                    if port_name in port_connections:
                        docker_net = port_connections[port_name].get("docker_net")
                        print(f"[DEPLOY] PC {node_id} port {port_name} -> docker_net: {docker_net}")
                        if docker_net:
                            current_nets.add(docker_net)
                    else:
                        # 没有连线的端口，创建独立网络
                        standalone_br = f"br-{task[:3]}{node_id}{port_name}"[:15]
                        standalone_docker_net = f"dn-{task[:3]}{node_id}{port_name}"[:15]

                        # 检查是否已存在
                        result_check = sh(
                            f"docker network ls --format '{{{{.Name}}}}' | grep -x '{standalone_docker_net}'")
                        if result_check.returncode != 0 or standalone_docker_net not in result_check.stdout:
                            print(f"[DEPLOY] Creating standalone network for {container_name}:{port_name}")
                            create_bridge(standalone_br)
                            deployed_resources.append({
                                "type": "bridge",
                                "name": standalone_br,
                                "node_id": node_id,
                                "port": port_name,
                                "standalone": True
                            })

                            create_docker_macvlan_network(standalone_docker_net, standalone_br)
                            deployed_resources.append({
                                "type": "docker_net",
                                "name": standalone_docker_net,
                                "bridge": standalone_br,
                                "node_id": node_id,
                                "port": port_name,
                                "standalone": True
                            })

                        current_nets.add(standalone_docker_net)
                        print(
                            f"[DEPLOY] PC {node_id} port {port_name} -> standalone docker_net: {standalone_docker_net}")

                print(f"[DEPLOY] PC {node_id} current_nets: {current_nets}")

                # 连接新网络
                new_nets = current_nets - existing_nets
                print(f"[DEPLOY] PC {node_id} new_nets to connect: {new_nets}")
                for net in new_nets:
                    print(f"[DEPLOY] Connecting {container_name} to {net}")
                    sh(f"docker network connect {net} {container_name}")

                # 断开旧网络（但不断开管理网络）
                removed_nets = existing_nets - current_nets
                for net in removed_nets:
                    if net != DOCKER_MGMT_NET:
                        print(f"[DEPLOY] Disconnecting {container_name} from {net}")
                        sh(f"docker network disconnect {net} {container_name} 2>/dev/null || true")

                # 更新数据库中的网络信息
                if db_session:
                    from models import DeployedResource
                    res = db_session.query(DeployedResource).filter_by(
                        task=task, resource_name=container_name
                    ).first()
                    if res:
                        extra = json.loads(res.extra_info) if res.extra_info else {}
                        extra["connected_nets"] = list(current_nets)
                        res.extra_info = json.dumps(extra)

                pc_info.append({
                    "id": node_id,
                    "container": container_name,
                    "mgmt_ip": existing_nodes[node_id]["extra"].get("mgmt_ip", "")
                })
                continue

            print(f"[DEPLOY] Creating PC: {container_name}")

            result = sh(f"docker run -dit --name {container_name} "
                        f"--hostname {node_id} "
                        f"--network {DOCKER_MGMT_NET} "
                        f"--privileged "
                        f"ubuntu:pc bash")
            if result.returncode != 0:
                raise Exception(f"容器创建失败: {result.stderr}")

            connected_nets = [DOCKER_MGMT_NET]  # 管理网络在最前面，保证 eth0 顺序
            # 为所有端口创建网络连接（除了 eth0 管理口）
            for port_name in node_ports:
                if port_name == "eth0":
                    continue  # eth0 是管理口，已通过 --network 连接

                if port_name in port_connections:
                    # 有连线的端口，连接到对应网络
                    docker_net = port_connections[port_name].get("docker_net")
                    if docker_net:
                        sh(f"docker network connect {docker_net} {container_name}")
                        connected_nets.append(docker_net)
                else:
                    # 没有连线的端口，创建独立网络
                    standalone_br = f"br-{task[:3]}{node_id}{port_name}"[:15]
                    standalone_docker_net = f"dn-{task[:3]}{node_id}{port_name}"[:15]

                    # 检查是否已存在
                    result_check = sh(f"docker network ls --format '{{{{.Name}}}}' | grep -x '{standalone_docker_net}'")
                    if result_check.returncode != 0 or standalone_docker_net not in result_check.stdout:
                        print(f"[DEPLOY] Creating standalone network for {container_name}:{port_name}")
                        create_bridge(standalone_br)
                        deployed_resources.append({
                            "type": "bridge",
                            "name": standalone_br,
                            "node_id": node_id,
                            "port": port_name,
                            "standalone": True
                        })

                        create_docker_macvlan_network(standalone_docker_net, standalone_br)
                        deployed_resources.append({
                            "type": "docker_net",
                            "name": standalone_docker_net,
                            "bridge": standalone_br,
                            "node_id": node_id,
                            "port": port_name,
                            "standalone": True
                        })

                    sh(f"docker network connect {standalone_docker_net} {container_name}")
                    connected_nets.append(standalone_docker_net)

            result = sh(
                f"docker inspect -f '{{{{range .NetworkSettings.Networks}}}}{{{{.IPAddress}}}} {{{{end}}}}' {container_name}")
            mgmt_ip = result.stdout.strip().split()[0] if result.stdout.strip() else "DHCP"

            deployed_resources.append({
                "type": "container",
                "name": container_name,
                "node_id": node_id,
                "mgmt_ip": mgmt_ip,
                "connected_nets": connected_nets
            })

            pc_info.append({
                "id": node_id,
                "container": container_name,
                "mgmt_ip": mgmt_ip
            })

        # ========== 4. 删除不再需要的资源 ==========
        for node_id, info in existing_nodes.items():
            if node_id not in current_node_ids:
                print(f"[DEPLOY] Removing old node: {node_id}")
                if info["type"] == "vm":
                    sh(f"virsh destroy {info['name']} 2>/dev/null || true")
                    sh(f"virsh undefine {info['name']} 2>/dev/null || true")
                elif info["type"] == "container":
                    sh(f"docker rm -f {info['name']} 2>/dev/null || true")

                if db_session:
                    from models import DeployedResource
                    db_session.query(DeployedResource).filter_by(
                        task=task, resource_name=info['name']
                    ).delete()

        for edge_id, nets in existing_networks.items():
            if edge_id not in current_edge_ids:
                print(f"[DEPLOY] Removing old network: {edge_id}")
                if "docker_net" in nets:
                    delete_docker_network(nets["docker_net"])
                if "libvirt_net" in nets:
                    unregister_libvirt_network(nets["libvirt_net"])
                if "bridge" in nets:
                    delete_bridge(nets["bridge"])

                if db_session:
                    from models import DeployedResource
                    for key in ["bridge", "libvirt_net", "docker_net"]:
                        if key in nets:
                            db_session.query(DeployedResource).filter_by(
                                task=task, resource_name=nets[key]
                            ).delete()

        # 清理不再需要的独立网络
        # 检查所有已部署的独立网络，如果对应的端口不再存在，则删除
        if db_session:
            from models import DeployedResource
            standalone_resources = db_session.query(DeployedResource).filter_by(task=task).all()
            for res in standalone_resources:
                extra = json.loads(res.extra_info) if res.extra_info else {}
                if extra.get("standalone"):
                    res_node_id = extra.get("node_id")
                    res_port = extra.get("port")

                    # 检查对应节点是否还存在
                    node_exists = res_node_id in current_node_ids
                    port_exists = False

                    if node_exists:
                        # 检查端口是否还在
                        for node in nodes:
                            if node["id"] == res_node_id:
                                ports = node.get("data", {}).get("ports", [])
                                port_exists = res_port in ports
                                break

                    if not node_exists or not port_exists:
                        print(f"[DEPLOY] Removing orphan standalone resource: {res.resource_name}")
                        if res.resource_type == "libvirt_net":
                            unregister_libvirt_network(res.resource_name)
                        elif res.resource_type == "bridge":
                            delete_bridge(res.resource_name)
                        db_session.delete(res)

        # 保存新资源
        if db_session:
            from models import DeployedResource
            for res in deployed_resources:
                db_session.merge(DeployedResource(
                    id=f"{task}_{res['type']}_{res['name']}",
                    task=task,
                    resource_type=res["type"],
                    resource_name=res["name"],
                    extra_info=json.dumps(res)
                ))
            db_session.commit()

        return {
            "ok": True,
            "message": "部署成功（增量更新）",
            "resources": deployed_resources,
            "pc_info": pc_info,
            "rebuilt_vms": list(vms_need_rebuild.keys()) if vms_need_rebuild else None
        }

    except Exception as e:
        print(f"[ERROR] Deployment failed: {e}")
        import traceback
        traceback.print_exc()

        for res in deployed_resources:
            try:
                if res["type"] == "vm":
                    sh(f"virsh destroy {res['name']} 2>/dev/null || true")
                    sh(f"virsh undefine {res['name']} 2>/dev/null || true")
                elif res["type"] == "container":
                    sh(f"docker rm -f {res['name']} 2>/dev/null || true")
                elif res["type"] == "docker_net":
                    delete_docker_network(res["name"])
                elif res["type"] == "libvirt_net":
                    unregister_libvirt_network(res["name"])
                elif res["type"] == "bridge":
                    delete_bridge(res["name"])
            except:
                pass

        return {"ok": False, "error": str(e)}


def destroy(task, db_session=None):
    """销毁任务的所有资源"""
    print(f"[DESTROY] Task: {task}")
    destroyed = []
    errors = []

    type_order = {"container": 0, "vm": 1, "docker_net": 2, "libvirt_net": 3, "bridge": 4}

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()
            print(f"[DESTROY] Found {len(resources)} resources")

            for res in sorted(resources, key=lambda x: type_order.get(x.resource_type, 99)):
                try:
                    print(f"[DESTROY] {res.resource_type}: {res.resource_name}")

                    if res.resource_type == "vm":
                        sh(f"virsh destroy {res.resource_name} 2>/dev/null || true")
                        sh(f"virsh undefine {res.resource_name} 2>/dev/null || true")
                        destroyed.append(f"VM: {res.resource_name}")

                    elif res.resource_type == "container":
                        sh(f"docker rm -f {res.resource_name} 2>/dev/null || true")
                        destroyed.append(f"Container: {res.resource_name}")

                    elif res.resource_type == "docker_net":
                        delete_docker_network(res.resource_name)
                        destroyed.append(f"DockerNet: {res.resource_name}")

                    elif res.resource_type == "libvirt_net":
                        unregister_libvirt_network(res.resource_name)
                        destroyed.append(f"LibvirtNet: {res.resource_name}")

                    elif res.resource_type == "bridge":
                        delete_bridge(res.resource_name)
                        destroyed.append(f"Bridge: {res.resource_name}")

                    db_session.delete(res)

                except Exception as e:
                    errors.append(f"{res.resource_name}: {str(e)}")

            db_session.commit()

        else:
            result = sh(f"virsh list --all --name | grep '^{task}_' || true")
            for vm in result.stdout.strip().split('\n'):
                if vm:
                    sh(f"virsh destroy {vm} 2>/dev/null || true")
                    sh(f"virsh undefine {vm} 2>/dev/null || true")
                    destroyed.append(f"VM: {vm}")

            result = sh(f"docker ps -a --format '{{{{.Names}}}}' | grep '^{task}_' || true")
            for c in result.stdout.strip().split('\n'):
                if c:
                    sh(f"docker rm -f {c} 2>/dev/null || true")
                    destroyed.append(f"Container: {c}")

            result = sh(f"docker network ls --format '{{{{.Name}}}}' | grep '^dn-{task[:3]}' || true")
            for net in result.stdout.strip().split('\n'):
                if net:
                    delete_docker_network(net)
                    destroyed.append(f"DockerNet: {net}")

            result = sh(f"virsh net-list --all --name | grep '^{task}-' || true")
            for net in result.stdout.strip().split('\n'):
                if net:
                    unregister_libvirt_network(net)
                    destroyed.append(f"LibvirtNet: {net}")

            result = sh(f"ip -o link show type bridge | grep 'br-{task[:3]}' | awk -F': ' '{{print $2}}' || true")
            for br in result.stdout.strip().split('\n'):
                if br:
                    delete_bridge(br)
                    destroyed.append(f"Bridge: {br}")

        return {
            "ok": True,
            "message": "清理完成",
            "destroyed": destroyed,
            "errors": errors if errors else None
        }

    except Exception as e:
        return {"ok": False, "error": str(e), "destroyed": destroyed}


def get_status(task, db_session=None):
    """获取任务状态"""
    status = {"vms": [], "containers": [], "networks": []}

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                extra = json.loads(res.extra_info) if res.extra_info else {}

                if res.resource_type == "vm":
                    result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                    state = result.stdout.strip() if result.returncode == 0 else "unknown"
                    status["vms"].append({
                        "name": res.resource_name,
                        "state": state,
                        "node_id": extra.get("node_id"),
                        "ports": extra.get("ports", {})
                    })

                elif res.resource_type == "container":
                    result = sh(f"docker inspect -f '{{{{.State.Status}}}}' {res.resource_name} 2>/dev/null")
                    state = result.stdout.strip() if result.returncode == 0 else "unknown"

                    # 获取容器内所有网卡的 IP 信息
                    interfaces = {}
                    if state == "running":
                        # 使用 docker exec 获取容器内的网卡信息
                        ip_result = sh(f"docker exec {res.resource_name} ip -4 addr show 2>/dev/null")
                        if ip_result.returncode == 0:
                            current_iface = None
                            for line in ip_result.stdout.split('\n'):
                                # 匹配网卡名称行，如 "2: eth0@if123: <BROADCAST..."
                                if ': ' in line and not line.startswith(' '):
                                    parts = line.split(': ')
                                    if len(parts) >= 2:
                                        iface_name = parts[1].split('@')[0]  # 去掉 @ifXXX 部分
                                        current_iface = iface_name
                                # 匹配 IP 地址行，如 "    inet 192.168.1.100/24 ..."
                                elif 'inet ' in line and current_iface:
                                    parts = line.strip().split()
                                    if len(parts) >= 2:
                                        ip_with_mask = parts[1]
                                        ip_addr = ip_with_mask.split('/')[0]  # 去掉子网掩码
                                        interfaces[current_iface] = ip_addr

                    status["containers"].append({
                        "name": res.resource_name,
                        "state": state,
                        "node_id": extra.get("node_id"),
                        "mgmt_ip": extra.get("mgmt_ip"),
                        "interfaces": interfaces  # 新增：所有网卡的 IP
                    })

                elif res.resource_type in ("bridge", "libvirt_net", "docker_net"):
                    status["networks"].append({
                        "type": res.resource_type,
                        "name": res.resource_name
                    })

        return {"ok": True, "status": status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_fw_images(image_dir="/img"):
    """列出防火墙镜像"""
    images = []
    try:
        if os.path.exists(image_dir):
            for f in os.listdir(image_dir):
                if f.endswith('.qcow2'):
                    images.append({"path": os.path.join(image_dir, f), "name": f})
    except Exception as e:
        print(f"[ERROR] {e}")

    if not images:
        images.append({"path": DEFAULT_FW_IMAGE, "name": "默认防火墙镜像"})

    return images


def shutdown_all(task, db_session=None):
    """关闭任务中所有机器（VM 和容器）"""
    print(f"[SHUTDOWN] Task: {task}")
    shutdown_count = 0
    errors = []

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                try:
                    if res.resource_type == "vm":
                        # 检查 VM 状态
                        result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and "running" in result.stdout.lower():
                            # 使用 destroy 强制关机（因为很多防火墙镜像不响应 ACPI shutdown）
                            sh(f"virsh destroy {res.resource_name}")
                            print(f"[SHUTDOWN] VM {res.resource_name} destroyed (forced shutdown)")
                            shutdown_count += 1

                    elif res.resource_type == "container":
                        # 检查容器状态
                        result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and result.stdout.strip() == "true":
                            sh(f"docker stop {res.resource_name}")
                            print(f"[SHUTDOWN] Container {res.resource_name} stopped")
                            shutdown_count += 1

                except Exception as e:
                    errors.append(f"{res.resource_name}: {str(e)}")

        else:
            # 无数据库时，通过名称前缀查找
            result = sh(f"virsh list --name | grep '^{task}_' || true")
            for vm in result.stdout.strip().split('\n'):
                if vm:
                    sh(f"virsh destroy {vm}")
                    shutdown_count += 1

            result = sh(f"docker ps --format '{{{{.Names}}}}' | grep '^{task}_' || true")
            for c in result.stdout.strip().split('\n'):
                if c:
                    sh(f"docker stop {c}")
                    shutdown_count += 1

        return {
            "ok": True,
            "message": f"已关机 {shutdown_count} 台设备",
            "shutdown_count": shutdown_count,
            "errors": errors if errors else None
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


def startup_all(task, db_session=None):
    """启动任务中所有机器（VM 和容器）"""
    print(f"[STARTUP] Task: {task}")
    startup_count = 0
    errors = []

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                try:
                    if res.resource_type == "vm":
                        # 检查 VM 状态
                        result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and "shut off" in result.stdout.lower():
                            sh(f"virsh start {res.resource_name}")
                            print(f"[STARTUP] VM {res.resource_name} started")
                            startup_count += 1

                    elif res.resource_type == "container":
                        # 检查容器状态
                        result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and result.stdout.strip() == "false":
                            # 获取容器的网络连接信息（按正确顺序）
                            extra = json.loads(res.extra_info) if res.extra_info else {}
                            connected_nets = extra.get("connected_nets", [])

                            # 确保管理网络在列表最前面（兼容旧数据）
                            if connected_nets and DOCKER_MGMT_NET not in connected_nets:
                                connected_nets = [DOCKER_MGMT_NET] + connected_nets
                            elif not connected_nets:
                                # 没有记录，尝试从当前容器获取
                                net_result = sh(
                                    f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {res.resource_name}")
                                if net_result.returncode == 0:
                                    try:
                                        current_networks = json.loads(net_result.stdout.strip())
                                        connected_nets = list(current_networks.keys())
                                        # 确保管理网络在前面
                                        if DOCKER_MGMT_NET in connected_nets:
                                            connected_nets.remove(DOCKER_MGMT_NET)
                                            connected_nets = [DOCKER_MGMT_NET] + connected_nets
                                    except:
                                        pass

                            # 先启动容器
                            sh(f"docker start {res.resource_name}")
                            print(f"[STARTUP] Container {res.resource_name} started")

                            # 如果有记录的网络顺序，则重新按顺序连接网络
                            if connected_nets:
                                print(f"[STARTUP] Reconnecting networks in order: {connected_nets}")

                                # 获取当前连接的网络
                                net_result = sh(
                                    f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {res.resource_name}")
                                if net_result.returncode == 0:
                                    try:
                                        current_networks = json.loads(net_result.stdout.strip())
                                        current_net_names = list(current_networks.keys())

                                        # 断开所有当前网络
                                        for net_name in current_net_names:
                                            sh(f"docker network disconnect {net_name} {res.resource_name} 2>/dev/null || true")

                                        # 按记录的顺序重新连接
                                        for net_name in connected_nets:
                                            result = sh(
                                                f"docker network connect {net_name} {res.resource_name} 2>/dev/null")
                                            if result.returncode == 0:
                                                print(f"[STARTUP] Connected {res.resource_name} to {net_name}")
                                            else:
                                                print(f"[STARTUP] Failed to connect {res.resource_name} to {net_name}")
                                    except json.JSONDecodeError:
                                        print(f"[WARN] Failed to parse network info for {res.resource_name}")

                            startup_count += 1

                except Exception as e:
                    errors.append(f"{res.resource_name}: {str(e)}")

        else:
            # 无数据库时，通过名称前缀查找（无法保证网络顺序）
            result = sh(f"virsh list --all --name | grep '^{task}_' || true")
            for vm in result.stdout.strip().split('\n'):
                if vm:
                    state_result = sh(f"virsh domstate {vm} 2>/dev/null")
                    if state_result.returncode == 0 and "shut off" in state_result.stdout.lower():
                        sh(f"virsh start {vm}")
                        startup_count += 1

            result = sh(f"docker ps -a --format '{{{{.Names}}}}' | grep '^{task}_' || true")
            for c in result.stdout.strip().split('\n'):
                if c:
                    state_result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {c} 2>/dev/null")
                    if state_result.returncode == 0 and state_result.stdout.strip() == "false":
                        sh(f"docker start {c}")
                        startup_count += 1

        return {
            "ok": True,
            "message": f"已开机 {startup_count} 台设备",
            "startup_count": startup_count,
            "errors": errors if errors else None
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_node_state(task, node_id, db_session=None):
    """获取单个设备的状态"""
    try:
        if db_session:
            from models import DeployedResource
            # 查找设备
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                extra = json.loads(res.extra_info) if res.extra_info else {}
                if extra.get("node_id") == node_id:
                    if res.resource_type == "vm":
                        result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                        state = result.stdout.strip() if result.returncode == 0 else "unknown"
                        return {
                            "ok": True,
                            "node_id": node_id,
                            "type": "vm",
                            "name": res.resource_name,
                            "state": state,
                            "running": "running" in state.lower()
                        }
                    elif res.resource_type == "container":
                        result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {res.resource_name} 2>/dev/null")
                        running = result.returncode == 0 and result.stdout.strip() == "true"
                        return {
                            "ok": True,
                            "node_id": node_id,
                            "type": "container",
                            "name": res.resource_name,
                            "state": "running" if running else "stopped",
                            "running": running
                        }

            return {"ok": False, "error": f"设备 {node_id} 未找到"}
        else:
            return {"ok": False, "error": "需要数据库连接"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def shutdown_node(task, node_id, db_session=None):
    """关闭单个设备"""
    print(f"[SHUTDOWN] Task: {task}, Node: {node_id}")

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                extra = json.loads(res.extra_info) if res.extra_info else {}
                if extra.get("node_id") == node_id:
                    if res.resource_type == "vm":
                        result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and "running" in result.stdout.lower():
                            sh(f"virsh destroy {res.resource_name}")
                            return {"ok": True, "message": f"VM {node_id} 已关机", "node_id": node_id}
                        else:
                            return {"ok": True, "message": f"VM {node_id} 已经是关机状态", "node_id": node_id}

                    elif res.resource_type == "container":
                        result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and result.stdout.strip() == "true":
                            sh(f"docker stop {res.resource_name}")
                            return {"ok": True, "message": f"容器 {node_id} 已关机", "node_id": node_id}
                        else:
                            return {"ok": True, "message": f"容器 {node_id} 已经是关机状态", "node_id": node_id}

            return {"ok": False, "error": f"设备 {node_id} 未找到"}
        else:
            return {"ok": False, "error": "需要数据库连接"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def startup_node(task, node_id, db_session=None):
    """启动单个设备"""
    print(f"[STARTUP] Task: {task}, Node: {node_id}")

    try:
        if db_session:
            from models import DeployedResource
            resources = db_session.query(DeployedResource).filter_by(task=task).all()

            for res in resources:
                extra = json.loads(res.extra_info) if res.extra_info else {}
                if extra.get("node_id") == node_id:
                    if res.resource_type == "vm":
                        result = sh(f"virsh domstate {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and "shut off" in result.stdout.lower():
                            sh(f"virsh start {res.resource_name}")
                            return {"ok": True, "message": f"VM {node_id} 已开机", "node_id": node_id}
                        else:
                            return {"ok": True, "message": f"VM {node_id} 已经是运行状态", "node_id": node_id}

                    elif res.resource_type == "container":
                        result = sh(f"docker inspect -f '{{{{.State.Running}}}}' {res.resource_name} 2>/dev/null")
                        if result.returncode == 0 and result.stdout.strip() == "false":
                            connected_nets = extra.get("connected_nets", [])

                            # 确保管理网络在列表最前面
                            if connected_nets and DOCKER_MGMT_NET not in connected_nets:
                                connected_nets = [DOCKER_MGMT_NET] + connected_nets

                            # 启动容器
                            sh(f"docker start {res.resource_name}")

                            # 重新按顺序连接网络
                            if connected_nets:
                                net_result = sh(
                                    f"docker inspect -f '{{{{json .NetworkSettings.Networks}}}}' {res.resource_name}")
                                if net_result.returncode == 0:
                                    try:
                                        current_networks = json.loads(net_result.stdout.strip())
                                        for net_name in list(current_networks.keys()):
                                            sh(f"docker network disconnect {net_name} {res.resource_name} 2>/dev/null || true")
                                        for net_name in connected_nets:
                                            sh(f"docker network connect {net_name} {res.resource_name} 2>/dev/null || true")
                                    except:
                                        pass

                            return {"ok": True, "message": f"容器 {node_id} 已开机", "node_id": node_id}
                        else:
                            return {"ok": True, "message": f"容器 {node_id} 已经是运行状态", "node_id": node_id}

            return {"ok": False, "error": f"设备 {node_id} 未找到"}
        else:
            return {"ok": False, "error": "需要数据库连接"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def restart_node(task, node_id, db_session=None):
    """重启单个设备"""
    print(f"[RESTART] Task: {task}, Node: {node_id}")

    try:
        # 先关机
        shutdown_result = shutdown_node(task, node_id, db_session)
        if not shutdown_result.get("ok"):
            return shutdown_result

        # 等待一下确保关机完成
        import time
        time.sleep(1)

        # 再开机
        startup_result = startup_node(task, node_id, db_session)
        if startup_result.get("ok"):
            return {"ok": True, "message": f"设备 {node_id} 已重启", "node_id": node_id}
        else:
            return startup_result
    except Exception as e:
        return {"ok": False, "error": str(e)}