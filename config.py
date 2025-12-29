"""
配置管理模块
从环境变量和配置文件加载 Bot 配置
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
CHANNELS_FILE = CONFIG_DIR / "channels.txt"


class Config:
    """Bot 配置类"""

    # Discord Bot Token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # 仓库频道 ID（用于存储文件）
    WAREHOUSE_CHANNEL_ID: int = int(os.getenv("WAREHOUSE_CHANNEL_ID", "0"))

    # 允许使用 Bot 命令的论坛频道 ID 列表
    ALLOWED_FORUM_CHANNELS: list[int] = []

    @classmethod
    def _load_channels_from_file(cls) -> list[int]:
        """从 channels.txt 文件加载频道白名单"""
        if not CHANNELS_FILE.exists():
            return []

        channels = []
        try:
            with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith("#"):
                        continue
                    try:
                        channel_id = int(line)
                        channels.append(channel_id)
                    except ValueError:
                        print(f"⚠️ 无效的频道 ID: {line}")
        except Exception as e:
            print(f"⚠️ 读取频道白名单失败: {e}")

        return channels

    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN 未配置，请在 .env 文件中设置")
        if cls.WAREHOUSE_CHANNEL_ID == 0:
            raise ValueError("WAREHOUSE_CHANNEL_ID 未配置，请在 .env 文件中设置")

        # 加载频道白名单
        cls.ALLOWED_FORUM_CHANNELS = cls._load_channels_from_file()
        if cls.ALLOWED_FORUM_CHANNELS:
            print(f"📋 已加载 {len(cls.ALLOWED_FORUM_CHANNELS)} 个白名单频道")
        else:
            print("📋 未配置频道白名单，允许所有论坛频道")

        return True

    @classmethod
    def is_channel_allowed(cls, channel_id: int) -> bool:
        """检查频道是否允许使用 Bot"""
        # 如果未配置白名单，则允许所有频道
        if not cls.ALLOWED_FORUM_CHANNELS:
            return True
        return channel_id in cls.ALLOWED_FORUM_CHANNELS

    @classmethod
    def reload_channels(cls) -> int:
        """重新加载频道白名单，返回加载的频道数量"""
        cls.ALLOWED_FORUM_CHANNELS = cls._load_channels_from_file()
        return len(cls.ALLOWED_FORUM_CHANNELS)


# 导出配置实例
config = Config()
