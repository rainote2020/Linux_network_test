#!/bin/bash

# 确保脚本可以在任何目录下执行
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "网络测速工具 (Linux版)"
echo "====================="

# 检查iperf3是否已安装
if ! command -v iperf3 &> /dev/null; then
    echo "错误: 未找到iperf3命令。请先安装iperf3:"
    echo "  Ubuntu/Debian: sudo apt install iperf3"
    echo "  CentOS/RHEL:   sudo yum install iperf3"
    exit 1
fi

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3命令。请先安装Python 3"
    exit 1
fi

# 检查依赖库
python3 -c "import matplotlib, tabulate, colorama" &> /dev/null
if [ $? -ne 0 ]; then
    echo "正在安装Python依赖..."
    pip3 install -r requirements.txt
fi

read -p "请输入iperf3服务器地址: " server
read -p "请输入每个带宽测试的持续时间(秒)[默认10]: " duration
read -p "请输入并行连接数[默认1]: " parallel

duration=${duration:-10}
parallel=${parallel:-1}

echo
echo "开始测试服务器 $server..."
echo

# 设置脚本为可执行
chmod +x network_tester.py
./network_tester.py "$server" -t "$duration" -P "$parallel"

echo
echo "测试完成！"

# 显示结果目录
echo "结果保存在: $SCRIPT_DIR/results/"
echo
