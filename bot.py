"""
Discord 资源分发 Bot 核心类
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import Config


class PersistentViewHandler(discord.ui.View):
    """
    持久化视图处理器
    用于处理 Bot 重启后的按钮交互
    通过监听所有以 "manage:" 开头的 custom_id
    """

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(custom_id="manage:delete:placeholder", style=discord.ButtonStyle.danger)
    async def placeholder_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """占位符按钮，实际回调由 on_interaction 处理"""
        pass

    @discord.ui.button(custom_id="manage:pin:placeholder", style=discord.ButtonStyle.secondary)
    async def placeholder_pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        """占位符按钮，实际回调由 on_interaction 处理"""
        pass

    @discord.ui.button(custom_id="manage:update:placeholder", style=discord.ButtonStyle.primary)
    async def placeholder_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        """占位符按钮，实际回调由 on_interaction 处理"""
        pass


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
        print()
        print("=" * 50)
        print("  Jiuwo-Discord-Safe-Bot 启动完成")
        print("=" * 50)
        print()

        # Bot 基本信息
        print(f"🤖 Bot 名称: {self.user.name}")
        print(f"🆔 Bot ID: {self.user.id}")
        print(f"📦 仓库频道 ID: {self.warehouse_channel_id}")

        # 验证仓库频道
        if self.warehouse_channel is None:
            print("⚠️  警告: 无法找到仓库频道，请检查 WAREHOUSE_CHANNEL_ID 配置")
        else:
            print(f"📦 仓库频道: #{self.warehouse_channel.name}")

        print()

        # 已加入的服务器列表
        print(f"🌐 已加入 {len(self.guilds)} 个服务器:")
        for guild in self.guilds:
            print(f"   • {guild.name} (ID: {guild.id}, 成员: {guild.member_count})")

        print()

        # 频道白名单
        from config import Config
        if Config.ALLOWED_FORUM_CHANNELS:
            print(f"📋 频道白名单 ({len(Config.ALLOWED_FORUM_CHANNELS)} 个):")
            for ch_id in Config.ALLOWED_FORUM_CHANNELS:
                channel = self.get_channel(ch_id)
                if channel:
                    print(f"   • #{channel.name} (ID: {ch_id})")
                else:
                    print(f"   • [未找到] (ID: {ch_id})")
        else:
            print("📋 频道白名单: 未配置 (允许所有论坛频道)")

        print()
        print("=" * 50)
        print("  ✅ Bot 已就绪，等待用户交互...")
        print("=" * 50)
        print()

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """
        处理所有交互事件
        用于处理持久化按钮的回调
        """
        # 只处理组件交互（按钮、选择菜单等）
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        # 处理管理按钮
        if custom_id.startswith("manage:"):
            await self._handle_manage_button(interaction, custom_id)

    async def _handle_manage_button(self, interaction: discord.Interaction, custom_id: str) -> None:
        """处理管理按钮交互"""
        try:
            parts = custom_id.split(":")
            if len(parts) < 4:
                return

            action = parts[1]
            warehouse_id = int(parts[2])
            uploader_id = int(parts[3])

            # 权限检查
            if interaction.user.id != uploader_id:
                from utils.embed_builder import build_error_embed
                await interaction.response.send_message(
                    embed=build_error_embed("只有发布者才能执行此操作"),
                    ephemeral=True,
                )
                return

            # 根据动作类型分发
            if action == "delete":
                from cogs.manage import handle_delete_work
                await handle_delete_work(interaction, warehouse_id)
            elif action == "pin":
                from cogs.manage import handle_toggle_pin
                await handle_toggle_pin(interaction)
            elif action == "update":
                from cogs.manage import handle_update_work
                await handle_update_work(interaction, warehouse_id)

        except Exception as e:
            print(f"❌ 处理管理按钮失败: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"操作失败: {str(e)}",
                        ephemeral=True,
                    )
            except Exception:
                pass
