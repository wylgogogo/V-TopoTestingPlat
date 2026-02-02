#!/bin/bash
set -e

echo "=========================================="
echo "FW Lab 一键启动"
echo "=========================================="

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用 sudo 运行此脚本"
    echo "用法: sudo bash start-all.sh"
    exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 检查系统依赖
echo "检查系统依赖..."
for cmd in virsh virt-install docker ip python3 node npm; do
    if ! command -v $cmd &> /dev/null; then
        echo "错误: 缺少命令 $cmd"
        exit 1
    fi
done
echo "依赖检查通过 ✓"

# 确保 /img 目录存在
mkdir -p /img

# ========== 后端 ==========
echo ""
echo ">>> 启动后端..."
cd "$SCRIPT_DIR/backend"

# 创建虚拟环境
VENV_DIR="$SCRIPT_DIR/backend/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv "$VENV_DIR"
    chown -R $REAL_USER:$REAL_USER "$VENV_DIR"
fi

# 安装依赖（包括 websockets）
source "$VENV_DIR/bin/activate"
pip install -q fastapi uvicorn sqlalchemy python-multipart websockets

# 启动后端
"$VENV_DIR/bin/uvicorn" main:app --host 0.0.0.0 --port 8000 --reload > /tmp/fw-lab-backend.log 2>&1 &
BACKEND_PID=$!
echo "后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 2
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "后端启动失败，查看日志: /tmp/fw-lab-backend.log"
    exit 1
fi
echo "后端启动成功 ✓"

# ========== 前端 ==========
echo ""
echo ">>> 启动前端..."
cd "$SCRIPT_DIR/frontend"

# 检查 node_modules
echo "确保前端依赖是最新的..."
sudo -u $REAL_USER npm install

# 启动前端（以普通用户身份）
sudo -u $REAL_USER npm run dev > /tmp/fw-lab-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"

# 等待前端启动
sleep 3
echo "前端启动成功 ✓"

# ========== 完成 ==========
echo ""
echo "=========================================="
echo "✅ 所有服务已启动!"
echo "=========================================="
echo ""
echo "  前端地址: http://localhost:5173"
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "  日志文件:"
echo "   后端: /tmp/fw-lab-backend.log"
echo "   前端: /tmp/fw-lab-frontend.log"
echo ""
echo "查看日志: tail -f /tmp/fw-lab-backend.log /tmp/fw-lab-frontend.log"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID" > /tmp/fw-lab-backend.pid
echo "$FRONTEND_PID" > /tmp/fw-lab-frontend.pid

# 捕获退出信号
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f /tmp/fw-lab-backend.pid /tmp/fw-lab-frontend.pid
    echo "服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待任意进程结束
wait