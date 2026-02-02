<template>
  <div class="topology-container">
    <!-- 左侧工具面板 -->
    <aside class="toolbar">
      <div class="toolbar-section">
        <h3>添加设备</h3>
        <div class="device-buttons">
          <button class="btn-device btn-pc" @click="addPC">
            <div class="device-icon pc-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <path d="M8 21h8M12 17v4"/>
              </svg>
            </div>
            <span>PC 终端</span>
          </button>
          <button class="btn-device btn-fw" @click="addFW">
            <div class="device-icon fw-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
            </div>
            <span>防火墙</span>
          </button>
        </div>
      </div>

      <div class="toolbar-section">
        <h3>操作</h3>
        <div class="action-buttons">
          <button class="btn-action btn-save" @click="saveTopo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
              <polyline points="17,21 17,13 7,13 7,21"/>
              <polyline points="7,3 7,8 15,8"/>
            </svg>
            保存拓扑
          </button>
          <button class="btn-action btn-deploy" @click="deployTopo" :disabled="deploying">
            <svg v-if="!deploying" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="5,3 19,12 5,21 5,3"/>
            </svg>
            <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ deploying ? '部署中...' : '部署环境' }}
          </button>
          <button class="btn-action btn-destroy" @click="destroyTopo" :disabled="destroying">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <path d="M9 9l6 6M15 9l-6 6"/>
            </svg>
            {{ destroying ? '销毁中...' : '结束任务' }}
          </button>
          <div class="action-divider"></div>
          <button class="btn-action btn-shutdown" @click="shutdownAll" :disabled="shuttingDown">
            <svg v-if="!shuttingDown" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6"/>
            </svg>
            <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ shuttingDown ? '关机中...' : '全部关机' }}
          </button>
          <button class="btn-action btn-startup" @click="startupAll" :disabled="startingUp">
            <svg v-if="!startingUp" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
              <line x1="12" y1="2" x2="12" y2="12"/>
            </svg>
            <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ startingUp ? '开机中...' : '全部开机' }}
          </button>
          <div class="action-divider"></div>
          <button class="btn-action btn-clear" @click="clearTopo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3,6 5,6 21,6"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
            清空画布
          </button>
        </div>
      </div>

      <div class="toolbar-section stats">
        <h3>统计信息</h3>
        <div class="stat-item">
          <span class="stat-label">PC 终端</span>
          <span class="stat-value pc">{{ pcCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">防火墙</span>
          <span class="stat-value fw">{{ fwCount }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">连接数</span>
          <span class="stat-value">{{ edges.length }}</span>
        </div>
      </div>
    </aside>

    <!-- 拓扑画布 -->
    <div class="canvas-wrapper">
      <!-- 连线信息面板按钮 -->
      <div class="connections-panel-toggle" :class="{ active: showConnectionsPanel }" @click="showConnectionsPanel = !showConnectionsPanel">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
        </svg>
        <span class="badge" v-if="edges.length > 0">{{ edges.length }}</span>
      </div>

      <!-- 连线信息面板 -->
      <Transition name="slide-panel">
        <div class="connections-panel" v-if="showConnectionsPanel">
          <div class="panel-header">
            <h4>连线列表</h4>
            <button class="btn-close-panel" @click="showConnectionsPanel = false">×</button>
          </div>
          <div class="panel-content">
            <div v-if="edges.length === 0" class="no-connections">
              暂无连线
            </div>
            <div
              v-for="edge in edges"
              :key="edge.id"
              class="connection-item"
              :class="{ highlighted: highlightedEdgeId === edge.id }"
              @click="highlightEdge(edge.id)"
            >
              <div class="connection-info">
                <span class="port-label" :style="{ color: getNodeColor(edge.source) }">
                  {{ edge.source }}:{{ edge.data?.sourcePort }}
                </span>
                <span class="arrow">⟷</span>
                <span class="port-label" :style="{ color: getNodeColor(edge.target) }">
                  {{ edge.target }}:{{ edge.data?.targetPort }}
                </span>
              </div>
              <div class="connection-actions">
                <select
                  class="edge-type-select"
                  :value="edge.type || 'smoothstep'"
                  @change="changeEdgeType(edge.id, $event.target.value)"
                  @click.stop
                >
                  <option value="smoothstep">平滑折线</option>
                  <option value="straight">直线</option>
                  <option value="step">折线</option>
                  <option value="bezier">贝塞尔</option>
                </select>
                <button class="btn-delete-edge" @click.stop="deleteEdge(edge.id)" title="删除连线">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :default-edge-options="defaultEdgeOptions"
        :connection-mode="ConnectionMode.Loose"
        :snap-to-grid="true"
        :snap-grid="[20, 20]"
        fit-view-on-init
        @connect="onConnect"
        @edge-click="onEdgeClick"
        @node-click="onNodeClick"
        @node-drag-stop="onNodeDragStop"
        @pane-click="onPaneClick"
      >
        <Background pattern="dots" :gap="20" :size="1" />
        <Controls position="bottom-right"/>
        <MiniMap
          :node-color="nodeColor"
          :mask-color="'rgba(10, 14, 20, 0.8)'"
        />

        <!-- 自定义节点 -->
        <template #node-pc="nodeProps">
          <div class="custom-node pc-node" :class="{ selected: nodeProps.selected }">
            <div class="node-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="node-icon">
                <rect x="2" y="3" width="20" height="14" rx="2"/>
                <path d="M8 21h8M12 17v4"/>
              </svg>
              <span class="node-title">{{ nodeProps.id }}</span>
            </div>
            <div class="node-ports">
              <div v-for="port in nodeProps.data.ports" :key="port" class="port">{{ port }}</div>
            </div>
            <Handle type="source" :position="Position.Top" :id="`${nodeProps.id}-top`" class="handle-point" />
            <Handle type="source" :position="Position.Bottom" :id="`${nodeProps.id}-bottom`" class="handle-point" />
            <Handle type="source" :position="Position.Right" :id="`${nodeProps.id}-right`" class="handle-point" />
            <Handle type="source" :position="Position.Left" :id="`${nodeProps.id}-left`" class="handle-point" />
          </div>
        </template>

        <template #node-fw="nodeProps">
          <div class="custom-node fw-node" :class="{ selected: nodeProps.selected }">
            <div class="node-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="node-icon">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
              <span class="node-title">{{ nodeProps.id }}</span>
            </div>
            <div class="node-info" v-if="nodeProps.data.image">
              <span class="image-tag">{{ getImageName(nodeProps.data.image) }}</span>
            </div>
            <div class="node-ports">
              <div v-for="port in nodeProps.data.ports" :key="port" class="port">{{ port }}</div>
            </div>
            <Handle type="source" :position="Position.Top" :id="`${nodeProps.id}-top`" class="handle-point" />
            <Handle type="source" :position="Position.Bottom" :id="`${nodeProps.id}-bottom`" class="handle-point" />
            <Handle type="source" :position="Position.Right" :id="`${nodeProps.id}-right`" class="handle-point" />
            <Handle type="source" :position="Position.Left" :id="`${nodeProps.id}-left`" class="handle-point" />
          </div>
        </template>

        <!-- 自定义边标签 - 显示彩色端口名 -->
        <template #edge-label="{ edge }">
          <div class="edge-label-colored" v-if="edge.data?.sourcePort && edge.data?.targetPort">
            <span :style="{ color: getNodeColor(edge.source) }">{{ edge.data.sourcePort }}</span>
            <span class="separator">⟷</span>
            <span :style="{ color: getNodeColor(edge.target) }">{{ edge.data.targetPort }}</span>
          </div>
        </template>

        <!-- 空状态提示 -->
        <Panel v-if="nodes.length === 0" position="top-center" class="empty-hint">
          <div class="hint-content">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 16v-4M12 8h.01"/>
            </svg>
            <p>点击左侧按钮添加设备，从节点边缘拖拽创建连线</p>
          </div>
        </Panel>
      </VueFlow>
    </div>

    <!-- 连接配置弹窗 -->
    <Transition name="modal">
      <div v-if="showConnectionModal" class="modal-overlay" @click.self="closeConnectionModal">
        <div class="modal-content">
          <h3>配置连接端口</h3>
          <div class="connection-config">
            <div class="config-side">
              <label :style="{ color: getNodeColor(pendingConnection?.source) }">{{ pendingConnection?.source }} 端口</label>
              <select v-model="pendingConnection.sourcePort">
                <option v-for="port in getNodePorts(pendingConnection?.source)" :key="port" :value="port">
                  {{ port }}
                </option>
              </select>
            </div>
            <div class="config-arrow">⟷</div>
            <div class="config-side">
              <label :style="{ color: getNodeColor(pendingConnection?.target) }">{{ pendingConnection?.target }} 端口</label>
              <select v-model="pendingConnection.targetPort">
                <option v-for="port in getNodePorts(pendingConnection?.target)" :key="port" :value="port">
                  {{ port }}
                </option>
              </select>
            </div>
          </div>
          <!-- 连线类型选择 -->
          <div class="edge-type-config">
            <label>连线类型</label>
            <div class="edge-type-buttons">
              <button
                v-for="type in edgeTypes"
                :key="type.value"
                class="btn-edge-type"
                :class="{ active: pendingConnection.edgeType === type.value }"
                @click="pendingConnection.edgeType = type.value"
              >
                {{ type.label }}
              </button>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn-cancel" @click="closeConnectionModal">取消</button>
            <button class="btn-confirm" @click="confirmConnection">确认连接</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 节点配置弹窗 -->
    <Transition name="modal">
      <div v-if="showNodeModal" class="modal-overlay" @click.self="closeNodeModal">
        <div class="modal-content modal-content-wide">
          <h3>配置 {{ selectedNode?.id }}</h3>

          <!-- 防火墙专属配置 -->
          <template v-if="selectedNode?.type === 'fw'">
            <!-- 镜像选择 -->
            <div class="config-section">
              <div class="config-label-row">
                <label>防火墙镜像</label>
                <button class="btn-refresh" @click="refreshImages" :disabled="refreshingImages">
                  <svg :class="{ 'spin': refreshingImages }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 4v6h-6M1 20v-6h6"/>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                  </svg>
                  刷新
                </button>
              </div>
              <select v-model="selectedNode.data.image">
                <option v-for="img in fwImages" :key="img.path" :value="img.path">
                  {{ img.name }}
                </option>
              </select>
            </div>

            <!-- CPU 配置 -->
            <div class="config-section">
              <div class="config-label-row">
                <label>CPU 核心数</label>
                <span class="resource-hint" v-if="systemResources">
                  可用: {{ systemResources.cpu.available }} 核 / 共 {{ systemResources.cpu.total }} 核
                </span>
              </div>
              <div class="input-with-unit">
                <input
                  type="number"
                  v-model.number="selectedNode.data.cpu"
                  min="1"
                  :max="systemResources?.cpu?.available || 16"
                  placeholder="2"
                />
                <span class="unit">核</span>
              </div>
            </div>

            <!-- 内存配置 -->
            <div class="config-section">
              <div class="config-label-row">
                <label>内存大小</label>
                <span class="resource-hint" v-if="systemResources">
                  可用: {{ formatMemory(systemResources.memory.available) }} / 共 {{ formatMemory(systemResources.memory.total) }}
                </span>
              </div>
              <div class="input-with-unit">
                <input
                  type="number"
                  v-model.number="selectedNode.data.memory"
                  min="512"
                  :max="systemResources?.memory?.available || 65536"
                  step="512"
                  placeholder="4096"
                />
                <span class="unit">MB</span>
              </div>
              <div class="memory-presets">
                <button
                  v-for="preset in memoryPresets"
                  :key="preset"
                  class="btn-preset"
                  :class="{ active: selectedNode.data.memory === preset }"
                  @click="selectedNode.data.memory = preset"
                >
                  {{ formatMemory(preset) }}
                </button>
              </div>
            </div>
          </template>

          <!-- 端口配置 -->
          <div class="config-section">
            <label>网络端口</label>
            <div class="ports-list">
              <div v-for="(port, idx) in selectedNode?.data?.ports" :key="port + '-' + idx" class="port-item">
                <span>{{ port }}</span>
                <button v-if="idx > 0" class="btn-remove-port" @click="removePort(idx)">×</button>
              </div>
            </div>
            <button class="btn-add-port" @click="addPort">+ 添加端口</button>
          </div>

          <!-- 设备操作 -->
          <div class="config-section" v-if="selectedNodeState">
            <div class="config-label-row">
              <label>设备操作</label>
              <span class="node-state-badge" :class="selectedNodeState.running ? 'running' : 'stopped'">
                {{ selectedNodeState.running ? '运行中' : '已停止' }}
              </span>
            </div>
            <div class="node-actions">
              <button
                class="btn-node-action btn-node-startup"
                @click="handleStartupNode"
                :disabled="nodeOperating || selectedNodeState.running"
              >
                <svg v-if="!nodeOperating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="5,3 19,12 5,21 5,3"/>
                </svg>
                <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
                </svg>
                开机
              </button>
              <button
                class="btn-node-action btn-node-shutdown"
                @click="handleShutdownNode"
                :disabled="nodeOperating || !selectedNodeState.running"
              >
                <svg v-if="!nodeOperating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
                <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
                </svg>
                关机
              </button>
              <button
                class="btn-node-action btn-node-restart"
                @click="handleRestartNode"
                :disabled="nodeOperating || !selectedNodeState.running"
              >
                <svg v-if="!nodeOperating" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 4v6h-6M1 20v-6h6"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                </svg>
                <svg v-else class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/>
                </svg>
                重启
              </button>
            </div>
          </div>
          <div class="config-section" v-else-if="props.task">
            <div class="config-label-row">
              <label>设备操作</label>
              <span class="node-state-badge unknown">未部署</span>
            </div>
            <p class="hint-text">请先部署环境后再进行设备操作</p>
          </div>

          <div class="modal-actions">
            <button class="btn-delete" @click="deleteNode">删除设备</button>
            <button class="btn-confirm" @click="closeNodeModal">确定</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 消息提示 -->
    <Transition name="toast">
      <div v-if="toast.show" class="toast" :class="toast.type">
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { VueFlow, Panel, Position, Handle, ConnectionMode, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { saveTopology, deploy, destroy, getTopology, listImages, getSystemResources, shutdownAll as apiShutdownAll, startupAll as apiStartupAll, shutdownNode, startupNode, restartNode, getNodeState } from '../api'

const props = defineProps({
  task: String
})
const emit = defineEmits(['status', 'deployed', 'destroyed'])

const { addEdges, removeEdges, removeNodes, fitView, updateNode } = useVueFlow()

// 状态
const nodes = ref([])
const edges = ref([])
const deploying = ref(false)
const destroying = ref(false)
const shuttingDown = ref(false)
const startingUp = ref(false)
const toast = ref({ show: false, message: '', type: 'success' })

// 连线面板状态
const showConnectionsPanel = ref(false)
const highlightedEdgeId = ref(null)

// 弹窗状态
const showConnectionModal = ref(false)
const pendingConnection = ref(null)
const showNodeModal = ref(false)
const selectedNode = ref(null)
const selectedNodeState = ref(null)  // 设备运行状态
const nodeOperating = ref(false)     // 设备操作中

// 防火墙镜像列表
const fwImages = ref([
  { path: '/img/USG-FW-CMCC-VFEA-542-x86-9st.qcow2', name: '默认防火墙镜像' }
])

// 系统资源信息
const systemResources = ref(null)
const refreshingImages = ref(false)

// 内存预设选项
const memoryPresets = [1024, 2048, 4096, 8192, 16384]

// 连线类型选项
const edgeTypes = [
  { value: 'smoothstep', label: '平滑折线' },
  { value: 'straight', label: '直线' },
  { value: 'step', label: '折线' },
  { value: 'bezier', label: '贝塞尔' }
]

// 默认边样式
const defaultEdgeOptions = {
  type: 'smoothstep',
  animated: true,
  style: { stroke: '#58a6ff', strokeWidth: 2, strokeDasharray: '8 4' },
  labelBgStyle: { fill: '#1a2028', fillOpacity: 0.95 },
  labelStyle: { fill: '#e6edf3', fontSize: 11, fontWeight: 500 },
  pathOptions: { borderRadius: 20, offset: 15 }
}

let idCounter = { pc: 1, fw: 1 }

// 获取节点颜色
function getNodeColor(nodeId) {
  if (!nodeId) return '#58a6ff'
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) {
    // 根据ID前缀判断
    if (nodeId.startsWith('fw')) return '#f0883e'
    return '#58a6ff'
  }
  return node.type === 'fw' ? '#f0883e' : '#58a6ff'
}

// 根据两个节点的相对位置，计算最佳的连接方向
function getBestHandles(sourceId, targetId) {
  const sourceNode = nodes.value.find(n => n.id === sourceId)
  const targetNode = nodes.value.find(n => n.id === targetId)

  if (!sourceNode || !targetNode) {
    return { sourceHandle: `${sourceId}-right`, targetHandle: `${targetId}-left` }
  }

  const sx = sourceNode.position.x
  const sy = sourceNode.position.y
  const tx = targetNode.position.x
  const ty = targetNode.position.y

  const dx = tx - sx
  const dy = ty - sy

  const angle = Math.atan2(dy, dx) * 180 / Math.PI

  let sourceHandle, targetHandle

  if (angle >= -45 && angle < 45) {
    sourceHandle = `${sourceId}-right`
    targetHandle = `${targetId}-left`
  } else if (angle >= 45 && angle < 135) {
    sourceHandle = `${sourceId}-bottom`
    targetHandle = `${targetId}-top`
  } else if (angle >= 135 || angle < -135) {
    sourceHandle = `${sourceId}-left`
    targetHandle = `${targetId}-right`
  } else {
    sourceHandle = `${sourceId}-top`
    targetHandle = `${targetId}-bottom`
  }

  return { sourceHandle, targetHandle }
}

// 计算属性
const pcCount = computed(() => nodes.value.filter(n => n.type === 'pc').length)
const fwCount = computed(() => nodes.value.filter(n => n.type === 'fw').length)

// 获取镜像显示名称
function getImageName(path) {
  if (!path) return ''
  const name = path.split('/').pop()
  return name.length > 20 ? name.substring(0, 17) + '...' : name
}

// 获取节点端口
function getNodePorts(nodeId) {
  const node = nodes.value.find(n => n.id === nodeId)
  return node?.data?.ports || ['eth0']
}

// 显示提示
function showToast(message, type = 'success') {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

// 添加 PC
function addPC() {
  const id = `pc${idCounter.pc++}`
  nodes.value.push({
    id,
    type: 'pc',
    data: {
      label: id,
      ports: ['eth0', 'eth1']
    },
    position: { x: 100 + Math.random() * 200, y: 100 + Math.random() * 200 }
  })
  showToast(`已添加 PC 终端: ${id}`)
}

// 添加防火墙
function addFW() {
  const id = `fw${idCounter.fw++}`
  nodes.value.push({
    id,
    type: 'fw',
    data: {
      label: id,
      ports: ['eth0', 'eth1', 'eth2', 'eth3'],
      image: fwImages.value[0]?.path || '',
      cpu: 2,
      memory: 4096
    },
    position: { x: 400 + Math.random() * 200, y: 100 + Math.random() * 200 }
  })
  showToast(`已添加防火墙: ${id}`)
}

// 连接处理 - 打开端口配置弹窗
function onConnect(params) {
  pendingConnection.value = {
    source: params.source,
    target: params.target,
    sourceHandle: params.sourceHandle,
    targetHandle: params.targetHandle,
    sourcePort: getNodePorts(params.source)[0],
    targetPort: getNodePorts(params.target)[0],
    edgeType: 'smoothstep'
  }
  showConnectionModal.value = true
}

// 确认连接
function confirmConnection() {
  if (!pendingConnection.value) return

  const { source, target, sourcePort, targetPort, edgeType } = pendingConnection.value

  const exists = edges.value.some(e =>
    (e.source === source && e.data?.sourcePort === sourcePort) ||
    (e.target === target && e.data?.targetPort === targetPort) ||
    (e.source === target && e.data?.sourcePort === targetPort) ||
    (e.target === source && e.data?.targetPort === sourcePort)
  )

  if (exists) {
    showToast('该端口已被占用', 'warning')
    return
  }

  const { sourceHandle, targetHandle } = getBestHandles(source, target)
  const edgeId = `e-${source}-${sourcePort}-${target}-${targetPort}`

  edges.value.push({
    id: edgeId,
    source,
    target,
    sourceHandle,
    targetHandle,
    sourceNode: source,
    targetNode: target,
    type: edgeType,
    data: {
      sourcePort,
      targetPort
    },
    label: `${sourcePort} ⟷ ${targetPort}`,
    animated: true,
    style: { stroke: '#58a6ff', strokeWidth: 2, strokeDasharray: '8 4' },
    labelBgStyle: { fill: '#1a2028', fillOpacity: 0.95 },
    labelStyle: { fill: '#e6edf3', fontSize: 11, fontWeight: 500 }
  })

  showToast(`已连接: ${source}:${sourcePort} ⟷ ${target}:${targetPort}`)
  closeConnectionModal()
}

// 关闭连接弹窗
function closeConnectionModal() {
  showConnectionModal.value = false
  pendingConnection.value = null
}

// 边点击 - 高亮
function onEdgeClick({ edge }) {
  highlightEdge(edge.id)
}

// 高亮连线
function highlightEdge(edgeId) {
  edges.value = edges.value.map(e => ({
    ...e,
    style: {
      ...e.style,
      stroke: e.id === edgeId ? '#7ee787' : '#58a6ff',
      strokeWidth: e.id === edgeId ? 3 : 2
    },
    animated: true
  }))
  highlightedEdgeId.value = edgeId

  setTimeout(() => {
    if (highlightedEdgeId.value === edgeId) {
      edges.value = edges.value.map(e => ({
        ...e,
        style: {
          ...e.style,
          stroke: '#58a6ff',
          strokeWidth: 2
        }
      }))
      highlightedEdgeId.value = null
    }
  }, 3000)
}

// 删除连线
function deleteEdge(edgeId) {
  if (confirm('确定删除这条连线吗？')) {
    edges.value = edges.value.filter(e => e.id !== edgeId)
    showToast('连线已删除', 'warning')
    if (highlightedEdgeId.value === edgeId) {
      highlightedEdgeId.value = null
    }
  }
}

// 修改连线类型
function changeEdgeType(edgeId, newType) {
  edges.value = edges.value.map(e => {
    if (e.id === edgeId) {
      return { ...e, type: newType }
    }
    return e
  })
  showToast(`连线类型已更改为: ${edgeTypes.find(t => t.value === newType)?.label}`)
}

// 点击画布空白处
function onPaneClick() {
  if (highlightedEdgeId.value) {
    edges.value = edges.value.map(e => ({
      ...e,
      style: {
        ...e.style,
        stroke: '#58a6ff',
        strokeWidth: 2
      }
    }))
    highlightedEdgeId.value = null
  }
}

// 节点点击
async function onNodeClick({ node }) {
  selectedNode.value = JSON.parse(JSON.stringify(node))
  selectedNodeState.value = null

  if (node.type === 'fw') {
    if (!selectedNode.value.data.cpu) {
      selectedNode.value.data.cpu = 2
    }
    if (!selectedNode.value.data.memory) {
      selectedNode.value.data.memory = 4096
    }
    loadSystemResources()
  }

  // 获取设备状态
  if (props.task) {
    try {
      const result = await getNodeState(props.task, node.id)
      if (result.ok) {
        selectedNodeState.value = result
      }
    } catch (err) {
      console.log('Failed to get node state:', err)
    }
  }

  showNodeModal.value = true
}

// 节点拖动结束
function onNodeDragStop({ node }) {
  const relatedEdges = edges.value.filter(
    e => e.source === node.id || e.target === node.id
  )

  if (relatedEdges.length === 0) return

  edges.value = edges.value.map(e => {
    if (e.source === node.id || e.target === node.id) {
      const { sourceHandle, targetHandle } = getBestHandles(e.source, e.target)
      return {
        ...e,
        sourceHandle,
        targetHandle
      }
    }
    return e
  })
}

// 关闭节点弹窗
function closeNodeModal() {
  if (selectedNode.value) {
    const nodeId = selectedNode.value.id
    const newData = JSON.parse(JSON.stringify(selectedNode.value.data))

    updateNode(nodeId, { data: newData })

    const idx = nodes.value.findIndex(n => n.id === nodeId)
    if (idx !== -1) {
      nodes.value[idx] = {
        ...nodes.value[idx],
        data: newData
      }
    }
  }
  showNodeModal.value = false
  selectedNode.value = null
  selectedNodeState.value = null
}

// 刷新节点状态
async function refreshNodeState() {
  if (!props.task || !selectedNode.value) return

  try {
    const result = await getNodeState(props.task, selectedNode.value.id)
    if (result.ok) {
      selectedNodeState.value = result
    }
  } catch (err) {
    console.log('Failed to refresh node state:', err)
  }
}

// 关闭单个设备
async function handleShutdownNode() {
  if (!props.task || !selectedNode.value) return

  nodeOperating.value = true
  try {
    const result = await shutdownNode(props.task, selectedNode.value.id)
    if (result.ok) {
      showToast(result.message || `${selectedNode.value.id} 已关机`)
      await refreshNodeState()
      emit('status', result)
    } else {
      showToast(result.error || '关机失败', 'error')
    }
  } catch (err) {
    showToast('关机失败: ' + err.message, 'error')
  } finally {
    nodeOperating.value = false
  }
}

// 开机单个设备
async function handleStartupNode() {
  if (!props.task || !selectedNode.value) return

  nodeOperating.value = true
  try {
    const result = await startupNode(props.task, selectedNode.value.id)
    if (result.ok) {
      showToast(result.message || `${selectedNode.value.id} 已开机`)
      await refreshNodeState()
      emit('status', result)
    } else {
      showToast(result.error || '开机失败', 'error')
    }
  } catch (err) {
    showToast('开机失败: ' + err.message, 'error')
  } finally {
    nodeOperating.value = false
  }
}

// 重启单个设备
async function handleRestartNode() {
  if (!props.task || !selectedNode.value) return

  nodeOperating.value = true
  try {
    const result = await restartNode(props.task, selectedNode.value.id)
    if (result.ok) {
      showToast(result.message || `${selectedNode.value.id} 已重启`)
      await refreshNodeState()
      emit('status', result)
    } else {
      showToast(result.error || '重启失败', 'error')
    }
  } catch (err) {
    showToast('重启失败: ' + err.message, 'error')
  } finally {
    nodeOperating.value = false
  }
}

// 删除节点
function deleteNode() {
  if (!selectedNode.value) return

  const nodeId = selectedNode.value.id

  edges.value = edges.value.filter(e =>
    e.source !== nodeId && e.target !== nodeId
  )

  nodes.value = nodes.value.filter(n => n.id !== nodeId)

  showToast(`已删除: ${nodeId}`, 'warning')
  closeNodeModal()
}

// 添加端口
function addPort() {
  if (!selectedNode.value) return
  const portNum = selectedNode.value.data.ports.length
  selectedNode.value.data.ports = [...selectedNode.value.data.ports, `eth${portNum}`]
}

// 删除端口
function removePort(idx) {
  if (!selectedNode.value) return
  selectedNode.value.data.ports = selectedNode.value.data.ports.filter((_, i) => i !== idx)
}

// 保存拓扑
async function saveTopo() {
  if (!props.task) {
    showToast('请先输入任务名称', 'warning')
    return
  }

  try {
    const topoData = {
      nodes: nodes.value.map(n => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data
      })),
      edges: edges.value.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceNode: e.source,
        targetNode: e.target,
        sourcePort: e.data?.sourcePort || 'eth0',
        targetPort: e.data?.targetPort || 'eth0',
        type: e.type || 'smoothstep',
        data: e.data
      }))
    }

    await saveTopology(props.task, topoData)
    showToast('拓扑保存成功！')
  } catch (err) {
    showToast('保存失败: ' + err.message, 'error')
  }
}

// 部署环境
async function deployTopo() {
  if (nodes.value.length === 0) {
    showToast('请先添加设备', 'warning')
    return
  }

  if (!props.task) {
    showToast('请先输入任务名称', 'warning')
    return
  }

  deploying.value = true
  try {
    await saveTopo()
    const result = await deploy(props.task)
    if (result.ok) {
      showToast('环境部署成功！')
      emit('deployed', result)
    } else {
      showToast('部署失败: ' + (result.error || '未知错误'), 'error')
    }
  } catch (err) {
    showToast('部署失败: ' + err.message, 'error')
  } finally {
    deploying.value = false
  }
}

// 销毁环境
async function destroyTopo() {
  if (!props.task) {
    showToast('请先输入任务名称', 'warning')
    return
  }

  if (!confirm('确定要销毁环境吗？这将删除所有虚拟机、容器和网络。')) {
    return
  }

  destroying.value = true
  try {
    const result = await destroy(props.task)
    if (result.ok) {
      showToast('环境已销毁')
      emit('destroyed', result)
    } else {
      showToast('销毁失败: ' + (result.error || '未知错误'), 'error')
    }
  } catch (err) {
    showToast('销毁失败: ' + err.message, 'error')
  } finally {
    destroying.value = false
  }
}

// 全部关机
async function shutdownAll() {
  if (!props.task) {
    showToast('请先输入任务名称', 'warning')
    return
  }

  if (nodes.value.length === 0) {
    showToast('没有可关机的设备', 'warning')
    return
  }

  shuttingDown.value = true
  try {
    const result = await apiShutdownAll(props.task)
    if (result.ok) {
      showToast(`已关机 ${result.shutdown_count || 0} 台设备`)
      emit('status', result)
    } else {
      showToast('关机失败: ' + (result.error || '未知错误'), 'error')
    }
  } catch (err) {
    showToast('关机失败: ' + err.message, 'error')
  } finally {
    shuttingDown.value = false
  }
}

// 全部开机
async function startupAll() {
  if (!props.task) {
    showToast('请先输入任务名称', 'warning')
    return
  }

  if (nodes.value.length === 0) {
    showToast('没有可开机的设备', 'warning')
    return
  }

  startingUp.value = true
  try {
    const result = await apiStartupAll(props.task)
    if (result.ok) {
      showToast(`已开机 ${result.startup_count || 0} 台设备`)
      emit('status', result)
    } else {
      showToast('开机失败: ' + (result.error || '未知错误'), 'error')
    }
  } catch (err) {
    showToast('开机失败: ' + err.message, 'error')
  } finally {
    startingUp.value = false
  }
}

// 清空画布
function clearTopo() {
  if (nodes.value.length === 0) return

  if (!confirm('确定要清空画布吗？')) return

  nodes.value = []
  edges.value = []
  idCounter = { pc: 1, fw: 1 }
  showToast('画布已清空', 'warning')
}

// MiniMap 节点颜色
function nodeColor(node) {
  return node.type === 'fw' ? '#f0883e' : '#58a6ff'
}

// 加载已有拓扑
async function loadTopology() {
  if (!props.task) return

  try {
    const result = await getTopology(props.task)
    if (result.ok && result.topology) {
      const topo = result.topology

      nodes.value = topo.nodes.map(n => ({
        ...n,
        data: n.data || { ports: ['eth0'] }
      }))

      edges.value = topo.edges.map(e => {
        const sourcePort = e.sourcePort || e.data?.sourcePort || 'eth0'
        const targetPort = e.targetPort || e.data?.targetPort || 'eth0'
        const source = e.sourceNode || e.source
        const target = e.targetNode || e.target
        const edgeType = e.type || 'smoothstep'

        return {
          id: e.id,
          source,
          target,
          sourceNode: source,
          targetNode: target,
          sourceHandle: e.sourceHandle,
          targetHandle: e.targetHandle,
          type: edgeType,
          data: {
            sourcePort,
            targetPort
          },
          label: `${sourcePort} ⟷ ${targetPort}`,
          animated: true,
          style: { stroke: '#58a6ff', strokeWidth: 2, strokeDasharray: '8 4' },
          labelBgStyle: { fill: '#1a2028', fillOpacity: 0.95 },
          labelStyle: { fill: '#e6edf3', fontSize: 11, fontWeight: 500 }
        }
      })

      nodes.value.forEach(n => {
        const match = n.id.match(/^(pc|fw)(\d+)$/)
        if (match) {
          const type = match[1]
          const num = parseInt(match[2])
          if (num >= idCounter[type]) {
            idCounter[type] = num + 1
          }
        }
      })

      setTimeout(() => {
        edges.value = edges.value.map(e => {
          const { sourceHandle, targetHandle } = getBestHandles(e.source, e.target)
          return {
            ...e,
            sourceHandle,
            targetHandle
          }
        })
        fitView()
      }, 100)
      showToast('拓扑已加载')
    }
  } catch (err) {
    console.log('No existing topology or error:', err)
  }
}

// 加载防火墙镜像列表
async function loadImages() {
  try {
    const result = await listImages()
    if (result.ok && result.images.length > 0) {
      fwImages.value = result.images
    }
  } catch (err) {
    console.error('Failed to load images:', err)
  }
}

// 刷新镜像列表
async function refreshImages() {
  refreshingImages.value = true
  try {
    const result = await listImages()
    if (result.ok && result.images.length > 0) {
      fwImages.value = result.images
      showToast(`已刷新，找到 ${result.images.length} 个镜像`)
    } else {
      showToast('未找到镜像文件', 'warning')
    }
  } catch (err) {
    showToast('刷新镜像失败: ' + err.message, 'error')
  } finally {
    refreshingImages.value = false
  }
}

// 加载系统资源信息
async function loadSystemResources() {
  try {
    const result = await getSystemResources()
    if (result.ok) {
      systemResources.value = result.resources
    }
  } catch (err) {
    console.error('Failed to load system resources:', err)
  }
}

// 格式化内存显示
function formatMemory(mb) {
  if (mb >= 1024) {
    return (mb / 1024).toFixed(mb % 1024 === 0 ? 0 : 1) + ' GB'
  }
  return mb + ' MB'
}

// 监听任务变化
watch(() => props.task, (newTask, oldTask) => {
  if (newTask !== oldTask) {
    nodes.value = []
    edges.value = []
    idCounter = { pc: 1, fw: 1 }
  }

  if (newTask) {
    loadTopology()
  }
}, { immediate: true })

onMounted(() => {
  loadImages()
  loadSystemResources()
})
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';

.topology-container {
  display: flex;
  gap: 20px;
  height: 100%;
}

.toolbar {
  width: 240px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex-shrink: 0;
}

.toolbar-section h3 {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.device-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.btn-device {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-device:hover {
  transform: translateX(4px);
  border-color: var(--accent-blue);
}

.btn-pc:hover {
  border-color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.1);
}

.btn-fw:hover {
  border-color: var(--accent-orange);
  background: rgba(240, 136, 62, 0.1);
}

.device-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-icon svg {
  width: 20px;
  height: 20px;
}

.pc-icon {
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent-blue);
}

.fw-icon {
  background: rgba(240, 136, 62, 0.15);
  color: var(--accent-orange);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-action:hover:not(:disabled) {
  border-color: var(--accent-blue);
}

.btn-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-action svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.btn-save:hover { border-color: var(--accent-blue); }
.btn-deploy:hover:not(:disabled) { border-color: var(--accent-green); color: var(--accent-green); }
.btn-destroy:hover:not(:disabled) { border-color: var(--accent-red); color: var(--accent-red); }
.btn-shutdown:hover:not(:disabled) { border-color: #f97316; color: #f97316; }
.btn-startup:hover:not(:disabled) { border-color: var(--accent-green); color: var(--accent-green); }
.btn-clear:hover { border-color: var(--accent-orange); color: var(--accent-orange); }

.action-divider {
  height: 1px;
  background: var(--border-color);
  margin: 4px 0;
}

.stats {
  margin-top: auto;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-value {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
}

.stat-value.pc { color: var(--accent-blue); }
.stat-value.fw { color: var(--accent-orange); }

.canvas-wrapper {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.connections-panel-toggle {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 100;
  width: 40px;
  height: 40px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.connections-panel-toggle:hover {
  border-color: var(--accent-blue);
  background: var(--bg-elevated);
}

.connections-panel-toggle.active {
  border-color: var(--accent-blue);
  background: rgba(88, 166, 255, 0.15);
}

.connections-panel-toggle svg {
  width: 20px;
  height: 20px;
  color: var(--text-secondary);
}

.connections-panel-toggle.active svg {
  color: var(--accent-blue);
}

.connections-panel-toggle .badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  background: var(--accent-blue);
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}

.connections-panel {
  position: absolute;
  top: 60px;
  left: 12px;
  z-index: 100;
  width: 320px;
  max-height: calc(100% - 80px);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.btn-close-panel {
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.btn-close-panel:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.no-connections {
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
  padding: 20px;
}

.connection-item {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.connection-item:last-child {
  margin-bottom: 0;
}

.connection-item:hover {
  border-color: var(--accent-blue);
}

.connection-item.highlighted {
  border-color: var(--accent-green);
  background: rgba(126, 231, 135, 0.1);
}

.connection-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-family: var(--font-mono);
  font-size: 12px;
}

.connection-info .port-label {
  font-weight: 600;
}

.connection-info .arrow {
  color: var(--text-secondary);
}

.connection-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edge-type-select {
  flex: 1;
  padding: 6px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 12px;
  cursor: pointer;
}

.edge-type-select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.btn-delete-edge {
  width: 28px;
  height: 28px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.btn-delete-edge:hover {
  border-color: var(--accent-red);
  color: var(--accent-red);
  background: rgba(248, 81, 73, 0.1);
}

.btn-delete-edge svg {
  width: 14px;
  height: 14px;
}

.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: all 0.25s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.vue-flow {
  background: var(--bg-card) !important;
}

.vue-flow__background pattern {
  fill: var(--border-color) !important;
}

.custom-node {
  background: var(--bg-card);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 12px;
  min-width: 120px;
  transition: all 0.2s ease;
}

.custom-node:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.custom-node.selected {
  box-shadow: 0 0 0 2px var(--accent-blue);
}

.pc-node {
  border-color: var(--accent-blue);
}

.pc-node .node-header {
  color: var(--accent-blue);
}

.fw-node {
  border-color: var(--accent-orange);
}

.fw-node .node-header {
  color: var(--accent-orange);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.node-icon {
  width: 18px;
  height: 18px;
}

.node-title {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
}

.node-info {
  margin-bottom: 8px;
}

.image-tag {
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
}

.node-ports {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.port {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-secondary);
  background: var(--bg-elevated);
  padding: 2px 6px;
  border-radius: 4px;
}

.empty-hint {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

.hint-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-size: 14px;
  padding: 40px;
  background: rgba(26, 32, 40, 0.9);
  border: 1px dashed var(--border-color);
  border-radius: 12px;
}

.hint-content svg {
  width: 32px;
  height: 32px;
  opacity: 0.6;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  min-width: 400px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content-wide {
  min-width: 500px;
}

.modal-content h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.connection-config {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.config-side {
  flex: 1;
}

.config-side label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 8px;
}

.config-side select {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-mono);
}

.config-side select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.config-arrow {
  color: var(--text-secondary);
  font-size: 18px;
}

.edge-type-config {
  margin-bottom: 20px;
}

.edge-type-config label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--text-secondary);
}

.edge-type-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-edge-type {
  padding: 8px 14px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-edge-type:hover {
  border-color: var(--accent-blue);
  color: var(--text-primary);
}

.btn-edge-type.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.config-section {
  margin-bottom: 20px;
}

.config-section label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.config-section select {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-sans);
}

.config-section select:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.config-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.config-label-row label {
  margin-bottom: 0;
}

.resource-hint {
  font-size: 11px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.btn-refresh {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-refresh:hover:not(:disabled) {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-refresh svg {
  width: 12px;
  height: 12px;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-with-unit input {
  flex: 1;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: var(--font-mono);
}

.input-with-unit input:focus {
  outline: none;
  border-color: var(--accent-blue);
}

.input-with-unit .unit {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 30px;
}

.memory-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.btn-preset {
  padding: 6px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-preset:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.btn-preset.active {
  background: var(--accent-blue);
  border-color: var(--accent-blue);
  color: white;
}

.ports-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.port-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
}

.btn-remove-port {
  width: 16px;
  height: 16px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--accent-red);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-add-port {
  padding: 8px 12px;
  background: transparent;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
}

.btn-add-port:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel, .btn-confirm, .btn-delete {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-cancel {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.btn-cancel:hover {
  background: var(--bg-elevated);
}

.btn-confirm {
  background: var(--accent-blue);
  border: none;
  color: white;
}

.btn-confirm:hover {
  background: #4090e0;
}

.btn-delete {
  background: var(--accent-red);
  border: none;
  color: white;
  margin-right: auto;
}

.btn-delete:hover {
  background: #d73a49;
}

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}

.toast {
  position: fixed;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 14px;
  color: var(--text-primary);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.toast.success {
  border-color: var(--accent-green);
  background: rgba(63, 185, 80, 0.15);
}

.toast.error {
  border-color: var(--accent-red);
  background: rgba(248, 81, 73, 0.15);
}

.toast.warning {
  border-color: var(--accent-orange);
  background: rgba(240, 136, 62, 0.15);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

.handle-point {
  width: 10px !important;
  height: 10px !important;
  background: var(--bg-card) !important;
  border: 2px solid var(--accent-blue) !important;
  border-radius: 50% !important;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.handle-point:hover {
  opacity: 1;
  transform: scale(1.3);
  background: var(--accent-blue) !important;
}

.pc-node .handle-point {
  border-color: var(--accent-blue) !important;
}

.pc-node .handle-point:hover {
  background: var(--accent-blue) !important;
}

.fw-node .handle-point {
  border-color: var(--accent-orange) !important;
}

.fw-node .handle-point:hover {
  background: var(--accent-orange) !important;
}

.vue-flow__edge-path {
  stroke-linecap: round !important;
  stroke-linejoin: round !important;
}

.vue-flow__edge.selected .vue-flow__edge-path {
  stroke: #7ee787 !important;
  stroke-width: 3px !important;
}

.vue-flow__edge-text {
  font-family: var(--font-mono) !important;
}

.edge-label-colored {
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-family: var(--font-mono);
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.edge-label-colored span {
  font-weight: 600;
}

.edge-label-colored .separator {
  color: var(--text-secondary);
  font-weight: 400;
}

/* 设备状态徽章 */
.node-state-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
}

.node-state-badge.running {
  background: rgba(63, 185, 80, 0.15);
  color: var(--accent-green);
  border: 1px solid var(--accent-green);
}

.node-state-badge.stopped {
  background: rgba(248, 81, 73, 0.15);
  color: var(--accent-red);
  border: 1px solid var(--accent-red);
}

.node-state-badge.unknown {
  background: rgba(139, 148, 158, 0.15);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

/* 设备操作按钮 */
.node-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn-node-action {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-node-action svg {
  width: 16px;
  height: 16px;
}

.btn-node-action:hover:not(:disabled) {
  border-color: var(--accent-blue);
}

.btn-node-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-node-startup:hover:not(:disabled) {
  border-color: var(--accent-green);
  color: var(--accent-green);
  background: rgba(63, 185, 80, 0.1);
}

.btn-node-shutdown:hover:not(:disabled) {
  border-color: var(--accent-red);
  color: var(--accent-red);
  background: rgba(248, 81, 73, 0.1);
}

.btn-node-restart:hover:not(:disabled) {
  border-color: var(--accent-orange);
  color: var(--accent-orange);
  background: rgba(240, 136, 62, 0.1);
}

.hint-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 8px 0 0 0;
}
</style>