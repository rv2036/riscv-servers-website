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
PAGES = ["", "servers/", "chips/", "software/", "data/", "news/", "blog/"]


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

    # 5) RSS：feed 齐全、条目字段合法、guid 唯一且不可当链接
    FEEDS = ["index.xml", "news/index.xml", "data/index.xml", "blog/index.xml"]
    rss_missing = 0
    feed_counts = {}
    for lang in LANGS:
        base = "" if lang == "zh" else lang + "/"
        for feed in FEEDS:
            path = os.path.join(PUB, base + feed)
            if not os.path.isfile(path):
                errors.append(f"缺 RSS: /{base}{feed}")
                rss_missing += 1
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                xml = fh.read()
            items = re.findall(r"<item>(.*?)</item>", xml, re.S)
            feed_counts[(lang, feed)] = len(items)
            if len(items) > 40:
                errors.append(f"/{base}{feed} 条目超过 40 条上限（{len(items)}）")
            guids = re.findall(r"<guid[^>]*>(.*?)</guid>", xml, re.S)
            if len(set(guids)) != len(guids):
                errors.append(f"/{base}{feed} guid 有重复")
            for it in items:
                missing_tag = [t for t in ("title", "link", "guid", "pubDate", "description") if f"<{t}" not in it]
                if missing_tag:
                    errors.append(f"/{base}{feed} 条目缺 {missing_tag}")
                    break
                if 'isPermaLink="false"' not in it:
                    errors.append(f"/{base}{feed} 条目 guid 缺 isPermaLink=false")
                    break
                m = re.search(r"<pubDate>(.*?)</pubDate>", it)
                if m and not re.match(r"^[A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2} [+-]\d{4}$",
                                      m.group(1).strip()):
                    errors.append(f"/{base}{feed} pubDate 格式异常: {m.group(1)[:40]}")
                    break
    # 新闻 feed 必须跟着 news.yaml 的条数（上限 40）
    for lang in LANGS:
        news_n = feed_counts.get((lang, "news/index.xml"), 0)
        if news_n == 0:
            errors.append(f"新闻 RSS 为空: /{' ' if lang == 'zh' else lang + '/'}news/index.xml")
    zh_news = feed_counts.get(("zh", "news/index.xml"), 0)
    zh_home = feed_counts.get(("zh", "index.xml"), 0)
    if zh_home < zh_news:
        errors.append(f"首页 RSS（{zh_home}）少于新闻 RSS（{zh_news}），合并逻辑有误")
    print(f"RSS: 检查 {len(LANGS) * len(FEEDS)} 个 feed，缺失 {rss_missing} 个；"
          f"首页/新闻/数据/博客条目数（zh）= "
          f"{feed_counts.get(('zh','index.xml'),0)}/{feed_counts.get(('zh','news/index.xml'),0)}/"
          f"{feed_counts.get(('zh','data/index.xml'),0)}/{feed_counts.get(('zh','blog/index.xml'),0)}")

    # 6) 每个语言的首页、新闻页、数据页都要在 head 里给出 feed 发现链接
    no_feed_link = 0
    for lang in LANGS:
        base = "" if lang == "zh" else lang + "/"
        for page in ("", "news/", "data/"):
            path = os.path.join(PUB, base, page, "index.html")
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8", errors="ignore") as fh:
                html = fh.read()
            if "application/rss+xml" not in html:
                errors.append(f"页面缺 feed 发现链接: /{base}{page}")
                no_feed_link += 1
    print(f"RSS 发现链接: 检查 {len(LANGS) * 3} 页，缺 {no_feed_link} 页")

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
