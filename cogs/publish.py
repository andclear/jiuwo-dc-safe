"""
模块 A：发布作品
实现 /发布作品 斜杠命令 - 交互式流程版本
支持多文件上传
"""

import discord
from discord import app_commands
from discord.ext import commands

from config import Config
from utils.metadata import create_metadata
from utils.embed_builder import build_publish_embed, build_error_embed, build_success_embed


class PersistentManageView(discord.ui.View):
    """
    持久化的发布者管理按钮视图
    将 warehouse_message_id 和 uploader_id 编码到 custom_id 中
    这样 Bot 重启后仍能处理按钮交互
    
    注意：按钮回调由 bot.py 的 on_interaction 统一处理，
    这里只负责创建带有正确 custom_id 的按钮
    """

    def __init__(self, warehouse_message_id: int = 0, uploader_id: int = 0):
        super().__init__(timeout=None)
        self.warehouse_message_id = warehouse_message_id
        self.uploader_id = uploader_id

        # 动态创建带有元数据的按钮（不设置回调，由 on_interaction 处理）
        if warehouse_message_id and uploader_id:
            self._create_buttons()

    def _create_buttons(self):
        """创建带有编码 ID 的按钮"""
        # 清除默认按钮
        self.clear_items()

        # ===== 第一行：所有用户可用的下载按钮 =====
        download_btn = discord.ui.Button(
            label="下载作品",
            emoji="📥",
            style=discord.ButtonStyle.success,
            custom_id=f"manage:download:{self.warehouse_message_id}:{self.uploader_id}",
            row=0,
        )
        self.add_item(download_btn)

        # ===== 第二行：仅发布者可用的管理按钮 =====
        # 格式: manage:action:warehouse_id:uploader_id
        # 注意：不设置 callback，由 bot.py 的 on_interaction 统一处理
        delete_btn = discord.ui.Button(
            label="删除",
            emoji="🗑️",
            style=discord.ButtonStyle.danger,
            custom_id=f"manage:delete:{self.warehouse_message_id}:{self.uploader_id}",
            row=1,
        )
        self.add_item(delete_btn)

        pin_btn = discord.ui.Button(
            label="标注",
            emoji="📌",
            style=discord.ButtonStyle.secondary,
            custom_id=f"manage:pin:{self.warehouse_message_id}:{self.uploader_id}",
            row=1,
        )
        self.add_item(pin_btn)

        update_btn = discord.ui.Button(
            label="更新",
            emoji="📝",
            style=discord.ButtonStyle.primary,
            custom_id=f"manage:update:{self.warehouse_message_id}:{self.uploader_id}",
            row=1,
        )
        self.add_item(update_btn)


class PublishSession:
    """发布会话数据"""

    def __init__(self, user_id: int, files: list[discord.Attachment]):
        self.user_id = user_id
        self.files = files
        self.title: str = ""
        self.rule_repost: bool = False  # 默认禁止二传
        self.rule_modify: bool = True   # 默认允许二改
        self.dl_req: str = "自由下载"
        self.passcode: str | None = None


class TitleModal(discord.ui.Modal, title="输入作品标题"):
    """标题输入弹窗"""

    title_input = discord.ui.TextInput(
        label="作品标题",
        placeholder="请输入作品标题",
        required=True,
        max_length=100,
    )

    def __init__(self, session: PublishSession, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__()
        self.session = session
        self.bot = bot
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        """提交标题后进入规则选择"""
        self.session.title = self.title_input.value
        # 进入规则选择步骤
        view = RulesSelectView(self.session, self.bot, self.channel)
        embed = discord.Embed(
            title="📋 设置版权规则",
            description=(
                f"**作品标题：** {self.session.title}\n"
                f"**文件数量：** {len(self.session.files)} 个\n\n"
                "请选择版权规则："
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.edit_message(embed=embed, view=view)


class RulesSelectView(discord.ui.View):
    """版权规则选择视图"""

    def __init__(self, session: PublishSession, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.session = session
        self.bot = bot
        self.channel = channel

    # 二传默认禁止：禁止按钮初始选中
    @discord.ui.button(label="允许二传", emoji="⬜", style=discord.ButtonStyle.secondary, row=0)
    async def allow_repost(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.rule_repost = True
        button.style = discord.ButtonStyle.success
        button.emoji = "✅"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "禁止二传":
                child.style = discord.ButtonStyle.secondary
                child.emoji = "⬜"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="禁止二传", emoji="❌", style=discord.ButtonStyle.danger, row=0)
    async def deny_repost(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.rule_repost = False
        button.style = discord.ButtonStyle.danger
        button.emoji = "❌"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "允许二传":
                child.style = discord.ButtonStyle.secondary
                child.emoji = "⬜"
        await interaction.response.edit_message(view=self)

    # 二改默认允许：允许按钮初始选中
    @discord.ui.button(label="允许二改", emoji="✅", style=discord.ButtonStyle.success, row=1)
    async def allow_modify(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.rule_modify = True
        button.style = discord.ButtonStyle.success
        button.emoji = "✅"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "禁止二改":
                child.style = discord.ButtonStyle.secondary
                child.emoji = "⬜"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="禁止二改", emoji="⬜", style=discord.ButtonStyle.secondary, row=1)
    async def deny_modify(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.rule_modify = False
        button.style = discord.ButtonStyle.danger
        button.emoji = "❌"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "允许二改":
                child.style = discord.ButtonStyle.secondary
                child.emoji = "⬜"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="下一步", emoji="➡️", style=discord.ButtonStyle.primary, row=2)
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):
        """进入下载门槛选择"""
        view = DownloadReqSelectView(self.session, self.bot, self.channel)
        embed = discord.Embed(
            title="🔒 设置下载门槛",
            description=(
                f"**作品标题：** {self.session.title}\n"
                f"**二传：** {'✅ 允许' if self.session.rule_repost else '❌ 禁止'}\n"
                f"**二改：** {'✅ 允许' if self.session.rule_modify else '❌ 禁止'}\n\n"
                "请选择下载门槛："
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.edit_message(embed=embed, view=view)


class DownloadReqSelectView(discord.ui.View):
    """下载门槛选择视图"""

    def __init__(self, session: PublishSession, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.session = session
        self.bot = bot
        self.channel = channel
        self._update_button_styles()

    def _update_button_styles(self):
        """更新按钮样式"""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == f"dl_{self.session.dl_req}":
                    child.style = discord.ButtonStyle.success
                elif child.custom_id and child.custom_id.startswith("dl_"):
                    child.style = discord.ButtonStyle.secondary

    @discord.ui.button(label="自由下载", emoji="🆓", style=discord.ButtonStyle.success, custom_id="dl_自由下载", row=0)
    async def free_download(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.dl_req = "自由下载"
        self.session.passcode = None
        self._update_button_styles()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="互动(回应/回复)", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="dl_互动", row=0)
    async def interaction_download(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.session.dl_req = "互动"
        self.session.passcode = None
        self._update_button_styles()
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="提取码", emoji="🔐", style=discord.ButtonStyle.secondary, custom_id="dl_提取码", row=0)
    async def passcode_download(self, interaction: discord.Interaction, button: discord.ui.Button):
        """选择提取码模式，弹出输入框"""
        modal = PasscodeInputModal(self.session, self.bot, self.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="确认发布", emoji="✅", style=discord.ButtonStyle.primary, row=1)
    async def confirm_publish(self, interaction: discord.Interaction, button: discord.ui.Button):
        """确认发布"""
        # 验证提取码模式
        if self.session.dl_req == "提取码" and not self.session.passcode:
            await interaction.response.send_message(
                embed=build_error_embed("提取码模式需要设置提取码"),
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self._do_publish(interaction)

    @discord.ui.button(label="取消", emoji="❌", style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """取消发布"""
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ 已取消发布", color=discord.Color.red()),
            view=None,
        )

    async def _do_publish(self, interaction: discord.Interaction):
        """执行发布操作"""
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
                uploader_id=self.session.user_id,
                title=self.session.title,
                rule_repost=self.session.rule_repost,
                rule_modify=self.session.rule_modify,
                dl_req_type=self.session.dl_req,
                passcode=self.session.passcode,
            )

            # 下载所有文件到内存
            files_data = []
            for attachment in self.session.files:
                file_data = await attachment.to_file()
                files_data.append(file_data)

            # 入库：将文件和元数据发送到仓库频道
            warehouse_message = await warehouse_channel.send(
                content=metadata.to_json(),
                files=files_data,
            )

            # 构建公开 Embed
            embed = build_publish_embed(
                metadata=metadata,
                warehouse_message_id=warehouse_message.id,
            )

            # 添加文件数量信息
            if len(self.session.files) > 1:
                embed.add_field(name="📎 文件数量", value=f"{len(self.session.files)} 个", inline=True)

            # 创建管理按钮视图
            view = PersistentManageView(
                warehouse_message_id=warehouse_message.id,
                uploader_id=self.session.user_id,
            )

            # 发送公开 Embed
            public_message = await self.channel.send(embed=embed, view=view)

            # 更新原消息
            await interaction.edit_original_response(
                embed=build_success_embed(f"作品「{self.session.title}」发布成功！"),
                view=None,
            )

        except Exception as e:
            await interaction.followup.send(
                embed=build_error_embed(f"发布失败: {str(e)}"),
                ephemeral=True,
            )


class PasscodeInputModal(discord.ui.Modal, title="设置提取码"):
    """提取码输入弹窗"""

    passcode_input = discord.ui.TextInput(
        label="提取码",
        placeholder="请输入提取码",
        required=True,
        max_length=50,
    )

    def __init__(self, session: PublishSession, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__()
        self.session = session
        self.bot = bot
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        """保存提取码"""
        self.session.dl_req = "提取码"
        self.session.passcode = self.passcode_input.value

        # 更新视图
        view = DownloadReqSelectView(self.session, self.bot, self.channel)
        embed = discord.Embed(
            title="🔒 设置下载门槛",
            description=(
                f"**作品标题：** {self.session.title}\n"
                f"**二传：** {'✅ 允许' if self.session.rule_repost else '❌ 禁止'}\n"
                f"**二改：** {'✅ 允许' if self.session.rule_modify else '❌ 禁止'}\n"
                f"**提取码：** `{self.session.passcode}`\n\n"
                "请确认下载门槛设置："
            ),
            color=discord.Color.blue(),
        )
        await interaction.response.edit_message(embed=embed, view=view)


class PublishCog(commands.Cog):
    """发布作品模块"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="发布作品", description="发布资源作品到当前帖子（交互式）")
    @app_commands.describe(
        file1="要上传的文件 1",
        file2="要上传的文件 2（可选）",
        file3="要上传的文件 3（可选）",
        file4="要上传的文件 4（可选）",
        file5="要上传的文件 5（可选）",
    )
    async def publish_work(
        self,
        interaction: discord.Interaction,
        file1: discord.Attachment,
        file2: discord.Attachment | None = None,
        file3: discord.Attachment | None = None,
        file4: discord.Attachment | None = None,
        file5: discord.Attachment | None = None,
    ):
        """发布作品命令 - 交互式流程"""
        channel = interaction.channel

        # ========== 权限检查 ==========

        # 1. 检查是否在论坛帖子（Thread）中
        if not isinstance(channel, discord.Thread):
            await interaction.response.send_message(
                embed=build_error_embed("此命令只能在论坛帖子中使用"),
                ephemeral=True,
            )
            return

        # 2. 检查是否是论坛频道的帖子
        parent = channel.parent
        if not isinstance(parent, discord.ForumChannel):
            await interaction.response.send_message(
                embed=build_error_embed("此命令只能在论坛类型的频道中使用"),
                ephemeral=True,
            )
            return

        # 3. 检查频道是否在白名单中
        if not Config.is_channel_allowed(parent.id):
            await interaction.response.send_message(
                embed=build_error_embed("此频道未被授权使用发布命令"),
                ephemeral=True,
            )
            return

        # 4. 检查是否是帖子发布者（owner）
        if channel.owner_id != interaction.user.id:
            await interaction.response.send_message(
                embed=build_error_embed("只有帖子发布者才能使用此命令"),
                ephemeral=True,
            )
            return

        # ========== 权限检查通过 ==========

        # 收集所有文件
        files = [file1]
        if file2:
            files.append(file2)
        if file3:
            files.append(file3)
        if file4:
            files.append(file4)
        if file5:
            files.append(file5)

        # 创建发布会话
        session = PublishSession(user_id=interaction.user.id, files=files)

        # 显示初始界面，请求输入标题
        embed = discord.Embed(
            title="📤 发布作品",
            description=(
                f"**文件数量：** {len(files)} 个\n"
                f"**文件列表：**\n" +
                "\n".join([f"  • {f.filename}" for f in files]) +
                "\n\n点击下方按钮开始设置作品信息"
            ),
            color=discord.Color.blue(),
        )

        view = StartPublishView(session, self.bot, interaction.channel)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class StartPublishView(discord.ui.View):
    """开始发布视图"""

    def __init__(self, session: PublishSession, bot: commands.Bot, channel: discord.TextChannel):
        super().__init__(timeout=300)
        self.session = session
        self.bot = bot
        self.channel = channel

    @discord.ui.button(label="开始设置", emoji="▶️", style=discord.ButtonStyle.primary)
    async def start_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        """弹出标题输入框"""
        modal = TitleModal(self.session, self.bot, self.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="取消", emoji="❌", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """取消发布"""
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ 已取消发布", color=discord.Color.red()),
            view=None,
        )


async def setup(bot: commands.Bot):
    """加载 Cog"""
    await bot.add_cog(PublishCog(bot))
