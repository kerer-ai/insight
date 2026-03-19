# -*- coding: utf-8 -*-
"""
GitCode Insight 命令行入口
"""

import argparse
import os

from .community import GitCodeCommunityStats
from .issue import GitCodeIssueInsight
from .dashboard import generate_dashboard


def cmd_community(args):
    """社区洞察命令"""
    config_file = args.config
    output_dir = args.output

    # 创建统计实例
    stats_crawler = GitCodeCommunityStats(config_file=config_file, output_dir=output_dir)

    # 爬取社区的统计数据
    stats = stats_crawler.crawl_community_stats()

    # 生成报告
    stats_crawler.generate_report(stats)

    # 保存到CSV
    stats_crawler.save_to_csv(stats)

    # 保存详细数据到JSON
    stats_crawler.save_to_json(stats)

    print("\n\n数据爬取和分析完成！")
    print("- 详细报告已打印到控制台")


def cmd_issue(args):
    """Issue 洞察命令"""
    insight = GitCodeIssueInsight(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        days=args.days,
        output_dir=args.output
    )

    insight.run()


def cmd_dashboard(args):
    """生成看板命令"""
    generate_dashboard(config_file=args.config, output_dir=args.output)


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        prog="gc-insight",
        description="GitCode 平台代码洞察工具"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # community 子命令
    community_parser = subparsers.add_parser("community", help="社区洞察")
    community_parser.add_argument("--config", default=None, help="配置文件路径，默认使用 ./config/gitcode.json")
    community_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    community_parser.set_defaults(func=cmd_community)

    # issue 子命令
    issue_parser = subparsers.add_parser("issue", help="Issue 洞察")
    issue_parser.add_argument("--repo", required=True, help="仓库名称（path）")
    issue_parser.add_argument("--token", required=True, help="API 访问令牌")
    issue_parser.add_argument("--days", type=int, default=30, help="统计天数，默认 30")
    issue_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
    issue_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    issue_parser.set_defaults(func=cmd_issue)

    # dashboard 子命令
    dashboard_parser = subparsers.add_parser("dashboard", help="生成看板")
    dashboard_parser.add_argument("--config", default=None, help="配置文件路径，默认使用 ./config/gitcode.json")
    dashboard_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()