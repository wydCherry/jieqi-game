"""
网络对战模块
"""

import socket
import json
import threading
import time
from typing import Optional, Callable, Dict, Any
from enum import Enum
import config


class NetworkState(Enum):
    """网络状态"""
    DISCONNECTED = 'disconnected'
    CONNECTING = 'connecting'
    HOSTING = 'hosting'
    CONNECTED = 'connected'
    PLAYING = 'playing'


class MessageType:
    """消息类型"""
    JOIN = 'join'           # 加入房间
    LEAVE = 'leave'         # 离开房间
    READY = 'ready'         # 准备就绪
    MOVE = 'move'           # 走棋
    FLIP = 'flip'           # 翻棋
    SYNC = 'sync'           # 状态同步
    CHAT = 'chat'           # 聊天
    RESIGN = 'resign'       # 认输
    PING = 'ping'           # 心跳
    PONG = 'pong'           # 心跳响应


class NetworkManager:
    """网络管理器"""

    def __init__(self):
        """初始化网络管理器"""
        self.socket: Optional[socket.socket] = None
        self.state = NetworkState.DISCONNECTED
        self.room_id: Optional[str] = None
        self.is_host = False

        self.host_address: Optional[str] = None
        self.host_port = 5555

        # 回调函数
        self.on_message: Optional[Callable] = None
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None

        # 接收线程
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False

        # 游戏状态缓存（用于断线重连）
        self.game_state: Dict[str, Any] = {}

    def get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def create_room(self, port: int = 5555) -> bool:
        """
        创建房间（作为主机）

        Args:
            port: 端口号

        Returns:
            是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(('', port))
            self.socket.listen(1)

            self.host_port = port
            self.room_id = f"{self.get_local_ip()}:{port}"
            self.is_host = True
            self.state = NetworkState.HOSTING

            # 启动监听线程
            self.running = True
            threading.Thread(target=self._accept_connection, daemon=True).start()

            return True
        except Exception as e:
            print(f"创建房间失败: {e}")
            return False

    def _accept_connection(self):
        """等待客户端连接（主机端）"""
        try:
            self.socket.settimeout(1.0)  # 设置超时以便检查running状态
            while self.running and self.state == NetworkState.HOSTING:
                try:
                    client_socket, address = self.socket.accept()
                    self.client_socket = client_socket
                    self.client_address = address

                    self.state = NetworkState.CONNECTED

                    if self.on_connected:
                        self.on_connected(address)

                    # 启动接收线程
                    self._start_receive_thread(client_socket)

                    break
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"接受连接失败: {e}")

    def join_room(self, host_ip: str, port: int = 5555) -> bool:
        """
        加入房间（作为客户端）

        Args:
            host_ip: 主机IP
            port: 端口号

        Returns:
            是否成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host_ip, port))

            self.host_address = host_ip
            self.host_port = port
            self.room_id = f"{host_ip}:{port}"
            self.is_host = False
            self.state = NetworkState.CONNECTED

            # 启动接收线程
            self._start_receive_thread(self.socket)

            if self.on_connected:
                self.on_connected((host_ip, port))

            return True
        except Exception as e:
            print(f"加入房间失败: {e}")
            return False

    def _start_receive_thread(self, sock: socket.socket):
        """启动接收线程"""
        self.receive_socket = sock

        def receive_loop():
            while self.running and self.state in [NetworkState.CONNECTED, NetworkState.PLAYING]:
                try:
                    data = sock.recv(4096)
                    if not data:
                        break

                    message = json.loads(data.decode('utf-8'))
                    self._handle_message(message)
                except socket.timeout:
                    continue
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    print(f"接收数据错误: {e}")
                    break

            # 连接断开
            self.state = NetworkState.DISCONNECTED
            if self.on_disconnected:
                self.on_disconnected()

        self.running = True
        self.receive_thread = threading.Thread(target=receive_loop, daemon=True)
        self.receive_thread.start()

    def _handle_message(self, message: Dict):
        """处理接收到的消息"""
        if self.on_message:
            self.on_message(message)

    def send_message(self, msg_type: str, data: Dict = None) -> bool:
        """
        发送消息

        Args:
            msg_type: 消息类型
            data: 消息数据

        Returns:
            是否成功
        """
        if self.state not in [NetworkState.CONNECTED, NetworkState.PLAYING]:
            return False

        message = {
            'type': msg_type,
            'data': data or {},
            'timestamp': time.time()
        }

        try:
            data_str = json.dumps(message, ensure_ascii=False)
            self.receive_socket.send(data_str.encode('utf-8'))
            return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False

    def send_move(self, from_pos: tuple, to_pos: tuple) -> bool:
        """
        发送走棋信息

        Args:
            from_pos: 起始位置
            to_pos: 目标位置

        Returns:
            是否成功
        """
        return self.send_message(MessageType.MOVE, {
            'from': from_pos,
            'to': to_pos
        })

    def send_flip(self, pos: tuple) -> bool:
        """
        发送翻棋信息

        Args:
            pos: 棋子位置

        Returns:
            是否成功
        """
        return self.send_message(MessageType.FLIP, {'pos': pos})

    def send_resign(self) -> bool:
        """发送认输"""
        return self.send_message(MessageType.RESIGN)

    def send_chat(self, message: str) -> bool:
        """发送聊天消息"""
        return self.send_message(MessageType.CHAT, {'message': message})

    def disconnect(self):
        """断开连接"""
        self.running = False

        try:
            if self.receive_socket:
                self.receive_socket.close()
        except:
            pass

        try:
            if self.socket:
                self.socket.close()
        except:
            pass

        self.state = NetworkState.DISCONNECTED
        self.room_id = None
        self.is_host = False

    def is_connected(self) -> bool:
        """是否已连接"""
        return self.state in [NetworkState.CONNECTED, NetworkState.PLAYING]

    def get_room_id(self) -> Optional[str]:
        """获取房间ID"""
        return self.room_id


class OnlineGameManager:
    """网络对战游戏管理器"""

    def __init__(self):
        """初始化"""
        self.network = NetworkManager()
        self.is_my_turn = False
        self.my_color: Optional[str] = None

        # 设置网络回调
        self.network.on_message = self._on_network_message

    def host_game(self) -> str:
        """
        创建房间

        Returns:
            房间ID（IP:端口）
        """
        if self.network.create_room():
            self.my_color = 'red'  # 主机执红
            return self.network.get_room_id()
        return ""

    def join_game(self, room_id: str) -> bool:
        """
        加入游戏

        Args:
            room_id: 房间ID

        Returns:
            是否成功
        """
        try:
            parts = room_id.split(':')
            ip = parts[0]
            port = int(parts[1]) if len(parts) > 1 else 5555

            if self.network.join_room(ip, port):
                self.my_color = 'black'  # 客户端执黑
                return True
        except:
            pass
        return False

    def _on_network_message(self, message: Dict):
        """处理网络消息"""
        msg_type = message.get('type')
        data = message.get('data', {})

        if msg_type == MessageType.MOVE:
            # 对手走棋
            self._handle_opponent_move(data)
        elif msg_type == MessageType.FLIP:
            # 对手翻棋
            self._handle_opponent_flip(data)
        elif msg_type == MessageType.RESIGN:
            # 对手认输
            self._handle_opponent_resign()
        elif msg_type == MessageType.CHAT:
            # 聊天消息
            pass

    def _handle_opponent_move(self, data: Dict):
        """处理对手走棋"""
        # 由外部处理
        pass

    def _handle_opponent_flip(self, data: Dict):
        """处理对手翻棋"""
        pass

    def _handle_opponent_resign(self):
        """处理对手认输"""
        pass

    def send_my_move(self, from_pos: tuple, to_pos: tuple) -> bool:
        """发送我的走棋"""
        return self.network.send_move(from_pos, to_pos)

    def disconnect(self):
        """断开连接"""
        self.network.disconnect()