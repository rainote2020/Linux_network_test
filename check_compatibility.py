#!/usr/bin/env python3

import sys
import subprocess
import pkg_resources
import os
from colorama import init, Fore, Style

init()


def check_numpy_version():
    """检查NumPy版本并提供解决建议"""
    try:
        import numpy as np

        numpy_version = np.__version__
        print(f"{Fore.BLUE}已安装的NumPy版本: {numpy_version}{Style.RESET_ALL}")

        # 检查是否为NumPy 2.x
        if numpy_version.startswith("2."):
            print(f"{Fore.YELLOW}警告: 检测到NumPy 2.x 版本{Style.RESET_ALL}")
            print("matplotlib等依赖包可能与NumPy 2.x不兼容，建议降级到NumPy 1.x版本。")
            return False
        return True
    except ImportError:
        print(f"{Fore.YELLOW}NumPy未安装{Style.RESET_ALL}")
        return False


def check_matplotlib_version():
    """检查matplotlib版本"""
    try:
        import matplotlib

        print(f"{Fore.BLUE}已安装的matplotlib版本: {matplotlib.__version__}{Style.RESET_ALL}")
        return True
    except ImportError:
        print(f"{Fore.YELLOW}matplotlib未安装{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}导入matplotlib时出错: {e}{Style.RESET_ALL}")
        return False


def check_tabulate_version():
    """检查tabulate版本"""
    try:
        import tabulate

        print(f"{Fore.BLUE}已安装的tabulate版本: {tabulate.__version__}{Style.RESET_ALL}")
        return True
    except ImportError:
        print(f"{Fore.YELLOW}tabulate未安装{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}导入tabulate时出错: {e}{Style.RESET_ALL}")
        return False


def check_colorama_version():
    """检查colorama版本"""
    try:
        import colorama

        print(f"{Fore.BLUE}已安装的colorama版本: {colorama.__version__}{Style.RESET_ALL}")
        return True
    except ImportError:
        print(f"{Fore.YELLOW}colorama未安装{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}导入colorama时出错: {e}{Style.RESET_ALL}")
        return False


def downgrade_numpy():
    """降级NumPy到1.x版本"""
    print(f"{Fore.CYAN}正在尝试将NumPy降级到兼容版本...{Style.RESET_ALL}")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "numpy>=1.20.0,<2.0.0", "--force-reinstall"], check=True
        )
        print(f"{Fore.GREEN}NumPy已成功降级{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}降级NumPy失败: {e}{Style.RESET_ALL}")
        return False


def install_dependencies():
    """安装所需依赖"""
    print(f"{Fore.CYAN}正在安装所需依赖...{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print(f"{Fore.GREEN}依赖安装成功{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}安装依赖失败: {e}{Style.RESET_ALL}")
        return False


def get_installed_packages():
    """获取已安装的包列表"""
    installed_packages = {}
    for dist in pkg_resources.working_set:
        installed_packages[dist.project_name] = dist.version
    return installed_packages


def check_for_conflicts():
    """检查依赖冲突"""
    conflicts = []
    required = {}

    # 解析requirements.txt
    try:
        with open("requirements.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 简单解析，只处理包名和版本要求
                parts = line.split("==")
                if len(parts) == 2:
                    pkg_name = parts[0].lower()
                    required[pkg_name] = f"=={parts[1]}"
                else:
                    parts = line.split(">=")
                    if len(parts) > 1:
                        pkg_name = parts[0].lower()
                        version_spec = ">=" + parts[1].split(",")[0]
                        required[pkg_name] = version_spec
                    else:
                        pkg_name = line.lower()
                        required[pkg_name] = "any"
    except Exception as e:
        print(f"{Fore.RED}解析requirements.txt失败: {e}{Style.RESET_ALL}")
        return []

    # 检查已安装的包
    installed = get_installed_packages()
    for pkg_name, req_version in required.items():
        pkg_name_lower = pkg_name.lower()

        # 查找已安装的相应包
        found = False
        for installed_name, installed_version in installed.items():
            if installed_name.lower() == pkg_name_lower:
                found = True

                # 版本要求检查 (简化版，仅检查特定格式)
                if req_version == "any":
                    continue  # 没有版本要求
                elif req_version.startswith("=="):
                    required_version = req_version[2:]
                    if installed_version != required_version:
                        conflicts.append(f"{installed_name}: 已安装 {installed_version}, 需要 {req_version}")
                elif req_version.startswith(">="):
                    min_version = req_version[2:]
                    if (
                        pkg_name_lower == "numpy"
                        and installed_version.startswith("2.")
                        and "1." in min_version
                    ):
                        conflicts.append(
                            f"{installed_name}: 已安装 2.x 版本 ({installed_version}), 但需要 1.x 版本"
                        )
                break

        if not found:
            conflicts.append(f"{pkg_name}: 未安装")

    return conflicts


def main():
    print(f"{Fore.YELLOW}网络测速工具兼容性检查{Style.RESET_ALL}")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print("=" * 60)

    numpy_ok = check_numpy_version()
    matplotlib_ok = check_matplotlib_version()
    tabulate_ok = check_tabulate_version()
    colorama_ok = check_colorama_version()

    print("=" * 60)
    conflicts = check_for_conflicts()

    if conflicts:
        print(f"{Fore.RED}检测到以下依赖冲突:{Style.RESET_ALL}")
        for conflict in conflicts:
            print(f" - {conflict}")

        print("\n是否要尝试自动修复这些问题?")
        print("1) 尝试修复所有问题")
        print("2) 仅降级NumPy到兼容版本")
        print("3) 重新安装所有依赖")
        print("4) 退出")

        choice = input("请选择操作 [1]: ") or "1"

        if choice == "1":
            if "numpy" in [c.split(":")[0].strip().lower() for c in conflicts]:
                downgrade_numpy()
            install_dependencies()
        elif choice == "2":
            downgrade_numpy()
        elif choice == "3":
            install_dependencies()
        else:
            return

        print("\n修复后重新检查:")
        check_numpy_version()
        check_matplotlib_version()
        check_tabulate_version()
        check_colorama_version()
    else:
        print(f"{Fore.GREEN}没有检测到依赖冲突，所有依赖看起来正常。{Style.RESET_ALL}")

    print("\n如果仍有问题，请尝试以下命令手动修复:")
    print(f"  {sys.executable} -m pip install numpy>=1.20.0,<2.0.0 --force-reinstall")
    print(f"  {sys.executable} -m pip install -r requirements.txt --force-reinstall")


if __name__ == "__main__":
    main()
