"""
Discord 资源分发 Bot
程序入口
"""

from config import Config
from bot import ResourceBot


def main():
    """主函数"""
    # 验证配置
    Config.validate()

    # 创建并运行 Bot
    bot = ResourceBot(warehouse_channel_id=Config.WAREHOUSE_CHANNEL_ID)
    bot.run(Config.BOT_TOKEN)


if __name__ == "__main__":
    main()
