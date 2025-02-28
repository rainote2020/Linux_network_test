#!/bin/bash

echo "网络测速工具安装程序"
echo "====================="

# 确保脚本在当前目录运行
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检测Linux发行版
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi

# 安装iperf3
echo "正在检查并安装iperf3..."
case $DISTRO in
    ubuntu|debian|linuxmint)
        sudo apt-get update
        sudo apt-get install -y iperf3
        ;;
    centos|rhel|fedora)
        if [ "$DISTRO" = "centos" ] || [ "$DISTRO" = "rhel" ]; then
            sudo yum install -y epel-release
        fi
        sudo yum install -y iperf3
        ;;
    arch|manjaro)
        sudo pacman -Sy --noconfirm iperf
        ;;
    *)
        echo "无法识别的Linux发行版，请手动安装iperf3"
        echo "在大多数发行版中，可以通过包管理器安装"
        echo "例如: apt install iperf3, yum install iperf3 等"
        ;;
esac

# 安装Python依赖
echo "正在安装Python依赖..."
pip3 install -r requirements.txt || {
    echo "通过pip3安装依赖失败，尝试使用pip..."
    pip install -r requirements.txt || {
        echo "无法安装Python依赖，请确保已安装pip"
        exit 1
    }
}

# 设置权限
echo "设置可执行权限..."
chmod +x network_tester.py
chmod +x start_test.sh

echo "安装完成！"
echo "可以使用以下命令开始测试:"
echo "  ./start_test.sh"
echo "或直接运行:"
echo "  ./network_tester.py 服务器地址"
