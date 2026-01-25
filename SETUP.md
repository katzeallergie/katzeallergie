# GitHub Profile Stats Setup Guide

このリポジトリは、private repositoryの統計情報を含むGitHubプロフィールを自動更新します。

## 🔧 セットアップ手順

### 1. Personal Access Token (PAT) の作成

private repositoryの情報にアクセスするためには、適切な権限を持つPersonal Access Tokenが必要です。

1. GitHubの設定ページにアクセス: https://github.com/settings/tokens
2. "Generate new token" → "Generate new token (classic)" を選択
3. Token名を入力（例: "Profile Stats Updater"）
4. 有効期限を設定（推奨: 90日、必要に応じて "No expiration"）
5. 以下の権限（scopes）を選択:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:user` (Read user profile data)
   - ✅ `user:email` (Access user email addresses)
   - ✅ `read:org` (Read organization data) ※Organization のリポジトリも含める場合
6. "Generate token" をクリック
7. **生成されたトークンを必ずコピーして安全な場所に保存**（再表示できません）

#### 📌 Organization のリポジトリについて

**Classic Personal Access Token** を使用する場合、以下の条件を満たせば Organization の private repository も自動的に含まれます：

- あなたが Organization のメンバーである
- Organization が Personal Access Token のアクセスを許可している

**SSO (Single Sign-On) を使用している Organization の場合**:

1. PAT 作成後、https://github.com/settings/tokens にアクセス
2. 作成したトークンの横に "Configure SSO" または "Authorize" ボタンが表示される
3. 対象の Organization ごとに "Authorize" をクリックして認可

**Fine-grained Personal Access Token** を使用する場合:

- Organization ごとに明示的にアクセス許可を設定する必要があります
- Organization の設定で Fine-grained PAT が許可されている必要があります
- より細かい権限制御が可能ですが、設定が複雑になります

### 2. GitHub Secretsにトークンを設定

1. このリポジトリの設定ページにアクセス: `Settings` → `Secrets and variables` → `Actions`
2. "New repository secret" をクリック
3. 以下のシークレットを作成:
   - **Name**: `PAT_TOKEN`
   - **Value**: 上記で作成したPersonal Access Token

### 3. ワークフローの初回実行

#### 方法1: 手動実行

1. リポジトリの `Actions` タブに移動
2. 左サイドバーから "Update GitHub Stats" ワークフローを選択
3. "Run workflow" ボタンをクリック
4. ワークフローが完了すると、README.mdが自動的に更新されます

#### 方法2: コードをプッシュ

```bash
git add .
git commit -m "feat: add GitHub stats auto-update"
git push
```

プッシュすると、ワークフローが自動的に実行されます。

### 4. 動作確認

1. `Actions` タブでワークフローの実行状況を確認
2. 正常に完了したら、README.mdを確認
3. Contribution StatsとLanguage Statsが更新されていることを確認

## 📅 自動更新スケジュール

- **定期実行**: 毎月1日 0:00 UTC（日本時間 9:00）に自動更新
- **手動実行**: Actionsタブから随時実行可能
- **コード変更時**: ワークフローファイルやスクリプトの変更時にも実行

## 🔍 トラブルシューティング

### アクセス可能なリポジトリを確認する

どのリポジトリにアクセスできるかテストするスクリプトを用意しています：

```bash
# Personal Access Tokenを環境変数に設定
export GITHUB_TOKEN='your_token_here'

# テストスクリプトを実行
python scripts/test_repos.py
```

このスクリプトは以下を表示します：
- アクセス可能な個人リポジトリ（public/private）
- アクセス可能な Organization リポジトリ（Organization 別）
- 各リポジトリの可視性（public/private）

**Organization のリポジトリが表示されない場合**:
1. その Organization のメンバーであることを確認
2. SSO を使用している場合、PAT を認可しているか確認
3. Organization の設定で Personal Access Token が許可されているか確認
4. `read:org` スコープが付与されているか確認

### Stats が更新されない

1. Personal Access Tokenの権限を確認
   - `repo`, `read:user`, `user:email`, `read:org` が必要です
2. GitHub Secretsに `PAT_TOKEN` が正しく設定されているか確認
3. Actions タブでワークフローのログを確認してエラーメッセージをチェック
4. 上記のテストスクリプトでアクセス可能なリポジトリを確認

### "GITHUB_TOKEN environment variable is required" エラー

- GitHub Secretsに `PAT_TOKEN` が設定されていない可能性があります
- セットアップ手順2を再確認してください

### API Rate Limit エラー

- GitHub APIには利用制限があります
- 通常、認証済みリクエストは1時間に5000リクエストまで可能です
- 多数のリポジトリがある場合は、スクリプトの実行頻度を調整してください

## 🛠 カスタマイズ

### 実行頻度の変更

`.github/workflows/update-stats.yml` の `cron` 設定を変更:

```yaml
schedule:
  - cron: '0 0 1 * *'  # 毎月1日0時UTC（現在の設定）
  # 例: 毎週月曜日の0時UTC
  # - cron: '0 0 * * 1'
  # 例: 毎日0時UTC
  # - cron: '0 0 * * *'
```

### 表示する統計情報の変更

`scripts/update_stats.py` を編集して、表示する統計情報をカスタマイズできます。

### Top言語の表示数を変更

`scripts/update_stats.py` の `format_language_stats` メソッドの `top_n` パラメータを変更:

```python
def format_language_stats(self, language_stats, top_n=10):
    # top_n の値を変更（デフォルト: 10）
```

## 📝 ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── update-stats.yml    # GitHub Actions ワークフロー
├── scripts/
│   ├── update_stats.py         # 統計情報取得スクリプト
│   └── test_repos.py           # リポジトリアクセステスト用スクリプト
├── README.md                    # プロフィールページ（自動更新）
├── SETUP.md                     # このファイル
└── requirements.txt             # Python依存関係
```

## 🔒 セキュリティに関する注意

- Personal Access Tokenは絶対に公開しないでください
- トークンは GitHub Secrets に保存し、コードに直接記述しないでください
- 必要最小限の権限のみを付与してください
- 定期的にトークンをローテーション（再生成）することを推奨します

## 📚 参考リンク

- [GitHub API Documentation](https://docs.github.com/en/rest)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
