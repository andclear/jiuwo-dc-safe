"""
模块 A：发布作品
实现 /发布作品 斜杠命令
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.metadata import create_metadata
from utils.embed_builder import build_publish_embed, build_error_embed, build_success_embed


class ManageView(discord.ui.View):
    """发布者管理按钮视图"""

    def __init__(self, warehouse_message_id: int, uploader_id: int, embed_message_id: int):
        super().__init__(timeout=None)
        self.warehouse_message_id = warehouse_message_id
        self.uploader_id = uploader_id
        self.embed_message_id = embed_message_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """检查是否为发布者本人"""
        if interaction.user.id != self.uploader_id:
            await interaction.response.send_message(
                embed=build_error_embed("只有发布者才能执行此操作"),
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="删除作品", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="delete_work")
    async def delete_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        """删除作品按钮"""
        # 导入管理模块的处理函数
        from cogs.manage import handle_delete_work

        await handle_delete_work(interaction, self.warehouse_message_id)

    @discord.ui.button(label="标注/取消标注", emoji="📌", style=discord.ButtonStyle.secondary, custom_id="toggle_pin")
    async def toggle_pin(self, interaction: discord.Interaction, button: discord.ui.Button):
        """标注/取消标注按钮"""
        from cogs.manage import handle_toggle_pin

        await handle_toggle_pin(interaction)

    @discord.ui.button(label="更新作品", emoji="📝", style=discord.ButtonStyle.primary, custom_id="update_work")
    async def update_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        """更新作品按钮"""
        from cogs.manage import handle_update_work

        await handle_update_work(interaction, self.warehouse_message_id)


class PublishCog(commands.Cog):
    """发布作品模块"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="发布作品", description="发布资源作品到当前帖子")
    @app_commands.describe(
        file="要上传的文件",
        title="作品标题",
        rule_repost="是否允许二传",
        rule_modify="是否允许二改",
        dl_req="下载门槛",
        passcode="提取码（仅当选择提取码模式时需要）",
    )
    @app_commands.choices(
        dl_req=[
            app_commands.Choice(name="自由下载", value="自由下载"),
            app_commands.Choice(name="互动(回应/回复)", value="互动"),
            app_commands.Choice(name="提取码", value="提取码"),
        ]
    )
    async def publish_work(
        self,
        interaction: discord.Interaction,
        file: discord.Attachment,
        title: str,
        rule_repost: bool,
        rule_modify: bool,
        dl_req: app_commands.Choice[str],
        passcode: str | None = None,
    ):
        """发布作品命令"""
        await interaction.response.defer(ephemeral=True)

        # 参数校验：提取码模式需要填写 passcode
        if dl_req.value == "提取码" and not passcode:
            await interaction.followup.send(
                embed=build_error_embed("选择提取码模式时，必须填写提取码"),
                ephemeral=True,
            )
            return

        # 获取仓库频道
        warehouse_channel = self.bot.warehouse_channel
        if warehouse_channel is None:
            await interaction.followup.send(
                embed=build_error_embed("仓库频道配置错误，请联系管理员"),
                ephemeral=True,
            )
            return

        try:
            # 构造元数据
            metadata = create_metadata(
                uploader_id=interaction.user.id,
                title=title,
                rule_repost=rule_repost,
                rule_modify=rule_modify,
                dl_req_type=dl_req.value,
                passcode=passcode,
            )

            # 下载文件到内存
            file_data = await file.to_file()

            # 入库：将文件和元数据发送到仓库频道
            warehouse_message = await warehouse_channel.send(
                content=metadata.to_json(),
                file=file_data,
            )

            # 构建公开 Embed
            embed = build_publish_embed(
                metadata=metadata,
                warehouse_message_id=warehouse_message.id,
            )

            # 创建管理按钮视图
            view = ManageView(
                warehouse_message_id=warehouse_message.id,
                uploader_id=interaction.user.id,
                embed_message_id=0,  # 稍后更新
            )

            # 发送公开 Embed
            public_message = await interaction.channel.send(embed=embed, view=view)

            # 更新视图中的消息 ID
            view.embed_message_id = public_message.id

            # 发送成功提示（私密）
            await interaction.followup.send(
                embed=build_success_embed(f"作品「{title}」发布成功！"),
                ephemeral=True,
            )

        except Exception as e:
            await interaction.followup.send(
                embed=build_error_embed(f"发布失败: {str(e)}"),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """加载 Cog"""
    await bot.add_cog(PublishCog(bot))
