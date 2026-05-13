#!/bin/bash
# 设置 GitHub Secrets
# 用法: bash setup-secrets.sh
# 前提: 已安装 gh 并登录 (gh auth login)

set -e

# 检查 gh 是否可用
if ! command -v gh &> /dev/null; then
    echo "请先安装 gh CLI: https://cli.github.com/"
    exit 1
fi

# 检查是否登录
if ! gh auth status &> /dev/null; then
    echo "请先登录: gh auth login"
    exit 1
fi

# ===== Boxying =====
read -p "BOXYING_SESSION: " val
[ -n "$val" ] && gh secret set BOXYING_SESSION -b "$val"

read -p "BOXYING_API_USER: " val
[ -n "$val" ] && gh secret set BOXYING_API_USER -b "$val"

# ===== XEM =====
read -p "XEM_SYSTEM_ACCESS_TOKEN: " val
[ -n "$val" ] && gh secret set XEM_SYSTEM_ACCESS_TOKEN -b "$val"

read -p "XEM_API_USER: " val
[ -n "$val" ] && gh secret set XEM_API_USER -b "$val"

# ===== ABRDNS =====
read -p "ABRDNS_ACCESS_TOKEN: " val
[ -n "$val" ] && gh secret set ABRDNS_ACCESS_TOKEN -b "$val"

read -p "ABRDNS_API_USER: " val
[ -n "$val" ] && gh secret set ABRDNS_API_USER -b "$val"

# ===== AINI8 =====
read -p "AINI8_ACCESS_TOKEN: " val
[ -n "$val" ] && gh secret set AINI8_ACCESS_TOKEN -b "$val"

read -p "AINI8_API_USER: " val
[ -n "$val" ] && gh secret set AINI8_API_USER -b "$val"

# ===== ELYSIVER =====
read -p "ELYSIVER_ACCESS_TOKEN: " val
[ -n "$val" ] && gh secret set ELYSIVER_ACCESS_TOKEN -b "$val"

read -p "ELYSIVER_API_USER: " val
[ -n "$val" ] && gh secret set ELYSIVER_API_USER -b "$val"

# ===== HUAN666 =====
read -p "HUAN666_ACCESS_TOKEN (可选): " val
[ -n "$val" ] && gh secret set HUAN666_ACCESS_TOKEN -b "$val"

read -p "HUAN666_SESSION (可选): " val
[ -n "$val" ] && gh secret set HUAN666_SESSION -b "$val"

read -p "HUAN666_API_USER: " val
[ -n "$val" ] && gh secret set HUAN666_API_USER -b "$val"

# ===== 通用推送 =====
read -p "PUSHPLUS_TOKEN (可选): " val
[ -n "$val" ] && gh secret set PUSHPLUS_TOKEN -b "$val"

echo ""
echo "✅ Secrets 设置完成！"
gh secret list
