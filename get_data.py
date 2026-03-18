from tkinter import NO
import argparse
import requests
import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import csv
import os

class GitCodeCommunityStats:
    def __init__(self, config_file: str = "config.json"):
        """
        初始化爬虫
        
        Args:
            config_file: 配置文件路径
        """
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        self.base_url = "https://api.gitcode.com/api/v5"
        self.headers = {
            "Content-Type": "application/json"
        }
        self.access_token = config.get("access_token", "")
        self.label_ci_success = config.get("label_ci_success", "ci-pipeline-passed")
        self.label_ci_running = config.get("label_ci_running", "ci-pipeline-running")
        self.label_yellow_ci_running = config.get("label_yellow_ci_running", "SC-RUNNING")
        self.label_yellow_ci_success = config.get("label_yellow_ci_success", "SC-SUCC")
        self.owner = config.get("owner", "boostkit")
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_community_projects(self, page: int = 1, per_page: int = 20) -> List[Dict]:
        """
        获取社区的项目列表
        """
        url = f"{self.base_url}/orgs/{self.owner}/repos?access_token={self.access_token}&page={page}&per_page={per_page}"
        
        for retry in range(3):  # 最多重试3次
            try:
                response = self.session.get(url)
                
                # 处理限流
                if response.status_code == 429:
                    time.sleep(5)  # 等待5秒后重试（调整为更合理的时间）
                    continue
                    
                response.raise_for_status()
                time.sleep(0.6)  # 增加请求间隔，确保不超过1分钟100次的限制
                return response.json()
            except requests.exceptions.RequestException as e:
                if retry == 2:  # 只在最后一次重试失败时打印错误
                    print(f"获取项目列表失败: {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"状态码: {e.response.status_code}")
                if retry < 2:  # 不是最后一次重试
                    time.sleep(3)  # 非限流错误等待3秒后重试
                else:
                    return []
        return []
    
    def get_project_contributors(self, project_path: str) -> List[Dict]:
        """
        获取项目的贡献者列表
        """
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/contributors?access_token={self.access_token}&per_page=100"
        
        for retry in range(3):  # 最多重试3次
            try:
                response = self.session.get(url)
                
                # 处理限流
                if response.status_code == 429:
                    time.sleep(5)  # 等待5秒后重试（调整为更合理的时间）
                    continue
                    
                response.raise_for_status()
                time.sleep(0.6)  # 增加请求间隔，确保不超过1分钟100次的限制
                return response.json()
            except requests.exceptions.RequestException as e:
                if retry == 2:  # 只在最后一次重试失败时打印错误
                    print(f"获取项目 {project_path} 的贡献者列表失败: {e}")
                if retry < 2:  # 不是最后一次重试
                    time.sleep(3)  # 非限流错误等待3秒后重试
                else:
                    return []
        return []
    
    def get_project_contributor_year(self, project_path: str) -> List[Dict]:
        """
        #依据分支查询从2025-01-01到2025-12-04的贡献者
        https://api.gitcode.com/api/v5/repos/:owner/:repo/contributors/statistic?access_token=:access_token&since=2025-01-01&until=2025-12-04
        """
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/contributors/statistic?access_token={self.access_token}&since=2025-01-01&until=2025-12-04"
        for retry in range(3):  # 最多重试3次
            try:
                response = self.session.get(url)
                
                # 处理限流
                if response.status_code == 429:
                    time.sleep(5)  # 等待5秒后重试（调整为更合理的时间）
                    continue
                    
                response.raise_for_status()
                time.sleep(0.6)  # 增加请求间隔，确保不超过1分钟100次的限制
                return response.json()
            except requests.exceptions.RequestException as e:
                if retry == 2:  # 只在最后一次重试失败时打印错误
                    print(f"获取项目 {project_path} 的贡献者列表失败: {e}")
                if retry < 2:  # 不是最后一次重试
                    time.sleep(3)  # 非限流错误等待3秒后重试
                else:
                    return []
        return []
    
    def get_project_merge_requests(self, project_path: str, days: int = 30) -> List[Dict]:
        """
        获取指定项目的合并请求（PR）
        """
        # 计算时间范围
        tz = timezone(timedelta(hours=8))
        since_date = (datetime.now(tz) - timedelta(days=days)).isoformat()
        
        all_mrs = []
        page = 1
        max_pages = 50  # 增加最大页数限制，支持最多5000条PR
        
        while page <= max_pages:  # 添加最大页数限制
            url = f"{self.base_url}/repos/{self.owner}/{project_path}/pulls?access_token={self.access_token}&since={since_date}&per_page=100&page={page}"
            
            got_data = False  # 标志位，用于标记是否成功获取到数据
            data_received = []  # 用于存储当前页获取到的数据
            
            for retry in range(3):  # 最多重试3次
                try:
                    response = self.session.get(url)
                    
                    # 处理限流
                    if response.status_code == 429:
                        time.sleep(5)  # 等待5秒后重试（调整为更合理的时间）
                        continue
                        
                    response.raise_for_status()
                    mrs = response.json()
                    
                    # 检查API响应格式是否正确
                    if not isinstance(mrs, list):
                        data_received = []
                    else:
                        data_received = mrs
                    
                    if not data_received:
                        got_data = True
                        # 如果没有获取到数据，跳出外层循环
                        page = max_pages + 1  # 直接设置为超出最大页数，跳出外层循环
                        break
                        
                    all_mrs.extend(data_received)
                    
                    # 检查是否还有更多页面
                    if len(data_received) < 100:
                        got_data = True
                        # 数据已经全部获取，跳出外层循环
                        page = max_pages + 1  # 直接设置为超出最大页数，跳出外层循环
                        break
                        
                    page += 1
                    time.sleep(0.6)  # 增加请求间隔，确保不超过1分钟100次的限制
                    got_data = True
                    break  # 成功获取后跳出重试循环
                    
                except requests.exceptions.RequestException as e:
                    if retry == 2:  # 只在最后一次重试失败时打印错误
                        print(f"获取项目 {project_path} 的PR失败: {e}")
                        if hasattr(e, 'response') and e.response is not None:
                            print(f"状态码: {e.response.status_code}")
                    if retry < 2:  # 不是最后一次重试
                        time.sleep(3)  # 非限流错误等待3秒后重试
                    else:
                        break  # 最后一次重试失败，跳出循环
            
            # 如果获取到数据且数据为空，或者所有重试都失败，跳出外层循环
            if not got_data:
                break
        
        return all_mrs
        
    def get_pr_events(self, project_path: str, pr_number: int) -> List[Dict]:
        """
        获取PR的操作日志
        """
        url = f"{self.base_url}/repos/{self.owner}/{project_path}/pulls/{pr_number}/operate_logs?access_token={self.access_token}&per_page=100"
        
        for retry in range(3):  # 最多重试3次
            try:
                response = self.session.get(url)
                
                # 处理限流
                if response.status_code == 429:
                    time.sleep(5)  # 等待5秒后重试（调整为更合理的时间）
                    continue
                    
                response.raise_for_status()
                time.sleep(0.6)  # 增加请求间隔，确保不超过1分钟100次的限制
                return response.json()
            except requests.exceptions.RequestException as e:
                if retry == 2:  # 只在最后一次重试失败时打印错误
                    print(f"获取PR {pr_number} 操作日志失败: {e}")
                if retry < 2:  # 不是最后一次重试
                    time.sleep(3)  # 非限流错误等待3秒后重试
                else:
                    return []
        return []
    
    def calculate_gatekeeper_duration(self, project_path: str, pr_number: int) -> Dict:
        """
        计算单个PR的门禁时长（分钟）
        按照用户新定义：倒序查询PR操作日志，先找Action是"enterprise_label"且content包含"add label ci-pipeline-passed"的记录，记录时间和user.id；
        然后找相邻最近的Action是"enterprise_label"且content包含"add label ci-pipeline-running"的记录，记录时间和user.id，
        确保两个标签是由同一个user.id添加的，计算两个时间的差值。
        
        特殊处理：如果user.id字段为空或不存在，表示系统无法提供账号信息，此时认为两个标签由同一账号添加。
        """
        events = self.get_pr_events(project_path, pr_number)
        
        if not events:
            print(f"[DEBUG] PR {pr_number} in {project_path}: 没有获取到操作日志")
            return None

        print(f"[DEBUG] PR {pr_number} in {project_path}: 共获取到 {len(events)} 条操作日志")

        # 倒序排列操作日志
        sorted_events = sorted(events, key=lambda x: x.get('created_at', ''), reverse=True)
        # 直接使用sorted_events进行后续分析，无需预先检查标志位
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
            print(f"[DEBUG] PR {pr_number} in {project_path}: 没有找到蓝区门禁通过标签")
            return {"yellow_ci_flag": yellow_ci_flag, "blue_ci_flag": blue_ci_flag, "duration_minutes": 0}

        # 重置变量
        ci_passed_time = None
        ci_running_time = None

        # 收集所有参与门禁标签操作的用户ID
        user_ids = set(
            event.get('user', {}).get('id', '')
            for event in sorted_events
            if (event.get('action', '') == 'enterprise_label' or event.get('action', '') == 'label')
             and (f'add label {self.label_ci_success}' in event.get('content', '')
             or f'add label {self.label_ci_running}' in event.get('content', ''))
        )
        print(f"[DEBUG] PR {pr_number} in {project_path}: 共涉及 {len(user_ids)} 个用户ID")

        # 针对每个用户ID，查找匹配的标签对
        for user_id in user_ids:            
            # 重置当前用户的查找状态
            user_passed_time = None
            user_running_time = None
            
            # 遍历所有事件
            for i, event in enumerate(sorted_events):
                action = event.get('action', '')
                content = event.get('content', '')
                current_user_id = event.get('user', {}).get('id', '')
                created_at = event.get('created_at', '')

                if pr_number == 726:
                    print(f"[DEBUG] PR {pr_number} in {project_path}: 事件 {i}: {action}, {content}, {current_user_id}, {created_at}")
                # 只处理当前用户的操作
                if current_user_id != user_id:
                    continue
                if user_passed_time and (action == 'enterprise_label' or action == 'label') and f'delete label {self.label_ci_success}' in content:
                    user_passed_time = None
                    continue

                # 寻找passed标签
                if user_passed_time is None:
                    if (action == 'enterprise_label' or action == 'label') and f'add label {self.label_ci_success}' in content:
                        user_passed_time = datetime.fromisoformat(created_at)
                else:
                    if (action == 'enterprise_label' or action == 'label') and f'add label {self.label_ci_running}' in content:
                        user_running_time = datetime.fromisoformat(created_at)
                        # 检查时间顺序是否正确
                        if user_running_time < user_passed_time:
                            # 找到匹配的标签对，记录结果
                            ci_passed_time = user_passed_time
                            ci_running_time = user_running_time
                            print(f"[DEBUG] PR {pr_number} in {project_path}: 找到匹配的标签对! 用户ID: {user_id}, 时长: {(ci_passed_time - ci_running_time).total_seconds()/60:.2f}分钟, {ci_passed_time}, {ci_running_time}")
                            break
            # 如果找到匹配的标签对，退出循环
            if ci_passed_time and ci_running_time:
                break

        print(f"[DEBUG] PR {self.label_ci_success} : {ci_passed_time}   {self.label_ci_running}: {ci_running_time}, 黄色CI标志位: {yellow_ci_flag}, 蓝色CI标志位: {blue_ci_flag}")
        # 计算门禁时长（分钟）
        if ci_passed_time and ci_running_time:
            duration_seconds = (ci_passed_time - ci_running_time).total_seconds()
            duration_minutes = max(0, duration_seconds / 60)
            print(f"[DEBUG] PR {pr_number} in {project_path}: 最终门禁时长: {duration_minutes:.2f}分钟")
            return {"yellow_ci_flag": yellow_ci_flag, "blue_ci_flag": blue_ci_flag, "duration_minutes": duration_minutes}
        else:
            print(f"[DEBUG] PR {pr_number} in {project_path}: 未找到匹配的标签对，无法计算门禁时长")
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
        
        # 获取总PR数（一年）
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
        # 筛选出最近7天内的PR
        pr_count_7_days = self.get_7_days_prs(all_prs)
        print(f"  最近7天PR数: {pr_count_7_days}")
        
        # 计算最近30天,单日PR提交峰值（按天计算）
        max_pr_count_30_days = 0
        max_pr_date_30_days = ""
        if len(prs_30_days) > 0:
            # 创建一个字典来存储每天的PR数量
            daily_pr_counts = {}
            for pr in prs_30_days:
                pr_date = datetime.fromisoformat(pr['created_at']).strftime('%Y-%m-%d')
                daily_pr_counts[pr_date] = daily_pr_counts.get(pr_date, 0) + 1
            
            if daily_pr_counts:
                max_pr_count_30_days = max(daily_pr_counts.values())
                # 找到峰值对应的日期（如果有多个日期达到峰值，取第一个）
                max_pr_date_30_days = max(daily_pr_counts, key=daily_pr_counts.get)
        
        # 计算门禁时长平均值（按照用户新定义：只统计最近10次合入PR的成功门禁时长）
        gatekeeper_durations = []
        max_duration_pr_url = ""
        max_duration = 0.0
        
        # 计算PR平均闭环时间（30天内）
        pr_close_durations = []
        max_pr_close_duration = 0.0
        max_close_duration_pr_url = ""
        
        # 筛选最近30天内已合入的PR，并按合入时间倒序排列
        merged_prs = sorted(
            [pr for pr in prs_30_days if pr['state'] == 'merged'],
            key=lambda x: x.get('merged_at', x.get('created_at', '')),
            reverse=True
        )
        
        # 计算PR闭环时间（创建到关闭/合并的时间间隔）
        for pr in prs_30_days:
            if pr['state'] in ['merged', 'closed']:
                try:
                    created_at = datetime.fromisoformat(pr['created_at'])
                    if pr['state'] == 'merged' and pr.get('merged_at'):
                        closed_at = datetime.fromisoformat(pr['merged_at'])
                    elif pr.get('closed_at'):
                        closed_at = datetime.fromisoformat(pr['closed_at'])
                    else:
                        continue  # 没有关闭时间，跳过
                    
                    # 计算时间差（分钟）
                    duration_minutes = (closed_at - created_at).total_seconds() / 60
                    pr_close_durations.append(duration_minutes)
                    
                    # 记录最长闭环时间的PR链接
                    if duration_minutes > max_pr_close_duration:
                        max_pr_close_duration = duration_minutes
                        # 构建PR页面链接，注意Ascend首字母大写
                        max_close_duration_pr_url = f"https://gitcode.com/{self.owner}/{project_path}/pull/{pr['number']}"
                except Exception as e:
                    print(f"计算PR #{pr['number']}闭环时间失败: {e}")
        
        # 只计算最近10个合入PR的门禁时长
        processed_prs = 0
        max_processed_prs = 10
        ci_flags = {"yellow_ci_flag": False, "blue_ci_flag": False}
        for pr in merged_prs:
            if processed_prs >= max_processed_prs:
                break
            
            ci_info = self.calculate_gatekeeper_duration(project_path, pr['number'])
            if ci_info is not None:
                # 更新CI标志
                ci_flags["yellow_ci_flag"] |= ci_info["yellow_ci_flag"]
                ci_flags["blue_ci_flag"] |= ci_info["blue_ci_flag"]

                gatekeeper_durations.append(ci_info["duration_minutes"])
                # 记录最长门禁时长的PR链接
                if ci_info["duration_minutes"] > max_duration:
                    max_duration = ci_info["duration_minutes"]
                    # 构建PR页面链接，注意Ascend首字母大写
                    max_duration_pr_url = f"https://gitcode.com/{self.owner}/{project_path}/pull/{pr['number']}"
            processed_prs += 1
        
        avg_gatekeeper_duration = round(sum(gatekeeper_durations) / len(gatekeeper_durations), 2) if gatekeeper_durations else 0
        
        # 计算平均闭环时间（分钟）
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
        """
        获取最近30天内的PR数量
        """
        prs_30_days = [pr for pr in all_prs if (datetime.now(timezone.utc) - datetime.fromisoformat(pr['created_at'])).days <= 30]
        return prs_30_days
    
    def get_7_days_prs(self, all_prs: List[Dict]) -> int:
        """
        获取最近7天内的PR数量
        """
        prs_7_days = [pr for pr in all_prs if (datetime.now(timezone.utc) - datetime.fromisoformat(pr['created_at'])).days <= 7]
        return len(prs_7_days)
    
    def get_all_community_projects(self) -> List[Dict]:
        """
        获取所有社区的项目列表
        """
        all_projects = []
        page = 1
        max_pages = 20  # 设置最大页数限制，防止无限循环
        
        print(f"获取项目列表：开始（最大页数限制：{max_pages}）")
        
        while page <= max_pages:
            print(f"  获取第 {page} 页项目...")
            projects = self.get_community_projects(page=page, per_page=100)
            
            if not projects:
                print(f"  第 {page} 页没有项目，结束获取")
                break
            
            print(f"  第 {page} 页获取到 {len(projects)} 个项目")
            all_projects.extend(projects)
            
            # 检查是否还有更多项目
            if len(projects) < 100:
                print(f"  第 {page} 页项目不足100个，所有项目已获取完成")
                break
                
            page += 1
            time.sleep(0.5)
        
        print(f"获取项目列表：完成，共获取到 {len(all_projects)} 个项目")
        return all_projects
    
    def crawl_community_stats(self) -> Dict:
        """
        主函数：爬取社区的统计数据
        """
        print(f"开始爬取{self.owner}社区统计数据...")
        
        # 获取所有项目
        projects = self.get_all_community_projects()

        print(f"共获取到{len(projects)}个{self.owner}项目")
        
        community_stats = {
            "total_repos": len(projects),
            "project_stats": {}
        }
        
        # 处理所有项目
        for i, project in enumerate(projects):
            project_name = project["name"]
            project_path = project["path"]
            project_url = project["html_url"]

            # if i > 3 :
            #     break

            # if "rackmount" not in project_path:
            #     continue
            
            print(f"\n===== 开始处理第 {i+1}/{len(projects)} 个项目: {project_name} =====")
            
            # 分析项目统计指标
            stats = self.analyze_project_stats(project_path)
            
            # 保存项目级指标
            community_stats["project_stats"][project_name] = {
                "project_info": {
                    "name": project_name,
                    "url": project_url,
                    "description": project.get("description", "")
                },
                "stats": stats
            }
            
            print(f"  - {project_name}: 贡献者{stats['contributor_count']}人, PR数{stats['total_pr_count']}, 最近7天{stats['pr_count_7_days']}, 最近30天{stats['pr_count_30_days']}, 30天最大{stats['max_pr_count_30_days']}, 平均门禁时长{stats['avg_gatekeeper_duration']}分钟")
            print(f"===== 完成处理第 {i+1}/{len(projects)} 个项目: {project_name} =====")
            
            time.sleep(1)  # 避免请求过于频繁
        
        print("\n爬取完成！")
        return community_stats
    
    def save_to_csv(self, stats: Dict, filename: str = None):
        """
        将统计结果保存为CSV文件
        """
        # 如果未指定文件名，则使用owner作为前缀
        if filename is None:
            filename = f"{self.owner}_community_stats.csv"
        """
        将统计结果保存为CSV文件
        """
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
                    '项目描述': project_info.get('description', '')[:100],  # 限制描述长度
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
    
    def generate_report(self, stats: Dict):
        """
        生成社区统计报告
        """
        print("\n" + "="*80)
        print(f"{self.owner}社区统计报告")
        print("="*80)
        
        # 打印社区级指标
        print(f"社区级指标:")
        print("-" * 40)
        print(f"总代码仓数: {stats['total_repos']}")
        print("\n")
        
        # 打印项目级指标
        print("项目级指标:")
        print("-" * 120)
        print(f"{'项目名称':<25} {'贡献者数':<10} {'总PR数':<10} {'最近7天':<10} {'最近30天':<10} {'30天最大':<10} {'平均门禁时长':<15} {'平均PR闭环时间':<15}")
        print("-" * 120)
        
        for project_name, data in stats["project_stats"].items():
            project_stats = data["stats"]
            print(f"{project_name:<25} {project_stats['contributor_count']:<10} {project_stats['total_pr_count']:<10} {project_stats['pr_count_7_days']:<10} {project_stats['pr_count_30_days']:<10} {project_stats['max_pr_count_30_days']:<10} {project_stats['avg_gatekeeper_duration']:<15}分钟 {project_stats['avg_pr_close_duration']:<15}分钟")

def main():
    """
    主函数
    """
    # 执行参数获取配置文件名
    parser = argparse.ArgumentParser(description="获取GitCode社区统计数据")
    parser.add_argument("--config", type=str, default="config.json", help="配置文件路径")
    args = parser.parse_args()
    
    # 创建统计实例
    stats_crawler = GitCodeCommunityStats(args.config)
    
    # 爬取社区的统计数据
    stats = stats_crawler.crawl_community_stats()
    
    # 生成报告
    stats_crawler.generate_report(stats)
    
    # 保存到CSV
    csv_filename = f"{stats_crawler.owner}_community_stats.csv"
    stats_crawler.save_to_csv(stats, csv_filename)
    
    # 保存详细数据到JSON
    json_filename = f"{stats_crawler.owner}_community_stats_detailed.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)
    
    print("\n\n数据爬取和分析完成！")
    print("- 详细报告已打印到控制台")
    print(f"- 统计结果已保存到: {csv_filename}")
    print(f"- 详细JSON数据已保存到: {json_filename}")

if __name__ == "__main__":
    main()
