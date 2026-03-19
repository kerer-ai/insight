# -*- coding: utf-8 -*-
"""
GitCode Insight 命令行入口
"""

import argparse
import os
import json

from .community import GitCodeCommunityStats
from .issue import GitCodeIssueInsight
from .pr import GitCodePRInsight
from .dashboard import generate_dashboard
from .repo_stats import GitCodeRepoStats
from .subscribers import GitCodeSubscribers
from .languages import GitCodeLanguages


def get_config_owner(config_file):
    """从配置文件获取 owner"""
    if config_file is None:
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")

    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get("owner", "")
    return ""


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


def cmd_pr(args):
    """PR 洞察命令"""
    insight = GitCodePRInsight(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        days=args.days,
        output_dir=args.output
    )

    insight.run()


def cmd_repo_stats(args):
    """仓库统计命令"""
    stats = GitCodeRepoStats(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        days=args.days,
        output_dir=args.output
    )

    stats.run()


def cmd_subscribers(args):
    """订阅用户命令"""
    subscribers = GitCodeSubscribers(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        days=args.days,
        output_dir=args.output
    )

    subscribers.run()


def cmd_languages(args):
    """编程语言统计命令"""
    languages = GitCodeLanguages(
        repo=args.repo,
        token=args.token,
        owner=args.owner,
        output_dir=args.output
    )

    languages.run()


def cmd_dashboard(args):
    """生成看板命令（自动检测数据是否存在，不存在则先采集）"""
    config_file = args.config
    output_dir = args.output

    # 设置默认路径
    if config_file is None:
        config_file = os.path.join(os.getcwd(), "config", "gitcode.json")
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "output")

    # 获取 owner
    owner = get_config_owner(config_file)
    if not owner:
        print("错误: 无法从配置文件获取 owner")
        return

    # 检测数据文件是否存在
    json_file = os.path.join(output_dir, f"{owner}_community_stats_detailed.json")

    if not os.path.exists(json_file):
        print(f"数据文件不存在: {json_file}")
        print("开始自动采集数据...\n")

        # 自动运行采集
        stats_crawler = GitCodeCommunityStats(config_file=config_file, output_dir=output_dir)
        stats = stats_crawler.crawl_community_stats()
        stats_crawler.generate_report(stats)
        stats_crawler.save_to_csv(stats)
        stats_crawler.save_to_json(stats)

        print("\n数据采集完成！\n")

    # 生成看板
    generate_dashboard(config_file=config_file, output_dir=output_dir)


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

    # pr 子命令
    pr_parser = subparsers.add_parser("pr", help="PR 洞察")
    pr_parser.add_argument("--repo", required=True, help="仓库名称（path）")
    pr_parser.add_argument("--token", required=True, help="API 访问令牌")
    pr_parser.add_argument("--days", type=int, default=30, help="统计天数，默认 30")
    pr_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
    pr_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    pr_parser.set_defaults(func=cmd_pr)

    # repo-stats 子命令
    repo_stats_parser = subparsers.add_parser("repo-stats", help="仓库统计")
    repo_stats_parser.add_argument("--repo", required=True, help="仓库名称（path）")
    repo_stats_parser.add_argument("--token", required=True, help="API 访问令牌")
    repo_stats_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
    repo_stats_parser.add_argument("--days", type=int, default=30, help="统计天数，默认 30")
    repo_stats_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    repo_stats_parser.set_defaults(func=cmd_repo_stats)

    # subscribers 子命令
    subscribers_parser = subparsers.add_parser("subscribers", help="订阅用户统计")
    subscribers_parser.add_argument("--repo", required=True, help="仓库名称（path）")
    subscribers_parser.add_argument("--token", required=True, help="API 访问令牌")
    subscribers_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
    subscribers_parser.add_argument("--days", type=int, default=30, help="统计天数，默认 30")
    subscribers_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    subscribers_parser.set_defaults(func=cmd_subscribers)

    # languages 子命令
    languages_parser = subparsers.add_parser("languages", help="编程语言统计")
    languages_parser.add_argument("--repo", required=True, help="仓库名称（path）")
    languages_parser.add_argument("--token", required=True, help="API 访问令牌")
    languages_parser.add_argument("--owner", default=None, help="组织名，默认从配置文件读取")
    languages_parser.add_argument("--output", default=None, help="输出目录，默认使用 ./output/")
    languages_parser.set_defaults(func=cmd_languages)

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