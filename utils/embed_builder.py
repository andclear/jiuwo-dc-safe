"""
Embed 构建器
用于创建美观的 Discord Embed 消息
"""

import discord
from datetime import datetime
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


# 规则图标映射
RULE_ICONS = {
    True: "✅",
    False: "❌",
}

# 下载要求样式映射
DL_REQ_STYLES = {
    "自由下载": {"emoji": "🆓", "text": "自由下载", "color": Colors.SUCCESS},
    "互动": {"emoji": "💬", "text": "需先回应或回复帖子", "color": Colors.WARNING},
    "提取码": {"emoji": "🔐", "text": "需要提取码", "color": Colors.INFO},
}


def get_rule_icon(allowed: bool) -> str:
    """获取规则图标"""
    return RULE_ICONS.get(allowed, "❓")


def get_dl_req_style(dl_req_type: str) -> dict:
    """获取下载要求样式"""
    return DL_REQ_STYLES.get(dl_req_type, {"emoji": "❓", "text": dl_req_type, "color": Colors.PRIMARY})


def build_publish_embed(
    metadata: ResourceMetadata,
    warehouse_message_id: int,
) -> discord.Embed:
    """
    构建发布作品的 Embed（美化版）
    """
    repost_icon = get_rule_icon(metadata.rules.get("repost", False))
    modify_icon = get_rule_icon(metadata.rules.get("modify", False))
    dl_style = get_dl_req_style(metadata.req.get("type", "自由下载"))

    # 使用根据下载要求类型的颜色
    embed = discord.Embed(
        title=f"📦 {metadata.title}",
        color=dl_style["color"],
    )

    # 版权规则区域
    rules_content = (
        f"```\n"
        f"二传  │ 二改  │ 商用\n"
        f" {repost_icon}   │  {modify_icon}   │  ❌\n"
        f"```"
    )
    embed.add_field(name="📜 版权规则", value=rules_content, inline=False)

    # 下载门槛区域
    dl_content = f"{dl_style['emoji']} **{dl_style['text']}**"
    embed.add_field(name="🔒 下载门槛", value=dl_content, inline=True)

    # 发布时间
    embed.add_field(
        name="🕐 发布时间",
        value=f"<t:{int(datetime.now().timestamp())}:R>",
        inline=True,
    )

    # 分隔线 + 使用说明
    embed.add_field(
        name="─" * 20,
        value=(
            "💡 **如何下载？**\n"
            "滑到页面底部，输入 `/获取作品` 获取下载链接"
        ),
        inline=False,
    )

    # 设置 Footer（作为索引凭证）
    embed.set_footer(
        text=f"资源 ID: {warehouse_message_id}",
        icon_url="https://cdn.discordapp.com/emojis/1234567890.png",  # 可替换为自定义图标
    )

    return embed


def build_download_embed(
    title: str,
    attachment_url: str,
) -> discord.Embed:
    """
    构建下载链接的 Embed（美化版）
    """
    embed = discord.Embed(
        title="📥 下载就绪",
        description=(
            f"**{title}**\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"� **下载链接**\n"
            f"[点击这里下载]({attachment_url})\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"⏰ 链接有效期约 **24 小时**"
        ),
        color=Colors.DOWNLOAD,
    )
    embed.set_footer(text="请遵守版权规则，尊重创作者劳动成果")
    return embed


def build_error_embed(message: str) -> discord.Embed:
    """
    构建错误提示 Embed（美化版）
    """
    embed = discord.Embed(
        title="❌ 操作失败",
        description=f"```\n{message}\n```",
        color=Colors.ERROR,
    )
    return embed


def build_success_embed(message: str) -> discord.Embed:
    """
    构建成功提示 Embed（美化版）
    """
    embed = discord.Embed(
        title="✅ 操作成功",
        description=message,
        color=Colors.SUCCESS,
    )
    return embed


def build_info_embed(title: str, message: str) -> discord.Embed:
    """
    构建信息提示 Embed
    """
    embed = discord.Embed(
        title=f"ℹ️ {title}",
        description=message,
        color=Colors.INFO,
    )
    return embed
