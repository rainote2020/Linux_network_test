#!/usr/bin/env python3

import subprocess
import re
import time
import argparse
import json
import statistics
import os
from datetime import datetime
from tabulate import tabulate
import matplotlib.pyplot as plt
from colorama import init, Fore, Style

# 初始化colorama
init(strip=not os.isatty(1))  # 当输出重定向时不使用颜色代码


class NetworkTester:
    def __init__(
        self, server, port=5201, duration=10, parallel=1, bandwidth_list=None, output_dir="results"
    ):
        """
        初始化网络测试器

        参数:
            server (str): iperf3服务器地址
            port (int): 服务器端口
            duration (int): 每次测试的持续时间(秒)
            parallel (int): 并行连接数
            bandwidth_list (list): 要测试的带宽列表，单位为Mbps，从高到低排序
            output_dir (str): 结果输出目录
        """
        self.server = server
        self.port = port
        self.duration = duration
        self.parallel = parallel
        self.output_dir = output_dir

        # 如果未指定带宽列表，使用默认值
        if bandwidth_list is None:
            self.bandwidth_list = [1000, 500, 200, 100, 50, 20, 10, 5, 2, 1]
        else:
            self.bandwidth_list = sorted(bandwidth_list, reverse=True)

        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # 保存测试结果
        self.results = []

    def run_iperf_test(self, target_bandwidth):
        """
        使用iperf3运行单次带宽测试

        参数:
            target_bandwidth (int): 目标带宽（Mbps）

        返回:
            dict: 测试结果
        """
        print(f"{Fore.CYAN}正在测试带宽: {target_bandwidth} Mbps{Style.RESET_ALL}")

        # 构建iperf3命令
        cmd = [
            "iperf3",
            "-c",
            self.server,
            "-p",
            str(self.port),
            "-t",
            str(self.duration),
            "-P",
            str(self.parallel),
            "-b",
            f"{target_bandwidth}m",
            "-J",  # 以JSON格式输出
        ]

        try:
            # 运行iperf3命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            # 调试信息 - 查看JSON结构
            if "end" not in data:
                print(f"{Fore.YELLOW}警告：JSON输出缺少'end'键{Style.RESET_ALL}")
                print(f"JSON数据结构：{list(data.keys())}")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "target_bandwidth": target_bandwidth,
                    "error": "JSON结构不完整，缺少'end'键",
                    "raw_structure": list(data.keys()),
                }

            # 安全地获取各项数据，使用get方法提供默认值
            end_data = data.get("end", {})
            sum_received = end_data.get("sum_received", {})
            sum_sent = end_data.get("sum_sent", {})

            # 提取结果，使用get方法来避免KeyError
            test_result = {
                "timestamp": datetime.now().isoformat(),
                "target_bandwidth": target_bandwidth,
                "achieved_bandwidth": sum_received.get("bits_per_second", 0) / 1_000_000,
                "retransmits": sum_sent.get("retransmits", 0),
                "jitter_ms": sum_received.get("jitter_ms", 0),  # 使用get方法，如果不存在则默认为0
                "lost_packets": sum_received.get("lost_packets", 0),
                "total_packets": sum_received.get("packets", 0),
                "raw_data": data,
            }

            # 计算丢包率
            if test_result["total_packets"] > 0:
                test_result["loss_percent"] = (
                    test_result["lost_packets"] / test_result["total_packets"]
                ) * 100
            else:
                test_result["loss_percent"] = 0

            print(
                f"{Fore.GREEN}测试完成: 达到 {test_result['achieved_bandwidth']:.2f} Mbps, "
                f"丢包率: {test_result['loss_percent']:.2f}%, "
                f"抖动: {test_result['jitter_ms']:.3f} ms{Style.RESET_ALL}"
            )

            return test_result

        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}测试失败: {e}{Style.RESET_ALL}")
            print(f"错误输出: {e.stderr}")
            return {
                "timestamp": datetime.now().isoformat(),
                "target_bandwidth": target_bandwidth,
                "error": str(e),
                "stderr": e.stderr,
            }
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}无法解析iperf3输出为JSON: {e}{Style.RESET_ALL}")
            if "result" in locals():
                print(f"非JSON输出的前100个字符: {result.stdout[:100]}")
            return {
                "timestamp": datetime.now().isoformat(),
                "target_bandwidth": target_bandwidth,
                "error": f"无法解析iperf3输出: {e}",
                "output": result.stdout[:500] if "result" in locals() else "未知输出",
            }
        except Exception as e:
            # 捕获所有其他类型的异常
            print(f"{Fore.RED}未预期的错误: {type(e).__name__}: {e}{Style.RESET_ALL}")
            return {
                "timestamp": datetime.now().isoformat(),
                "target_bandwidth": target_bandwidth,
                "error": f"未预期的错误: {type(e).__name__}: {e}",
            }

    def run_all_tests(self):
        """运行所有带宽测试"""
        print(f"{Fore.YELLOW}开始对服务器 {self.server} 进行测速...{Style.RESET_ALL}")
        print(f"测试持续时间: {self.duration}秒/带宽")
        print(f"并行连接: {self.parallel}")
        print(f"测试带宽列表: {', '.join(map(str, self.bandwidth_list))} Mbps")

        for bandwidth in self.bandwidth_list:
            result = self.run_iperf_test(bandwidth)
            self.results.append(result)
            time.sleep(2)  # 在测试之间等待，避免网络拥塞

        self.save_results()
        return self.results

    def analyze_results(self):
        """分析测试结果并返回汇总信息"""
        valid_results = [r for r in self.results if "error" not in r]

        if not valid_results:
            return {"status": "失败", "message": "所有测试均失败"}

        # 计算成功率
        success_rate = (len(valid_results) / len(self.results)) * 100

        # 找出最佳稳定带宽（丢包率<1%的最高带宽）
        stable_results = [r for r in valid_results if r.get("loss_percent", 100) < 1]
        best_stable_bandwidth = max(stable_results, key=lambda x: x["achieved_bandwidth"], default=None)

        # 计算平均达成率（实际带宽/目标带宽）
        achievement_rates = [
            (r["achieved_bandwidth"] / r["target_bandwidth"]) * 100
            for r in valid_results
            if r["target_bandwidth"] > 0
        ]

        # 安全地计算抖动平均值
        try:
            avg_jitter = statistics.mean(r.get("jitter_ms", 0) for r in valid_results)
        except statistics.StatisticsError:
            avg_jitter = 0

        return {
            "status": "成功",
            "test_count": len(self.results),
            "successful_tests": len(valid_results),
            "success_rate": success_rate,
            "best_bandwidth": max((r["achieved_bandwidth"] for r in valid_results), default=0),
            "best_stable_bandwidth": (
                best_stable_bandwidth["achieved_bandwidth"] if best_stable_bandwidth else 0
            ),
            "average_jitter_ms": avg_jitter,
            "average_achievement_rate": statistics.mean(achievement_rates) if achievement_rates else 0,
        }

    def generate_report(self):
        """生成测试报告"""
        analysis = self.analyze_results()

        # 为表格准备数据
        table_data = []
        for result in self.results:
            if "error" in result:
                row = [
                    result["target_bandwidth"],
                    "失败",
                    "N/A",
                    "N/A",
                    "N/A",
                    result.get("error", "未知错误"),
                ]
            else:
                achievement_rate = (result["achieved_bandwidth"] / result["target_bandwidth"]) * 100
                row = [
                    result["target_bandwidth"],
                    f"{result['achieved_bandwidth']:.2f}",
                    f"{achievement_rate:.1f}%",
                    f"{result['jitter_ms']:.3f}",
                    f"{result['loss_percent']:.2f}%",
                    "成功",
                ]
            table_data.append(row)

        # 生成报告
        report = [
            f"{Fore.YELLOW}网络测速报告 - {self.server}{Style.RESET_ALL}",
            f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"测试数量: {analysis['test_count']}",
            f"成功率: {analysis['success_rate']:.1f}%",
            "",
            f"{Fore.GREEN}最佳带宽: {analysis['best_bandwidth']:.2f} Mbps{Style.RESET_ALL}",
            f"最佳稳定带宽 (丢包<1%): {analysis['best_stable_bandwidth']:.2f} Mbps",
            f"平均抖动: {analysis['average_jitter_ms']:.3f} ms",
            f"平均达成率: {analysis['average_achievement_rate']:.1f}%",
            "",
            tabulate(
                table_data,
                headers=["目标带宽(Mbps)", "实际带宽(Mbps)", "达成率", "抖动(ms)", "丢包率", "状态"],
                tablefmt="grid",
            ),
        ]

        return "\n".join(report)

    def save_results(self):
        """保存测试结果到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"network_test_{timestamp}.json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"{Fore.BLUE}测试结果已保存到 {filename}{Style.RESET_ALL}")

        # 保存报告
        report_file = os.path.join(self.output_dir, f"network_report_{timestamp}.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            # 移除ANSI颜色代码后保存
            report = self.generate_report()
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            clean_report = ansi_escape.sub("", report)
            f.write(clean_report)

        print(f"{Fore.BLUE}报告已保存到 {report_file}{Style.RESET_ALL}")

        # 生成图表
        self.generate_charts(timestamp)

    def generate_charts(self, timestamp):
        """生成测试结果图表"""
        valid_results = [r for r in self.results if "error" not in r]

        if not valid_results:
            print(f"{Fore.RED}没有有效数据来生成图表{Style.RESET_ALL}")
            return

        # 提取数据
        target_bw = [r["target_bandwidth"] for r in valid_results]
        achieved_bw = [r["achieved_bandwidth"] for r in valid_results]
        jitter = [r["jitter_ms"] for r in valid_results]
        loss = [r["loss_percent"] for r in valid_results]

        # 创建图表目录
        charts_dir = os.path.join(self.output_dir, "charts")
        if not os.path.exists(charts_dir):
            os.makedirs(charts_dir)

        # 带宽对比图
        plt.figure(figsize=(10, 6))
        plt.plot(target_bw, label="目标带宽", marker="o")
        plt.plot(achieved_bw, label="实际带宽", marker="x")
        plt.xlabel("测试序号")
        plt.ylabel("带宽 (Mbps)")
        plt.title("目标带宽 vs 实际带宽")
        plt.grid(True)
        plt.legend()
        chart_file = os.path.join(charts_dir, f"bandwidth_{timestamp}.png")
        plt.savefig(chart_file)

        # 丢包率和抖动图
        fig, ax1 = plt.subplots(figsize=(10, 6))

        color = "tab:red"
        ax1.set_xlabel("目标带宽 (Mbps)")
        ax1.set_ylabel("丢包率 (%)", color=color)
        ax1.plot(target_bw, loss, color=color, marker="o")
        ax1.tick_params(axis="y", labelcolor=color)

        ax2 = ax1.twinx()
        color = "tab:blue"
        ax2.set_ylabel("抖动 (ms)", color=color)
        ax2.plot(target_bw, jitter, color=color, marker="x")
        ax2.tick_params(axis="y", labelcolor=color)

        fig.tight_layout()
        plt.title("丢包率和抖动 vs 带宽")
        plt.grid(True)
        chart_file = os.path.join(charts_dir, f"quality_{timestamp}.png")
        plt.savefig(chart_file)

        print(f"{Fore.BLUE}图表已保存到 {charts_dir} 目录{Style.RESET_ALL}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="网络带宽测试工具")
    parser.add_argument("server", help="iperf3服务器地址")
    parser.add_argument("-p", "--port", type=int, default=5201, help="服务器端口 (默认: 5201)")
    parser.add_argument("-t", "--time", type=int, default=10, help="每次测试的持续时间(秒) (默认: 10)")
    parser.add_argument("-P", "--parallel", type=int, default=1, help="并行连接数 (默认: 1)")
    parser.add_argument(
        "-b",
        "--bandwidths",
        type=str,
        help="要测试的带宽列表(Mbps)，用逗号分隔 (默认: 1000,500,200,100,50,20,10,5,2,1)",
    )
    parser.add_argument("-o", "--output", type=str, default="results", help="结果输出目录 (默认: results)")
    parser.add_argument("--no-color", action="store_true", help="禁用彩色输出")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    # 如果指定了禁用颜色
    if args.no_color:
        init(autoreset=True, strip=True)

    # 检查iperf3是否已安装
    try:
        subprocess.run(["iperf3", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    except FileNotFoundError:
        print(f"{Fore.RED}错误: 未找到iperf3命令。请先安装iperf3:{Style.RESET_ALL}")
        print("  Ubuntu/Debian: sudo apt install iperf3")
        print("  CentOS/RHEL:   sudo yum install iperf3")
        return 1

    # 解析带宽列表
    if args.bandwidths:
        try:
            bandwidth_list = [int(b.strip()) for b in args.bandwidths.split(",")]
        except ValueError:
            print(f"{Fore.RED}错误: 带宽列表格式不正确{Style.RESET_ALL}")
            return 1
    else:
        bandwidth_list = None

    # 创建测试器并运行测试
    tester = NetworkTester(
        server=args.server,
        port=args.port,
        duration=args.time,
        parallel=args.parallel,
        bandwidth_list=bandwidth_list,
        output_dir=args.output,
    )

    tester.run_all_tests()

    # 打印报告
    print("\n" + "=" * 80)
    print(tester.generate_report())
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
