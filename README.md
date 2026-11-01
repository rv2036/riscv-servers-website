# RISC-V Servers · riscvservers.org

收集、记录并展示全世界范围内 **RISC-V 服务器**的最新消息与进展，并把它们传递给全世界的读者。

站点：<https://riscvservers.org> · 镜像仓库：<https://github.com/rv2036/riscv-servers-website>

## 五个栏目

| 栏目 | 路径 | 收什么 |
| --- | --- | --- |
| **Servers** | `/servers/` | 服务器级整机、主板、工作站、云实例与 HPC 集群，同一型号只留一条 |
| **Chips** | `/chips/` | 服务器级 SoC 与 CPU IP：核数、ISA、工艺、厂商公布性能 |
| **Solutions** | `/solutions/` | 发行版、虚拟化、容器、HPC、数据库与推理服务，分清「已经能跑」与「还差什么」 |
| **News** | `/news/` | 每天检索到的新闻，一条摘要 + 原文 URL |
| **Blog** | `/blog/` | 站主自己写的长文 |

## 收录口径

- 每条都要指得回**一手来源**：厂商产品页、规格书、发布说明或官方仓库
- 媒体转述标明是转述，不与一手信息混写
- 查不到的参数留空，不猜；性能数字注明是厂商公布还是第三方实测
- 只为**确认过规格**的产品建条目，不为传闻建条目
- 新闻只给摘要与链接，不做二次解读

`LX500` 与 `V100` 两条带「甲辰计划主理人验证过」徽标，表示主理人本人核对过一手资料。

## 站点结构

```
website/
  hugo.toml                 # 五语言：zh（根）/ en / ja / ru / ko
  content/<lang>/           # 每种语言 6 页：首页、servers、chips、solutions、news、blog
  data/i18n/<lang>/         # servers.yaml / chips.yaml / solutions.yaml / news.yaml
  i18n/<lang>.toml          # 界面文案
  layouts/                  # 布局（servers/chips/solutions/news 走同名 layout）
  assets/css/main.css       # 明暗双主题，跟随系统并可手动切换
  static/                   # favicon.svg、CNAME
scripts/check_site.py       # 页面矩阵 / hreflang / 站内链接 / 新闻去重
.github/workflows/pages.yml # GitHub Actions：构建 + 自检 + 部署
```

数据在 `data/i18n/<lang>/` 里，但 Hugo 的 `data/` 没有语言维度，靠 `layouts/partials/site-data.html` 按当前语言取、缺则回退中文。

## 本地构建

```sh
make site         # 构建到 website/public
make site-serve   # 预览 http://localhost:1315/
make site-check   # 构建 + 自检（页面矩阵 / hreflang / 站内链接 / 新闻去重）
```

需要 Hugo **0.147.9 extended**。

## 加一条内容

**新闻**（`website/data/i18n/zh/news.yaml`，其余语言同结构）：

```yaml
items:
  - date: "2026-10-31"        # 必须真实
    title: "标题"
    summary: "两句话讲清发生了什么、对 RISC-V 服务器意味着什么"
    source: "厂商 / 媒体名"
    url: "https://…"          # 必须实测能打开
    vendors: ["涉及厂商"]
    tags: ["芯片发布"]
    importance: high          # high / medium / low
```

**服务器 / 芯片 / 解决方案**：改对应的 `servers.yaml` / `chips.yaml` / `solutions.yaml`。`status` 与 `maturity` 用程序值（`production` / `sampling` / `announced` / `eol`，`production` / `limited` / `experimental` / `demo`），由 `i18n/<lang>.toml` 翻成各语言显示文案。

新增条目只改中文数据是不够的：其余四种语言的同名文件也要有对应条目，否则那些语言的页面会显示中文（回退），`make site-check` 的新闻去重也会按语言分别检查。

## 部署

`main` / `master` 分支 push 后由 GitHub Actions 构建并部署到 GitHub Pages。**部署只在主仓 `rv2036/riscv-servers-website` 执行**：下游 fork 继承同一个 workflow 但没有 Pages 站点与部署凭据，`configure-pages` 与 `deploy` 作业在这些仓库里会被跳过；构建与 `scripts/check_site.py` 照跑，所以 fork 改内容仍能拿到「能不能构建、链接有没有坏」的信号。

站点侧需要在仓库 Settings → Pages 里把 Source 设为 **GitHub Actions**，并配置自定义域名 `riscvservers.org`（`website/static/CNAME` 已带）。

## 许可

本站文字以 **CC BY-SA 4.0** 发布。站内图表与图标为自绘 SVG，不使用网络字体与第三方图片。
