# Call Quality Dashboard - Infrastructure

GCPインフラストラクチャのTerraform設定

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────┐
│                         Cloud Run                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Frontend   │  │   Backend    │  │   Celery     │          │
│  │  (Next.js)   │  │  (FastAPI)   │  │   Worker     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                 │                 │                    │
│         │                 │                 │                    │
│         └────────────────┼─────────────────┘                    │
│                          │                                       │
│                 ┌────────┴────────┐                             │
│                 │  VPC Connector  │                             │
│                 └────────┬────────┘                             │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         │                │                │                      │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌─────┴─────┐              │
│  │  Cloud SQL  │  │ Memorystore │  │   Cloud   │              │
│  │ (PostgreSQL)│  │   (Redis)   │  │  Storage  │              │
│  └─────────────┘  └─────────────┘  └───────────┘              │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Cloud Scheduler                       │   │
│  │   ┌─────────────────┐    ┌─────────────────────┐       │   │
│  │   │  Daily Batch    │    │   Recovery Check    │       │   │
│  │   │  (AM 3:00 JST)  │    │   (AM 6:00 JST)     │       │   │
│  │   └─────────────────┘    └─────────────────────┘       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               Cloud Monitoring & Logging                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 前提条件

1. **GCP プロジェクト**: GCPプロジェクトが作成済みであること
2. **gcloud CLI**: インストール済みで認証済みであること
3. **Terraform**: v1.5.0以上がインストールされていること
4. **GitHub リポジトリ**: Secretsが設定可能であること

## 初期セットアップ

### 1. GCP プロジェクトの準備

```bash
# プロジェクトを設定
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化（Terraformでも有効化されるが、事前に有効化推奨）
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  iam.googleapis.com \
  servicenetworking.googleapis.com
```

### 2. Terraform State バケットの作成

```bash
# Terraform state 用のバケットを作成
gsutil mb -l asia-northeast1 gs://${PROJECT_ID}-tfstate

# バージョニングを有効化
gsutil versioning set on gs://${PROJECT_ID}-tfstate
```

### 3. Workload Identity Federation の設定（GitHub Actions用）

```bash
# サービスアカウントを作成
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# 必要な権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Workload Identity Pool を作成
gcloud iam workload-identity-pools create github-pool \
  --location="global" \
  --display-name="GitHub Pool"

# Provider を作成
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# サービスアカウントにWorkload Identity を紐付け
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@${PROJECT_ID}.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_ORG/YOUR_REPO"
```

### 4. Terraform 変数ファイルの作成

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を編集
```

### 5. Terraform の実行

```bash
# 初期化
terraform init

# プラン確認
terraform plan

# 適用
terraform apply
```

## GitHub Secrets の設定

以下のSecretsをGitHubリポジトリに設定してください:

| Secret Name | Description |
|-------------|-------------|
| `GCP_PROJECT_ID` | GCPプロジェクトID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | `github-actions@PROJECT_ID.iam.gserviceaccount.com` |
| `DATABASE_PASSWORD` | データベースパスワード |
| `SECRET_KEY` | JWT署名用シークレット |
| `GOOGLE_CLIENT_ID` | Google OAuth クライアントID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth クライアントシークレット |
| `OPENAI_API_KEY` | OpenAI APIキー |
| `HUME_API_KEY` | Hume AI APIキー |
| `ANTHROPIC_API_KEY` | Anthropic APIキー |
| `NOTIFICATION_EMAIL` | アラート通知先メール |
| `BACKEND_URL` | デプロイ後のバックエンドURL |
| `FRONTEND_URL` | デプロイ後のフロントエンドURL |
| `SLACK_WEBHOOK_URL` | (オプション) Slack通知用 |

## モジュール構成

```
infra/terraform/
├── main.tf                 # メイン設定
├── variables.tf            # 変数定義
├── outputs.tf              # 出力定義
├── terraform.tfvars.example
└── modules/
    ├── networking/         # VPC, VPCコネクタ
    ├── database/           # Cloud SQL (PostgreSQL)
    ├── redis/              # Memorystore (Redis)
    ├── storage/            # Cloud Storage
    ├── cloud-run/          # Cloud Run サービス
    ├── scheduler/          # Cloud Scheduler
    └── monitoring/         # Logging & Monitoring
```

## 本番環境の推奨設定

| リソース | 開発環境 | 本番環境 |
|---------|---------|---------|
| Cloud SQL | db-f1-micro | db-custom-2-4096 以上 |
| Memorystore | BASIC (1GB) | STANDARD_HA (2GB以上) |
| Cloud Run (Backend) | 1 vCPU, 512Mi | 2 vCPU, 1Gi |
| Cloud Run (Celery) | 2 vCPU, 1Gi | 4 vCPU, 2Gi |

## コスト見積もり（月額概算）

| サービス | 開発環境 | 本番環境 |
|---------|---------|---------|
| Cloud SQL | ~$10 | ~$50 |
| Memorystore | ~$35 | ~$100 |
| Cloud Run | ~$5 | ~$30 |
| Cloud Storage | ~$1 | ~$5 |
| Cloud Scheduler | 無料 | 無料 |
| **合計** | **~$50** | **~$185** |

※ 実際のコストは使用量により変動します

## トラブルシューティング

### Cloud SQL 接続エラー
- VPCコネクタが正しく設定されているか確認
- Private IP が有効になっているか確認

### Cloud Run デプロイエラー
- Artifact Registry にイメージがpushされているか確認
- サービスアカウントの権限を確認

### Scheduler ジョブ失敗
- Cloud Run サービスのIAM設定を確認
- ログでエラー詳細を確認
