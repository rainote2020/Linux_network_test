# 网络测速工具 (Linux版)

这是一个基于iperf3的Linux网络测速工具，可以自动对服务器进行不同带宽的测试，并生成详细报告。

## 特性

- 自动从高到低测试不同带宽
- 计算实际带宽、丢包率和抖动
- 生成命令行友好的格式化报告
- 保存详细的JSON测试结果
- 生成带宽和网络质量图表
- 识别最佳稳定带宽（丢包率低于1%的最高带宽）

## 安装

### 前提条件

- Python 3.7+
- iperf3 命令行工具

### 安装iperf3

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install iperf3

# CentOS/RHEL
sudo yum install epel-release
sudo yum install iperf3

# Arch Linux
sudo pacman -S iperf3

# Fedora
sudo dnf install iperf3
```

### 安装Python依赖

```bash
pip3 install -r requirements.txt
```

### 依赖问题排查

如果遇到 NumPy 版本兼容性问题（例如 "A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.3"），请运行：

```bash
# 运行兼容性检查脚本
./check_compatibility.py

# 或使用自动修复脚本
./fix_dependencies.sh
```

也可以手动降级 NumPy 到兼容版本：

```bash
pip3 install "numpy>=1.20.0,<2.0.0" --force-reinstall
pip3 install -r requirements.txt
```

## 使用方法

### 使用启动脚本

最简单的方式是使用附带的启动脚本：

```bash
# 确保脚本可执行
chmod +x start_test.sh
./start_test.sh
```

脚本会引导您选择操作：
1. 运行完整网络测试 - 对服务器进行不同带宽的测试
2. 运行单次测试并查看JSON结构 - 用于调试JSON输出格式问题
3. 分析ping日志文件 - 分析之前保存的ping日志

### 直接使用命令行

基本用法：

```bash
./network_tester.py 服务器地址
```

完整参数：

```bash
./network_tester.py [-h] [-p PORT] [-t TIME] [-P PARALLEL] [-b BANDWIDTHS] [-o OUTPUT] [--no-color] [-v] server
```

参数说明：

- `server`: iperf3服务器地址
- `-p, --port PORT`: 服务器端口 (默认: 5201)
- `-t, --time TIME`: 每次测试的持续时间(秒) (默认: 10)
- `-P, --parallel PARALLEL`: 并行连接数 (默认: 1)
- `-b, --bandwidths BANDWIDTHS`: 要测试的带宽列表(Mbps)，用逗号分隔 (默认: 1000,500,200,100,50,20,10,5,2,1)
- `-o, --output OUTPUT`: 结果输出目录 (默认: results)
- `--no-color`: 禁用彩色输出（用于重定向输出到文件时）
- `-v, --verbose`: 显示详细信息

## 故障排除

### 常见错误

1. **JSON解析错误**

如果遇到JSON解析错误，请使用调试工具检查iperf3的输出格式：

```bash
./start_test.sh   # 选择选项2进行JSON调试
```

2. **缺少jitter_ms字段**

某些iperf3版本可能不输出`jitter_ms`字段，程序已经进行了修复，会自动处理缺失字段。

3. **NumPy兼容性问题**

如果遇到NumPy版本兼容性问题，请参见上方的"依赖问题排查"部分。

### 调试模式

使用`-v`或`--verbose`参数启用详细输出：

```bash
./network_tester.py 192.168.1.100 -v
```

## 服务器端设置

在被测试的服务器上需运行iperf3服务端：

```bash
# 基本服务端
iperf3 -s

# 以守护进程方式运行
iperf3 -s -D

# 指定端口
iperf3 -s -p 5201
```

## 延伸用法

### 定期测试

可以使用cron设置定期测试：

```bash
# 编辑cron任务
crontab -e

# 每天凌晨2点运行测试
0 2 * * * cd /path/to/network_tester && ./network_tester.py 192.168.1.100 -o results/daily
```

### 多服务器测试

批量测试多台服务器：

```bash
for server in 192.168.1.100 192.168.1.101 192.168.1.102; do
  ./network_tester.py $server -o "results/$server"
done
```

### 虚拟环境安装

如果遇到依赖冲突问题，可以考虑在虚拟环境中运行：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./network_tester.py 服务器地址
```
