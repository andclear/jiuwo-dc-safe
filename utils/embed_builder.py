"""
Embed 构建器
用于创建美观的 Discord Embed 消息
"""

import discord
from utils.metadata import ResourceMetadata


# 主题颜色
class Colors:
    """主题颜色定义"""
    PRIMARY = 0x5865F2      # Discord Blurple 蓝紫色
    SUCCESS = 0x57F287      # 绿色
    WARNING = 0xFEE75C      # 黄色
    ERROR = 0xED4245        # 红色
    INFO = 0x5865F2         # 蓝紫色
    DOWNLOAD = 0x3BA55C     # 深绿色


# 下载要求样式映射
DL_REQ_STYLES = {
    "自由下载": {"emoji": "🆓", "text": "自由下载", "color": Colors.SUCCESS},
    "互动": {"emoji": "💬", "text": "需先回应或回复帖子", "color": Colors.WARNING},
    "提取码": {"emoji": "🔐", "text": "需要提取码", "color": Colors.INFO},
}


def get_rule_text(allowed: bool) -> str:
    """获取规则文本"""
    return "允许" if allowed else "禁止"


def get_dl_req_style(dl_req_type: str) -> dict:
    """获取下载要求样式"""
    return DL_REQ_STYLES.get(dl_req_type, {"emoji": "❓", "text": dl_req_type, "color": Colors.PRIMARY})


def build_publish_embed(
    metadata: ResourceMetadata,
    warehouse_message_id: int,
) -> discord.Embed:
    """
    构建发布作品的 Embed（简洁版）
    """
    repost = get_rule_text(metadata.rules.get("repost", False))
    modify = get_rule_text(metadata.rules.get("modify", False))
    dl_style = get_dl_req_style(metadata.req.get("type", "自由下载"))

    # 使用根据下载要求类型的颜色
    embed = discord.Embed(
        title=f"📦 {metadata.title}",
        color=dl_style["color"],
    )

    # 版权规则 - 简洁的行内格式
    embed.add_field(
        name="📜 版权规则",
        value=f"二传 `{repost}` ・ 二改 `{modify}` ・ 商用 `禁止`",
        inline=False,
    )

    # 下载门槛
    embed.add_field(
        name="� 下载门槛",
        value=f"{dl_style['emoji']} {dl_style['text']}",
        inline=False,
    )

    # 使用说明
    embed.add_field(
        name="💡 如何下载",
        value="点击下方 **「下载作品」** 按钮获取链接",
        inline=False,
    )

    # 设置 Footer
    embed.set_footer(text=f"ID: {warehouse_message_id}")

    return embed


def build_download_embed(
    title: str,
    attachment_url: str,
) -> discord.Embed:
    """
    构建下载链接的 Embed
    """
    embed = discord.Embed(
        title="📥 下载就绪",
        description=(
            f"**{title}**\n\n"
            f"🔗 [点击下载]({attachment_url})\n\n"
            f"⏰ 链接有效期约 24 小时"
        ),
        color=Colors.DOWNLOAD,
    )
    embed.set_footer(text="请遵守版权规则")
    return embed


def build_error_embed(message: str) -> discord.Embed:
    """
    构建错误提示 Embed
    """
    return discord.Embed(
        title="❌ 操作失败",
        description=message,
        color=Colors.ERROR,
    )


def build_success_embed(message: str) -> discord.Embed:
    """
    构建成功提示 Embed
    """
    return discord.Embed(
        title="✅ 操作成功",
        description=message,
        color=Colors.SUCCESS,
    )
