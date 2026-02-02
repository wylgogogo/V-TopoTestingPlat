"""
VM Serial Console WebShell
通过 virsh console 实现 VM 的 Web 终端访问
"""
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import pty
import os
import select
import subprocess
import fcntl
import struct
import termios
import signal


class UTF8Decoder:
    """
    UTF-8 流式解码器
    处理字节流中 UTF-8 多字节字符被截断的情况
    """
    def __init__(self):
        self.buffer = b''

    def decode(self, data: bytes) -> str:
        """
        解码字节数据，保留不完整的 UTF-8 序列到下次
        """
        self.buffer += data

        if not self.buffer:
            return ''

        # 从后往前扫描，找到最后一个完整字符的位置
        complete_end = len(self.buffer)

        # 从末尾开始，跳过所有续字节 (10xxxxxx, 0x80-0xBF)
        i = len(self.buffer) - 1
        while i >= 0 and 0x80 <= self.buffer[i] < 0xC0:
            i -= 1

        # 现在 i 指向的要么是 ASCII (<0x80)，要么是多字节首字节 (>=0xC0)，要么是 -1
        if i >= 0 and self.buffer[i] >= 0xC0:
            # 找到了多字节首字节，检查序列是否完整
            byte = self.buffer[i]
            if byte < 0xE0:
                expected_len = 2   # 110xxxxx 开头，2字节
            elif byte < 0xF0:
                expected_len = 3   # 1110xxxx 开头，3字节
            else:
                expected_len = 4   # 11110xxx 开头，4字节

            actual_len = len(self.buffer) - i
            if actual_len < expected_len:
                # 序列不完整，保留从 i 开始的部分到下次
                complete_end = i
        elif i < 0 and len(self.buffer) > 0:
            # 整个缓冲区都是续字节，说明首字节还没收到
            # 保留所有数据到下次（最多保留3个续字节）
            keep = min(len(self.buffer), 3)
            complete_end = len(self.buffer) - keep

        # 分离完整部分和不完整部分
        complete_data = self.buffer[:complete_end]
        self.buffer = self.buffer[complete_end:]

        # 解码完整部分
        if not complete_data:
            return ''

        try:
            return complete_data.decode('utf-8')
        except UnicodeDecodeError:
            # 如果还是解码失败，使用 replace 模式
            return complete_data.decode('utf-8', errors='replace')


async def vm_shell(ws: WebSocket, vm_name: str):
    """
    WebSocket Shell - 通过 virsh console 连接 VM 串口
    """
    await ws.accept()

    # 检查 VM 是否存在且运行中
    check = subprocess.run(
        ["virsh", "domstate", vm_name],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        await ws.send_text(f"\r\n\x1b[31m错误: VM {vm_name} 不存在\x1b[0m\r\n")
        await ws.close()
        return

    if "running" not in check.stdout.lower():
        await ws.send_text(f"\r\n\x1b[31m错误: VM {vm_name} 未运行 (状态: {check.stdout.strip()})\x1b[0m\r\n")
        await ws.close()
        return

    # 检查 VM 是否有串口设备
    check_serial = subprocess.run(
        ["virsh", "dumpxml", vm_name],
        capture_output=True, text=True
    )
    if "<serial type=" not in check_serial.stdout and "<console type=" not in check_serial.stdout:
        await ws.send_text(f"\r\n\x1b[33m警告: VM {vm_name} 可能未配置串口设备\x1b[0m\r\n")
        await ws.send_text(f"\x1b[33m如果无法连接，请确保 VM 镜像支持串口控制台\x1b[0m\r\n\r\n")

    # 创建伪终端
    master_fd, slave_fd = pty.openpty()

    # 设置初始终端大小
    winsize = struct.pack('HHHH', 24, 80, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

    # 启动 virsh console
    # --force 参数可以断开其他连接
    process = subprocess.Popen(
        ["virsh", "console", vm_name, "--force"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        preexec_fn=os.setsid,
        env={**os.environ, "TERM": "xterm-256color", "LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}
    )

    # 关闭 slave 端
    os.close(slave_fd)

    # 设置 master_fd 为非阻塞
    fl = fcntl.fcntl(master_fd, fcntl.F_GETFL)
    fcntl.fcntl(master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    stop_flag = asyncio.Event()

    # 创建 UTF-8 解码器
    utf8_decoder = UTF8Decoder()

    # 发送欢迎信息
    welcome_msg = (
        f"\x1b[32m正在连接到 {vm_name} 串口控制台...\x1b[0m\r\n"
        f"\x1b[90m提示: 如果没有显示，请按 Enter 键\x1b[0m\r\n"
        f"\x1b[90m退出: 关闭此终端窗口\x1b[0m\r\n\r\n"
    )
    try:
        await ws.send_text(welcome_msg)
    except:
        pass

    async def read_from_pty():
        """从 PTY 读取数据并发送到 WebSocket"""
        try:
            while not stop_flag.is_set():
                if process.poll() is not None:
                    break

                try:
                    r, _, _ = select.select([master_fd], [], [], 0.02)
                except (ValueError, OSError):
                    break

                if master_fd in r:
                    try:
                        data = os.read(master_fd, 4096)
                        if data:
                            try:
                                # 使用流式 UTF-8 解码器处理可能被截断的多字节字符
                                text = utf8_decoder.decode(data)
                                if text:
                                    await ws.send_text(text)
                            except:
                                break
                        else:
                            break
                    except (OSError, IOError) as e:
                        if e.errno not in (11, 35):  # EAGAIN, EWOULDBLOCK
                            break
                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"[VMShell] Read error: {e}")

    async def write_to_pty():
        """从 WebSocket 读取数据并写入 PTY"""
        try:
            while not stop_flag.is_set():
                try:
                    data = await asyncio.wait_for(ws.receive_text(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                except WebSocketDisconnect:
                    break

                # 处理终端大小调整
                if data.startswith('\x1b[8;') and data.endswith('t'):
                    try:
                        parts = data[4:-1].split(';')
                        if len(parts) == 2:
                            rows, cols = int(parts[0]), int(parts[1])
                            winsize = struct.pack('HHHH', rows, cols, 0, 0)
                            fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                            # 发送 SIGWINCH 给进程组
                            try:
                                os.killpg(os.getpgid(process.pid), signal.SIGWINCH)
                            except:
                                pass
                    except:
                        pass
                    continue

                try:
                    os.write(master_fd, data.encode('utf-8'))
                except (OSError, IOError):
                    break

        except Exception as e:
            print(f"[VMShell] Write error: {e}")

    try:
        read_task = asyncio.create_task(read_from_pty())
        write_task = asyncio.create_task(write_to_pty())

        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        stop_flag.set()

        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    except Exception as e:
        print(f"[VMShell] Error: {e}")

    finally:
        stop_flag.set()

        try:
            os.close(master_fd)
        except:
            pass

        if process.poll() is None:
            try:
                # 发送 Ctrl+] 退出 virsh console
                # 0x1d 是 Ctrl+] 的 ASCII 码
                try:
                    os.write(master_fd, b'\x1d')
                except:
                    pass

                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            except:
                pass

        try:
            await ws.close()
        except:
            pass

        print(f"[VMShell] Connection closed for {vm_name}")


async def check_vm_console(vm_name: str) -> dict:
    """检查 VM 控制台状态"""
    # 检查 VM 状态
    result = subprocess.run(
        ["virsh", "domstate", vm_name],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        return {"ok": False, "error": "VM 不存在"}

    state = result.stdout.strip()
    if "running" not in state.lower():
        return {"ok": False, "error": f"VM 未运行 (状态: {state})"}

    # 检查是否有串口
    xml_result = subprocess.run(
        ["virsh", "dumpxml", vm_name],
        capture_output=True, text=True
    )

    has_serial = "<serial type=" in xml_result.stdout or "<console type=" in xml_result.stdout

    return {
        "ok": True,
        "vm_name": vm_name,
        "state": state,
        "has_serial": has_serial
    }