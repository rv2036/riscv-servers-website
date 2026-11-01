all:
	@echo "RISC-V Servers"

# ---- 站点（riscvservers.org） ----
site:
	hugo --source website --gc --minify --cleanDestinationDir

site-serve:
	hugo server --source website --disableFastRender --port 1315

site-check: site
	python3 scripts/check_site.py

site-clean:
	rm -rf website/public website/resources

help:
	@echo "type an action:"
	@echo "  site        构建站点到 website/public"
	@echo "  site-serve  本地预览 http://localhost:1315/"
	@echo "  site-check  构建后自检：页面矩阵、hreflang、站内链接、新闻去重"
	@echo "  site-clean  清掉构建产物"

.PHONY: all help site site-serve site-check site-clean
