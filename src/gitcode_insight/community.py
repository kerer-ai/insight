# -*- coding: utf-8 -*-
"""
GitCode 社区数据爬取模块
从 GitCode API 获取社区项目的统计数据
"""

import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import csv
import os
import requests

from .utils import request_with_retry, load_config


class GitCodeCommunityStats:
    """GitCode 社区统计数据爬取器"""

    def __init__(self, config_file: str = None, output_dir: str = None):
        """
        初始化爬虫

        Args:
            config_file: 配置文件路径，默认使用 ./config/gitcode.json
            output_dir: 输出目录，默认使用 ./output/
        """
        # 设置默认配置文件路径
        if config_file is None:
            config_file = os.path.join(os.getcwd(), "config", "gitcode.json")

        # 设置输出目录
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")

        self.output_dir = output_dir

        # 读取并验证配置文件
        config = load_config(config_file)

        self.base_url = "https://api.gitcode.com/api/v5"
        self.access_token = config.get("access_token", "")
        self.label_ci_success = config.get("label_ci_success", "ci-pipeline-passed")
        self.label_ci_running = config.get("label_ci_running", "ci-pipeline-running")
        self.label_yellow_ci_running = config.get("label_yellow_ci_running", "SC-RUNNING")
        self.label_yellow_ci_success = config.get("label_yellow_ci_success", "SC-SUCC")
        self.owner = config.get("owner", "boostkit")
        self.repo_whitelist = self._normalize_repo_list(config.get("repo_whitelist"))
        self.repo_blacklist = self._normalize_repo_list(config.get("repo_blacklist"))

        self.session = requests.Session()

    @staticmethod
    def _normalize_repo_list(value) -> List[str]:
        if not isinstance(value, list):
            return []
        result = []
        for item in value:
            if not isinstance(item, str):
                continue
            s = item.strip()
            if s:
                result.append(s)
        return result

    def _apply_repo_filters(self, projects: List[Dict]) -> List[Dict]:
        if not projects:
            return []

        if self.repo_whitelist:
            whitelist = set(self.repo_whitelist)
            return [
                p for p in projects
                if p.get("path") in whitelist or p.get("name") in whitelist
            ]

        if self.repo_blacklist:
            blacklist = set(self.repo_blacklist)
            return [
                p for p in projects
                if p.get("path") not in blacklist and p.get("name") not in blacklist
            ]

        return projects

    def get_community_projects(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        """
        获取社区的项目列表
        """
        url = f"{self.base_url}/orgs/{self.owner}/repos"
        params = {
            "access_token": self.access_token,
            "page": page,
            "per_page": per_page
        }

        result = request_with_retry(self.session, url, params)
        return result if isinstance(result, list) else []

    def get_project_contributors(self, project_path: str) -> List[Dict]:
        """
        获取项目的贡献者列表
        """
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/contributors"
        params = {
            "access_token": self.access_token,
            "per_page": 100
        }

        result = request_with_retry(self.session, url, params)
        return result if isinstance(result, list) else []

    def get_project_contributor_year(self, project_path: str) -> List[Dict]:
        """
        查询从年初到年末的贡献者
        """
        current_year = datetime.now().year
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/contributors/statistic"
        params = {
            "access_token": self.access_token,
            "since": f"{current_year}-01-01",
            "until": f"{current_year}-12-31"
        }

        result = request_with_retry(self.session, url, params)
        return result if isinstance(result, list) else []

    def get_project_merge_requests(self, project_path: str, days: int = 30) -> List[Dict]:
        """
        获取指定项目的合并请求（PR）
        """
        # 计算时间范围
        tz = timezone(timedelta(hours=8))
        since_date = (datetime.now(tz) - timedelta(days=days)).isoformat()

        all_mrs = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            url = f"{self.base_url}/repos/{self.owner}/{project_path}/pulls"
            params = {
                "access_token": self.access_token,
                "since": since_date,
                "per_page": 100,
                "page": page
            }

            data = request_with_retry(self.session, url, params)
            if data is None or not isinstance(data, list):
                break

            if not data:
                break

            all_mrs.extend(data)

            if len(data) < 100:
                break

            page += 1
            time.sleep(0.6)

        return all_mrs

    def get_pr_events(self, project_path: str, pr_number: int) -> List[Dict]:
        """
        获取PR的操作日志
        """
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/pulls/{pr_number}/operate_logs"
        params = {
            "access_token": self.access_token,
            "per_page": 100
        }

        result = request_with_retry(self.session, url, params)
        return result if isinstance(result, list) else []

    def calculate_gatekeeper_duration(self, project_path: str, pr_number: int) -> Dict:
        """
        计算单个PR的门禁时长（分钟）
        """
        events = self.get_pr_events(project_path, pr_number)

        if not events:
            return None

        # 倒序排列操作日志
        sorted_events = sorted(events, key=lambda x: x.get('created_at', ''), reverse=True)

        # 检查CI标志
        yellow_ci_flag = False
        blue_ci_flag = False
        for event in events:
            if not yellow_ci_flag and (event.get('action', '') == 'enterprise_label' or event.get('action', '') == 'label') and f'add label {self.label_yellow_ci_success}' in event.get('content', ''):
                yellow_ci_flag = True
            if not blue_ci_flag and (event.get('action', '') == 'enterprise_label' or event.get('action', '') == 'label') and f'add label {self.label_ci_success}' in event.get('content', ''):
                blue_ci_flag = True
            if yellow_ci_flag and blue_ci_flag:
                break

        if not blue_ci_flag:
            return {"yellow_ci_flag": yellow_ci_flag, "blue_ci_flag": blue_ci_flag, "duration_minutes": 0}

        # 收集所有参与门禁标签操作的用户ID
        user_ids = set(
            event.get('user', {}).get('id', '')
            for event in sorted_events
            if (event.get('action', '') == 'enterprise_label' or event.get('action', '') == 'label')
            and (f'add label {self.label_ci_success}' in event.get('content', '')
                 or f'add label {self.label_ci_running}' in event.get('content', ''))
        )

        ci_passed_time = None
        ci_running_time = None

        # 针对每个用户ID，查找匹配的标签对
        for user_id in user_ids:
            user_passed_time = None
            user_running_time = None

            for event in sorted_events:
                action = event.get('action', '')
                content = event.get('content', '')
                current_user_id = event.get('user', {}).get('id', '')
                created_at = event.get('created_at', '')

                if current_user_id != user_id:
                    continue

                if user_passed_time and (action == 'enterprise_label' or action == 'label') and f'delete label {self.label_ci_success}' in content:
                    user_passed_time = None
                    continue

                if user_passed_time is None:
                    if (action == 'enterprise_label' or action == 'label') and f'add label {self.label_ci_success}' in content:
                        user_passed_time = datetime.fromisoformat(created_at)
                else:
                    if (action == 'enterprise_label' or action == 'label') and f'add label {self.label_ci_running}' in content:
                        user_running_time = datetime.fromisoformat(created_at)
                        if user_running_time < user_passed_time:
                            ci_passed_time = user_passed_time
                            ci_running_time = user_running_time
                            break

            if ci_passed_time and ci_running_time:
                break

        if ci_passed_time and ci_running_time:
            duration_seconds = (ci_passed_time - ci_running_time).total_seconds()
            duration_minutes = max(0, duration_seconds / 60)
            return {"yellow_ci_flag": yellow_ci_flag, "blue_ci_flag": blue_ci_flag, "duration_minutes": duration_minutes}
        else:
            return {"yellow_ci_flag": yellow_ci_flag, "blue_ci_flag": blue_ci_flag, "duration_minutes": 0}

    def analyze_project_stats(self, project_path: str) -> Dict:
        """
        分析单个项目的统计指标
        """
        print(f"[分析中] {project_path}")

        # 获取贡献者数量
        print(f"  获取贡献者数量...")
        contributors = self.get_project_contributors(project_path)
        contributor_count = len(contributors)
        print(f"  贡献者数量: {contributor_count}")

        # 获取贡献者数量（一年）
        print(f"  获取贡献者数量（一年）...")
        contributors_year = self.get_project_contributor_year(project_path)
        contributor_count_year = len(contributors_year)
        print(f"  贡献者数量(一年): {contributor_count_year}")

        # 获取总PR数（100天）
        print(f"  获取总PR数（100天）...")
        all_prs = self.get_project_merge_requests(project_path, days=100)
        total_pr_count = len(all_prs)
        print(f"  总PR数(100天): {total_pr_count}")

        # 获取最近30天PR数
        print(f"  获取最近30天PR数...")
        prs_30_days = self.get_30_days_prs(all_prs)
        pr_count_30_days = len(prs_30_days)
        print(f"  最近30天PR数: {pr_count_30_days}")

        # 获取最近7天PR数
        print(f"  获取最近7天PR数...")
        pr_count_7_days = self.get_7_days_prs(all_prs)
        print(f"  最近7天PR数: {pr_count_7_days}")

        # 计算最近30天单日PR提交峰值
        max_pr_count_30_days = 0
        max_pr_date_30_days = ""
        if len(prs_30_days) > 0:
            daily_pr_counts = {}
            for pr in prs_30_days:
                pr_date = datetime.fromisoformat(pr['created_at']).strftime('%Y-%m-%d')
                daily_pr_counts[pr_date] = daily_pr_counts.get(pr_date, 0) + 1

            if daily_pr_counts:
                max_pr_count_30_days = max(daily_pr_counts.values())
                max_pr_date_30_days = max(daily_pr_counts, key=daily_pr_counts.get)

        # 计算门禁时长
        gatekeeper_durations = []
        max_duration_pr_url = ""
        max_duration = 0.0

        # 计算PR闭环时间
        pr_close_durations = []
        max_pr_close_duration = 0.0
        max_close_duration_pr_url = ""

        # 筛选最近30天内已合入的PR
        merged_prs = sorted(
            [pr for pr in prs_30_days if pr['state'] == 'merged'],
            key=lambda x: x.get('merged_at', x.get('created_at', '')),
            reverse=True
        )

        # 计算PR闭环时间
        for pr in prs_30_days:
            if pr['state'] in ['merged', 'closed']:
                try:
                    created_at = datetime.fromisoformat(pr['created_at'])
                    if pr['state'] == 'merged' and pr.get('merged_at'):
                        closed_at = datetime.fromisoformat(pr['merged_at'])
                    elif pr.get('closed_at'):
                        closed_at = datetime.fromisoformat(pr['closed_at'])
                    else:
                        continue

                    duration_minutes = (closed_at - created_at).total_seconds() / 60
                    pr_close_durations.append(duration_minutes)

                    if duration_minutes > max_pr_close_duration:
                        max_pr_close_duration = duration_minutes
                        max_close_duration_pr_url = f"https://gitcode.com/{self.owner}/{project_path}/pull/{pr['number']}"
                except Exception as e:
                    print(f"计算PR #{pr['number']}闭环时间失败: {e}")

        # 计算门禁时长（最近10个合入PR）
        processed_prs = 0
        max_processed_prs = 10
        ci_flags = {"yellow_ci_flag": False, "blue_ci_flag": False}

        for pr in merged_prs:
            if processed_prs >= max_processed_prs:
                break

            ci_info = self.calculate_gatekeeper_duration(project_path, pr['number'])
            if ci_info is not None:
                ci_flags["yellow_ci_flag"] |= ci_info["yellow_ci_flag"]
                ci_flags["blue_ci_flag"] |= ci_info["blue_ci_flag"]

                gatekeeper_durations.append(ci_info["duration_minutes"])
                if ci_info["duration_minutes"] > max_duration:
                    max_duration = ci_info["duration_minutes"]
                    max_duration_pr_url = f"https://gitcode.com/{self.owner}/{project_path}/pull/{pr['number']}"
            processed_prs += 1

        avg_gatekeeper_duration = round(sum(gatekeeper_durations) / len(gatekeeper_durations), 2) if gatekeeper_durations else 0
        avg_pr_close_duration = round(sum(pr_close_durations) / len(pr_close_durations), 2) if pr_close_durations else 0

        return {
            'contributor_count': contributor_count,
            'contributor_count_year': contributor_count_year,
            'total_pr_count': total_pr_count,
            'pr_count_7_days': pr_count_7_days,
            'pr_count_30_days': pr_count_30_days,
            'max_pr_count_30_days': max_pr_count_30_days,
            'max_pr_date_30_days': max_pr_date_30_days,
            'avg_gatekeeper_duration': avg_gatekeeper_duration,
            'max_duration_pr_url': max_duration_pr_url,
            'max_duration': max_duration,
            'avg_pr_close_duration': avg_pr_close_duration,
            'max_pr_close_duration': max_pr_close_duration,
            'max_close_duration_pr_url': max_close_duration_pr_url,
            'yellow_ci_flag': ci_flags["yellow_ci_flag"],
            'blue_ci_flag': ci_flags["blue_ci_flag"]
        }

    def get_30_days_prs(self, all_prs: List[Dict]) -> List[Dict]:
        """获取最近30天内的PR"""
        prs_30_days = [pr for pr in all_prs if (datetime.now(timezone.utc) - datetime.fromisoformat(pr['created_at'])).days <= 30]
        return prs_30_days

    def get_7_days_prs(self, all_prs: List[Dict]) -> int:
        """获取最近7天内的PR数量"""
        prs_7_days = [pr for pr in all_prs if (datetime.now(timezone.utc) - datetime.fromisoformat(pr['created_at'])).days <= 7]
        return len(prs_7_days)

    def get_all_community_projects(self) -> List[Dict]:
        """获取所有社区的项目列表"""
        all_projects = []
        page = 1
        max_pages = 20

        print(f"获取项目列表：开始（最大页数限制：{max_pages}）")

        while page <= max_pages:
            print(f"  获取第 {page} 页项目...")
            projects = self.get_community_projects(page=page, per_page=100)

            if not projects:
                print(f"  第 {page} 页没有项目，结束获取")
                break

            print(f"  第 {page} 页获取到 {len(projects)} 个项目")
            all_projects.extend(projects)

            if len(projects) < 100:
                print(f"  第 {page} 页项目不足100个，所有项目已获取完成")
                break

            page += 1
            time.sleep(0.5)

        print(f"获取项目列表：完成，共获取到 {len(all_projects)} 个项目")
        filtered_projects = self._apply_repo_filters(all_projects)
        if len(filtered_projects) != len(all_projects):
            if self.repo_whitelist:
                print(f"已启用仓库白名单过滤：{len(all_projects)} -> {len(filtered_projects)}")
            elif self.repo_blacklist:
                print(f"已启用仓库黑名单过滤：{len(all_projects)} -> {len(filtered_projects)}")
        return filtered_projects

    def crawl_community_stats(self) -> Dict:
        """主函数：爬取社区的统计数据"""
        print(f"开始爬取{self.owner}社区统计数据...")

        projects = self.get_all_community_projects()

        print(f"共获取到{len(projects)}个{self.owner}项目")

        community_stats = {
            "total_repos": len(projects),
            "project_stats": {}
        }

        for i, project in enumerate(projects):
            project_name = project["name"]
            project_path = project["path"]
            project_url = project["html_url"]

            print(f"\n===== 开始处理第 {i+1}/{len(projects)} 个项目: {project_name} =====")

            stats = self.analyze_project_stats(project_path)

            community_stats["project_stats"][project_name] = {
                "project_info": {
                    "name": project_name,
                    "url": project_url,
                    "description": project.get("description", "")
                },
                "stats": stats
            }

            print(f"  - {project_name}: 贡献者{stats['contributor_count']}人, PR数{stats['total_pr_count']}, 最近7天{stats['pr_count_7_days']}, 最近30天{stats['pr_count_30_days']}")
            print(f"===== 完成处理第 {i+1}/{len(projects)} 个项目: {project_name} =====")

            time.sleep(1)

        print("\n爬取完成！")
        return community_stats

    def save_to_csv(self, stats: Dict, filename: str = None):
        """将统计结果保存为CSV文件"""
        if filename is None:
            os.makedirs(self.output_dir, exist_ok=True)
            filename = os.path.join(self.output_dir, f"{self.owner}_community_stats.csv")

        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = [
                '项目名称', '项目URL', '项目描述',
                '贡献者数量', '总PR数',
                '最近7天PR数', '最近30天PR数', 'PR单日峰值数（最近30天内）', '最近30天最大PR日期',
                '门禁类型', '平均门禁时长(分钟)', '最长门禁时长(分钟)', '最长门禁时长PR链接',
                '平均PR闭环时间(分钟)', '最长PR闭环时间(分钟)', '最长闭环PR链接'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for project_name, data in stats["project_stats"].items():
                project_info = data["project_info"]
                project_stats = data["stats"]

                writer.writerow({
                    '项目名称': project_name,
                    '项目URL': project_info.get('url', ''),
                    '项目描述': project_info.get('description', '')[:100],
                    '贡献者数量': project_stats["contributor_count"],
                    '总PR数': project_stats["total_pr_count"],
                    '最近7天PR数': project_stats["pr_count_7_days"],
                    '最近30天PR数': project_stats["pr_count_30_days"],
                    'PR单日峰值数（最近30天内）': project_stats["max_pr_count_30_days"],
                    '最近30天最大PR日期': project_stats["max_pr_date_30_days"],
                    '门禁类型': f"{'黄区 and 蓝区' if project_stats['yellow_ci_flag'] and project_stats['blue_ci_flag'] else '黄区' if project_stats['yellow_ci_flag'] else '蓝区' if project_stats['blue_ci_flag'] else '无'}",
                    '平均门禁时长(分钟)': project_stats["avg_gatekeeper_duration"],
                    '最长门禁时长(分钟)': project_stats["max_duration"],
                    '最长门禁时长PR链接': project_stats["max_duration_pr_url"],
                    '平均PR闭环时间(分钟)': project_stats["avg_pr_close_duration"],
                    '最长PR闭环时间(分钟)': project_stats["max_pr_close_duration"],
                    '最长闭环PR链接': project_stats["max_close_duration_pr_url"]
                })

        print(f"统计结果已保存到: {filename}")

    def save_to_json(self, stats: Dict, filename: str = None):
        """将统计结果保存为JSON文件"""
        if filename is None:
            os.makedirs(self.output_dir, exist_ok=True)
            filename = os.path.join(self.output_dir, f"{self.owner}_community_stats_detailed.json")

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)

        print(f"详细JSON数据已保存到: {filename}")

    def generate_report(self, stats: Dict):
        """生成社区统计报告"""
        print("\n" + "="*80)
        print(f"{self.owner}社区统计报告")
        print("="*80)

        print(f"社区级指标:")
        print("-" * 40)
        print(f"总代码仓数: {stats['total_repos']}")
        print("\n")

        print("项目级指标:")
        print("-" * 120)
        print(f"{'项目名称':<25} {'贡献者数':<10} {'总PR数':<10} {'最近7天':<10} {'最近30天':<10} {'30天最大':<10} {'平均门禁时长':<15} {'平均PR闭环时间':<15}")
        print("-" * 120)

        for project_name, data in stats["project_stats"].items():
            project_stats = data["stats"]
            print(f"{project_name:<25} {project_stats['contributor_count']:<10} {project_stats['total_pr_count']:<10} {project_stats['pr_count_7_days']:<10} {project_stats['pr_count_30_days']:<10} {project_stats['max_pr_count_30_days']:<10} {project_stats['avg_gatekeeper_duration']:<15}分钟 {project_stats['avg_pr_close_duration']:<15}分钟")
