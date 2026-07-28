from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

import requests
import pandas as pd
import time
import os

from datetime import datetime

from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor

BASE_URL = ""


# =========================
# ✅ 既存CSV読み込み
# =========================
def load_existing_data(filepath="all_result.csv"):
    if os.path.exists(filepath):
        return pd.read_csv(filepath, encoding="utf-8-sig")
    else:
        return pd.DataFrame()


# =========================
# ✅ 更新日時ベース差分判定
# =========================
def needs_update(existing_df, new_item):
    if existing_df.empty:
        return True

    # 初回対応（updated列がない）
    if "updated" not in existing_df.columns:
        return True

    old = existing_df[existing_df["id"].astype(str)== str(new_item["id"])]

    if old.empty:
        return True  # 新規

    old = old.iloc[0]

    old_updated = str(old.get("updated", ""))
    new_updated = str(new_item.get("updated", ""))

    return new_updated > old_updated


# =========================
# ✅ 機関URL読込
# =========================
def load_repositories(filepath="base_url.txt"):

    repositories = []

    with open(filepath, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            # コメント行・空行除外
            if not line or line.startswith("#"):
                continue

            if ":" in line:

                institution, url = line.split(":", 1)

                repositories.append({
                    "institution": institution.strip(),
                    "url": url.strip().rstrip("/")
                })

    return repositories


# =========================
# ✅ sets → Department Tree Structure
# =========================
def load_sets_table(filepath="departments.txt"):
    sets_map = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                dept, ids = line.strip().split(":", 1)
                for i in ids.split(","):
                    i = i.strip()
                    if i:
                        sets_map[i] = dept.strip()
    return sets_map


# =========================
# ✅ 部局 → 系 変換
# =========================
def load_department_category(filepath="fields.txt"):
    dept_cat_map = {}
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                dept, cat = line.strip().split(":", 1)
                dept_cat_map[dept.strip()] = cat.strip()
    return dept_cat_map


# =========================
# ✅ エラーログ出力
# =========================
def write_error_log(
    group_name,
    url,
    error
):

    with open(
        "error_log.txt",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"日時: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        )

        f.write(
            f"グループ: {group_name}\n"
        )

        f.write(
            f"URL:{url}\n"
        )

        f.write(
            f"エラー種別:{type(error).__name__}\n"
        )

        f.write(
            f"内容:{str(error)}\n"
        )

        f.write(
            "-" * 80 + "\n"
        )


# =========================
# ✅ 文献種別変換
# =========================
def convert_type(rt):
    mapping = {
        "article": "記事",
        "book": "図書",
        "conference output": "会議資料",
        "conference paper": "会議発表論文",
        "dataset": "データセット",
        "departmental bulletin paper": "紀要論文",
        "doctoral thesis": "博士論文",
        "journal article": "学術雑誌論文",
        "learning object": "教材",
        "other": "その他",
        "research report": "研究報告書",
        "thesis": "学位論文",
        "video": "動画資料"
    }
    return mapping.get(rt, rt)


# =========================
# ✅ attribute_name取得
# =========================
def find_by_attr(meta, name):
    for v in meta.values():
        if isinstance(v, dict) and v.get("attribute_name") == name:
            return v.get("attribute_value_mlt", [])
    return []


# =========================
# ✅ URL取得
# =========================
def get_urls(keyword):
    all_results = []
    page = 1
    q = quote(keyword)

    while True:
        print(f"  → ページ {page} 取得中...")

        url = f"{BASE_URL}/search?page={page}&size=50&sort=custom_sort&q={q}"
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                lambda d: len(d.find_elements(By.XPATH, "//a[contains(@href,'records')]")) > 0
            )

            time.sleep(2)
            links = driver.find_elements(By.XPATH, "//a[contains(@href,'records')]")

        except TimeoutException:

            print(f"⚠️ ページ {page} 取得失敗")
            print("10秒後に再試行します")

            time.sleep(10)

            try:
                driver.get(url)

                WebDriverWait(driver, 15).until(
                    lambda d: len(
                        d.find_elements(
                            By.XPATH,
                            "//a[contains(@href,'records')]"
                        )
                    ) > 0
                )

                links = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href,'records')]"
                )

                print("✅ 再取得成功")

            except TimeoutException:

                print(
                    f" ↓{page}ページ取得しAPI取得へ"
                )

                break

        page_data = []

        for link in links:
            page_url = link.get_attribute("href")
            title = link.text.strip()

            if page_url and title:
                record = {
                    "keyword": keyword,
                    "title": title,
                    "url": page_url
                }
                page_data.append(record)
                all_results.append(record)

        print(f"🔵 {len(page_data)}件取得")

        page += 1
        time.sleep(2)

    return all_results


# =========================
# ✅ 詳細取得（更新日時追加）
# =========================
def get_detail_api(
    url,
    sets_map,
    group_name
):
    try:
        record_id = url.split("/")[-1]
        api_url = f"{BASE_URL}/api/records/{record_id}"

        last_error = None

        for retry_no, sleep_sec in enumerate(
            [5, 7, 10],
            start=1
        ):

            try:

                r = requests.get(
                    api_url,
                    timeout=15
                )

                r.raise_for_status()

                data = r.json()

                break

            except Exception as e:

                last_error = e

                print(
                    f"⚠️ API取得失敗 "
                    f"({retry_no}/3)"
                )

                if retry_no < 3:

                    print(
                        f"{sleep_sec}秒後に再試行"
                    )

                    time.sleep(sleep_sec)

        else:

            raise last_error

        meta = data.get("metadata", {})

        # ✅ 更新日時取得
        updated = data.get("updated", "")

        # 著者
        author = ""
        creators = find_by_attr(meta, "著者")
        names = []

        for c in creators:

            if not isinstance(c, dict):
                continue

            creator_names = c.get(
                "creatorNames"
            ) or []

            if isinstance(
                creator_names,
                str
            ):

                creator_names = [{
                    "creatorName":
                        creator_names
                }]

            elif isinstance(
                creator_names,
                dict
            ):

                creator_names = [
                    creator_names
                ]

            for n in creator_names:

                if not isinstance(
                    n,
                    dict
                ):
                    continue

                creator_name = (
                    n.get(
                        "creatorName",
                        ""
                    )
                    .replace(",", " ")
                    .strip()
                )

                if creator_name:

                    names.append(
                        creator_name
                    )

        if len(names) == 1:
            author = names[0]
        elif len(names) >= 2:
            author = f"{names[0]} 他"

        # 年
        year = ""

        # パターン１
        dates = find_by_attr(meta, "作成日")

        for d in dates:

            dt = d.get(
                "subitem_date_issued_datetime",
                ""
            )

            if dt:

                year = dt[:4]

                break


        # パターン２
        if not year:

            biblio = find_by_attr(
                meta,
                "書誌情報"
            )

            for b in biblio:

                if not isinstance(b, dict):
                    continue

                issue_dates = b.get(
                    "bibliographicIssueDates"
                ) or []

                if isinstance(issue_dates, dict):
                    issue_dates = [issue_dates]

                elif isinstance(issue_dates, str):

                    issue_dates = [{
                        "bibliographicIssueDate":
                            issue_dates
                    }]

                for issue in issue_dates:

                    if not isinstance(issue, dict):
                        continue

                    dt = issue.get(
                        "bibliographicIssueDate",
                        ""
                    )

                    if dt:

                        year = dt[:4]

                        break

                if year:
                    break

        # パターン３
        if not year:

            granted = find_by_attr(
                meta,
                "学位授与年月日"
            )

            for g in granted:

                if not isinstance(
                    g,
                    dict
                ):
                    continue

                dt = g.get(
                    "subitem_dategranted",
                    ""
                )

                if dt:

                    year = dt[:4]

                    break

        # 部局
        sets = meta.get("_oai", {}).get("sets", [])

        departments = []
        for s in sets:
            if s in sets_map:
                departments.append(sets_map[s])

        # カンマ区切りで連結
        department = "，".join(departments)


        # ----------------------
        # ✅ 部局 → 系 変換
        # ----------------------
        category = ""

        if department:
            dept_list = [d.strip() for d in department.split("，")]

            cats = []
            for d in dept_list:
                if d in dept_cat_map:
                    cats.append(dept_cat_map[d])

            category = "，".join(cats)

        # 文献タイプ
        types = find_by_attr(meta, "資源タイプ")
        doc_type = convert_type(types[0].get("resourcetype", "")) if types else ""

        return {
            "id": record_id,
            "url": url,
            "updated": updated,
            "author": author,
            "department": department,
            "category": category,
            "year": year,
            "type": doc_type
        }

    except Exception as e:

        global api_error_count

        api_error_count += 1

        write_error_log(
            group_name=group_name,
            url=url,
            error=e
        )

        print(
            f"❌ API取得失敗: {url}"
        )

        print(
            f"原因: {type(e).__name__}"
        )

        print(
            str(e)
        )

        return {
            "id": "",
            "url": url,
            "updated": ""
        }

# API取得失敗件数
api_error_count = 0

# =========================
# ✅ 並列処理
# =========================
def fetch_detail(item):
    print(item["index"], item["title"])
    item.pop("index", "")
    detail = get_detail_api(item["url"],sets_map,item["keyword"])
    item.update(detail)
    return item


# =========================
# ✅ main
# =========================
driver = webdriver.Chrome()

repositories = load_repositories()

sets_map = load_sets_table()
dept_cat_map = load_department_category()

existing_df = load_existing_data()

updated_rows = []
all_rows = []

with open("keywords.txt", encoding="utf-8") as f:
    keywords = [line.strip() for line in f if line.strip()]

for repo in repositories:

    BASE_URL = repo["url"]
    institution = repo["institution"]

    print(f"\n===== {institution} =====")

    for k in keywords:

        print(f"\n🔍 {k} 検索中...")

        url_list = get_urls(k)

        for i, item in enumerate(url_list):
            item["index"] = f"{i+1}/{len(url_list)}"
            item["institution"] = institution

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(fetch_detail, url_list))

        # ✅ 更新日時で差分判定
        for r in results:

            if r.get("id"):
                all_rows.append(r)

            if r.get("id") and needs_update(existing_df, r):
                updated_rows.append(r)

        # =========================
        # キーワード単位で途中保存
        # =========================

        df_keyword = pd.DataFrame(results)

        excel_file = "result_by_keyword.xlsx"

        if os.path.exists(excel_file):

            with pd.ExcelWriter(
                excel_file,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace"
            ) as writer:

                sheet_name = str(k)[:31]

                df_keyword.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

        else:

            with pd.ExcelWriter(
                excel_file,
                engine="openpyxl"
            ) as writer:

                sheet_name = str(k)[:31]

                df_keyword.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

        print(
            f"✅ キーワード[{k}] 保存完了"
        )


driver.quit()


# =========================
# ✅ 差分統合（追加・削除・更新）
# =========================
all_df = pd.DataFrame(all_rows)

new_df = pd.DataFrame(
    updated_rows,
    columns=[
        "institution",
        "keyword",
        "title",
        "url",
        "id",
        "updated",
        "author",
        "department",
        "category",
        "year",
        "type"
    ]
)

if existing_df.empty:

    merged = new_df

    print(f"✅ 初回取得: {len(merged)}件")

else:

    # ID集合
    existing_ids = set(
        existing_df["id"].astype(str)
    )

    new_ids = set(
        all_df["id"].astype(str)
    )

    # ----------------------------
    # ✅ 追加
    # ----------------------------
    add_ids = new_ids - existing_ids

    df_add = new_df[
        new_df["id"].isin(add_ids)
    ]

    # ----------------------------
    # ✅ 削除
    # ----------------------------
    if api_error_count > 0:

        print(
            f"⚠️ API取得失敗 {api_error_count}件"
        )

        print(
            "⚠️ 削除判定をスキップ"
        )

        delete_ids = set()

    else:

        delete_ids = existing_ids - new_ids

    df_keep = existing_df[
        ~existing_df["id"].isin(delete_ids)
    ]

    # ----------------------------
    # ✅ 更新
    # ----------------------------
    df_update = []

    if "updated" in existing_df.columns:

        for _, row in new_df.iterrows():

            rid = str(row["id"])

            if rid in existing_ids:

                old = existing_df[
                    existing_df["id"].astype(str)
                    == rid
                ].iloc[0]

                old_u = str(
                    old.get("updated", "")
                )

                new_u = str(
                    row.get("updated", "")
                )

                if new_u > old_u:

                    df_update.append(row)

    df_update = pd.DataFrame(df_update)

    # ----------------------------
    # ✅ 更新対象除外
    # ----------------------------
    update_ids = (
        set(df_update["id"])
        if not df_update.empty
        else set()
    )

    df_keep = df_keep[
        ~df_keep["id"].isin(update_ids)
    ]

    # ----------------------------
    # ✅ 最終結合
    # ----------------------------
    merged = pd.concat(
        [
            df_keep,
            df_add,
            df_update
        ],
        ignore_index=True
    )

    print("========== 差分ログ ==========")
    print(f"追加: {len(df_add)}件")
    print(f"更新: {len(df_update)}件")
    print(f"削除: {len(delete_ids)}件")
    print(f"最終件数: {len(merged)}件")
    print("==============================")

output_columns = [
    "institution",
    "keyword",
    "title",
    "url",
    "id",
    "updated",
    "author",
    "department",
    "category",
    "year",
    "type"
]

merged = merged.reindex(columns=output_columns)

merged.to_csv(
    "all_result.csv",
    index=False,
    encoding="utf-8-sig"
)

print("✅ 取得完了")