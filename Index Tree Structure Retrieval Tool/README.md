# 機関リポジトリ インデックスツリー構造取得ツール

## 概要

　本プログラムは，JAIRO Cloudを用いた機関リポジトリが提供するAPIからインデックスツリーの組織階層情報を取得し，部局・研究科・センター等のノードIDを収集して，一覧化するPythonスクリプトです。

<img width="703" height="180" alt="image" src="https://github.com/user-attachments/assets/c06bf582-bdb9-4a0a-8a8d-3cc1fc1e5b75" />

### ファイル説明

| ファイル | 説明 |
|----------|------|
| `indextree_domains.txt` | 検索対象機関リポジトリの URL を設定するファイル |
| `tree_structure_retrieval.py` | プログラム本体 |
| `departments.txt` | 部局情報取得のためのインデックスツリー情報をまとめたファイル |
| `error_log.txt` | エラーログを出力するファイル |

> 出力された `departments.txt` は、そのまま「機関リポジトリ キーワード検索・書誌情報収集ツール」のフォルダ内へ配置して利用できます。

---

## フォルダ構成

```text
C:\kgos\hp\indextree
├─ indextree_domains.txt
├─ tree_structure_retrieval.py
├─ departments.txt
└─ error_log.txt
```

---

## 必要環境

### OS

- 推奨：Windows 11

### Python（推奨：Python 3.11 以上）

Python 公式サイト：以下よりインストールしてください。

https://www.python.org/

### バージョン確認

```bash
python --version
```

### ライブラリのインストール

以下コマンドを実行し，requestsをインストールしてください。
```bash
pip install requests
```

### インストール確認

以下コマンドを実行ください。
```bash
pip list
```

`requests` が表示されれば準備完了です。

---

## 事前準備

### 1. 作業フォルダ作成

任意の場所に作業フォルダを作成します。

例

```text
C:/kgos/hp/indextree
```

### 2. ファイル配置

```text
C:/kgos/hp/indextree
├─ tree_structure_retrieval.py
└─ indextree_domains.txt
```

※ `departments.txt` および `error_log.txt` は実行後に生成されます。

### 3. 機関情報ファイル作成

`indextree_domains.txt` に以下のとおり記載します。

記述形式

```text
機関名:URLまたはドメイン名
```

記述例

```text
鹿児島大学:https://ir.kagoshima-u.ac.jp
```

または

```text
鹿児島大学:ir.kagoshima-u.ac.jp
```

も利用できます。

### 注意事項

以下の行は無視されます。

```text
# コメント行
```

```text
空行
```

---

## 処理フロー

```text
 機関一覧読込
      ↓
部局ID収集(JSON取得)
      ↓
   結果出力
      ↓
     終了
```

---

## 実行手順

1. コマンドプロンプトまたは PowerShell を開きます。

2. 対象ディレクトリへ移動します。
以下のように，対象ディレクトリを指定します。
```bash
cd C:/kgos/hp/indextree
```

3. プログラムを実行します。
```bash
python  tree_structure_retrieval.py
```

## API仕様

### 接続先

各機関のURLまたはドメインから自動生成し、ツリー構造情報を取得します。

例

```text
https://ir.kagoshima-u.ac.jp/api/tree?action=browsing
```

## 除外対象

インデックスツリー情報の掲載誌一覧を除外します。

```python
EXCLUDE_ROOT_NAMES = [
    "掲載誌一覧",
    "List of Journals"
]
```

### 理由

```text
掲載誌一覧
  ↓
雑誌名
  ↓
巻号
```

という構造であり、部局分類ではないためです。

---

## エラー処理

### リトライ処理

通信エラーが発生した場合、自動的に再試行を行います。

#### 設定値

```python
MAX_RETRY = 4
RETRY_WAITS = [5, 7, 10]
```

#### 動作

```text
初回実行
 ↓失敗
5秒待機

再試行1回目
 ↓失敗
7秒待機

再試行2回目
 ↓失敗
10秒待機

再試行3回目
 ↓失敗
error_log.txtへ記録
```

---

## 引用について

本ソースコードを利用した研究成果を公表する場合、または改変して再配布する場合には、以下のとおり出典の明記にご協力をお願いいたします。

### 引用例

```text
KGOS:https://github.com/KGOS-Promotion/KGOS.code/tree/main/Index%20Tree%20Structure%20Retrieval%20Tool
（YYYY年MM月DD日取得）
```

---

## ライセンス

ライセンス条件（MITライセンス）の詳細については、配布元リポジトリをご確認ください。

- KGOS.code Repository
  - https://github.com/kagoshimakgos/KGOS.code/tree/main/Regional%20dataset
