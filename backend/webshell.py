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

        # 找到最后一个完整的 UTF-8 字符的位置
        complete_end = len(self.buffer)

        # 从后往前检查，找到可能不完整的 UTF-8 序列
        # UTF-8 编码规则：
        # - 单字节: 0xxxxxxx (0x00-0x7F)
        # - 多字节首字节: 11xxxxxx (0xC0-0xFF)
        # - 多字节后续字节: 10xxxxxx (0x80-0xBF)

        for i in range(min(4, len(self.buffer)), 0, -1):
            idx = len(self.buffer) - i
            if idx < 0:
                continue

            byte = self.buffer[idx]

            # 检查是否是多字节序列的开始
            if byte >= 0xC0:  # 多字节首字节
                # 计算这个字符应该有多少字节
                if byte < 0xE0:
                    expected_len = 2
                elif byte < 0xF0:
                    expected_len = 3
                else:
                    expected_len = 4

                # 检查是否有足够的后续字节
                remaining = len(self.buffer) - idx
                if remaining < expected_len:
                    # 不完整的序列，保留到下次
                    complete_end = idx
                break
            elif byte < 0x80:
                # ASCII 字符，之前的都是完整的
                break

        # 分离完整部分和不完整部分
        complete_data = self.buffer[:complete_end]
        self.buffer = self.buffer[complete_end:]

        # 解码完整部分
        try:
            return complete_data.decode('utf-8')
        except UnicodeDecodeError:
            # 如果还是解码失败，使用 replace 模式
            return complete_data.decode('utf-8', errors='replace')


async def shell(ws: WebSocket, container: str):
    """
    WebSocket Shell - 使用 PTY 实现真正的实时交互式终端
    """
    await ws.accept()

    # 检查容器是否存在且运行中
    check = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        await ws.send_text(f"\r\n\x1b[31m错误: 容器 {container} 不存在\x1b[0m\r\n")
        await ws.close()
        return

    if check.stdout.strip() != "true":
        await ws.send_text(f"\r\n\x1b[31m错误: 容器 {container} 未运行\x1b[0m\r\n")
        await ws.close()
        return

    # 创建伪终端
    master_fd, slave_fd = pty.openpty()

    # 设置初始终端大小
    winsize = struct.pack('HHHH', 24, 80, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)

    # 启动 docker exec
    process = subprocess.Popen(
        ["docker", "exec", "-it", container, "/bin/bash"],
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
                        if e.errno not in (11, 35):
                            break
                else:
                    await asyncio.sleep(0.01)

        except Exception as e:
            print(f"[WebShell] Read error: {e}")

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
                            os.kill(process.pid, signal.SIGWINCH)
                    except:
                        pass
                    continue

                try:
                    os.write(master_fd, data.encode('utf-8'))
                except (OSError, IOError):
                    break

        except Exception as e:
            print(f"[WebShell] Write error: {e}")

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
        print(f"[WebShell] Error: {e}")

    finally:
        stop_flag.set()

        try:
            os.close(master_fd)
        except:
            pass

        if process.poll() is None:
            try:
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

        print(f"[WebShell] Connection closed for {container}")