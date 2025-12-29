#!/usr/bin/env python3
"""
Discord Bot 命令清除工具
用于清除所有已注册的斜杠命令

使用方法：
  本地运行: python scripts/clear_commands.py
  Docker 运行: docker-compose run --rm discord-bot python scripts/clear_commands.py
"""

import discord
import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ 错误: BOT_TOKEN 未配置")
    print("请确保 .env 文件存在并包含 BOT_TOKEN")
    sys.exit(1)


async def clear_commands():
    """清除所有斜杠命令"""
    intents = discord.Intents.default()
    bot = discord.Client(intents=intents)
    tree = discord.app_commands.CommandTree(bot)

    @bot.event
    async def on_ready():
        print(f"🤖 已登录为: {bot.user}")
        print(f"📋 Bot ID: {bot.user.id}")
        print()

        try:
            # 清除全局命令
            print("🔄 正在清除全局命令...")
            tree.clear_commands(guild=None)
            await tree.sync()
            print("✅ 全局命令已清除")

            # 清除所有服务器的 Guild 命令
            for guild in bot.guilds:
                print(f"🔄 正在清除服务器 [{guild.name}] 的命令...")
                tree.clear_commands(guild=guild)
                await tree.sync(guild=guild)
                print(f"✅ 服务器 [{guild.name}] 的命令已清除")

            print()
            print("=" * 50)
            print("✅ 所有命令已成功清除！")
            print()
            print("ℹ️  Discord 命令缓存可能需要几分钟才能更新")
            print("ℹ️  请等待 1-2 分钟后重新部署 Bot")
            print("=" * 50)

        except Exception as e:
            print(f"❌ 清除命令失败: {e}")

        await bot.close()

    print("=" * 50)
    print("  Discord Bot 命令清除工具")
    print("=" * 50)
    print()

    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(clear_commands())
