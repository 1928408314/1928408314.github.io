#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把外部源(mowang)的包索引合并进本仓库 Packages。
- 本地 debs/ 里已有的同名文件 -> 用本地路径（优先）
- 否则 Filename 改写为上游 raw 绝对地址，按需回源下载
- 按 (Package, Version, Architecture) 去重
"""
import os, sys, urllib.request, urllib.parse

UPSTREAM = "https://mowang7426.github.io/mowang/Packages"
RAW_BASE = "https://raw.githubusercontent.com/mowang7426/mowang/main/debs/"
CACHE = "/tmp/mowang_Packages.cache"

def fetch():
    if os.path.isfile(CACHE) and os.path.getsize(CACHE) > 1000:
        return open(CACHE, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(UPSTREAM, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        txt = r.read().decode("utf-8", "replace")
    open(CACHE, "w", encoding="utf-8").write(txt)
    return txt

def fields(rec):
    d = {}
    for line in rec.split("\n"):
        if line.startswith(" ") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip().lower()] = v.strip()
    return d

def main():
    local = open("Packages", encoding="utf-8", errors="replace").read() if os.path.isfile("Packages") else ""
    seen = set()
    for rec in local.split("\n\n"):
        f = fields(rec)
        if "package" in f:
            seen.add((f.get("package"), f.get("version"), f.get("architecture")))

    have = set()
    if os.path.isdir("debs"):
        have = set(os.listdir("debs"))

    try:
        up = fetch()
    except Exception as e:
        print("  [merge] 拉取上游失败: %s" % e)
        return 0

    out = []
    added = 0
    skipped_local = 0
    skipped_dup = 0
    for rec in up.split("\n\n"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        f = fields(rec)
        if "package" not in f or "filename" not in f:
            continue
        key = (f.get("package"), f.get("version"), f.get("architecture"))
        if key in seen:
            skipped_dup += 1
            continue

        fn = f["filename"]
        name = fn.split("/")[-1]
        lines = []
        replaced = False
        for line in rec.split("\n"):
            if line.startswith("Filename:") and not replaced:
                if name in have:
                    lines.append("Filename: debs/" + name)
                    skipped_local += 1
                else:
                    lines.append("Filename: " + RAW_BASE + urllib.parse.quote(name))
                replaced = True
            else:
                lines.append(line)
        if not replaced:
            continue
        out.append("\n".join(lines))
        seen.add(key)
        added += 1

    if out:
        with open("Packages", "a", encoding="utf-8") as fh:
            fh.write("\n")
            fh.write("\n\n".join(out))
            fh.write("\n")
    print("  [merge] 合并 %d 条 (本地命中 %d, 重复跳过 %d)" % (added, skipped_local, skipped_dup))
    return 0

if __name__ == "__main__":
    sys.exit(main())
