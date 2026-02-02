<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="logo">
        <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
        <span class="logo-text">VTTP</span>
      </div>

      <div class="task-controls">
        <div class="task-selector">
          <label>当前任务</label>
          <select v-model="currentTask" @change="onTaskChange">
            <option value="">选择任务...</option>
            <option v-for="t in tasks" :key="t.name" :value="t.name">
              {{ t.name }} ({{ t.status }})
            </option>
          </select>
        </div>

        <div class="task-input">
          <input
            v-model="newTaskName"
            placeholder="新任务名称..."
            @keyup.enter="createNewTask"
          />
          <button class="btn-create" @click="createNewTask" :disabled="!newTaskName">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            创建
          </button>
        </div>
      </div>

      <div class="header-actions">
        <button class="btn-refresh" @click="refreshTasks" title="刷新任务列表">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </button>
        <div class="status-indicator" :class="{ active: isConnected }">
          <span class="dot"></span>
          {{ isConnected ? '已连接' : '未连接' }}
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <div v-if="!currentTask" class="welcome-screen">
        <div class="welcome-content">
          <svg class="welcome-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
          </svg>
          <h2>欢迎使用 VTTP </h2>
          <p>网络拓扑实验平台</p>
          <div class="welcome-actions">
            <div class="action-card" @click="focusNewTask">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12h14"/>
              </svg>
              <span>创建新任务</span>
            </div>
            <div class="action-card" v-if="tasks.length > 0" @click="selectFirstTask">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 12h18M3 6h18M3 18h18"/>
              </svg>
              <span>选择已有任务</span>
            </div>
          </div>
        </div>
      </div>

      <template v-else>
        <!-- 任务信息栏 -->
        <div class="task-info-bar">
          <div class="task-meta">
            <h2>{{ currentTask }}</h2>
            <span class="task-status" :class="currentTaskStatus">{{ currentTaskStatus }}</span>
          </div>
          <div class="task-actions">
            <button class="btn-action btn-status" @click="refreshStatus" title="刷新状态">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
              状态
            </button>
            <button class="btn-action btn-delete-task" @click="deleteCurrentTask" title="删除任务">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3,6 5,6 21,6"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
              删除任务
            </button>
          </div>
        </div>

        <!-- 拓扑编辑器 -->
        <Topology
          :task="currentTask"
          @status="updateStatus"
          @deployed="onDeployed"
          @destroyed="onDestroyed"
        />
      </template>
    </main>

    <!-- 右侧资源状态抽屉 - 始终显示 -->
    <div
      v-if="currentTask"
      class="status-drawer-container"
      :class="{ expanded: isDrawerOpen }"
    >
      <!-- 触发标签 -->
      <div class="drawer-trigger" @click.stop="toggleDrawerAndRefresh">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 6v6l4 2"/>
        </svg>
        <span>资源状态</span>
        <span class="resource-count" v-if="totalResourceCount > 0">{{ totalResourceCount }}</span>
      </div>

      <!-- 抽屉内容 -->
      <div class="drawer-content" @click.stop>
        <div class="drawer-header">
          <span>资源状态</span>
          <button class="btn-refresh-small" @click="refreshStatus" title="刷新">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
          </button>
        </div>

        <!-- 加载中状态 -->
        <div v-if="!resourceStatus" class="loading-status">
          <span>加载中...</span>
        </div>

        <template v-else>
          <!-- VM 列表 -->
          <div class="status-section" v-if="resourceStatus.vms?.length">
            <h4>🖥️ 虚拟机 ({{ resourceStatus.vms.length }})</h4>
            <div class="resource-list">
              <div v-for="vm in resourceStatus.vms" :key="vm.name" class="resource-item vm-item">
                <div class="resource-info">
                  <span class="resource-name">{{ vm.name }}</span>
                  <span class="resource-node" v-if="vm.node_id">{{ vm.node_id }}</span>
                </div>
                <span class="resource-state" :class="vm.state">{{ vm.state }}</span>
                <button
                  class="btn-shell btn-vm-shell"
                  @click="openTerminal(vm.name, 'vm')"
                  :disabled="vm.state !== 'running'"
                  title="打开串口控制台"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 17l6-6-6-6M12 19h8"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 容器列表 -->
          <div class="status-section" v-if="resourceStatus.containers?.length">
            <h4>📦 容器 ({{ resourceStatus.containers.length }})</h4>
            <div class="resource-list">
              <div v-for="c in resourceStatus.containers" :key="c.name" class="resource-item container-item">
                <div class="resource-info">
                  <span class="resource-name">{{ c.name }}</span>
                  <!-- IP 下拉列表 -->
                  <div class="ip-dropdown" v-if="c.interfaces && Object.keys(c.interfaces).length > 0">
                    <button
                      class="ip-dropdown-trigger"
                      @click.stop="toggleIpDropdown(c.name)"
                      :class="{ active: expandedIpContainer === c.name }"
                    >
                      <span class="ip-preview">{{ getFirstIp(c.interfaces) }}</span>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-arrow">
                        <path d="M6 9l6 6 6-6"/>
                      </svg>
                    </button>
                    <div class="ip-dropdown-content" v-show="expandedIpContainer === c.name">
                      <div
                        v-for="(ip, iface) in c.interfaces"
                        :key="iface"
                        class="ip-item"
                      >
                        <span class="iface-name">{{ iface }}</span>
                        <span class="iface-ip">{{ ip }}</span>
                      </div>
                    </div>
                  </div>
                  <span class="resource-ip" v-else-if="c.mgmt_ip">{{ c.mgmt_ip }}</span>
                </div>
                <span class="resource-state" :class="c.state">{{ c.state }}</span>
                <button class="btn-shell" @click="openTerminal(c.name, 'container')" title="打开终端">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 17l6-6-6-6M12 19h8"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 网络列表 -->
          <div class="status-section" v-if="resourceStatus.networks?.length">
            <h4>🔗 网络 ({{ resourceStatus.networks.length }})</h4>
            <div class="resource-list networks">
              <div v-for="net in resourceStatus.networks" :key="net.name" class="resource-item network-item">
                <span class="resource-name">{{ net.name }}</span>
                <span class="resource-type">{{ net.type }}</span>
              </div>
            </div>
          </div>

          <div v-if="!resourceStatus.vms?.length && !resourceStatus.containers?.length && !resourceStatus.networks?.length" class="no-resources">
            环境未部署
          </div>
        </template>
      </div>
    </div>

    <!-- 点击遮罩层关闭抽屉 -->
    <div
      v-if="isDrawerOpen"
      class="drawer-overlay"
      @click="closeDrawer"
    ></div>

    <!-- 终端弹窗 - 使用 xterm.js -->
    <Transition name="modal">
      <div v-if="showTerminal" class="terminal-overlay" @click.self="closeTerminal">
        <div class="terminal-window">
          <div class="terminal-header">
            <div class="terminal-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 17l6-6-6-6M12 19h8"/>
              </svg>
              <span>{{ terminalContainer }}</span>
              <!-- 新增：显示终端类型 -->
              <span class="terminal-type">{{ terminalType === 'vm' ? '串口控制台' : '终端' }}</span>
              <span class="terminal-status" :class="{ connected: terminalConnected }">
                {{ terminalConnected ? '已连接' : '连接中...' }}
              </span>
            </div>
            <button class="btn-close" @click="closeTerminal">×</button>
          </div>
          <div class="terminal-body" ref="terminalRef"></div>
        </div>
      </div>
    </Transition>

    <!-- 底部状态栏 -->
    <footer class="footer">
      <span>VTTP v1.0 - 虚拟化拓扑测试平台</span>
      <span class="task-count">任务数: {{ tasks.length }}</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit/lib/xterm-addon-fit.js'
import { WebLinksAddon } from 'xterm-addon-web-links/lib/xterm-addon-web-links.js'
import 'xterm/css/xterm.css'
import Topology from './components/Topology.vue'
import {
  listTasks,
  createTask,
  deleteTask,
  getTaskStatus,
  healthCheck
} from './api'

// 状态
const tasks = ref([])
const currentTask = ref('')
const newTaskName = ref('')
const isConnected = ref(false)
const showStatusPanel = ref(false)
const resourceStatus = ref(null)
const isPanelHovered = ref(false)
const isDrawerOpen = ref(false)  // 右侧抽屉是否展开
const expandedIpContainer = ref(null)  // 当前展开 IP 列表的容器名

// 终端状态
const showTerminal = ref(false)
const terminalContainer = ref('')
const terminalConnected = ref(false)
const terminalRef = ref(null)
const terminalType = ref('container')  // 新增：'container' 或 'vm'

// 终端实例
let terminal = null
let fitAddon = null
let websocket = null

// 计算当前任务状态
const currentTaskStatus = computed(() => {
  const task = tasks.value.find(t => t.name === currentTask.value)
  return task?.status || 'new'
})

// 计算资源总数
const totalResourceCount = computed(() => {
  if (!resourceStatus.value) return 0
  return (resourceStatus.value.vms?.length || 0) +
         (resourceStatus.value.containers?.length || 0) +
         (resourceStatus.value.networks?.length || 0)
})

// 切换抽屉
function toggleDrawer() {
  isDrawerOpen.value = !isDrawerOpen.value
}

// 切换抽屉并刷新状态
async function toggleDrawerAndRefresh() {
  isDrawerOpen.value = !isDrawerOpen.value
  // 展开时自动刷新状态
  if (isDrawerOpen.value) {
    await refreshStatus()
  }
}

// 关闭抽屉
function closeDrawer() {
  isDrawerOpen.value = false
  expandedIpContainer.value = null  // 同时关闭 IP 下拉
}

// 切换 IP 下拉列表
function toggleIpDropdown(containerName) {
  if (expandedIpContainer.value === containerName) {
    expandedIpContainer.value = null
  } else {
    expandedIpContainer.value = containerName
  }
}

// 获取第一个 IP（用于预览显示）
function getFirstIp(interfaces) {
  if (!interfaces) return ''
  const keys = Object.keys(interfaces)
  if (keys.length === 0) return ''
  // 优先显示 eth0
  if (interfaces['eth0']) return interfaces['eth0']
  return interfaces[keys[0]]
}

// 加载任务列表
async function refreshTasks() {
  try {
    const result = await listTasks()
    if (result.ok) {
      tasks.value = result.tasks
    }
  } catch (err) {
    console.error('Failed to load tasks:', err)
  }
}

// 创建新任务
async function createNewTask() {
  if (!newTaskName.value.trim()) return

  const name = newTaskName.value.trim()
  try {
    const result = await createTask(name)
    if (result.ok) {
      await refreshTasks()
      currentTask.value = name
      newTaskName.value = ''
    }
  } catch (err) {
    console.error('Failed to create task:', err)
    alert('创建任务失败: ' + err.message)
  }
}

// 删除当前任务
async function deleteCurrentTask() {
  if (!currentTask.value) return

  if (!confirm(`确定要删除任务 "${currentTask.value}" 吗？\n这将销毁所有相关的虚拟机、容器和网络！`)) {
    return
  }

  try {
    const result = await deleteTask(currentTask.value)
    if (result.ok) {
      currentTask.value = ''
      resourceStatus.value = null
      showStatusPanel.value = false
      await refreshTasks()
    } else {
      alert('删除失败: ' + (result.error || '未知错误'))
    }
  } catch (err) {
    console.error('Failed to delete task:', err)
    alert('删除任务失败: ' + err.message)
  }
}

// 任务变更
function onTaskChange() {
  resourceStatus.value = null
  showStatusPanel.value = false
  isDrawerOpen.value = false
}

// 刷新资源状态
async function refreshStatus() {
  if (!currentTask.value) return

  try {
    const result = await getTaskStatus(currentTask.value)
    if (result.ok) {
      resourceStatus.value = result.status
      showStatusPanel.value = true
    }
  } catch (err) {
    console.error('Failed to get status:', err)
  }
}

// 部署完成
function onDeployed(result) {
  refreshTasks()
  refreshStatus()
}

// 销毁完成
function onDestroyed(result) {
  refreshTasks()
  resourceStatus.value = null
  showStatusPanel.value = false
}

// 更新连接状态
function updateStatus(status) {
  isConnected.value = status
}

// ========== 修改：打开终端 - 支持 VM 和容器 ==========
async function openTerminal(name, type = 'container') {
  terminalContainer.value = name
  terminalType.value = type  // 记录类型
  terminalConnected.value = false
  showTerminal.value = true

  // 等待 DOM 更新
  await nextTick()

  // 清理之前的终端
  if (terminal) {
    terminal.dispose()
  }
  if (websocket) {
    websocket.close()
  }

  // 创建新终端
  terminal = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
    theme: {
      background: '#0d1117',
      foreground: '#c9d1d9',
      cursor: '#58a6ff',
      cursorAccent: '#0d1117',
      selection: '#264f78',
      black: '#0d1117',
      red: '#f85149',
      green: '#3fb950',
      yellow: '#d29922',
      blue: '#58a6ff',
      magenta: '#bc8cff',
      cyan: '#39c5cf',
      white: '#b1bac4',
      brightBlack: '#6e7681',
      brightRed: '#ffa198',
      brightGreen: '#56d364',
      brightYellow: '#e3b341',
      brightBlue: '#79c0ff',
      brightMagenta: '#d2a8ff',
      brightCyan: '#56d4dd',
      brightWhite: '#f0f6fc'
    }
  })

  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.loadAddon(new WebLinksAddon())

  // 挂载终端
  if (terminalRef.value) {
    terminal.open(terminalRef.value)
    fitAddon.fit()
  }

  // ========== 关键修改：根据类型选择不同的 WebSocket 端点 ==========
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsPath = type === 'vm' ? `/vmws/${name}` : `/ws/${name}`
  websocket = new WebSocket(`${protocol}//${window.location.host}${wsPath}`)

  websocket.onopen = () => {
    terminalConnected.value = true
    terminal.focus()

    // 发送终端大小
    const dims = fitAddon.proposeDimensions()
    if (dims) {
      websocket.send(`\x1b[8;${dims.rows};${dims.cols}t`)
    }
  }

  websocket.onmessage = (event) => {
    terminal.write(event.data)
  }

  websocket.onclose = () => {
    terminalConnected.value = false
    terminal.write('\r\n\x1b[33m[连接已关闭]\x1b[0m\r\n')
  }

  websocket.onerror = (err) => {
    console.error('WebSocket error:', err)
    terminal.write('\r\n\x1b[31m[连接错误]\x1b[0m\r\n')
  }

  // 终端输入发送到 WebSocket
  terminal.onData((data) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(data)
    }
  })

  // 终端大小变化
  terminal.onResize(({ cols, rows }) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(`\x1b[8;${rows};${cols}t`)
    }
  })
}

// 关闭终端
function closeTerminal() {
  showTerminal.value = false

  if (websocket) {
    websocket.close()
    websocket = null
  }

  if (terminal) {
    terminal.dispose()
    terminal = null
  }

  fitAddon = null
}

// 窗口大小变化时调整终端
function handleResize() {
  if (fitAddon && showTerminal.value) {
    fitAddon.fit()
  }
}

// 聚焦新任务输入
function focusNewTask() {
  const input = document.querySelector('.task-input input')
  if (input) input.focus()
}

// 选择第一个任务
function selectFirstTask() {
  if (tasks.value.length > 0) {
    currentTask.value = tasks.value[0].name
  }
}

// 检查连接状态
async function checkConnection() {
  isConnected.value = await healthCheck()
}

// 初始化
onMounted(async () => {
  await checkConnection()
  await refreshTasks()

  // 定期检查连接
  setInterval(checkConnection, 10000)

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  closeTerminal()
})
</script>

<style>
/* CSS 变量 */
:root {
  --bg-primary: #0a0e14;
  --bg-card: #12171e;
  --bg-elevated: #1a2028;
  --border-color: #2a3441;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent-blue: #58a6ff;
  --accent-green: #3fb950;
  --accent-orange: #f0883e;
  --accent-red: #f85149;
  --font-sans: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.5;
}

/* 应用容器 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* 顶部导航 */
.header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--accent-orange);
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-orange), var(--accent-blue));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.task-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.task-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-selector label {
  font-size: 12px;
  color: var(--text-secondary);
}

.task-selector select {
  padding: 6px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  min-width: 180px;
}

.task-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-input input {
  padding: 6px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 13px;
  width: 160px;
}

.task-input input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.btn-create {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--accent-blue);
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-create:hover:not(:disabled) {
  background: #4090e0;
}

.btn-create:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-create svg {
  width: 14px;
  height: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-refresh {
  padding: 6px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-refresh:hover {
  background: var(--bg-elevated);
  color: var(--accent-blue);
}

.btn-refresh svg {
  width: 16px;
  height: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-indicator .dot {
  width: 8px;
  height: 8px;
  background: var(--accent-red);
  border-radius: 50%;
}

.status-indicator.active .dot {
  background: var(--accent-green);
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

/* 欢迎页面 */
.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  color: var(--accent-orange);
  opacity: 0.8;
  margin-bottom: 24px;
}

.welcome-content h2 {
  font-size: 28px;
  margin-bottom: 8px;
}

.welcome-content p {
  color: var(--text-secondary);
  margin-bottom: 32px;
}

.welcome-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 32px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover {
  border-color: var(--accent-blue);
  transform: translateY(-2px);
}

.action-card svg {
  width: 32px;
  height: 32px;
  color: var(--accent-blue);
}

.action-card span {
  font-size: 14px;
  color: var(--text-primary);
}

/* 任务信息栏 */
.task-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  margin-bottom: 12px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-meta h2 {
  font-size: 16px;
  font-weight: 600;
  font-family: var(--font-mono);
}

.task-status {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.task-status.new {
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent-blue);
}

.task-status.deployed {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
}

.task-status.stopped {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
}

.task-actions {
  display: flex;
  gap: 8px;
}

.task-actions .btn-action {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.task-actions .btn-action svg {
  width: 14px;
  height: 14px;
}

.task-actions .btn-action:hover {
  background: var(--bg-elevated);
}

.btn-status:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.btn-delete-task:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
}

/* 右侧资源状态抽屉 */
.status-drawer-container {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  align-items: center;
}

.drawer-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-right: none;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  transition: all 0.2s ease;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.2);
}

.drawer-trigger:hover {
  background: var(--bg-elevated);
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.drawer-trigger svg {
  width: 16px;
  height: 16px;
  transform: rotate(90deg);
}

.drawer-trigger .resource-count {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--accent-blue);
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  writing-mode: horizontal-tb;
}

.drawer-content {
  position: absolute;
  right: 100%;
  top: 50%;
  transform: translateY(-50%) translateX(100%);
  width: 320px;
  max-height: 70vh;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
  margin-right: 8px;
}

.status-drawer-container.expanded .drawer-content {
  transform: translateY(-50%) translateX(0);
  opacity: 1;
  visibility: visible;
}

.status-drawer-container.expanded .drawer-trigger {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.drawer-header span {
  font-size: 15px;
  font-weight: 600;
}

.btn-refresh-small {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-refresh-small:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.btn-refresh-small svg {
  width: 14px;
  height: 14px;
}

/* 遮罩层 */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
  background: transparent;
}

.status-section {
  margin-bottom: 16px;
}

.status-section:last-child {
  margin-bottom: 0;
}

.status-section h4 {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.resource-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.resource-list.networks {
  flex-direction: row;
  flex-wrap: wrap;
}

.resource-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border-radius: 8px;
  font-size: 12px;
}

.resource-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.resource-name {
  font-family: var(--font-mono);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-ip {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent-blue);
}

/* IP 下拉列表样式 */
.ip-dropdown {
  position: relative;
}

.ip-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ip-dropdown-trigger:hover {
  border-color: var(--accent-blue);
}

.ip-dropdown-trigger.active {
  border-color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.1);
}

.ip-dropdown-trigger .ip-preview {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent-blue);
}

.ip-dropdown-trigger .dropdown-arrow {
  width: 12px;
  height: 12px;
  color: var(--text-secondary);
  transition: transform 0.2s ease;
}

.ip-dropdown-trigger.active .dropdown-arrow {
  transform: rotate(180deg);
}

.ip-dropdown-content {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  min-width: 160px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 6px 0;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.ip-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  font-size: 11px;
}

.ip-item:hover {
  background: var(--bg-elevated);
}

.ip-item .iface-name {
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--text-secondary);
}

.ip-item .iface-ip {
  font-family: var(--font-mono);
  color: var(--accent-blue);
}

/* VM 节点 ID 显示 */
.resource-node {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--accent-orange);
}

.resource-state {
  padding: 3px 8px;
  border-radius: 10px;
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  flex-shrink: 0;
}

.resource-state.running {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
}

.resource-state.stopped, .resource-state.exited {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
}

.resource-type {
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(240, 136, 62, 0.15);
  color: var(--accent-orange);
  border-radius: 4px;
}

.btn-shell {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  background: var(--accent-green);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-shell:hover {
  background: #2ea043;
}

.btn-shell svg {
  width: 14px;
  height: 14px;
}

/* VM 控制台按钮样式（橙色） */
.btn-vm-shell {
  background: var(--accent-orange) !important;
}

.btn-vm-shell:hover {
  background: #d76a2a !important;
}

.btn-vm-shell:disabled {
  background: var(--bg-elevated) !important;
  color: var(--text-secondary) !important;
  cursor: not-allowed;
  opacity: 0.6;
}

.no-resources {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-size: 13px;
}

.loading-status {
  text-align: center;
  color: var(--text-secondary);
  padding: 30px 20px;
  font-size: 13px;
}

/* 终端弹窗 */
.terminal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.terminal-window {
  width: 90%;
  max-width: 1100px;
  height: 80%;
  background: #0d1117;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--accent-green);
}

.terminal-title svg {
  width: 16px;
  height: 16px;
}

/* 新增：终端类型标签 */
.terminal-type {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(240, 136, 62, 0.15);
  color: var(--accent-orange);
}

.terminal-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
}

.terminal-status.connected {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
}

.btn-close {
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-close:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
}

.terminal-body {
  flex: 1;
  padding: 8px;
  background: #0d1117;
  overflow: hidden;
}

/* xterm.js 样式覆盖 */
.terminal-body .xterm {
  height: 100%;
  padding: 8px;
}

.terminal-body .xterm-viewport {
  overflow-y: auto !important;
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .terminal-window,
.modal-leave-to .terminal-window {
  transform: scale(0.95);
}

/* 底部状态栏 */
.footer {
  display: flex;
  justify-content: space-between;
  padding: 10px 24px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  font-size: 11px;
  color: var(--text-secondary);
}

.task-count {
  font-family: var(--font-mono);
}
</style>