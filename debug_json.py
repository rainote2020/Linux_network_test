#!/usr/bin/env python3

import subprocess
import json
import sys
import argparse


def print_json_structure(obj, prefix="", max_level=3, current_level=0):
    """递归打印JSON结构，显示关键字段但不显示完整数据"""
    if current_level > max_level:
        print(f"{prefix}...")
        return

    if isinstance(obj, dict):
        print(f"{prefix}{{")
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                print(f'{prefix}  "{key}": ', end="")
                print_json_structure(value, prefix + "  ", max_level, current_level + 1)
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                print(f'{prefix}  "{key}": {value_str}')
        print(f"{prefix}}}")
    elif isinstance(obj, list):
        print(f"{prefix}[")
        if len(obj) > 0:
            if len(obj) > 3:
                # 只显示前两个和最后一个元素
                for item in obj[:2]:
                    print_json_structure(item, prefix + "  ", max_level, current_level + 1)
                print(f"{prefix}  ... ({len(obj) - 3} more items)")
                print_json_structure(obj[-1], prefix + "  ", max_level, current_level + 1)
            else:
                for item in obj:
                    print_json_structure(item, prefix + "  ", max_level, current_level + 1)
        print(f"{prefix}]")
    else:
        print(obj)


def run_iperf3_test(server, port=5201, duration=5, bandwidth="100m", parallel=1):
    """运行一个简短的iperf3测试并获取JSON输出"""
    cmd = [
        "iperf3",
        "-c",
        server,
        "-p",
        str(port),
        "-t",
        str(duration),
        "-b",
        bandwidth,
        "-P",
        str(parallel),
        "-J",
    ]

    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"iperf3执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="调试iperf3 JSON输出格式")
    parser.add_argument("server", help="iperf3服务器地址")
    parser.add_argument("-p", "--port", type=int, default=5201, help="服务器端口 (默认: 5201)")
    parser.add_argument("-t", "--time", type=int, default=5, help="测试持续时间(秒) (默认: 5)")
    parser.add_argument("-b", "--bandwidth", default="100m", help="测试带宽 (默认: 100m)")
    parser.add_argument("-P", "--parallel", type=int, default=1, help="并行连接数 (默认: 1)")
    parser.add_argument("-o", "--output", help="将JSON输出保存到文件")
    parser.add_argument("--full", action="store_true", help="显示完整的JSON结构")

    args = parser.parse_args()

    # 运行iperf3测试
    json_output = run_iperf3_test(args.server, args.port, args.time, args.bandwidth, args.parallel)

    # 解析JSON
    try:
        data = json.loads(json_output)

        # 保存到文件
        if args.output:
            with open(args.output, "w") as f:
                json.dump(data, f, indent=2)
            print(f"JSON输出已保存到: {args.output}")

        # 打印JSON结构
        print("\niperf3 JSON输出结构:")
        if args.full:
            print(json.dumps(data, indent=2))
        else:
            print_json_structure(data)

        # 检查关键路径是否存在
        print("\n检查关键路径:")

        def check_path(data, path):
            current = data
            for key in path:
                if key in current:
                    current = current[key]
                else:
                    return False
            return True

        paths_to_check = [
            ["end", "sum_received", "bits_per_second"],
            ["end", "sum_received", "jitter_ms"],
            ["end", "sum_received", "lost_packets"],
            ["end", "sum_received", "packets"],
            ["end", "sum_sent", "retransmits"],
        ]

        for path in paths_to_check:
            path_str = " -> ".join(path)
            if check_path(data, path):
                print(f"✓ {path_str} 存在")
                # 显示值
                current = data
                for key in path:
                    current = current[key]
                print(f"  值: {current}")
            else:
                print(f"✗ {path_str} 不存在")

                # 找出在哪一级路径断开
                current = data
                broken_at = None
                for i, key in enumerate(path):
                    if key not in current:
                        broken_at = i
                        break
                    current = current[key]

                if broken_at is not None:
                    print(f"  路径在 '{path[broken_at]}' 处断开")
                    # 显示上一级的可用键
                    current = data
                    for i in range(broken_at):
                        current = current[path[i]]
                    if isinstance(current, dict):
                        print(f"  可用键: {list(current.keys())}")

    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print("原始输出的前500个字符:")
        print(json_output[:500])
        sys.exit(1)


if __name__ == "__main__":
    main()
