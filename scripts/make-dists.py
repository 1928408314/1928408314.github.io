#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把根目录的平铺 Packages 拆成标准 dists 结构：
  dists/stable/Release
  dists/stable/main/binary-<arch>/Packages(.gz)
根目录的 Packages / Release 保留，平铺源照样能用。
"""
import os, sys, gzip, hashlib

DISTS = "dists/stable"
COMPONENT = "main"
REPO_URL = os.environ.get("REPO_URL", "https://1928408314.github.io/")

def rd(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()

def fields(rec):
    d = {}
    for line in rec.split("\n"):
        if line.startswith(" ") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        d[k.strip().lower()] = v.strip()
    return d

def main():
    if not os.path.isfile("Packages"):
        print("缺少 Packages"); return 1
    txt = rd("Packages")
    recs = [r.strip("\n") for r in txt.split("\n\n") if r.strip()]

    buckets = {}
    for r in recs:
        a = fields(r).get("architecture", "iphoneos-arm64")
        buckets.setdefault(a, []).append(r)

    entries = []
    for arch, rs in sorted(buckets.items()):
        d = os.path.join(DISTS, COMPONENT, "binary-" + arch)
        os.makedirs(d, exist_ok=True)
        body = "\n\n".join(rs) + "\n"
        p = os.path.join(d, "Packages")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        with open(p + ".gz", "wb") as f:
            f.write(gzip.compress(body.encode("utf-8"), 9, mtime=0))
        for fn in ("Packages", "Packages.gz"):
            fp = os.path.join(d, fn)
            data = open(fp, "rb").read()
            rel = "%s/binary-%s/%s" % (COMPONENT, arch, fn)
            entries.append((rel, len(data),
                            hashlib.md5(data).hexdigest(),
                            hashlib.sha256(data).hexdigest()))
        print("  %-42s %d 个包" % ("binary-" + arch, len(rs)))

    out = [
        "Origin: 爱玩机", "Label: 爱玩机", "Suite: stable", "Version: 1.0",
        "Codename: ios",
        "Architectures: " + " ".join(sorted(buckets)),
        "Components: " + COMPONENT,
        "Description: 爱玩机",
        "Support: " + REPO_URL,
        "Icon: " + REPO_URL.rstrip("/") + "/CydiaIcon.png",
        "MD5Sum:",
    ]
    for rel, size, md5, sha in entries:
        out.append(" %s %d %s" % (md5, size, rel))
    out.append("SHA256:")
    for rel, size, md5, sha in entries:
        out.append(" %s %d %s" % (sha, size, rel))

    os.makedirs(DISTS, exist_ok=True)
    with open(os.path.join(DISTS, "Release"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("  dists/stable/Release 已生成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
