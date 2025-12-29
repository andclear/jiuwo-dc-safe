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
    "自由下载": {"emoji": "🆓", "text": "自由下载", "desc": "可直接获取"},
    "互动": {"emoji": "💬", "text": "互动", "desc": "需先对帖子首楼点赞(反应)或在帖内回复"},
    "提取码": {"emoji": "🔐", "text": "提取码", "desc": "寻找作者在帖内贴出的的提取码"},
}


def get_rule_icon(allowed: bool) -> str:
    """获取规则 emoji 图标"""
    return "✅" if allowed else "❌"


def get_dl_req_style(dl_req_type: str) -> dict:
    """获取下载要求样式"""
    return DL_REQ_STYLES.get(dl_req_type, {"emoji": "❓", "text": dl_req_type, "desc": ""})


def build_publish_embed(
    metadata: ResourceMetadata,
    warehouse_message_id: int,
) -> discord.Embed:
    """
    构建发布作品的 Embed（参考截图风格）
    """
    # 默认：禁止二传、允许二改
    repost_icon = get_rule_icon(metadata.rules.get("repost", False))
    modify_icon = get_rule_icon(metadata.rules.get("modify", True))
    dl_style = get_dl_req_style(metadata.req.get("type", "自由下载"))

    # 构建描述内容（使用列表和缩进格式）
    description = (
        "请在此处交互获取本帖作品\n"
        "或者直接发送 **/获取作品** 来使用命令获取\n\n"
        
        f"• **版权规则**\n"
        f"> 　二传 {repost_icon}　　二改 {modify_icon}　　商用 ❌\n\n"
        
        f"• **下载门槛: {dl_style['text']}**\n"
        f"> 　{dl_style['desc']}\n\n"
        
        "**Tips:**\n"
        "> 如果出现了点击按钮后没有作品消息\n"
        "> 可以滑到最下面后输入 **/获取作品** 来使用命令获取\n\n"
        
        "**作者专属交互**"
    )

    embed = discord.Embed(
        title=f"📦 {metadata.title}",
        description=description,
        color=Colors.PRIMARY,
    )

    # 设置 Footer（使用引用样式）
    embed.set_footer(text=f"作品ID: {warehouse_message_id}")

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
