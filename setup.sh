#!/bin/bash
set -e
echo "========================================="
echo "  占卜知识库系统 - 一键部署"
echo "========================================="

# 1. Install dependencies
echo ""
echo "[1/4] 安装依赖包..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv sshpass curl > /dev/null 2>&1

# 2. Create project directory
echo "[2/4] 创建项目目录..."
mkdir -p ~/knowledge-base
mkdir -p ~/uploads/knowledge-base

# 3. Install Python packages
echo "[3/4] 安装Python依赖（可能需要几分钟）..."
python3 -m venv ~/knowledge-base/venv
source ~/knowledge-base/venv/bin/activate
pip install --quiet chromadb pypdf python-docx langchain langchain-text-splitters sentence-transformers 2>&1 | tail -3

# 4. Download kb_system.py and kb_web.py
echo "[4/4] 下载知识库程序..."
cd ~/knowledge-base
curl -sO https://raw.githubusercontent.com/LittleSiobhan/knowledge-base/main/kb_system.py
curl -sO https://raw.githubusercontent.com/LittleSiobhan/knowledge-base/main/kb_web.py

echo ""
echo "========================================="
echo "  安装完成！"
echo "========================================="
echo ""
echo "启动知识库管理界面："
echo "  cd ~/knowledge-base"
echo "  source venv/bin/activate"
echo "  python3 kb_web.py"
echo ""
echo "然后访问: http://43.130.44.103:8898"
echo "上传文件到: ~/uploads/knowledge-base/"
echo ""
echo "========================================="
