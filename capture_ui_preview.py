"""本地生成 EasyEnglishListening 主界面截图。

用法：
  python capture_ui_preview.py
  python capture_ui_preview.py --output artifacts/ui_preview.png
  python capture_ui_preview.py --show
"""

from __future__ import annotations

import argparse
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 PyQt 主界面截图")
    parser.add_argument(
        "--output",
        default=os.path.join("artifacts", "ui_preview.png"),
        help="截图输出路径（默认：artifacts/ui_preview.png）",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="显示窗口而不是离屏渲染（便于手动观察）",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # 仅在离屏模式下注入环境变量，避免影响用户正常使用
    if not args.show:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PyQt5.QtWidgets import QApplication
    except Exception as exc:  # noqa: BLE001
        print("未检测到 PyQt5，请先安装依赖：pip install PyQt5", file=sys.stderr)
        print(f"详细错误：{exc}", file=sys.stderr)
        return 1

    from audio_segmenter_pyqt import AudioSegmenterPyQt

    app = QApplication([])
    window = AudioSegmenterPyQt()
    window.show()
    app.processEvents()

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    ok = window.grab().save(args.output)
    if not ok:
        print(f"截图保存失败：{args.output}", file=sys.stderr)
        return 2

    print(f"截图已保存：{args.output}")

    if args.show:
        return app.exec_()

    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
