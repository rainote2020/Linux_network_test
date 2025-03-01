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

# 显示菜单
echo "请选择操作:"
echo "1) 运行完整网络测试"
echo "2) 运行单次测试并查看JSON结构 (debug)"
echo "3) 分析ping日志文件"
echo "q) 退出"
read -p "请输入选择 [1]: " choice

choice=${choice:-1}

case $choice in
    1)
        # 检查依赖库
        python3 -c "import matplotlib, tabulate, colorama" &> /dev/null
        if [ $? -ne 0 ]; then
            echo "正在安装Python依赖..."
            pip3 install -r requirements.txt
        fi

        read -p "请输入iperf3服务器地址: " server
        read -p "请输入每个带宽测试的持续时间(秒)[默认10]: " duration
        read -p "请输入并行连接数[默认1]: " parallel
        read -p "是否只测试部分带宽(y/n)[默认n]: " custom_bw
        
        duration=${duration:-10}
        parallel=${parallel:-1}
        bandwidths=""
        
        if [[ "$custom_bw" == "y" || "$custom_bw" == "Y" ]]; then
            read -p "请输入要测试的带宽(Mbps)，用逗号分隔 [例如:100,50,20]: " bandwidths
            if [ -n "$bandwidths" ]; then
                bw_option="-b $bandwidths"
            else
                bw_option=""
            fi
        else
            bw_option=""
        fi

        echo
        echo "开始测试服务器 $server..."
        echo

        # 设置脚本为可执行
        chmod +x network_tester.py
        ./network_tester.py "$server" -t "$duration" -P "$parallel" $bw_option
        
        echo
        echo "测试完成！"
        echo "结果保存在: $SCRIPT_DIR/results/"
        ;;
        
    2)
        # 调试模式
        read -p "请输入iperf3服务器地址: " server
        read -p "请输入带宽(Mbps)[默认100]: " debug_bw
        
        debug_bw=${debug_bw:-100}
        
        echo
        echo "正在执行调试测试..."
        
        chmod +x debug_json.py
        ./debug_json.py "$server" -b "${debug_bw}m" --output "debug_output.json"
        ;;
        
    3)
        # 分析ping日志
        read -p "请输入ping日志文件路径: " ping_log
        
        if [ ! -f "$ping_log" ]; then
            echo "错误: 找不到文件 $ping_log"
            exit 1
        fi
        
        chmod +x ping_analyzer.py
        ./ping_analyzer.py "$ping_log"
        ;;
        
    q|Q)
        echo "退出"
        exit 0
        ;;
        
    *)
        echo "无效的选择"
        exit 1
        ;;
esac
