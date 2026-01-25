#!/usr/bin/env python3
"""
リポジトリ取得テストスクリプト
どのリポジトリにアクセスできるか確認する
"""

import os
import requests
from collections import defaultdict


def get_language_stats(repos, headers, exclude_orgs=None):
    """言語統計を取得"""
    if exclude_orgs is None:
        exclude_orgs = []

    language_bytes = defaultdict(int)

    print("\n=== Fetching language statistics ===")
    if exclude_orgs:
        print(f"Excluding organizations: {', '.join(exclude_orgs)}")
    print("This may take a while...\n")

    for repo in repos:
        # フォークは除外
        if repo["fork"]:
            continue

        # 特定のOrganizationを除外
        if repo["owner"]["type"] == "Organization" and repo["owner"]["login"] in exclude_orgs:
            continue

        try:
            lang_url = repo["languages_url"]
            response = requests.get(lang_url, headers=headers)
            response.raise_for_status()
            languages = response.json()

            for lang, bytes_count in languages.items():
                # Jupyter Notebookを除外
                if lang != "Jupyter Notebook":
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


def test_repo_access(token):
    """アクセス可能なリポジトリを一覧表示"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    base_url = "https://api.github.com"

    print("=== Fetching accessible repositories ===\n")

    repos = []
    page = 1
    per_page = 100

    while True:
        url = f"{base_url}/user/repos"
        params = {
            "page": page,
            "per_page": per_page,
            "affiliation": "owner,collaborator,organization_member"
        }
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.json())
            return

        page_repos = response.json()
        if not page_repos:
            break

        repos.extend(page_repos)
        page += 1

    print(f"Total repositories accessible: {len(repos)}\n")

    # Organization ごとに分類
    org_repos = defaultdict(list)
    personal_repos = []

    for repo in repos:
        owner = repo["owner"]["login"]
        repo_info = {
            "name": repo["name"],
            "full_name": repo["full_name"],
            "private": repo["private"],
            "fork": repo["fork"]
        }

        if repo["owner"]["type"] == "Organization":
            org_repos[owner].append(repo_info)
        else:
            personal_repos.append(repo_info)

    # 個人リポジトリ
    print("=== Personal Repositories ===")
    print(f"Total: {len(personal_repos)}")
    public_count = sum(1 for r in personal_repos if not r["private"])
    private_count = sum(1 for r in personal_repos if r["private"])
    print(f"  - Public: {public_count}")
    print(f"  - Private: {private_count}")

    if personal_repos:
        print("\nList:")
        for repo in sorted(personal_repos, key=lambda x: x["full_name"]):
            visibility = "🔒 Private" if repo["private"] else "🌐 Public"
            fork_mark = " (Fork)" if repo["fork"] else ""
            print(f"  {visibility} - {repo['full_name']}{fork_mark}")

    # Organization ごと
    if org_repos:
        print("\n=== Organization Repositories ===")
        for org_name in sorted(org_repos.keys()):
            repos_list = org_repos[org_name]
            public_count = sum(1 for r in repos_list if not r["private"])
            private_count = sum(1 for r in repos_list if r["private"])

            print(f"\n[{org_name}]")
            print(f"Total: {len(repos_list)} (Public: {public_count}, Private: {private_count})")

            print("List:")
            for repo in sorted(repos_list, key=lambda x: x["name"]):
                visibility = "🔒 Private" if repo["private"] else "🌐 Public"
                fork_mark = " (Fork)" if repo["fork"] else ""
                print(f"  {visibility} - {repo['name']}{fork_mark}")

    # 統計サマリー
    print("\n=== Summary ===")
    total_public = sum(1 for r in repos if not r["private"])
    total_private = sum(1 for r in repos if r["private"])
    print(f"Total Repositories: {len(repos)}")
    print(f"  - Public: {total_public}")
    print(f"  - Private: {total_private}")
    print(f"Organizations with access: {len(org_repos)}")
    if org_repos:
        print(f"Organization names: {', '.join(sorted(org_repos.keys()))}")

    # 言語統計を取得（vrdevelを除外）
    language_stats = get_language_stats(repos, headers, exclude_orgs=["vrdevel"])

    # 言語統計を表示
    if language_stats:
        print("\n=== Language Statistics (Top 10, excluding Jupyter Notebook & vrdevel org) ===")
        top_languages = sorted(language_stats.items(), key=lambda x: x[1]["percentage"], reverse=True)[:10]

        for lang, data in top_languages:
            bar_length = int(data["percentage"] / 2)  # 50% = 25文字のバー
            bar = "█" * bar_length
            print(f"{lang:20s} {bar} {data['percentage']:5.2f}%")


def main():
    github_token = os.environ.get("GITHUB_TOKEN")

    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is required")
        print("\nUsage:")
        print("  export GITHUB_TOKEN='your_token_here'")
        print("  python scripts/test_repos.py")
        return

    test_repo_access(github_token)


if __name__ == "__main__":
    main()
