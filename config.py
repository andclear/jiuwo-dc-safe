"""
配置管理模块
从环境变量加载 Bot 配置
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """Bot 配置类"""

    # Discord Bot Token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    # 仓库频道 ID（用于存储文件）
    WAREHOUSE_CHANNEL_ID: int = int(os.getenv("WAREHOUSE_CHANNEL_ID", "0"))

    @classmethod
    def validate(cls) -> bool:
        """验证配置是否完整"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN 未配置，请在 .env 文件中设置")
        if cls.WAREHOUSE_CHANNEL_ID == 0:
            raise ValueError("WAREHOUSE_CHANNEL_ID 未配置，请在 .env 文件中设置")
        return True


# 导出配置实例
config = Config()
