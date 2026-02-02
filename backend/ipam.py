import ipaddress

# 管理网络配置（桥接物理网卡，与宿主机同网段）
MGMT_BRIDGE = "br-mgmt"
MGMT_NETWORK = "192.168.168.0/24"
MGMT_GATEWAY = "192.168.168.1"
MGMT_DHCP_START = "192.168.168.50"
MGMT_DHCP_END = "192.168.168.200"

# 静态分配范围（DHCP范围外）: 201-250
STATIC_IP_START = 201
STATIC_IP_END = 250

# 已使用的静态IP
used_static_ips = set()


def alloc_mgmt():
    """
    分配管理网络静态IP（DHCP范围外）
    返回: IP地址字符串，如 "192.168.168.201"
    """
    network = ipaddress.ip_network(MGMT_NETWORK, strict=False)
    base = str(network.network_address).rsplit('.', 1)[0]  # "192.168.168"

    for i in range(STATIC_IP_START, STATIC_IP_END + 1):
        ip = f"{base}.{i}"
        if ip not in used_static_ips:
            used_static_ips.add(ip)
            return ip

    raise Exception("静态IP池已耗尽")


def release_mgmt(ip):
    """释放管理网络IP"""
    used_static_ips.discard(ip)


def get_mgmt_config():
    """获取管理网络配置"""
    network = ipaddress.ip_network(MGMT_NETWORK, strict=False)
    return {
        "bridge": MGMT_BRIDGE,
        "network": MGMT_NETWORK,
        "gateway": MGMT_GATEWAY,
        "netmask": str(network.netmask),
        "prefix": network.prefixlen,
        "dhcp_start": MGMT_DHCP_START,
        "dhcp_end": MGMT_DHCP_END
    }