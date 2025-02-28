#!/usr/bin/env python3

import re
import sys
import statistics
import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from colorama import init, Fore, Style

# 初始化colorama
init()


def parse_ping_log(file_path):
    """
    解析ping日志文件

    参数:
        file_path (str): ping日志文件路径

    返回:
        list: ping响应时间列表(ms)
    """
    ping_times = []

    # 正则表达式匹配ping输出行
    pattern = r"icmp_seq=(\d+).*time=([\d\.]+) ms"

    try:
        with open(file_path, "r") as f:
            for line in f:
                match = re.search(pattern, line)
                if match:
                    seq_num = int(match.group(1))
                    time_ms = float(match.group(2))
                    ping_times.append((seq_num, time_ms))
    except Exception as e:
        print(f"{Fore.RED}Error reading file {file_path}: {e}{Style.RESET_ALL}")
        sys.exit(1)

    return ping_times


def analyze_ping_data(ping_times):
    """
    分析ping数据并返回统计结果

    参数:
        ping_times (list): (seq_num, time_ms) 元组列表

    返回:
        dict: 包含ping统计信息的字典
    """
    if not ping_times:
        return {"status": "No data", "message": "No ping data found in the log file"}

    # 提取时间值
    times = [t[1] for t in ping_times]

    # 检查是否有丢失的序列号
    seq_nums = [t[0] for t in ping_times]
    expected_seq = list(range(min(seq_nums), max(seq_nums) + 1))
    lost_seq = set(expected_seq) - set(seq_nums)

    # 计算统计数据
    stats = {
        "count": len(ping_times),
        "min": min(times),
        "max": max(times),
        "avg": sum(times) / len(times),
        "median": statistics.median(times),
        "stddev": statistics.stdev(times) if len(times) > 1 else 0,
        "lost_packets": len(lost_seq),
        "total_packets": len(expected_seq),
        "packet_loss_percent": (len(lost_seq) / len(expected_seq) * 100) if expected_seq else 0,
        "jitter": calculate_jitter(times),
    }

    # 将波动较大的数据点标识出来 (超过平均值的2个标准差)
    threshold = stats["avg"] + 2 * stats["stddev"]
    stats["spikes"] = [(seq, time) for seq, time in ping_times if time > threshold]

    return stats


def calculate_jitter(times):
    """
    计算抖动 (连续ping间的时间差异的平均值)
    """
    if len(times) < 2:
        return 0

    diffs = [abs(times[i] - times[i - 1]) for i in range(1, len(times))]
    return sum(diffs) / len(diffs)


def generate_report(stats):
    """
    生成ping分析报告

    参数:
        stats (dict): 包含ping统计信息的字典

    返回:
        str: 格式化后的报告
    """
    report = [
        f"{Fore.YELLOW}Ping分析报告{Style.RESET_ALL}",
        f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"共计 {stats['count']} 个ping数据点",
        f"丢包: {stats['lost_packets']}个 ({stats['packet_loss_percent']:.2f}%)",
        "",
        f"{Fore.CYAN}延迟统计:{Style.RESET_ALL}",
        f"  最小值: {stats['min']:.3f} ms",
        f"  最大值: {stats['max']:.3f} ms",
        f"  平均值: {stats['avg']:.3f} ms",
        f"  中位数: {stats['median']:.3f} ms",
        f"  标准差: {stats['stddev']:.3f} ms",
        f"  抖动: {stats['jitter']:.3f} ms",
        "",
    ]

    if stats["spikes"]:
        report.append(f"{Fore.RED}发现 {len(stats['spikes'])} 个异常延迟峰值:{Style.RESET_ALL}")
        for seq, time in stats["spikes"][:10]:  # 只显示前10个
            report.append(f"  序列号 {seq}: {time:.3f} ms")
        if len(stats["spikes"]) > 10:
            report.append(f"  ...以及更多 {len(stats['spikes'])-10} 个异常值")
    else:
        report.append(f"{Fore.GREEN}未发现明显的延迟峰值{Style.RESET_ALL}")

    return "\n".join(report)


def generate_charts(ping_times, output_file=None):
    """
    生成ping数据的图表

    参数:
        ping_times (list): (seq_num, time_ms) 元组列表
        output_file (str): 输出文件路径(可选)
    """
    if not ping_times:
        print(f"{Fore.RED}没有数据用于生成图表{Style.RESET_ALL}")
        return

    # 转换为NumPy数组以便更好的数据处理
    data = np.array(ping_times)
    seq_nums = data[:, 0]
    times = data[:, 1]

    plt.figure(figsize=(12, 8))

    # 绘制主图表 - 响应时间随时间变化
    plt.subplot(2, 1, 1)
    plt.plot(seq_nums, times, "b-", alpha=0.7)
    plt.plot(seq_nums, times, "ko", alpha=0.3, markersize=3)
    plt.title("Ping响应时间")
    plt.xlabel("序列号")
    plt.ylabel("响应时间 (ms)")
    plt.grid(True, alpha=0.3)

    # 计算移动平均线 (使用10个数据点的窗口)
    window_size = min(10, len(times))
    if window_size > 1:
        moving_avg = np.convolve(times, np.ones(window_size) / window_size, mode="valid")
        # 绘制移动平均线
        avg_x = seq_nums[window_size - 1 :]
        plt.plot(avg_x, moving_avg, "r-", linewidth=2, label=f"{window_size}点移动平均线")
        plt.legend()

    # 绘制统计分布图 - 直方图
    plt.subplot(2, 1, 2)
    plt.hist(times, bins=30, alpha=0.7, color="green")
    plt.title("Ping响应时间分布")
    plt.xlabel("响应时间 (ms)")
    plt.ylabel("频率")
    plt.grid(True, alpha=0.3)

    # 添加垂直线标识平均值和中位数
    avg = np.mean(times)
    median = np.median(times)
    plt.axvline(avg, color="r", linestyle="--", alpha=0.8, label=f"平均值: {avg:.2f} ms")
    plt.axvline(median, color="b", linestyle="--", alpha=0.8, label=f"中位数: {median:.2f} ms")
    plt.legend()

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file)
        print(f"{Fore.GREEN}图表已保存到: {output_file}{Style.RESET_ALL}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Ping日志分析工具")
    parser.add_argument("log_file", help="ping日志文件路径")
    parser.add_argument("-o", "--output", help="图表输出文件路径 (可选)")
    parser.add_argument("--no-chart", action="store_true", help="不生成图表")

    args = parser.parse_args()

    # 解析ping日志
    ping_times = parse_ping_log(args.log_file)

    if not ping_times:
        print(f"{Fore.RED}在文件中未找到有效的ping数据{Style.RESET_ALL}")
        return 1

    # 分析数据
    stats = analyze_ping_data(ping_times)

    # 打印报告
    print(generate_report(stats))

    # 生成图表
    if not args.no_chart:
        generate_charts(ping_times, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
