# 機関リポジトリキーワード検索・収集システム

## 1.概要
本システムは、大学機関リポジトリに登録された研究成果を対象として、指定したキーワードで全文検索を実施し、検索結果から文献情報およびメタデータを自動収集するためのプログラムです。収集したデータは以下のファイルとして出力されます。
- `oai_result.csv`
- `oai_result_by_area.xlsx`
- `error_log.txt`

本システムは検索キーワードを変更することで、多様な調査・分析用途に利用できます。

### 利用例

#### 地域研究
- 鹿児島市
- 霧島市
- 桜島

#### キーワード例
- 生成AI
- LLM

---

## 2.汎用性

本システムは鹿児島大学機関リポジトリ向けに作成されていますが、検索URLおよびAPI URLを変更することで、他大学や研究機関のリポジトリにも応用可能です。

## 現在設定されているURL

### 検索画面
```text
https://ir.kagoshima-u.ac.jp/search/
```
### API
```text
https://ir.kagoshima-u.ac.jp/api/records/
```

## 他機関へ適用する場合

以下の部分を各機関のURLへ変更してください。

```text
https://ir.kagoshima-u.ac.jp/
https://ir.kagoshima-u.ac.jp/api/records/
↓
各機関リポジトリのURL
```

---

## 3.必要環境

### 3.1. OS

推奨環境

```text
Windows 11
```

### 3.2. Google Chrome

Seleniumを利用して検索を実施するため、最新版のGoogle Chromeをインストールしてください。

https://www.google.com/chrome/

### 3.3. Python

推奨バージョン

```text
Python 3.11以上
```

#### Pythonのインストール

Python公式サイトからインストールしてください。

https://www.python.org

※ インストール時に **Add Python to PATH** にチェックを入れてください。

#### バージョン確認

```bash
python --version
```

#### 必要ライブラリのインストール

```bash
pip install selenium pandas requests openpyxl
```

#### インストール確認

```bash
pip list
```

以下が表示されれば準備完了です。

```text
selenium
pandas
requests
openpyxl
```

---

# 4.事前準備

## 1. 検索キーワードファイル

検索対象となるキーワードを1行1件で記載します。

今回は，ファイル名 `areas.txt` を利用していますが、用途に応じて変更可能です。

### 例：areas.txt

```text
桜島
鹿児島市
霧島市
```

---

## 2. 部局識別番号表.txt

リポジトリのインデックスツリー情報から取得した `sets番号` を部局名称へ変換するテーブルです。

※ 各機関ごとに設定が必要です。

### 例

```text
医学部:123,456
農学部:789
```

---

## 3. 部局中分類変換.txt

部局名を中分類へ変換するためのテーブルです。

### 例

```text
医学部:医歯学系
農学部:農水産学系
```

---

# 出力ファイル

| ファイル名 | 内容 |
|------------|------|
| oai_result.csv | 差分管理用・検索結果全件一覧 |
| oai_result_by_area.xlsx | キーワード別一覧 |
| error_log.txt | エラーログ |

---

# 処理フロー

```text
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

# 処理詳細

## 1. URL一覧取得機能

### URL例

```text
https://ir.kagoshima-u.ac.jp/search?page=1&size=50&sort=custom_sort&q=桜島
```

### 処理内容

- 1ページあたり50件取得
- ページを順次巡回
- 検索結果がなくなるまで継続

```text
1ページ
 ↓
2ページ
 ↓
3ページ
 ↓
・・・
```

URL取得完了後にAPI詳細取得へ移行します。

### URL取得リトライ機能

通信障害等により取得できなかった場合

```text
10秒待機
↓
再取得
```

を実施します。

---

## 2. API取得機能

### API例

```text
https://機関リポジトリURL/api/records/{id}
```

### 主な取得項目

- レコードID
- 更新日時
- 著者
- 所属
- 発行年
- 文献種別
- その他メタデータ

### APIリトライ機能

取得失敗時は以下の待機時間で最大3回リトライします。

```text
1回目：5秒
2回目：7秒
3回目：10秒
```

それでも失敗した場合はエラーログへ出力します。

### エラーログ例

```text
日時: 2026-07-24 15:10:23
グループ: 保健学研究科
URL:https://ir.kagoshima-u.ac.jp/records/12345
エラー種別: ReadTimeout
内容: HTTPSConnectionPool(host='ir.kagoshima-u.ac.jp', port=443): Read timed out.
```

---

# 差分管理

取得結果は `oai_result.csv` に保存され、前回結果との差分を自動判定します。

## 新規追加

CSVに存在しないIDを追加登録します。

## 更新

`updated` が変更されていた場合は更新として上書きします。

## 削除

前回存在し、今回取得できなかったIDは削除対象として除外します。

---

# データ保全機能

URL一覧は取得できたものの、API取得に失敗した場合は削除判定を停止します。

これにより、一時的な通信障害による誤削除を防止します。

---

# 並列取得

文献詳細取得には以下を利用しています。

```python
ThreadPoolExecutor(max_workers=5)
```

現在は5件同時取得です。

利用環境やサーバ負荷を考慮し、必要に応じて調整してください。

---

# 利用部門例

- 図書館
- 学術情報課
- IR担当部署
- 研究推進部門
- 研究戦略部門
- 地域連携部門
- URA部門

---

# 各機関向けカスタマイズ箇所

## 1. 検索URL

変更箇所

```python
# 各機関向けにURLをご変更ください
url = f"https://ir.kagoshima-u.ac.jp/search?page={page}&size=50&sort=custom_sort&q={q}"
```

変更例

```text
https://xxxx/search
```

---

## 2. API URL

変更箇所

```python
def get_detail_api(
    url,
    sets_map,
    group_name
):
    try:
        record_id = url.split("/")[-1]
        api_url = f"https://ir.kagoshima-u.ac.jp/api/records/{record_id}"
```

変更例

```text
https://xxxx/api/records
```

---

## 3. メタデータ項目

各機関のデータ構造に合わせて変更してください。

例

- 著者
- 作成日
- 資源タイプ
- 所属
- 発行年

など

---

# ライセンス

本ソースコードは **MIT License** の下で公開されています。

MIT Licenseの範囲内で、商用・非商用を問わず利用、改変、再配布が可能です。

---

# 引用について

本ソースコードを利用した研究成果の公表、または改変版の再配布を行う場合は、以下の出典表記にご協力ください。

```text
KGOS.code Regional Dataset
KGOS:https://github.com/kagoshimakgos/KGOS.code/tree/main/Regional%20dataset（参照日：YYYY年MM月DD日）
```

### 推奨引用例

```text
KGOS:「KGOS.code Regional Dataset」.
https://github.com/kagoshimakgos/KGOS.code/tree/main/Regional%20dataset（参照日：YYYY年MM月DD日）
```
