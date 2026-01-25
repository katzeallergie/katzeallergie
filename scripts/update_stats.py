#!/usr/bin/env python3
"""
GitHub Stats Updater
Private repositoryの統計情報を含めてREADMEを更新するスクリプト
"""

import os
import requests
from datetime import datetime
from collections import defaultdict
import re


class GitHubStatsUpdater:
    def __init__(self, token, username):
        self.token = token
        self.username = username
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"

    def get_user_repos(self):
        """ユーザーのすべてのリポジトリ（private含む）を取得"""
        repos = []
        page = 1
        per_page = 100

        while True:
            url = f"{self.base_url}/user/repos"
            params = {
                "page": page,
                "per_page": per_page,
                "affiliation": "owner,collaborator,organization_member"
            }
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            page_repos = response.json()
            if not page_repos:
                break

            repos.extend(page_repos)
            page += 1

        return repos

    def get_contribution_stats(self):
        """Contribution統計を取得"""
        repos = self.get_user_repos()

        stats = {
            "total_repos": len(repos),
            "public_repos": sum(1 for r in repos if not r["private"]),
            "private_repos": sum(1 for r in repos if r["private"]),
            "total_stars": sum(r["stargazers_count"] for r in repos),
            "total_forks": sum(r["forks_count"] for r in repos),
            "total_commits": 0,
            "total_prs": 0,
            "total_issues": 0,
        }

        # コミット数を取得（過去1年分）
        # Note: 完全なコミット数を取得するには各リポジトリをチェックする必要がありますが、
        # API制限を考慮して、ユーザーのイベントから概算を取得
        try:
            events_url = f"{self.base_url}/users/{self.username}/events"
            events_response = requests.get(events_url, headers=self.headers, params={"per_page": 100})
            events = events_response.json()

            # PushEventからコミット数を推定
            for event in events:
                if event["type"] == "PushEvent":
                    stats["total_commits"] += len(event.get("payload", {}).get("commits", []))
        except Exception as e:
            print(f"Warning: Could not fetch events: {e}")

        # PRとIssueの数を取得
        try:
            # 自分が作成したPRの数
            search_url = f"{self.base_url}/search/issues"
            pr_params = {"q": f"author:{self.username} is:pr"}
            pr_response = requests.get(search_url, headers=self.headers, params=pr_params)
            if pr_response.status_code == 200:
                stats["total_prs"] = pr_response.json()["total_count"]

            # 自分が作成したIssueの数
            issue_params = {"q": f"author:{self.username} is:issue"}
            issue_response = requests.get(search_url, headers=self.headers, params=issue_params)
            if issue_response.status_code == 200:
                stats["total_issues"] = issue_response.json()["total_count"]
        except Exception as e:
            print(f"Warning: Could not fetch PR/Issue counts: {e}")

        return stats

    def get_language_stats(self):
        """言語使用統計を取得"""
        repos = self.get_user_repos()
        language_bytes = defaultdict(int)

        for repo in repos:
            # フォークは除外
            if repo["fork"]:
                continue

            try:
                lang_url = repo["languages_url"]
                response = requests.get(lang_url, headers=self.headers)
                response.raise_for_status()
                languages = response.json()

                for lang, bytes_count in languages.items():
                    language_bytes[lang] += bytes_count
            except Exception as e:
                print(f"Warning: Could not fetch languages for {repo['name']}: {e}")
                continue

        # パーセンテージを計算
        total_bytes = sum(language_bytes.values())
        language_stats = {}

        if total_bytes > 0:
            for lang, bytes_count in sorted(language_bytes.items(), key=lambda x: x[1], reverse=True):
                percentage = (bytes_count / total_bytes) * 100
                language_stats[lang] = {
                    "bytes": bytes_count,
                    "percentage": round(percentage, 2)
                }

        return language_stats

    def format_contribution_stats(self, stats):
        """Contribution統計をMarkdown形式でフォーマット"""
        return f"""
| 📊 Metric | Value |
|-----------|-------|
| 📦 Total Repos | {stats['total_repos']} ({stats['public_repos']} public, {stats['private_repos']} private) |
| ⭐ Total Stars | {stats['total_stars']} |
| 🔀 Total Forks | {stats['total_forks']} |
| 📝 Total PRs | {stats['total_prs']} |
| 🐛 Total Issues | {stats['total_issues']} |

<sub>Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</sub>
"""

    def format_language_stats(self, language_stats, top_n=10):
        """言語統計をMarkdown形式でフォーマット"""
        if not language_stats:
            return "No language data available."

        # Top N言語のみを表示
        top_languages = sorted(language_stats.items(), key=lambda x: x[1]["percentage"], reverse=True)[:top_n]

        lines = ["| Language | Percentage |", "|----------|------------|"]
        for lang, data in top_languages:
            bar_length = int(data["percentage"] / 2)  # 50% = 25文字のバー
            bar = "█" * bar_length
            lines.append(f"| {lang} | {bar} {data['percentage']}% |")

        result = "\n".join(lines)
        result += f"\n\n<sub>Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</sub>"
        return result

    def update_readme(self, readme_path="README.md"):
        """READMEファイルを更新"""
        print("Fetching contribution stats...")
        contribution_stats = self.get_contribution_stats()

        print("Fetching language stats...")
        language_stats = self.get_language_stats()

        print("Formatting stats...")
        contribution_markdown = self.format_contribution_stats(contribution_stats)
        language_markdown = self.format_language_stats(language_stats)

        # READMEを読み込む
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()

        # マーカーコメント間のコンテンツを置換
        # Contribution stats
        contribution_pattern = r"<!-- CONTRIBUTION_STATS_START -->.*?<!-- CONTRIBUTION_STATS_END -->"
        contribution_replacement = f"<!-- CONTRIBUTION_STATS_START -->\n{contribution_markdown}\n<!-- CONTRIBUTION_STATS_END -->"

        if "<!-- CONTRIBUTION_STATS_START -->" in readme_content:
            readme_content = re.sub(contribution_pattern, contribution_replacement, readme_content, flags=re.DOTALL)
        else:
            print("Warning: CONTRIBUTION_STATS markers not found in README")

        # Language stats
        language_pattern = r"<!-- LANGUAGE_STATS_START -->.*?<!-- LANGUAGE_STATS_END -->"
        language_replacement = f"<!-- LANGUAGE_STATS_START -->\n{language_markdown}\n<!-- LANGUAGE_STATS_END -->"

        if "<!-- LANGUAGE_STATS_START -->" in readme_content:
            readme_content = re.sub(language_pattern, language_replacement, readme_content, flags=re.DOTALL)
        else:
            print("Warning: LANGUAGE_STATS markers not found in README")

        # READMEを更新
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print("README updated successfully!")
        print("\nContribution Stats:")
        print(contribution_markdown)
        print("\nLanguage Stats:")
        print(language_markdown)


def main():
    # 環境変数から設定を取得
    github_token = os.environ.get("GITHUB_TOKEN")
    github_username = os.environ.get("GITHUB_USERNAME")

    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")

    if not github_username:
        raise ValueError("GITHUB_USERNAME environment variable is required")

    updater = GitHubStatsUpdater(github_token, github_username)
    updater.update_readme()


if __name__ == "__main__":
    main()
