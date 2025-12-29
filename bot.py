"""
Discord 资源分发 Bot 核心类
"""

import discord
from discord.ext import commands


class ResourceBot(commands.Bot):
    """资源分发 Bot 核心类"""

    def __init__(self, warehouse_channel_id: int):
        # 设置 intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.members = True

        super().__init__(
            command_prefix="!",  # 传统命令前缀（主要使用斜杠命令）
            intents=intents,
        )

        self.warehouse_channel_id = warehouse_channel_id
        self._warehouse_channel: discord.TextChannel | None = None

    @property
    def warehouse_channel(self) -> discord.TextChannel | None:
        """获取仓库频道"""
        if self._warehouse_channel is None:
            self._warehouse_channel = self.get_channel(self.warehouse_channel_id)
        return self._warehouse_channel

    async def setup_hook(self) -> None:
        """Bot 启动时的钩子函数"""
        # 加载所有 Cogs
        cogs = [
            "cogs.publish",
            "cogs.download",
            "cogs.manage",
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"✅ 已加载模块: {cog}")
            except Exception as e:
                print(f"❌ 加载模块失败 {cog}: {e}")

        # 同步斜杠命令
        await self.tree.sync()
        print("✅ 斜杠命令已同步")

    async def on_ready(self) -> None:
        """Bot 就绪事件"""
        print(f"🤖 Bot 已登录: {self.user}")
        print(f"📦 仓库频道 ID: {self.warehouse_channel_id}")

        # 验证仓库频道
        if self.warehouse_channel is None:
            print("⚠️ 警告: 无法找到仓库频道，请检查 WAREHOUSE_CHANNEL_ID 配置")
        else:
            print(f"📦 仓库频道: {self.warehouse_channel.name}")
