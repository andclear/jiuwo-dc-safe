"""
Embed 构建器
用于创建 Discord Embed 消息
"""

import discord
from utils.metadata import ResourceMetadata


# 规则图标映射
RULE_ICONS = {
    True: "✅",
    False: "❌",
}

# 下载要求文案映射
DL_REQ_TEXT = {
    "自由下载": "🆓 自由下载",
    "互动": "💬 需先对帖子回应或回复",
    "提取码": "🔐 需要提取码",
}


def get_rule_icon(allowed: bool) -> str:
    """
    获取规则图标

    Args:
        allowed: 是否允许

    Returns:
        对应的 emoji 图标
    """
    return RULE_ICONS.get(allowed, "❓")


def get_dl_req_text(dl_req_type: str) -> str:
    """
    获取下载要求文案

    Args:
        dl_req_type: 下载要求类型

    Returns:
        对应的文案
    """
    return DL_REQ_TEXT.get(dl_req_type, dl_req_type)


def build_publish_embed(
    metadata: ResourceMetadata,
    warehouse_message_id: int,
) -> discord.Embed:
    """
    构建发布作品的 Embed

    Args:
        metadata: 资源元数据
        warehouse_message_id: 仓库消息 ID

    Returns:
        discord.Embed 实例
    """
    # 构建描述内容
    repost_icon = get_rule_icon(metadata.rules.get("repost", False))
    modify_icon = get_rule_icon(metadata.rules.get("modify", False))
    dl_req_text = get_dl_req_text(metadata.req.get("type", "自由下载"))

    description = (
        f"**版权要求：** 二传 {repost_icon} | 二改 {modify_icon} | 商业化 ❌\n"
        f"**下载要求：** {dl_req_text}\n\n"
        f"⚠️ **使用说明：** 请滑到页面最底部，输入 `/获取作品` 来获取最新下载链接。"
    )

    embed = discord.Embed(
        title=metadata.title,
        description=description,
        color=discord.Color.blue(),
    )

    # 设置 Footer（作为索引凭证）
    embed.set_footer(text=f"WarehouseID: {warehouse_message_id}")

    return embed


def build_download_embed(
    title: str,
    attachment_url: str,
) -> discord.Embed:
    """
    构建下载链接的 Embed（私密消息）

    Args:
        title: 作品标题
        attachment_url: 附件 URL

    Returns:
        discord.Embed 实例
    """
    embed = discord.Embed(
        title=f"📥 {title}",
        description=f"点击下方链接下载：\n{attachment_url}",
        color=discord.Color.green(),
    )
    return embed


def build_error_embed(message: str) -> discord.Embed:
    """
    构建错误提示 Embed

    Args:
        message: 错误信息

    Returns:
        discord.Embed 实例
    """
    return discord.Embed(
        title="❌ 错误",
        description=message,
        color=discord.Color.red(),
    )


def build_success_embed(message: str) -> discord.Embed:
    """
    构建成功提示 Embed

    Args:
        message: 成功信息

    Returns:
        discord.Embed 实例
    """
    return discord.Embed(
        title="✅ 成功",
        description=message,
        color=discord.Color.green(),
    )
