import sys
import os
import subprocess
import importlib
import logging
import argparse
import traceback
import time

# 添加调试信息
print(f"Python 可执行文件: {sys.executable}")
print(f"Python 版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"PATH 环境变量: {os.environ.get('PATH')}")

# 尝试直接导入 PyQt5.QtWidgets 以进行调试
try:
    import PyQt5.QtWidgets
    print("PyQt5.QtWidgets 直接导入成功!")
except ImportError as e:
    print(f"PyQt5.QtWidgets 直接导入失败: {e}")
    print(f"错误详情: {traceback.format_exc()}")

# ANSI 颜色代码
class Colors:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 初始化颜色实例
c = Colors()

# 解析命令行参数
parser = argparse.ArgumentParser(description='音频分割工具')
parser.add_argument('--skip-dependency', type=str, help='跳过指定依赖项的检查，多个依赖项用逗号分隔')
parser.add_argument('--auto-install', action='store_true', help='自动安装缺失的依赖项')
args = parser.parse_args()

# 初始化跳过的依赖项集合
SKIPPED_DEPENDENCIES = set()
if args.skip_dependency:
    SKIPPED_DEPENDENCIES = set(args.skip_dependency.split(','))
    print(f"{c.YELLOW}跳过依赖项检查: {', '.join(SKIPPED_DEPENDENCIES)}{c.RESET}")

# 是否自动安装依赖
AUTO_INSTALL = args.auto_install
if AUTO_INSTALL:
    print(f"{c.GREEN}已启用自动安装依赖模式{c.RESET}")

# 延迟导入packaging模块，直到确保其已安装
packaging = None
version = None
SpecifierSet = None

# 确保packaging库已安装（用于版本检查）
def ensure_packaging_installed():
    global packaging, version, SpecifierSet
    try:
        import packaging
        from packaging import version
        from packaging.specifiers import SpecifierSet
        return True
    except ImportError:
        print(f"{c.YELLOW}packaging库未安装，正在尝试安装...{c.RESET}")
        try:
            # 使用run而不是check_call，以便获取更多输出信息
            result = subprocess.run([sys.executable, "-m", "pip", "install", "packaging"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{c.GREEN}packaging库安装成功。{c.RESET}")
                # 安装成功后尝试重新导入
                try:
                    import packaging
                    from packaging import version
                    from packaging.specifiers import SpecifierSet
                    return True
                except ImportError:
                    print(f"{c.YELLOW}警告: 虽然packaging库安装成功，但导入仍然失败。{c.RESET}")
                    print(f"{c.CYAN}请尝试重启程序或手动安装。{c.RESET}")
                    return False
            else:
                print(f"{c.RED}错误: 安装packaging库失败: {result.stderr}{c.RESET}")
                print(f"{c.CYAN}请手动安装: pip install packaging{c.RESET}")
                return False
        except Exception as e:
            print(f"{c.RED}错误: 安装packaging库时发生异常: {str(e)}{c.RESET}")
            print(f"{c.CYAN}请手动安装: pip install packaging{c.RESET}")
            return False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 依赖配置 - 集中管理所有依赖及其版本要求
DEPENDENCIES = {
    'PyQt5': {
        'module': 'PyQt5',
        'install_command': 'PyQt5',
        'version_requirement': '>=5.15.0',
        'description': '用于创建图形用户界面',
        'critical': True,
        'submodules': [],  # 暂时移除直接子模块检查
        'module_submodules': {'PyQt5': ['QtWidgets', 'QtCore', 'QtGui']}  # 添加模块级子模块检查
    },
    'pydub': {
        'module': 'pydub',
        'install_command': 'pydub',
        'version_requirement': '>=0.25.0',
        'description': '用于音频处理和分段',
        'critical': True,
        'submodules': ['AudioSegment'],  # 修正子模块列表
        'module_functions': {'silence': ['split_on_silence']}  # 添加模块函数检查
    },
    'ffmpeg': {
        'type': 'external',
        'command': 'ffmpeg',
        'version_requirement': '>=4.0.0',
        'description': '用于音频文件格式转换和处理',
        'critical': False,
        'install_guide': '请访问 https://ffmpeg.org/download.html 下载并安装FFmpeg，并确保其在系统PATH中'
    }
}

def check_python_version():
    """检查Python版本是否满足要求"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    print(f"{c.CYAN}当前Python版本: {sys.version}{c.RESET}")
    if current_version < required_version:
        error_msg = f"{c.RED}错误: 请使用Python {required_version[0]}.{required_version[1]}或更高版本。{c.RESET}"
        print(error_msg)
        logger.error(error_msg)
        return False
    print(f"{c.GREEN}Python版本满足要求。{c.RESET}")
    return True


def check_python_dependency(dep_config):
    """检查Python库依赖是否安装并满足版本要求，若缺失则自动安装"""
    module_name = dep_config['module']
    install_command = dep_config['install_command']
    version_requirement = dep_config['version_requirement']
    description = dep_config['description']
    critical = dep_config['critical']
    submodules = dep_config.get('submodules', [])
    module_functions = dep_config.get('module_functions', {})
    module_submodules = dep_config.get('module_submodules', {})
    
    # 如果启用了自动安装，则将critical视为True
    if AUTO_INSTALL:
        critical = True

    # 首先尝试导入模块
    try:
        pass
        module = importlib.import_module(module_name)
        print(f"{c.GREEN}{module_name} 已安装。{c.RESET}")

        # 检查版本
        if hasattr(module, '__version__'):
            current_version = version.parse(module.__version__)
            spec = SpecifierSet(version_requirement)
            if current_version in spec:
                print(f"{c.GREEN}{module_name} 版本 {current_version} 满足要求 ({version_requirement})。{c.RESET}")
            else:
                error_msg = f"错误: {module_name} 版本 {current_version} 不满足要求 ({version_requirement})。"
                print(error_msg)
                logger.error(error_msg)
                if critical:
                    print(f"{c.YELLOW}正在尝试更新 {module_name}...{c.RESET}")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", install_command])
                        print(f"{c.GREEN}{module_name} 更新成功。{c.RESET}")
                        logger.info(f"{module_name} 更新成功。")
                        # 重新导入以获取新版本
                        module = importlib.import_module(module_name)
                    except subprocess.CalledProcessError as e:
                        error_msg = f"错误: 更新 {module_name} 失败。"
                        print(error_msg)
                        logger.error(f"{error_msg} 错误详情: {str(e)}")
                        print(f"请手动更新 {module_name}: pip install --upgrade {install_command}")
                        return False
                else:
                    print(f"{c.YELLOW}警告: {module_name} 版本可能不兼容，但将继续尝试运行。{c.RESET}")
        else:
            print(f"{c.CYAN}无法检查 {module_name} 版本，但假设其满足要求。{c.RESET}")

        # 检查子模块
        all_submodules_ok = True
        for submodule in submodules:
            try:
                # 对于像PyQt5.QtWidgets这样的子模块
                if '.' in submodule:
                    parent_module, child_module = submodule.split('.', 1)
                    getattr(importlib.import_module(f"{module_name}.{parent_module}"), child_module)
                else:
                    # 对于像pydub.AudioSegment这样的子模块
                    getattr(module, submodule)
                print(f"{c.GREEN}{module_name}.{submodule} 子模块检查通过。{c.RESET}")
            except (ImportError, AttributeError) as e:
                error_msg = f"错误: 无法导入 {module_name}.{submodule} 子模块: {str(e)}"
                print(error_msg)
                logger.error(error_msg)
                all_submodules_ok = False
                if critical:
                    print(f"{c.YELLOW}正在尝试重新安装 {module_name} 以修复子模块问题...{c.RESET}")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", install_command])
                        print(f"{c.GREEN}{module_name} 重新安装成功。{c.RESET}")
                        logger.info(f"{module_name} 重新安装成功。")
                        # 重新导入以检查修复情况
                        module = importlib.import_module(module_name)
                        # 再次检查子模块
                        if '.' in submodule:
                            parent_module, child_module = submodule.split('.', 1)
                            getattr(importlib.import_module(f"{module_name}.{parent_module}"), child_module)
                        else:
                            getattr(module, submodule)
                        print(f"{c.GREEN}{module_name}.{submodule} 子模块检查通过。{c.RESET}")
                        all_submodules_ok = True
                    except (subprocess.CalledProcessError, ImportError, AttributeError) as e:
                        error_msg = f"错误: 修复 {module_name}.{submodule} 子模块失败: {str(e)}"
                        print(error_msg)
                        logger.error(error_msg)
                        print(f"请手动安装 {module_name}: pip install --force-reinstall {install_command}")
                        return False

        # 检查模块级子模块 (如PyQt5.QtWidgets)
        # 打印调试信息
        print(f"{c.CYAN}开始检查模块级子模块: {module_submodules}{c.RESET}")
        for parent_module, submodules_list in module_submodules.items():
            print(f"{c.CYAN}检查父模块: {parent_module}{c.RESET}")
            for submodule in submodules_list:
                full_module_name = f"{parent_module}.{submodule}"
                print(f"{c.CYAN}尝试导入: {full_module_name}{c.RESET}")
                # 直接尝试导入完整路径
                try:
                    importlib.import_module(full_module_name)
                    print(f"{c.GREEN}{full_module_name} 模块级子模块检查通过。{c.RESET}")
                except ImportError as e:
                    # 增加详细的错误信息
                    import traceback
                    error_msg = f"错误: 无法导入 {full_module_name} 模块级子模块: {str(e)}"
                    print(error_msg)
                    print(f"{c.YELLOW}错误详情: {traceback.format_exc()}{c.RESET}")
                    logger.error(error_msg)
                    all_submodules_ok = False
                    # 对于PyQt5特定的DLL错误，提供额外的建议
                    if module_name == 'PyQt5':
                        print(f"{c.YELLOW}PyQt5 DLL错误可能是由于缺少Visual C++运行时库。{c.RESET}")
                        print(f"{c.CYAN}请下载并安装Microsoft Visual C++ Redistributable for Visual Studio 2015-2022。{c.RESET}")
                        print(f"{c.CYAN}下载链接: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170{c.RESET}")
                        print(f"{c.YELLOW}额外建议: 尝试使用 pip install PyQt5==5.15.4 安装特定版本{c.RESET}")
                        print(f"{c.YELLOW}注意: 请确保下载与您系统架构匹配的版本(x86或x64)。{c.RESET}")
                        print(f"{c.YELLOW}如果问题仍然存在，可能需要重新安装Python并确保选择了'Add Python to PATH'选项。{c.RESET}")
                    if critical:
                        print(f"正在尝试重新安装 {module_name} 以修复模块级子模块问题...")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", install_command])
                        print(f"{c.GREEN}{module_name} 重新安装成功。{c.RESET}")
                        logger.info(f"{module_name} 重新安装成功。")
                        # 重新尝试导入
                        importlib.import_module(full_module_name)
                        print(f"{c.GREEN}{full_module_name} 模块级子模块检查通过。{c.RESET}")
                        all_submodules_ok = True
                    except (subprocess.CalledProcessError, ImportError) as e2:
                        error_msg = f"{c.RED}错误: 修复 {full_module_name} 模块级子模块失败: {str(e2)}{c.RESET}"
                        print(error_msg)
                        logger.error(error_msg)
                        print(f"请手动安装 {module_name}: pip install --force-reinstall {install_command}")
                        # 对于PyQt5，提供额外的安装建议
                        if module_name == 'PyQt5':
                            print("额外建议: 尝试使用 pip install PyQt5==5.15.4 安装特定版本")
                        return False
    except ImportError as e:
        error_msg = f"错误: 无法导入 {module_name} 模块: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        print(f"{module_name} 未安装，正在尝试自动安装...")
        logger.info(f"正在安装 {module_name}...")
        try:
            # 尝试安装依赖
            subprocess.check_call([sys.executable, "-m", "pip", "install", install_command])
            print(f"{module_name} 安装成功。")
            logger.info(f"{module_name} 安装成功。")
            # 安装成功后尝试导入
            module = importlib.import_module(module_name)
            # 检查子模块
            all_submodules_ok = True
            for submodule in submodules:
                try:
                    if '.' in submodule:
                        parent_module, child_module = submodule.split('.', 1)
                        getattr(importlib.import_module(f"{module_name}.{parent_module}"), child_module)
                    else:
                        getattr(module, submodule)
                    print(f"{module_name}.{submodule} 子模块检查通过。")
                except (ImportError, AttributeError) as e:
                    error_msg = f"错误: 无法导入 {module_name}.{submodule} 子模块: {str(e)}"
                    print(error_msg)
                    logger.error(error_msg)
                    all_submodules_ok = False
            return all_submodules_ok
        except subprocess.CalledProcessError as e:
            error_msg = f"错误: 安装 {module_name} 失败: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            print(f"请手动安装 {module_name}: pip install {install_command}")
            return False
    except Exception as e:
        error_msg = f"错误: 模块级子模块检查过程中发生异常: {str(e)}"
        print(error_msg)
        logger.error(error_msg)
        return False

    # 检查模块函数
    for submodule, functions in module_functions.items():
            try:
                # 导入子模块
                submodule_obj = importlib.import_module(f"{module_name}.{submodule}")
                print(f"{c.GREEN}{module_name}.{submodule} 模块已导入。{c.RESET}")
                # 检查每个函数
                for func_name in functions:
                    try:
                        getattr(submodule_obj, func_name)
                        print(f"{module_name}.{submodule}.{func_name} 函数检查通过。")
                    except AttributeError as e:
                        error_msg = f"错误: 无法找到 {module_name}.{submodule}.{func_name} 函数: {str(e)}"
                        print(error_msg)
                        logger.error(error_msg)
                        all_submodules_ok = False
                        if critical:
                            print(f"正在尝试重新安装 {module_name} 以修复函数缺失问题...")
                            try:
                                subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", install_command])
                                print(f"{module_name} 重新安装成功。")
                                logger.info(f"{module_name} 重新安装成功。")
                                # 重新导入以检查修复情况
                                submodule_obj = importlib.import_module(f"{module_name}.{submodule}")
                                getattr(submodule_obj, func_name)
                                print(f"{module_name}.{submodule}.{func_name} 函数检查通过。")
                                all_submodules_ok = True
                            except (subprocess.CalledProcessError, ImportError, AttributeError) as e2:
                                error_msg = f"错误: 修复 {module_name}.{submodule}.{func_name} 函数失败: {str(e2)}"
                                print(error_msg)
                                logger.error(error_msg)
                                print(f"{c.CYAN}请手动安装 {module_name}: pip install --force-reinstall {install_command}{c.RESET}")
                                return False
            except ImportError as e:
                error_msg = f"错误: 无法导入 {module_name}.{submodule} 模块: {str(e)}"
                print(error_msg)
                logger.error(error_msg)
                all_submodules_ok = False
                if critical:
                    print(f"正在尝试重新安装 {module_name} 以修复模块缺失问题...")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "--force-reinstall", install_command])
                        print(f"{module_name} 重新安装成功。")
                        logger.info(f"{module_name} 重新安装成功。")
                        # 重新导入以检查修复情况
                        submodule_obj = importlib.import_module(f"{module_name}.{submodule}")
                        # 检查每个函数
                        for func_name in functions:
                            getattr(submodule_obj, func_name)
                            print(f"{module_name}.{submodule}.{func_name} 函数检查通过。")
                        all_submodules_ok = True
                    except (subprocess.CalledProcessError, ImportError, AttributeError) as e2:
                        error_msg = f"错误: 修复 {module_name}.{submodule} 模块失败: {str(e2)}"
                        print(error_msg)
                        logger.error(error_msg)
                        print(f"请手动安装 {module_name}: pip install --force-reinstall {install_command}")
                        return False

    if not all_submodules_ok and not critical:
        print(f"警告: {module_name} 的某些子模块或函数缺失，但将继续尝试运行。")

    return True


def check_external_dependency(dep_config):
    """检查外部命令行依赖是否安装并满足版本要求"""
    command = dep_config['command']
    version_requirement = dep_config['version_requirement']
    description = dep_config['description']
    critical = dep_config['critical']
    install_guide = dep_config.get('install_guide', '')

    try:
        # 尝试运行命令获取版本
        result = subprocess.run([command, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stderr if result.returncode != 0 else result.stdout
        print(f"{c.GREEN}{command} 已安装。{c.RESET}")
        logger.info(f"{command} 已安装。")

        # 尝试解析版本号
        # 这是一个简化的示例，实际解析可能需要更复杂的逻辑
        version_str = output.split(' ')[2].split('\n')[0] if len(output.split(' ')) > 2 else 'unknown'
        if version_str != 'unknown':
            try:
                current_version = version.parse(version_str)
                spec = SpecifierSet(version_requirement)
                if current_version in spec:
                    print(f"{c.GREEN}{command} 版本 {current_version} 满足要求 ({version_requirement})。{c.RESET}")
                    return True
                else:
                    error_msg = f"{c.RED}错误: {command} 版本 {current_version} 不满足要求 ({version_requirement})。{c.RESET}"
                    print(error_msg)
                    logger.error(error_msg)
                    if critical:
                        print(f"{c.CYAN}请更新 {command} 到符合要求的版本。{c.RESET}")
                        return False
                    else:
                        print(f"{c.YELLOW}警告: {command} 版本可能不兼容，但将继续尝试运行。{c.RESET}")
                        return True
            except Exception as e:
                print(f"{c.YELLOW}无法解析 {command} 版本号: {str(e)}{c.RESET}")
                logger.warning(f"无法解析 {command} 版本号: {str(e)}")
                return True
        else:
            print(f"{c.CYAN}无法确定 {command} 版本号。{c.RESET}")
            return True

    except (subprocess.SubprocessError, FileNotFoundError):
        error_msg = f"{c.RED}错误: 未找到 {command}。{c.RESET}"
        print(error_msg)
        logger.error(error_msg)
        print(f"{c.CYAN}{description}{c.RESET}")
        if install_guide:
            print(f"{c.CYAN}{install_guide}{c.RESET}")
        if critical:
            return False
        else:
            print(f"{c.YELLOW}警告: 未找到 {command}，但将继续尝试运行。这可能导致某些功能不可用。{c.RESET}")
            return True


def check_dependencies():
    """检查所有依赖项"""
    print(f"{c.BOLD}{c.PURPLE}=== 依赖检查开始 ==={c.RESET}")
    all_checks_passed = True
    failed_deps = []

    # 检查Python版本
    if not check_python_version():
        all_checks_passed = False
        failed_deps.append("Python版本不符合要求")

    # 检查所有依赖
    for dep_name, dep_config in DEPENDENCIES.items():
        if dep_name in SKIPPED_DEPENDENCIES:
            print(f"{c.YELLOW}跳过依赖项检查: {dep_name}{c.RESET}")
            logger.info(f"跳过依赖项检查: {dep_name}")
            continue
        if dep_config.get('type') == 'external':
            if not check_external_dependency(dep_config):
                all_checks_passed = False
                failed_deps.append(f"外部依赖: {dep_name}")
        else:
            if not check_python_dependency(dep_config):
                all_checks_passed = False
                failed_deps.append(f"Python库: {dep_name}")

    print(f"{c.BOLD}{c.PURPLE}=== 依赖检查结束 ==={c.RESET}")
    return all_checks_passed, failed_deps

def ensure_packaging_installed():
    """确保packaging库已安装"""
    try:
        import packaging
        from packaging.version import Version
        from packaging.specifiers import SpecifierSet
        return True
    except ImportError:
        print(f"{c.YELLOW}packaging库未安装，正在尝试安装...{c.RESET}")
        try:
            # 使用run而不是check_call，以便获取更多输出信息
            result = subprocess.run([sys.executable, "-m", "pip", "install", "packaging==23.2"], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"{c.GREEN}packaging库安装成功。{c.RESET}")
                # 安装成功后尝试重新导入
                try:
                    import packaging
                    from packaging.version import Version
                    from packaging.specifiers import SpecifierSet
                    return True
                except ImportError:
                    print(f"{c.YELLOW}警告: 虽然packaging库安装成功，但导入仍然失败。{c.RESET}")
                    print(f"{c.CYAN}请尝试重启程序或手动安装。{c.RESET}")
                    return False
            else:
                print(f"{c.RED}错误: 安装packaging库失败: {result.stderr}{c.RESET}")
                print(f"{c.CYAN}请手动安装: pip install packaging==23.2{c.RESET}")
                return False
        except Exception as e:
            print(f"错误: 安装packaging库时发生异常: {str(e)}")
            print("请手动安装: pip install packaging==23.2")
            return False

def main():
    print(f"{c.BOLD}{c.BLUE}=== 英语听力MP3对话分段工具 (PyQt版) 启动器 ===={c.RESET}")

    # 首先确保packaging库已安装
    if not ensure_packaging_installed():
        print(f"{c.RED}错误: 无法安装必要的packaging库，程序无法启动。{c.RESET}")
        sys.exit(1)
        
    # 检查依赖
    all_checks_passed, failed_deps = check_dependencies()
    
    # 如果依赖检查失败但启用了自动安装
    if not all_checks_passed and AUTO_INSTALL:
        print(f"{c.YELLOW}检测到依赖问题，正在尝试自动修复...{c.RESET}")
        # 等待一会儿，让用户看到信息
        time.sleep(1)
        # 重新检查依赖
        all_checks_passed, failed_deps = check_dependencies()
        
    # 如果依赖检查仍然失败
    if not all_checks_passed:
        print(f"{c.RED}错误: 依赖检查失败，无法启动程序。{c.RESET}")
        print(f"{c.RED}失败的依赖项: {', '.join(failed_deps)}{c.RESET}")
        print(f"{c.CYAN}请尝试手动安装缺失的依赖项，或使用 --auto-install 参数自动安装。{c.RESET}")
        #input("按Enter键重试...")
        sys.exit(1)
    # 启动主程序
    print(f"{c.GREEN}正在启动英语听力MP3对话分段工具...{c.RESET}")
    logger.info("正在启动英语听力MP3对话分段工具...")
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_segmenter_pyqt.py")
        subprocess.run([sys.executable, script_path])
    except Exception as e:
        error_msg = f"{c.RED}错误: 启动程序时发生异常: {str(e)}{c.RESET}"
        print(error_msg)
        logger.error(error_msg)
        sys.exit(1)



if __name__ == "__main__":
    # 首先确保packaging库已安装
    if not ensure_packaging_installed():
        sys.exit(1)
    try:
        main()
    except Exception as e:
        print(f"{c.RED}程序运行时发生错误: {str(e)}{c.RESET}")
        print(f"{c.RED}错误详情: {traceback.format_exc()}{c.RESET}")
        print(f"{c.CYAN}如果是依赖相关问题，请尝试使用 --auto-install 参数启动程序。{c.RESET}")
        #input("按Enter键重试...")
        sys.exit(1)

# 使用说明:
# 1. 双击此Python文件启动程序
# 2. 程序会自动检查必要的依赖
# 3. 如果遇到依赖问题，可以使用 --auto-install 参数自动安装缺失的依赖
#    例如: python start_pyqt_app.py --auto-install
# 4. 如果遇到问题，错误信息会显示在窗口中
# 5. FFmpeg需要手动安装并添加到系统PATH中
# 6. 更多帮助信息，请查看README.md文件