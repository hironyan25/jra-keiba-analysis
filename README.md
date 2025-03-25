# JRA競馬データ分析プロジェクト

## 概要

JRA（日本中央競馬会）の競馬データを活用して、馬券回収率の向上を目指す分析・予測システムを構築するプロジェクトです。JVD（JRA-VAN Data Lab）のデータベースを基盤とし、特に回収率に寄与する特化型特徴量の開発と予測モデルの実装を行います。

## 目標

- PostgreSQLデータベースから効率的にJRAデータを抽出・加工するパイプラインの構築
- 回収率向上に貢献する特化型特徴量の開発（30種類以上）
- 機械学習モデルによる予測システムの実装
- 回収率110%以上を目指す投資戦略の確立

## 特化型特徴量

本プロジェクトでは以下の特化型特徴量に特に注目しています：

1. **種牡馬×馬場適性ROI**: 特定の種牡馬の産駒が特定の馬場条件で示す単勝回収率
2. **騎手のコース別平均配当**: 各騎手が特定コースで勝利したときの平均配当
3. **前走ペース偏差（展開不利指標）**: 前走の脚質とペースの相性による展開不利度合い
4. **馬のコース実績ROI**: 特定コースでの回収率と人気の乖離
5. **上がりタイム順位**: レース内での上がり3Fの順位による評価
6. **道悪適性指標**: 馬場状態別の相対成績に基づく適性評価

## プロジェクト構造

```
./
├── config/                      # 設定ファイル
├── data/                        # データディレクトリ
├── notebooks/                   # Jupyter notebooks
├── src/                         # ソースコード
│   ├── data/                    # データ処理モジュール
│   ├── features/                # 特徴量エンジニアリング
│   ├── models/                  # モデル実装
│   └── visualization/           # 可視化モジュール
├── tests/                       # テストコード
├── scripts/                     # 実行スクリプト
├── requirements.txt             # 依存ライブラリ
├── Dockerfile                   # Docker設定
└── docker-compose.yml           # Docker Compose設定
```

## 環境セットアップ

### 前提条件

- Python 3.10以上
- PostgreSQL 14.0以上
- Docker および Docker Compose (オプション)

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/hironyan25/jra-keiba-analysis.git
cd jra-keiba-analysis

# 依存関係のインストール
pip install -r requirements.txt

# 設定ファイルの準備
cp config/database.yml.example config/database.yml
# database.ymlを編集して接続情報を設定

# Docker環境の起動（オプション）
docker-compose up -d
```

## 使用方法

### データ抽出

```bash
python scripts/extract_data.py --years 2010-2023
```

### 特徴量生成

```bash
python scripts/generate_features.py
```

### モデル訓練

```bash
python scripts/train_model.py
```

### 予測実行

```bash
python scripts/predict.py --race_date 20230101
```

## ライセンス

[MIT License](LICENSE)

## 貢献方法

1. このリポジトリをフォークする
2. 新しいブランチを作成する (`git checkout -b feature/amazing-feature`)
3. 変更をコミットする (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュする (`git push origin feature/amazing-feature`)
5. Pull Requestを作成する
