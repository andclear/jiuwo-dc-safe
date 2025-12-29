"""
元数据处理工具
用于创建、解析和验证资源元数据
"""

import json
from typing import Any
from dataclasses import dataclass, asdict


@dataclass
class ResourceMetadata:
    """资源元数据结构"""

    uploader: int  # 上传者用户 ID
    title: str  # 作品标题
    rules: dict[str, bool]  # 规则：{"repost": bool, "modify": bool}
    req: dict[str, Any]  # 下载要求：{"type": str, "code": str | None}

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "ResourceMetadata":
        """从 JSON 字符串反序列化"""
        data = json.loads(json_str)
        return cls(**data)


def create_metadata(
    uploader_id: int,
    title: str,
    rule_repost: bool,
    rule_modify: bool,
    dl_req_type: str,
    passcode: str | None = None,
) -> ResourceMetadata:
    """
    创建资源元数据

    Args:
        uploader_id: 上传者用户 ID
        title: 作品标题
        rule_repost: 是否允许二传
        rule_modify: 是否允许二改
        dl_req_type: 下载要求类型 ("自由下载" | "互动" | "提取码")
        passcode: 提取码（仅当 dl_req_type 为 "提取码" 时需要）

    Returns:
        ResourceMetadata 实例
    """
    return ResourceMetadata(
        uploader=uploader_id,
        title=title,
        rules={"repost": rule_repost, "modify": rule_modify},
        req={"type": dl_req_type, "code": passcode},
    )


def parse_metadata(json_str: str) -> ResourceMetadata | None:
    """
    解析元数据 JSON 字符串

    Args:
        json_str: JSON 字符串

    Returns:
        ResourceMetadata 实例，解析失败返回 None
    """
    try:
        return ResourceMetadata.from_json(json_str)
    except (json.JSONDecodeError, TypeError, KeyError):
        return None


def validate_metadata(metadata: ResourceMetadata) -> tuple[bool, str]:
    """
    验证元数据格式

    Args:
        metadata: ResourceMetadata 实例

    Returns:
        (是否有效, 错误信息)
    """
    if not metadata.title:
        return False, "标题不能为空"

    if metadata.req["type"] not in ["自由下载", "互动", "提取码"]:
        return False, "无效的下载要求类型"

    if metadata.req["type"] == "提取码" and not metadata.req.get("code"):
        return False, "提取码模式需要设置提取码"

    return True, ""
