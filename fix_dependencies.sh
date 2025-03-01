#!/bin/bash

echo "正在修复依赖问题..."
echo "=================================="

# 确定 Python 解释器
if command -v python3 &> /dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

echo "使用 Python 解释器: $PYTHON"

# 确保 pip 已安装
if ! $PYTHON -m pip --version &> /dev/null; then
    echo "错误: 未找到 pip。请先安装 pip:"
    echo "  Ubuntu/Debian: sudo apt install python3-pip"
    echo "  CentOS/RHEL:   sudo yum install python3-pip"
    exit 1
fi

# 首先降级 NumPy 到兼容版本
echo "步骤 1: 将 NumPy 降级到兼容版本 (1.x)"
$PYTHON -m pip install "numpy>=1.20.0,<2.0.0" --force-reinstall

# 安装其他依赖
echo "步骤 2: 安装其他依赖"
$PYTHON -m pip install -r requirements.txt

# 运行兼容性检查脚本
echo "步骤 3: 验证依赖"
chmod +x check_compatibility.py
$PYTHON check_compatibility.py

echo "完成！"
echo "如果仍有问题，请尝试在虚拟环境中运行此程序:"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  ./network_tester.py <服务器地址>"
