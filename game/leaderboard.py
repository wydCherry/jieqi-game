"""
排行榜模块 - 本地战绩统计
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import config


class GameRecord:
    """对局记录"""

    def __init__(self, mode: str, result: str, opponent: str,
                 duration: int = 0, moves: int = 0, player_color: str = 'red'):
        self.date = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.mode = mode  # 游戏模式
        self.result = result  # 胜/负/和
        self.opponent = opponent  # 对手信息
        self.duration = duration  # 对局时长（秒）
        self.moves = moves  # 总步数
        self.player_color = player_color  # 玩家执方

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'date': self.date,
            'mode': self.mode,
            'result': self.result,
            'opponent': self.opponent,
            'duration': self.duration,
            'moves': self.moves,
            'player_color': self.player_color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameRecord':
        """从字典创建"""
        record = cls(
            data.get('mode', ''),
            data.get('result', ''),
            data.get('opponent', ''),
            data.get('duration', 0),
            data.get('moves', 0),
            data.get('player_color', 'red'),
        )
        record.date = data.get('date', '')
        return record


class Leaderboard:
    """排行榜系统"""

    def __init__(self):
        """初始化排行榜"""
        self.records: List[GameRecord] = []
        self.data_file = config.RECORDS_FILE
        self._ensure_data_dir()
        self.load()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.data_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def add_record(self, mode: str, result: str, opponent: str,
                   duration: int = 0, moves: int = 0, player_color: str = 'red'):
        """
        添加对局记录

        Args:
            mode: 游戏模式
            result: 结果（胜/负/和）
            opponent: 对手信息
            duration: 对局时长
            moves: 总步数
            player_color: 玩家执方
        """
        record = GameRecord(mode, result, opponent, duration, moves, player_color)
        self.records.append(record)
        self.save()

    def load(self):
        """从文件加载记录"""
        if not os.path.exists(self.data_file):
            return

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.records = [GameRecord.from_dict(r) for r in data]
        except (json.JSONDecodeError, IOError):
            self.records = []

    def save(self):
        """保存记录到文件"""
        data = [r.to_dict() for r in self.records]
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def get_stats(self) -> Dict:
        """
        获取统计数据

        Returns:
            统计数据字典
        """
        total = len(self.records)
        wins = sum(1 for r in self.records if r.result == '胜')
        losses = sum(1 for r in self.records if r.result == '负')
        draws = sum(1 for r in self.records if r.result == '和')

        win_rate = (wins / total * 100) if total > 0 else 0

        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': round(win_rate, 1),
        }

    def get_mode_stats(self, mode: str) -> Dict:
        """
        获取指定模式的统计

        Args:
            mode: 游戏模式

        Returns:
            统计数据
        """
        mode_records = [r for r in self.records if r.mode == mode]
        total = len(mode_records)
        wins = sum(1 for r in mode_records if r.result == '胜')
        losses = sum(1 for r in mode_records if r.result == '负')
        draws = sum(1 for r in mode_records if r.result == '和')

        return {
            'total': total,
            'wins': wins,
            'losses': losses,
            'draws': draws,
        }

    def get_recent_records(self, limit: int = 10) -> List[GameRecord]:
        """
        获取最近的对局记录

        Args:
            limit: 数量限制

        Returns:
            记录列表
        """
        return self.records[-limit:][::-1]

    def clear(self):
        """清空所有记录"""
        self.records = []
        self.save()

    def export_to_file(self, filepath: str) -> bool:
        """
        导出记录到文件

        Args:
            filepath: 文件路径

        Returns:
            是否成功
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                data = [r.to_dict() for r in self.records]
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

    def import_from_file(self, filepath: str) -> bool:
        """
        从文件导入记录

        Args:
            filepath: 文件路径

        Returns:
            是否成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                new_records = [GameRecord.from_dict(r) for r in data]
                self.records.extend(new_records)
                self.save()
            return True
        except (json.JSONDecodeError, IOError):
            return False


# 全局排行榜实例
_leaderboard: Optional[Leaderboard] = None


def get_leaderboard() -> Leaderboard:
    """获取排行榜实例"""
    global _leaderboard
    if _leaderboard is None:
        _leaderboard = Leaderboard()
    return _leaderboard