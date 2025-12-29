"""
模块 C：管理功能
实现删除、更新和标注功能
"""

import discord
from discord.ext import commands

from utils.metadata import create_metadata, parse_metadata
from utils.embed_builder import (
    build_publish_embed,
    build_error_embed,
    build_success_embed,
)


class UpdateWorkModal(discord.ui.Modal, title="更新作品信息"):
    """更新作品信息弹窗"""

    title_input = discord.ui.TextInput(
        label="标题",
        placeholder="输入新标题",
        required=True,
        max_length=100,
    )

    rule_repost_input = discord.ui.TextInput(
        label="允许二传 (输入 是 或 否)",
        placeholder="是",
        required=True,
        max_length=2,
    )

    rule_modify_input = discord.ui.TextInput(
        label="允许二改 (输入 是 或 否)",
        placeholder="是",
        required=True,
        max_length=2,
    )

    dl_req_input = discord.ui.TextInput(
        label="下载要求 (自由下载/互动/提取码)",
        placeholder="自由下载",
        required=True,
        max_length=10,
    )

    passcode_input = discord.ui.TextInput(
        label="提取码 (仅提取码模式需要)",
        placeholder="留空表示不修改",
        required=False,
        max_length=50,
    )

    def __init__(self, warehouse_message_id: int, bot: commands.Bot, original_message: discord.Message):
        super().__init__()
        self.warehouse_message_id = warehouse_message_id
        self.bot = bot
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        """提交更新"""
        await interaction.response.defer(ephemeral=True)

        # 解析输入
        new_title = self.title_input.value
        rule_repost = self.rule_repost_input.value.strip() in ["是", "yes", "true", "1"]
        rule_modify = self.rule_modify_input.value.strip() in ["是", "yes", "true", "1"]
        dl_req = self.dl_req_input.value.strip()
        passcode = self.passcode_input.value.strip() or None

        # 验证下载要求
        valid_dl_reqs = ["自由下载", "互动", "提取码"]
        if dl_req not in valid_dl_reqs:
            await interaction.followup.send(
                embed=build_error_embed(f"无效的下载要求，有效值: {', '.join(valid_dl_reqs)}"),
                ephemeral=True,
            )
            return

        # 验证提取码
        if dl_req == "提取码" and not passcode:
            await interaction.followup.send(
                embed=build_error_embed("提取码模式需要填写提取码"),
                ephemeral=True,
            )
            return

        try:
            # 获取仓库频道
            warehouse_channel = self.bot.warehouse_channel
            if warehouse_channel is None:
                await interaction.followup.send(
                    embed=build_error_embed("仓库频道配置错误"),
                    ephemeral=True,
                )
                return

            # 获取旧的仓库消息
            old_warehouse_message = await warehouse_channel.fetch_message(
                self.warehouse_message_id
            )

            # 下载旧附件到内存
            if not old_warehouse_message.attachments:
                await interaction.followup.send(
                    embed=build_error_embed("原资源文件不存在"),
                    ephemeral=True,
                )
                return

            file_data = await old_warehouse_message.attachments[0].to_file()

            # 构造新的元数据
            new_metadata = create_metadata(
                uploader_id=interaction.user.id,
                title=new_title,
                rule_repost=rule_repost,
                rule_modify=rule_modify,
                dl_req_type=dl_req,
                passcode=passcode,
            )

            # 删除旧的仓库消息
            await old_warehouse_message.delete()

            # 发送新的仓库消息
            new_warehouse_message = await warehouse_channel.send(
                content=new_metadata.to_json(),
                file=file_data,
            )

            # 更新公开 Embed
            new_embed = build_publish_embed(
                metadata=new_metadata,
                warehouse_message_id=new_warehouse_message.id,
            )

            # 创建新的管理按钮视图
            from cogs.publish import PersistentManageView

            new_view = PersistentManageView(
                warehouse_message_id=new_warehouse_message.id,
                uploader_id=interaction.user.id,
            )

            # 编辑原公开消息
            await self.original_message.edit(embed=new_embed, view=new_view)

            await interaction.followup.send(
                embed=build_success_embed("作品信息已更新"),
                ephemeral=True,
            )

        except Exception as e:
            await interaction.followup.send(
                embed=build_error_embed(f"更新失败: {str(e)}"),
                ephemeral=True,
            )


async def handle_delete_work(
    interaction: discord.Interaction, warehouse_message_id: int
):
    """处理删除作品"""
    await interaction.response.defer(ephemeral=True)

    try:
        # 获取仓库频道
        warehouse_channel = interaction.client.warehouse_channel
        if warehouse_channel is None:
            await interaction.followup.send(
                embed=build_error_embed("仓库频道配置错误"),
                ephemeral=True,
            )
            return

        # 删除仓库消息
        try:
            warehouse_message = await warehouse_channel.fetch_message(warehouse_message_id)
            await warehouse_message.delete()
        except discord.NotFound:
            pass  # 仓库消息可能已被删除

        # 删除公开 Embed 消息
        await interaction.message.delete()

        await interaction.followup.send(
            embed=build_success_embed("作品已删除"),
            ephemeral=True,
        )

    except Exception as e:
        await interaction.followup.send(
            embed=build_error_embed(f"删除失败: {str(e)}"),
            ephemeral=True,
        )


async def handle_toggle_pin(interaction: discord.Interaction):
    """处理标注/取消标注"""
    await interaction.response.defer(ephemeral=True)

    try:
        message = interaction.message

        if message.pinned:
            await message.unpin()
            await interaction.followup.send(
                embed=build_success_embed("已取消标注"),
                ephemeral=True,
            )
        else:
            await message.pin()
            await interaction.followup.send(
                embed=build_success_embed("已标注消息"),
                ephemeral=True,
            )

    except discord.Forbidden:
        await interaction.followup.send(
            embed=build_error_embed("Bot 没有标注消息的权限"),
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            embed=build_error_embed(f"操作失败: {str(e)}"),
            ephemeral=True,
        )


async def handle_update_work(
    interaction: discord.Interaction, warehouse_message_id: int
):
    """处理更新作品"""
    modal = UpdateWorkModal(
        warehouse_message_id=warehouse_message_id,
        bot=interaction.client,
        original_message=interaction.message,
    )
    await interaction.response.send_modal(modal)


class ManageCog(commands.Cog):
    """管理功能模块"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def find_user_embed_in_thread(
        self, channel: discord.TextChannel | discord.Thread, user_id: int
    ) -> tuple[discord.Message, int] | None:
        """
        在当前 Thread 中查找用户发布的作品 Embed

        Returns:
            (消息对象, warehouse_id) 或 None
        """
        async for message in channel.history(limit=100):
            # 检查是否是 Bot 发送的消息
            if message.author.id != self.bot.user.id:
                continue

            # 检查是否有 Embed
            if not message.embeds:
                continue

            embed = message.embeds[0]

            # 检查 footer 是否包含作品ID
            if not embed.footer or not embed.footer.text:
                continue

            footer_text = embed.footer.text
            
            # 支持多种 footer 格式
            warehouse_id = None
            if footer_text.startswith("WarehouseID:"):
                try:
                    warehouse_id = int(footer_text.replace("WarehouseID:", "").strip())
                except ValueError:
                    continue
            elif footer_text.startswith("作品ID:") or footer_text.startswith("ID:"):
                try:
                    warehouse_id = int(footer_text.split(":")[-1].strip())
                except ValueError:
                    continue
            else:
                continue
            
            if warehouse_id is None:
                continue

            # 获取仓库消息验证上传者
            try:
                warehouse_channel = self.bot.warehouse_channel
                if warehouse_channel is None:
                    continue

                warehouse_message = await warehouse_channel.fetch_message(warehouse_id)
                metadata = parse_metadata(warehouse_message.content)

                if metadata and metadata.uploader == user_id:
                    return (message, warehouse_id)
            except Exception:
                continue

        return None

    @discord.app_commands.command(name="更新作品", description="更新当前帖子中你发布的作品文件")
    @discord.app_commands.describe(
        file1="新文件 1（必填）",
        file2="新文件 2（选填）",
        file3="新文件 3（选填）",
        file4="新文件 4（选填）",
        file5="新文件 5（选填）",
    )
    async def update_work_command(
        self,
        interaction: discord.Interaction,
        file1: discord.Attachment,
        file2: discord.Attachment = None,
        file3: discord.Attachment = None,
        file4: discord.Attachment = None,
        file5: discord.Attachment = None,
    ):
        """更新作品命令"""
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel

        # 收集所有文件
        files = [f for f in [file1, file2, file3, file4, file5] if f is not None]

        # 查找用户在当前帖子发布的作品
        result = await self.find_user_embed_in_thread(channel, interaction.user.id)

        if result is None:
            await interaction.followup.send(
                embed=build_error_embed("在当前帖子中未找到你发布的作品"),
                ephemeral=True,
            )
            return

        original_message, old_warehouse_id = result

        try:
            # 获取仓库频道
            warehouse_channel = self.bot.warehouse_channel
            if warehouse_channel is None:
                await interaction.followup.send(
                    embed=build_error_embed("仓库频道配置错误"),
                    ephemeral=True,
                )
                return

            # 获取旧的仓库消息和元数据
            old_warehouse_message = await warehouse_channel.fetch_message(old_warehouse_id)
            old_metadata = parse_metadata(old_warehouse_message.content)

            if old_metadata is None:
                await interaction.followup.send(
                    embed=build_error_embed("原作品元数据解析失败"),
                    ephemeral=True,
                )
                return

            # 下载新文件到内存
            files_data = []
            for f in files:
                file_data = await f.to_file()
                files_data.append(file_data)

            # 构造新的元数据（保留原有设置）
            new_metadata = create_metadata(
                uploader_id=interaction.user.id,
                title=old_metadata.title,
                rule_repost=old_metadata.rules.get("repost", False),
                rule_modify=old_metadata.rules.get("modify", True),
                dl_req_type=old_metadata.req.get("type", "自由下载"),
                passcode=old_metadata.req.get("code"),
            )

            # 删除旧的仓库消息
            await old_warehouse_message.delete()

            # 发送新的仓库消息（包含新文件）
            new_warehouse_message = await warehouse_channel.send(
                content=new_metadata.to_json(),
                files=files_data,
            )

            # 更新公开 Embed
            new_embed = build_publish_embed(
                metadata=new_metadata,
                warehouse_message_id=new_warehouse_message.id,
            )

            # 添加文件数量信息
            if len(files) > 1:
                new_embed.add_field(name="📎 文件数量", value=f"{len(files)} 个", inline=True)

            # 创建新的管理按钮视图
            from cogs.publish import PersistentManageView

            new_view = PersistentManageView(
                warehouse_message_id=new_warehouse_message.id,
                uploader_id=interaction.user.id,
            )

            # 编辑原公开消息
            await original_message.edit(embed=new_embed, view=new_view)

            await interaction.followup.send(
                embed=build_success_embed(f"作品文件已更新（共 {len(files)} 个文件）"),
                ephemeral=True,
            )

        except Exception as e:
            await interaction.followup.send(
                embed=build_error_embed(f"更新失败: {str(e)}"),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    """加载 Cog"""
    await bot.add_cog(ManageCog(bot))
