import argparse
import json
from pathlib import Path

import requests
import time
from datetime import datetime


EXCLUDE_ROOT_NAMES = [
    "掲載誌一覧",
    "List of Journals"
]

DEFAULT_DOMAINS_FILE = "indextree_domains.txt"

API_PATH = "/api/tree?action=browsing"

MAX_RETRY = 4  # 初回 + リトライ3回
RETRY_WAITS = [5, 7, 10]


# ------------------------------------------------------------
# 機関一覧ファイルの読み込み
# ------------------------------------------------------------
def load_institutions(domains_file: str) -> dict:

    path = Path(domains_file)

    if not path.exists():
        raise FileNotFoundError(
            f"機関一覧ファイルが見つかりません: {domains_file}"
        )

    institutions = {}

    for lineno, raw_line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1
    ):

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if ":" not in line:

            print(
                f"[警告] "
                f"{domains_file}:{lineno} "
                f"行の形式が不正なためスキップします -> "
                f"{raw_line!r}"
            )

            continue

        name, domain = line.split(":", 1)

        name = name.strip()
        domain = domain.strip()

        domain = (
            domain
            .replace("https://", "")
            .replace("http://", "")
            .strip("/")
        )

        if not name or not domain:

            print(
                f"[警告] "
                f"{domains_file}:{lineno} "
                f"機関名またはドメインが空のためスキップします -> "
                f"{raw_line!r}"
            )

            continue

        url = f"https://{domain}{API_PATH}"

        institutions[name] = url

    return institutions


# ------------------------------------------------------------
# ツリーAPI取得
# ------------------------------------------------------------
def fetch_tree(url: str) -> list:

    headers = {
        "Accept-Language": "ja"
    }

    resp = requests.get(
        url,
        headers=headers,
        timeout=30,
        allow_redirects=False
    )

    if resp.status_code != 200:

        raise requests.HTTPError(
            f"HTTP {resp.status_code}"
        )

    return resp.json()


# ------------------------------------------------------------
# ID取得
# ------------------------------------------------------------
def get_id(node: dict):

    raw = node.get(
        "id",
        node.get("cid")
    )

    if raw is None:
        return None

    try:
        return int(raw)

    except (TypeError, ValueError):
        return raw


# ------------------------------------------------------------
# 配下全ID取得
# ------------------------------------------------------------
def collect_all_ids(node):

    ids = []

    nid = get_id(node)

    if nid is not None:
        ids.append(nid)

    for child in node.get("children", []):
        ids.extend(
            collect_all_ids(child)
        )

    return ids


# ------------------------------------------------------------
# トップレベルごとのID収集
# ------------------------------------------------------------
def extract_department_ids(
    tree,
    exclude_names=None
):

    exclude_names = {
        x.lower()
        for x in (exclude_names or [])
    }

    result = {}

    for top_node in tree:

        name = (
            top_node.get("name")
            or
            top_node.get("value")
        )

        if not name:
            continue

        # 除外対象をスキップ
        if name.lower() in exclude_names:
            continue

        ids = collect_all_ids(
            top_node
        )

        if name in result:

            result[name].extend(ids)

            result[name] = list(
                dict.fromkeys(
                    result[name]
                )
            )

        else:

            result[name] = ids

    return result


# ------------------------------------------------------------
# 出力整形
# ------------------------------------------------------------
def format_output(
    dept_ids: dict
) -> str:

    lines = []

    for name, ids in dept_ids.items():

        ids_str = ",".join(
            str(i)
            for i in ids
        )

        lines.append(
            f"{name}:{ids_str}"
        )

    return "\n".join(lines)


# ------------------------------------------------------------
# エラーログ
# ------------------------------------------------------------
def write_error_log(
    errors,
    out_dir="."
):

    if not errors:
        return

    log_path = (Path(out_dir)/ "error_log.txt")

    lines = []

    for err in errors:

        lines.extend([
            f"日時: {err['datetime']}",
            f"グループ: {err['label']}",
            f"URL: {err['url']}",
            f"エラー: {err['error']}",
            "",
            "-" * 40,
            ""
        ])

    log_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(
        f"[ERROR] "
        f"{log_path} に "
        f"{len(errors)} 件出力"
    )


# ------------------------------------------------------------
# 1機関処理
# ------------------------------------------------------------
def process_institution(
    label: str,
    url: str,
    exclude_names=None,
    out_dir="."
):

    print(
        f"[{label}] "
        f"取得中: {url}"
    )

    tree = fetch_tree(url)

    dept_ids = extract_department_ids(
        tree,
        exclude_names=exclude_names
    )

    text = format_output(
        dept_ids
    )

    out_path = (
        Path(out_dir)
        / "departments.txt"
    )

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    out_path.write_text(
        text,
        encoding="utf-8"
    )

    print(
        f"[{label}] "
        f"出力完了: "
        f"{out_path} "
        f"({len(dept_ids)}組織)"
    )

    return out_path


# ------------------------------------------------------------
# メイン処理
# ------------------------------------------------------------
def main():

    parser = argparse.ArgumentParser(
        description=
        "機関リポジトリのツリーJSON(action=browsing)から部局別IDを抽出する"
    )

    parser.add_argument(
        "--domains-file",
        default=DEFAULT_DOMAINS_FILE,
        help=
        f"機関一覧ファイル "
        f"(既定: {DEFAULT_DOMAINS_FILE})"
    )

    parser.add_argument(
        "--url",
        help=
        "単一機関用API URL"
    )

    parser.add_argument(
        "--label",
        default="機関",
        help=
        "出力ファイル用ラベル"
    )

    parser.add_argument(
        "--out-dir",
        default=".",
        help=
        "出力ディレクトリ"
    )

    parser.add_argument(
        "--include-journal-list",
        action="store_true",
        help=
        "掲載誌一覧も処理する"
    )

    args = parser.parse_args()

    exclude_names = (
        []
        if args.include_journal_list
        else EXCLUDE_ROOT_NAMES
    )

    if args.url:

        process_institution(
            args.label,
            args.url,
            exclude_names=exclude_names,
            out_dir=args.out_dir
        )

        return

    try:

        institutions = load_institutions(
            args.domains_file
        )

    except FileNotFoundError as e:

        print(
            f"[エラー] {e}"
        )

        return

    if not institutions:

        print(
            f"[エラー] "
            f"{args.domains_file} "
            f"から有効な機関情報を読み込めませんでした。"
        )

        return

    errors = []

    for label, url in institutions.items():

        success = False

        for retry in range(MAX_RETRY):

            try:

                process_institution(
                    label,
                    url,
                    exclude_names=exclude_names,
                    out_dir=args.out_dir
                )

                success = True
                break


            except requests.RequestException as e:

                print(
                    f"[{label}] "
                    f"取得エラー "
                    f"(試行 {retry + 1}/{MAX_RETRY}) : "
                    f"{e}"
                )

                if retry < len(RETRY_WAITS):

                    wait_sec = RETRY_WAITS[retry]

                    print(
                        f"{wait_sec}秒後に再試行します"
                    )

                    time.sleep(wait_sec)

                else:

                    errors.append({
                        "datetime":
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        "label": label,
                        "url": url,
                        "error": str(e)
                    })


            except json.JSONDecodeError as e:

                print(
                    f"[{label}] "
                    f"JSON解析エラー "
                    f"(試行 {retry + 1}/{MAX_RETRY}) : "
                    f"{e}"
                )

                if retry < len(RETRY_WAITS):

                    wait_sec = RETRY_WAITS[retry]

                    print(
                        f"{wait_sec}秒後に再試行します"
                    )

                    time.sleep(wait_sec)

                else:

                    errors.append({
                        "datetime":
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        "label": label,
                        "url": url,
                        "error":
                            f"JSON解析エラー: {e}"
                    })


            except Exception as e:

                print(
                    f"[{label}] "
                    f"予期しないエラー "
                    f"(試行 {retry + 1}/{MAX_RETRY}) : "
                    f"{e}"
                )

                if retry < len(RETRY_WAITS):

                    wait_sec = RETRY_WAITS[retry]

                    print(
                        f"{wait_sec}秒後に再試行します"
                    )

                    time.sleep(wait_sec)

                else:

                    errors.append({
                        "datetime":
                            datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        "label": label,
                        "url": url,
                        "error":
                            f"予期しないエラー: {e}"
                    })

        if not success:
            print(f"[{label}] 失敗")

    write_error_log(
        errors,
        out_dir=args.out_dir
    )


if __name__ == "__main__":
    main()