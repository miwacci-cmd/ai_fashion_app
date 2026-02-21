⚠️ これはテスト環境です。修正はここで実験してからmainへ！

# 👗 AI Fashion Stylist Pro
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-41ADAA?logo=openai)
![Replicate](https://img.shields.io/badge/Flux.1-pro-black)

> **あなたのクローゼットに眠る逸品を、AIが最高のコーディネートへ昇華させる。**

AI Fashion Stylist Proは、個人のクローゼット資産と最新のファッション・インテリジェンスを融合させた、パーソナライズ・スタイリング・プラットフォームです。


## ✨ 特徴

- **Personal Closet Sync**: ユーザーごとに独立したクローゼット管理（`closet_user.json`）。
- **High-Fidelity Visualization**: Flux.1-pro による「助言と100%同期した」全身イメージ生成。
- **Smart Shopping Link**: アイテム属性（衣類/小物）を判別し、性別・体型を考慮した楽天検索。
- **No-Monotone Logic**: AIが陥りがちな全身黒・白コーデを禁止し、コントラストを重視したスタイリングを強制。

## 🛠️ システムアーキテクチャ

1. **Analysis**: クローゼットデータとユーザー属性（体型・季節・シーン）を分析。
2. **Styling**: GPT-4o-miniが、手持ちを活かした「買い足しアイテム」を特定。
3. **Synchronization**: スタイリストの言語情報をそのまま画像プロンプトへ変換。
4. **Execution**: Flux.1-proによる画像生成と、楽天APIによる商品マッチング。

![男性](image.png)
![女性](image-2.png)

🚀 セットアップ
1. 動作環境
Python 3.9以上

Streamlit

2. 環境変数の設定
プロジェクトのルートディレクトリに .env ファイルを作成し、以下の情報を入力してください。
※ .env ファイルはセキュリティのため、絶対にGitHubに公開しないでください。

コード スニペット
OPENAI_API_KEY=your_openai_api_key
REPLICATE_API_TOKEN=your_replicate_token
RAKUTEN_APPLICATION_ID=your_rakuten_app_id
3. インストールと実行
Bash
# 必要ライブラリのインストール
pip install -r requirements.txt

# アプリケーションの起動
streamlit run app.py
📂 ディレクトリ構造
app.py: メインアプリケーション

users.json: ユーザー認証データ

closet_username.json: ユーザー別クローゼットデータ（自動生成）

requirements.txt: 必要ライブラリ一覧

.env: 環境変数（各自作成）

⚖️ 免責事項
当アプリケーションで表示されるブランド名、製品名、およびロゴは、各権利所有者の商標または登録商標です。本アプリでの使用は識別およびスタイリング提案のみを目的としており、各ブランドとの公式な提携、推奨、または承認を示すものではありません。生成される画像はAIによるイメージであり、実際の製品と完全に一致することを保証するものではありません。

© 2026 AI Fashion Stylist Pro | Developed by miwacci
