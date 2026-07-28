# 機関リポジトリ キーワード検索・書誌情報収集ツール

## はじめに

　本ツールは，KGOS（Kagoshima Open Science）ホームページのサポートツールです。本ツールを用いることで，機関リポジトリからキーワード出力された文献について、基本書誌情報（タイトル，主著者，(部局)，(分野)，出版年，文献種別）の一覧表を作成することが可能です。KGOSでは、これを「地域別 文献・データセット」の各市町村等のページに掲載する文献リスト（以下、利用事例参照）に用いていますが、地名以外のキーワードを用いた利用も可能です。なお、本ツールは，JAIRO Cloudを用いた機関リポジトリを想定したプログラムとなります。
　利用事例：KGOS＞KGOS発信＞地域別 文献・データセット＞鹿児島市


### 利用事例
KGOS > KGOS発信 > 地域別 文献・データセット > 鹿児島市

https://www.lib.kagoshima-u.ac.jp/kgos/showcase/area_dataset/category/kagoshima/

<img width="629" height="218" alt="image" src="https://github.com/user-attachments/assets/67e0c16b-5109-4385-a092-650add68a531" />

※ 基本書誌情報（タイトル，主著者，出版年，文献種別）については一般的に、機関リポジトリ内に収録されている文献等アイテムのランディングページから取得可能ですが、「部局」「分野」は書誌情報として管理されていないため、これができません。このため、鹿児島大学ではこの情報をインデックスツリーの情報から取得しています。
大学の機関リポジトリのインデックスツリーが鹿児島大学と同様、部局名別になっている場合は、鹿児島大学と同様の方法で、「部局」「分野」を含むリストの作成が可能です。（3.(3)参考）

## プログラム概要
　本プログラムは，大学機関リポジトリに登録された研究成果を対象として，指定したキーワードで全文検索を実施し，検索結果から文献情報およびメタデータを自動収集するためのプログラムです。本プログラムは，キーワードを変更することで，様々な用途で利用できます。

<img width="693" height="237" alt="image" src="https://github.com/user-attachments/assets/a2119a8c-febd-4269-86c6-3d45687d79dd" />

### ファイルの説明

| ファイル名 | 説明 |
|------------|------|
| `base_url.txt` | 検索対象機関リポジトリのURLを設定するファイル |
| `keywords.txt` | 検索対象キーワード設定ファイル（１行１キーワード） |
| `departments.txt` | 部局情報取得のためのインデックスツリー情報をまとめたファイル<br>（自動取得する場合，3.(3)を参考に別途プログラムを実行ください。）|
| `fields.txt` | 部局名を分野名に変換するための対応表 |

### 実行プログラム

| ファイル名 | 説明 |
|------------|------|
| `run_meta_collector.py` | プログラムファイル<br>詳細は以下の実行手順を参照してください。 |

### 出力ファイル

| ファイル名 | 説明 |
|------------|------|
| `all_result.csv` | 検索キーワード全件一覧リスト。差分管理にも使用。 |
| `result_by_keyword.xlsx` | 検索キーワード別リスト（エクセルシート別） |
| `error_log.txt` | エラーログを出力するファイル |

---

## フォルダ構成

```text
例：C:\kgos\hp
　　├─ base_url.txt（入力ファイル）
　　├─ keywords.txt（入力ファイル）
　　├─ departments.txt（入力ファイル）
　　├─ fields.txt（入力ファイル）
　　├─ run_meta_collector.py（プログラムファイル）
　　├─ all_result.csv（出力ファイル）
　　├─ result_by_keyword.xlsx（出力ファイル）
　　└─ error_log.txt（出力ファイル）
```

すべてのファイルを同一フォルダに配置してください。

---

## 動作環境

### OS

- Windows 11 推奨

### Google Chrome

Seleniumを利用するため、最新版のGoogle Chromeをインストールしてください。

https://www.google.com/chrome/

### Python（推奨：Python 3.11以上）

Python公式サイト：https://www.python.org （※インストール時にAdd Python to PATHへチェックを入れてください。）

以下コマンドにてバージョンご確認ください。
```bash
python --version
```
### 必要ライブラリ

Pythonを起動し，以下コマンドを実行してください。
```bash
pip install selenium pandas requests openpyxl
```

インストール確認：

```bash
pip list
```

以下が表示されていれば準備完了です。

- selenium
- pandas
- requests
- openpyxl

---

## 事前準備

### 1. 機関リポジトリURL設定

`base_url.txt`に大学名および機関リポジトリURLを設定してください。

```text
例：鹿児島大学:https://ir.kagoshima-u.ac.jp
```

---

### 2. 検索キーワード設定

`keywords.txt`に検索キーワードを設定してください。

```text
例：桜島
　　鹿児島市
　　霧島市
```

1行につき1キーワードを設定してください。

---

### 3. 部局名－インデックスツリー番号対応表作成

`departments.txt`

　本ファイルは、API情報から部局名を抽出する際に必要となる、部局名とインデックスツリー番号を対応づけるファイルです。本対応表は「Automatic Index Tree Data Acquisition tool」（URL）を用いて自動取得可能です。また、以下例のとおり，インデックスツリーごとのページのURL末尾から手動で取得することも可能です。


#### インデックスツリー番号例

```
https://ir.kagoshima-u.ac.jp/search?page=1&size=50&sort=custom_sort&search_type=2&q=46 ← ここの番号
```

上記番号を各学部・文献種別（例：紀要論文や学術誌論文）等すべてのインデックスツリー番号を取得ください。

#### ツリー構造例

```text
法文学部 45
├─ 学術誌論文 66
├─ 紀要論文 46
└─ 科研費報告 96
```

#### departments.txt 記載例

```text
法文学部:45,66,46,96
教育学部:41,158,42,63
```

---

### 4. 部局名－分野名対応表作成

`fields.txt`

部局名を分野名へ変換するための対応表です。上記3で取得した部局名に対応するように表を作成してください。

#### 記載例

```text
医学部:医歯学系
農学部:農水産学系
```

---

## 処理フロー

```text
  環境ファイル読込
        ↓
   キーワード読込
        ↓
     検索実行
        ↓
    URL一覧取得
        ↓
    API詳細取得
        ↓
     差分判定
        ↓
     CSV更新
        ↓
    Excel出力
```

---

## 実行方法

### 1. Python起動

### 2. 作業フォルダへ移動

例：保存先フォルダをご指定ください。
```bash
cd C:/kgos/hp
```

### 3. プログラム実行

```bash
python run_meta_collector.py
```

---

## 詳細仕様

### URL一覧取得機能

検索URL例：

```text
{機関リポジトリURL}/search?page=1&size=50&sort=custom_sort&q={keyword}
```

仕様：

- 1ページ50件取得
- 検索結果がなくなるまで巡回
- URL取得完了後にAPI取得を実行

#### リトライ機能

通信エラー時：

- 10秒待機
- 再試行（1回）

---

### API取得機能

取得URL例：

```text
{機関リポジトリURL}/api/records/{id}
```

取得項目：

- レコードID
- 更新日時
- 著者
- 所属
- 発行年
- 文献種別

#### APIリトライ

取得失敗時：

| 回数 | 待機時間 |
|--------|--------|
| 1回目 | 5秒 |
| 2回目 | 7秒 |
| 3回目 | 10秒 |

3回失敗した場合はエラーログへ出力します。

#### エラーログ例

```text
日時: 2026-07-24 15:10:23
グループ: 保健学研究科
URL: https://ir.kagoshima-u.ac.jp/records/12345
エラー種別: ReadTimeout
内容: HTTPSConnectionPool(host='ir.kagoshima-u.ac.jp', port=443): Read timed out.
```

---

## 差分管理

検索結果は `all_result.csv` に保存され，次回取得の際の差分取得で使用します。

### 新規追加

CSVに存在しないID

→ 「追加」

### 更新

`updated` が変更されているID

→ 「更新」

### 削除

前回存在したが今回存在しないID

→ 削除

---

## データ保全機能

URL取得成功後にAPI取得が失敗した場合は、誤削除を防ぐため削除判定を停止します。

---

## 並列取得

文献詳細情報の取得には以下を利用しています。

```python
ThreadPoolExecutor(max_workers=5)
```

### 推奨設定

サーバ負荷を考慮し、

```python
max_workers = 2 ～ 5
```

の範囲で調整してください。

---

## 引用について

本ソースコードを利用した研究成果 等を公表する場合、または改変して再配布する場合は、以下の出典表記をお願いいたします。

```text
KGOS:
https://github.com/kagoshimakgos/KGOS.code/tree/main/Regional%20dataset

（YYYY年MM月DD日取得）
```

---

## ライセンス

ライセンス条件（MITライセンス）の詳細については、配布元リポジトリをご確認ください。

- KGOS.code Repository
  - https://github.com/kagoshimakgos/KGOS.code/tree/main/Regional%20dataset
