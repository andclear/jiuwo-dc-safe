"""
模块 B：获取作品
实现 /获取作品 斜杠命令
"""

import discord
from discord import app_commands
from discord.ext import commands

from utils.metadata import parse_metadata
from utils.embed_builder import build_download_embed, build_error_embed


class PasscodeModal(discord.ui.Modal, title="输入提取码"):
    """提取码输入弹窗"""

    passcode_input = discord.ui.TextInput(
        label="提取码",
        placeholder="请输入提取码",
        required=True,
        max_length=50,
    )

    def __init__(self, expected_code: str, attachment_url: str, title: str):
        super().__init__()
        self.expected_code = expected_code
        self.attachment_url = attachment_url
        self.resource_title = title

    async def on_submit(self, interaction: discord.Interaction):
        """提交时验证提取码"""
        if self.passcode_input.value == self.expected_code:
            embed = build_download_embed(self.resource_title, self.attachment_url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                embed=build_error_embed("提取码错误，请重试"),
                ephemeral=True,
            )


class DownloadCog(commands.Cog):
    """获取作品模块"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def find_warehouse_id_in_thread(
        self, channel: discord.TextChannel | discord.Thread
    ) -> int | None:
        """
        在当前 Thread 中查找包含 WarehouseID 的 Embed

        Returns:
            仓库消息 ID，未找到返回 None
        """
        async for message in channel.history(limit=100):
            if message.embeds:
                for embed in message.embeds:
                    if embed.footer and embed.footer.text:
                        footer_text = embed.footer.text
                        # 支持多种 footer 格式
                        if footer_text.startswith("WarehouseID:"):
                            try:
                                warehouse_id = int(
                                    footer_text.replace("WarehouseID:", "").strip()
                                )
                                return warehouse_id
                            except ValueError:
                                continue
                        elif footer_text.startswith("作品ID:") or footer_text.startswith("ID:"):
                            try:
                                warehouse_id = int(footer_text.split(":")[-1].strip())
                                return warehouse_id
                            except ValueError:
                                continue
        return None

    async def check_user_interaction(
        self,
        user: discord.User | discord.Member,
        thread: discord.Thread,
    ) -> bool:
        """
        检查用户是否对帖子有互动（Reaction 或回复）

        Args:
            user: 用户
            thread: 帖子 Thread

        Returns:
            是否有互动
        """
        # 获取首楼消息（Thread 的 starter_message）
        try:
            # 方法1：直接使用 thread.starter_message（如果可用）
            starter_message = thread.starter_message
            if starter_message is None:
                # 方法2：通过 API 获取首楼消息
                starter_message = await thread.fetch_message(thread.id)
                if starter_message is None:
                    # 方法3：从父频道获取首楼消息
                    if thread.starter_message_id:
                        starter_message = await thread.parent.fetch_message(thread.starter_message_id)
        except Exception:
            starter_message = None

        # 检查是否有 Reaction
        if starter_message:
            for reaction in starter_message.reactions:
                async for reactor in reaction.users():
                    if reactor.id == user.id:
                        return True

        # 检查是否在 Thread 中有回复
        async for message in thread.history(limit=200):
            if message.author.id == user.id:
                return True

        return False

    @app_commands.command(name="获取作品", description="获取当前帖子的资源下载链接")
    async def get_work(self, interaction: discord.Interaction):
        """获取作品命令"""
        await interaction.response.defer(ephemeral=True)

        # 获取当前频道
        channel = interaction.channel

        # 查找 WarehouseID
        warehouse_id = await self.find_warehouse_id_in_thread(channel)

        if warehouse_id is None:
            await interaction.followup.send(
                embed=build_error_embed("当前帖子中未找到已发布的作品"),
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
            # 读取仓库消息
            warehouse_message = await warehouse_channel.fetch_message(warehouse_id)

            # 解析元数据
            metadata = parse_metadata(warehouse_message.content)
            if metadata is None:
                await interaction.followup.send(
                    embed=build_error_embed("资源元数据解析失败"),
                    ephemeral=True,
                )
                return

            # 获取附件 URL
            if not warehouse_message.attachments:
                await interaction.followup.send(
                    embed=build_error_embed("资源文件不存在"),
                    ephemeral=True,
                )
                return

            attachment_url = warehouse_message.attachments[0].url
            attachments = warehouse_message.attachments  # 所有附件

            # 构建多文件下载 Embed 的辅助函数
            def build_multi_file_embed(title: str, attachments: list) -> discord.Embed:
                if len(attachments) == 1:
                    return build_download_embed(title, attachments[0].url)
                else:
                    links = "\n".join([f"📎 [{att.filename}]({att.url})" for att in attachments])
                    embed = discord.Embed(
                        title="📥 下载就绪",
                        description=f"**{title}**\n\n{links}\n\n⏰ 链接有效期约 24 小时",
                        color=0x3BA55C,
                    )
                    embed.set_footer(text="请遵守版权规则")
                    return embed

            # 根据下载要求进行鉴权
            dl_req_type = metadata.req.get("type", "自由下载")

            if dl_req_type == "自由下载":
                # 直接发送下载链接
                embed = build_multi_file_embed(metadata.title, attachments)
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif dl_req_type == "互动":
                # 检查用户是否有互动
                if isinstance(channel, discord.Thread):
                    has_interaction = await self.check_user_interaction(
                        interaction.user, channel
                    )
                    if has_interaction:
                        embed = build_multi_file_embed(metadata.title, attachments)
                        await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await interaction.followup.send(
                            embed=build_error_embed(
                                "需要先对帖子进行回应（Reaction）或回复才能下载"
                            ),
                            ephemeral=True,
                        )
                else:
                    await interaction.followup.send(
                        embed=build_error_embed("此命令只能在帖子（Thread）中使用"),
                        ephemeral=True,
                    )

            elif dl_req_type == "提取码":
                # 弹出提取码验证 Modal
                expected_code = metadata.req.get("code", "")
                # 多文件时，传递所有附件 URL
                all_urls = "\n".join([att.url for att in attachments])
                await interaction.followup.send(
                    content="请点击下方按钮输入提取码：",
                    view=PasscodeButtonView(
                        expected_code=expected_code,
                        attachment_url=all_urls,
                        title=metadata.title,
                    ),
                    ephemeral=True,
                )

        except discord.NotFound:
            await interaction.followup.send(
                embed=build_error_embed("资源已被删除或不存在"),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                embed=build_error_embed(f"获取失败: {str(e)}"),
                ephemeral=True,
            )


class PasscodeButtonView(discord.ui.View):
    """提取码按钮视图"""

    def __init__(self, expected_code: str, attachment_url: str, title: str):
        super().__init__(timeout=300)  # 5分钟超时
        self.expected_code = expected_code
        self.attachment_url = attachment_url
        self.resource_title = title

    @discord.ui.button(label="输入提取码", emoji="🔐", style=discord.ButtonStyle.primary)
    async def enter_passcode(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        """点击按钮弹出提取码 Modal"""
        modal = PasscodeModal(
            expected_code=self.expected_code,
            attachment_url=self.attachment_url,
            title=self.resource_title,
        )
        await interaction.response.send_modal(modal)

async def handle_download_button(interaction: discord.Interaction, warehouse_id: int):
    """
    处理下载按钮点击
    由 bot.py 的 on_interaction 调用
    """
    bot = interaction.client
    channel = interaction.channel

    # 获取仓库频道
    warehouse_channel = bot.warehouse_channel
    if warehouse_channel is None:
        await interaction.response.send_message(
            embed=build_error_embed("仓库频道配置错误，请联系管理员"),
            ephemeral=True,
        )
        return

    try:
        # 读取仓库消息
        warehouse_message = await warehouse_channel.fetch_message(warehouse_id)

        # 解析元数据
        metadata = parse_metadata(warehouse_message.content)
        if metadata is None:
            await interaction.response.send_message(
                embed=build_error_embed("资源元数据解析失败"),
                ephemeral=True,
            )
            return

        # 获取附件 URL
        if not warehouse_message.attachments:
            await interaction.response.send_message(
                embed=build_error_embed("资源文件不存在"),
                ephemeral=True,
            )
            return

        # 多文件支持：构建所有附件的下载信息
        attachments = warehouse_message.attachments

        # 根据下载要求进行鉴权
        dl_req_type = metadata.req.get("type", "自由下载")

        if dl_req_type == "自由下载":
            # 直接发送下载链接
            if len(attachments) == 1:
                embed = build_download_embed(metadata.title, attachments[0].url)
            else:
                # 多文件
                links = "\n".join([f"📎 [{att.filename}]({att.url})" for att in attachments])
                embed = discord.Embed(
                    title="📥 下载就绪",
                    description=f"**{metadata.title}**\n\n{links}\n\n⏰ 链接有效期约 24 小时",
                    color=0x3BA55C,
                )
                embed.set_footer(text="请遵守版权规则")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif dl_req_type == "互动":
            # 检查用户是否有互动（Reaction 或回复）
            if isinstance(channel, discord.Thread):
                has_interaction = await self.check_user_interaction(
                    interaction.user, channel
                )

                if has_interaction:
                    if len(attachments) == 1:
                        embed = build_download_embed(metadata.title, attachments[0].url)
                    else:
                        links = "\n".join([f"📎 [{att.filename}]({att.url})" for att in attachments])
                        embed = discord.Embed(
                            title="📥 下载就绪",
                            description=f"**{metadata.title}**\n\n{links}\n\n⏰ 链接有效期约 24 小时",
                            color=0x3BA55C,
                        )
                        embed.set_footer(text="请遵守版权规则")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.response.send_message(
                        embed=build_error_embed("需要先对帖子【首楼】进行回应（Reaction）或回复才能下载"),
                        ephemeral=True,
                    )
            else:
                await interaction.response.send_message(
                    embed=build_error_embed("此功能只能在帖子中使用"),
                    ephemeral=True,
                )

        elif dl_req_type == "提取码":
            # 弹出提取码验证 Modal
            expected_code = metadata.req.get("code", "")
            # 多文件时，使用第一个附件的 URL（或者可以在 Modal 中处理）
            modal = PasscodeModal(
                expected_code=expected_code,
                attachment_url=attachments[0].url,
                title=metadata.title,
            )
            await interaction.response.send_modal(modal)

    except discord.NotFound:
        await interaction.response.send_message(
            embed=build_error_embed("资源已被删除或不存在"),
            ephemeral=True,
        )
    except Exception as e:
        await interaction.response.send_message(
            embed=build_error_embed(f"获取失败: {str(e)}"),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    """加载 Cog"""
    await bot.add_cog(DownloadCog(bot))
