// API 封装模块

const API_BASE = ''

// ========== 任务管理 ==========

export async function listTasks() {
  const response = await fetch(`${API_BASE}/tasks`)
  if (!response.ok) {
    throw new Error(`获取任务列表失败: ${response.status}`)
  }
  return response.json()
}

export async function createTask(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`创建任务失败: ${response.status}`)
  }
  return response.json()
}

export async function deleteTask(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}`, {
    method: 'DELETE'
  })
  if (!response.ok) {
    throw new Error(`删除任务失败: ${response.status}`)
  }
  return response.json()
}

export async function getTask(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}`)
  if (!response.ok) {
    throw new Error(`获取任务详情失败: ${response.status}`)
  }
  return response.json()
}

// ========== 拓扑管理 ==========

export async function saveTopology(task, topo) {
  const response = await fetch(`${API_BASE}/tasks/${task}/topology`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(topo)
  })
  if (!response.ok) {
    throw new Error(`保存拓扑失败: ${response.status}`)
  }
  return response.json()
}

export async function getTopology(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/topology`)
  if (!response.ok) {
    throw new Error(`获取拓扑失败: ${response.status}`)
  }
  return response.json()
}

// ========== 部署管理 ==========

export async function deploy(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/deploy`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`部署失败: ${response.status}`)
  }
  return response.json()
}

export async function destroy(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/destroy`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`销毁失败: ${response.status}`)
  }
  return response.json()
}

export async function getTaskStatus(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/status`)
  if (!response.ok) {
    throw new Error(`获取状态失败: ${response.status}`)
  }
  return response.json()
}

// ========== 开关机管理 ==========

export async function shutdownAll(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/shutdown`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`关机失败: ${response.status}`)
  }
  return response.json()
}

export async function startupAll(task) {
  const response = await fetch(`${API_BASE}/tasks/${task}/startup`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`开机失败: ${response.status}`)
  }
  return response.json()
}

// ========== 单个设备操作 ==========

export async function shutdownNode(task, nodeId) {
  const response = await fetch(`${API_BASE}/tasks/${task}/nodes/${nodeId}/shutdown`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`设备关机失败: ${response.status}`)
  }
  return response.json()
}

export async function startupNode(task, nodeId) {
  const response = await fetch(`${API_BASE}/tasks/${task}/nodes/${nodeId}/startup`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`设备开机失败: ${response.status}`)
  }
  return response.json()
}

export async function restartNode(task, nodeId) {
  const response = await fetch(`${API_BASE}/tasks/${task}/nodes/${nodeId}/restart`, {
    method: 'POST'
  })
  if (!response.ok) {
    throw new Error(`设备重启失败: ${response.status}`)
  }
  return response.json()
}

export async function getNodeState(task, nodeId) {
  const response = await fetch(`${API_BASE}/tasks/${task}/nodes/${nodeId}/state`)
  if (!response.ok) {
    throw new Error(`获取设备状态失败: ${response.status}`)
  }
  return response.json()
}

// ========== 防火墙镜像 ==========

export async function listImages() {
  const response = await fetch(`${API_BASE}/images`)
  if (!response.ok) {
    throw new Error(`获取镜像列表失败: ${response.status}`)
  }
  return response.json()
}

// ========== WebSocket - 容器终端 ==========

export function createWebShell(container, onMessage, onError, onClose) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws/${container}`)

  ws.onopen = () => {
    console.log(`WebShell connected to ${container}`)
  }

  ws.onmessage = (event) => {
    if (onMessage) onMessage(event.data)
  }

  ws.onerror = (event) => {
    console.error('WebSocket error:', event)
    if (onError) onError(event)
  }

  ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason)
    if (onClose) onClose(event)
  }

  return {
    send: (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    },
    resize: (rows, cols) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(`\x1b[8;${rows};${cols}t`)
      }
    },
    close: () => ws.close(),
    getState: () => ws.readyState
  }
}

// ========== WebSocket - VM 串口终端 ==========

export function createVMShell(vmName, onMessage, onError, onClose) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/vmws/${vmName}`)

  ws.onopen = () => {
    console.log(`VMShell connected to ${vmName}`)
  }

  ws.onmessage = (event) => {
    if (onMessage) onMessage(event.data)
  }

  ws.onerror = (event) => {
    console.error('VM WebSocket error:', event)
    if (onError) onError(event)
  }

  ws.onclose = (event) => {
    console.log('VM WebSocket closed:', event.code, event.reason)
    if (onClose) onClose(event)
  }

  return {
    send: (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    },
    resize: (rows, cols) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(`\x1b[8;${rows};${cols}t`)
      }
    },
    close: () => ws.close(),
    getState: () => ws.readyState
  }
}

// ========== VM 控制台状态检查 ==========

export async function getVMConsoleInfo(vmName) {
  const response = await fetch(`${API_BASE}/vms/${vmName}/console`)
  if (!response.ok) {
    throw new Error(`获取 VM 控制台状态失败: ${response.status}`)
  }
  return response.json()
}

// ========== 健康检查 ==========

export async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE}/health`)
    return response.ok
  } catch {
    return false
  }
}

// ========== 系统资源 ==========

export async function getSystemResources() {
  const response = await fetch(`${API_BASE}/system/resources`)
  if (!response.ok) {
    throw new Error(`获取系统资源失败: ${response.status}`)
  }
  return response.json()
}

// 兼容旧API
export const save = saveTopology