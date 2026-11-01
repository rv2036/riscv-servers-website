#!/usr/bin/env python3
"""构建产物自检：页面齐全度矩阵、hreflang、站内链接。

用法（先构建，再跑）：
    make site-check

退出码 1 = 有闸门没过。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "website", "public")

LANGS = ["zh", "en", "ja", "ru", "ko"]
# 每种语言都应存在的页面（相对站点根；zh 在根，其余在 /<lang>/）
PAGES = ["", "servers/", "chips/", "solutions/", "news/", "blog/"]


def page_url(lang, page):
    return "/" + (page if lang == "zh" else f"{lang}/{page}")


def find_file(url):
    """把站内 URL 映射到构建产物里的文件。"""
    p = url.split("#")[0].split("?")[0]
    if not p.startswith("/"):
        return None
    rel = p.lstrip("/")
    cand = [
        os.path.join(PUB, rel),
        os.path.join(PUB, rel, "index.html"),
        os.path.join(PUB, rel + ".html"),
        os.path.join(PUB, rel.rstrip("/") + "/index.html"),
    ]
    for c in cand:
        if os.path.isfile(c):
            return c
    return None


def attr(tag, name):
    m = re.search(name + r'=(?:"([^"]*)"|([^\s>]+))', tag)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def main():
    if not os.path.isdir(PUB):
        print("找不到构建产物目录 website/public，请先 make site")
        return 1

    errors = []

    # 1) 页面齐全度矩阵
    missing = 0
    for lang in LANGS:
        for page in PAGES:
            url = page_url(lang, page)
            if not find_file(url):
                errors.append(f"缺少页面 {url}")
                missing += 1
    print(f"页面矩阵: {len(LANGS)} 语言 × {len(PAGES)} 页，缺失 {missing} 处")

    # 2) hreflang / x-default
    html_files = []
    for dirpath, _dirnames, filenames in os.walk(PUB):
        for fn in filenames:
            if fn.endswith(".html"):
                html_files.append(os.path.join(dirpath, fn))

    no_xdefault = 0
    checked = 0
    for path in html_files:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            html = fh.read()
        # alias 跳转页（meta refresh）不做 hreflang 检查
        if re.search(r'http-equiv=["\']?refresh', html, re.I):
            continue
        checked += 1
        if not re.search(r'hreflang=["\']?x-default', html, re.I):
            errors.append(f"缺 x-default: {os.path.relpath(path, PUB)}")
            no_xdefault += 1
    print(f"hreflang: 检查 {checked} 页，缺 x-default {no_xdefault} 页")

    # 3) 站内链接与静态资源
    link_total = 0
    link_bad = 0
    for path in html_files:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            html = fh.read()
        html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
        html = re.sub(r"<script.*?</script>", "", html, flags=re.S | re.I)
        for tag in re.findall(r"<a\b[^>]*>|<img\b[^>]*>|<link\b[^>]*>|<source\b[^>]*>", html, re.I):
            target = attr(tag, "href") or attr(tag, "src")
            if not target:
                continue
            if target.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
                continue
            link_total += 1
            if not find_file(target):
                # 相对链接按其所在页面路径解析
                base = os.path.relpath(path, PUB).replace("index.html", "")
                resolved = "/" + os.path.normpath(os.path.join(base, target.lstrip("/"))).lstrip("./")
                if not find_file(resolved):
                    errors.append(f"坏链 {target} 于 {os.path.relpath(path, PUB)}")
                    link_bad += 1
    print(f"站内链接: 检查 {link_total} 个，坏链 {link_bad} 个")

    # 4) 新闻数据：URL 必须非空、不重复
    for lang in LANGS:
        p = os.path.join(ROOT, "website", "data", "i18n", lang, "news.yaml")
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8").read()
        urls = re.findall(r"^\s+url:\s*(\S+)\s*$", text, re.M)
        dups = {u for u in urls if urls.count(u) > 1}
        if dups:
            errors.append(f"news.yaml({lang}) 有重复 URL: {sorted(dups)[:3]}")
    print("新闻数据: 重复 URL 检查完成")

    if errors:
        print("\n未通过：")
        for e in errors[:40]:
            print("  ·", e)
        if len(errors) > 40:
            print(f"  … 还有 {len(errors) - 40} 条")
        return 1
    print("\n全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
