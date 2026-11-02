#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把外部源索引合并进本仓库 Packages（多源）。
- 本地 debs/ 里已有同名文件 -> 用本地路径（优先）
- 否则 Filename 改写为该源的上游绝对地址，按需回源
- 按 (Package, Version, Architecture) 去重，先到先得
"""
import os, sys, urllib.request, urllib.parse

# name, Packages 地址, 文件根地址(结尾带斜杠)
SOURCES = [
    ("mowang", "https://mowang7426.github.io/mowang/Packages",
     "https://raw.githubusercontent.com/mowang7426/mowang/main/debs/"),
    ("byg", "https://byg.iosios.net/Packages",
     "https://byg.iosios.net/debs/"),
]

CACHE_DIR = "/tmp"

def fetch(url):
    fn = os.path.join(CACHE_DIR, "ext_" + urllib.parse.quote(url, safe="")[-60:].replace("/", "_"))
    if os.path.isfile(fn) and os.path.getsize(fn) > 500:
        return open(fn, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=90) as r:
        raw = r.read()
    txt = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    open(fn, "w", encoding="utf-8").write(txt)
    return txt

def fields(rec):
    d = {}
    for line in rec.split("\n"):
        if line.startswith(" ") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip().lower()] = v.strip()
    return d

def basename(fn):
    n = fn.strip()
    n = n.split("?")[0]
    n = n.rstrip("/").split("/")[-1]
    return n

def main():
    local = open("Packages", encoding="utf-8", errors="replace").read() if os.path.isfile("Packages") else ""
    seen = set()
    for rec in local.split("\n\n"):
        f = fields(rec)
        if "package" in f:
            seen.add((f.get("package"), f.get("version"), f.get("architecture")))

    have = set(os.listdir("debs")) if os.path.isdir("debs") else set()

    for name, url, base in SOURCES:
        try:
            up = fetch(url)
        except Exception as e:
            print("  [%s] 拉取失败: %s" % (name, e))
            continue

        out, added, dup, loc = [], 0, 0, 0
        for rec in up.split("\n\n"):
            rec = rec.strip("\n")
            if not rec.strip():
                continue
            f = fields(rec)
            if "package" not in f or "filename" not in f:
                continue
            key = (f.get("package"), f.get("version"), f.get("architecture"))
            if key in seen:
                dup += 1
                continue

            fn = basename(f["filename"])
            newfn = None
            if fn in have:
                newfn = "Filename: debs/" + fn
                loc += 1
            else:
                newfn = "Filename: " + base + urllib.parse.quote(fn)

            lines, done = [], False
            for line in rec.split("\n"):
                if line.startswith("Filename:") and not done:
                    lines.append(newfn); done = True
                else:
                    lines.append(line)
            if not done:
                continue
            out.append("\n".join(lines))
            seen.add(key)
            added += 1

        if out:
            with open("Packages", "a", encoding="utf-8") as fh:
                fh.write("\n")
                fh.write("\n\n".join(out))
                fh.write("\n")
        print("  [%s] 合并 %d 条 (本地命中 %d, 重复跳过 %d)" % (name, added, loc, dup))
    return 0

if __name__ == "__main__":
    sys.exit(main())
