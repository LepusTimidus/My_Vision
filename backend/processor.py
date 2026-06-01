"""
processor.py — UHDRes 图像处理引擎

加载 UHDRes 模型权重，对上传的图片执行修复任务（低光增强/去雾/去模糊/去雨）。

用法：
    from processor import UHDResProcessor
    proc = UHDResProcessor()
    ok, msg = proc.process("input.jpg", "output.jpg", "dehaze")
"""

import os
import sys
import cv2
import torch
import numpy as np

# ── 添加 UHDRes 路径（避免触发 basicsr.__init__ 自动导入所有模型） ------------
_UHDRES_ARCH_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "UHDRes", "basicsr", "archs"
)
_UHDRES_UTILS_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "UHDRes", "basicsr", "utils"
)
for _d in [_UHDRES_ARCH_DIR, _UHDRES_UTILS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

# 单独导入所需模块（不经过 basicsr.__init__，跳过 pyiqa 等缺失依赖）
import UHDRes_arch
from img_util import img2tensor, tensor2img

# ── 配置 ------------------------------------------------------------------
WEIGHT_DIR = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "UHDRes", "PSCCNet_pretrained"
)

WEIGHT_MAP = {
    "lowlight": "UHD-LL.pth",
    "dehaze":   "UHD-Haze.pth",
    "deblur":   "UHD-Blur.pth",
    "derain":   "4K-Rain13k.pth",
}

TASK_NAMES = {
    "lowlight": "低光增强",
    "dehaze": "去雾",
    "deblur": "去模糊",
    "derain": "去雨",
}


class UHDResProcessor:
    """UHDRes 图像处理器（单例模式，模型只加载一次）"""

    _instance = None
    _models = {}       # task_type → (model, device)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------------------------------------------------------------
    def get_model(self, task_type: str):
        """按任务类型获取 / 缓存模型"""
        if task_type not in WEIGHT_MAP:
            raise ValueError(f"不支持的任务类型: {task_type}，可选: {list(WEIGHT_MAP.keys())}")

        if task_type not in self._models:
            weight_path = os.path.join(WEIGHT_DIR, WEIGHT_MAP[task_type])
            if not os.path.isfile(weight_path):
                raise FileNotFoundError(f"模型权重不存在: {weight_path}")

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            print(f"[UHDRes] 加载 {TASK_NAMES[task_type]} 模型 → {device}")

            model = UHDRes_arch.UHDRes().to(device)
            state = torch.load(weight_path, map_location=device, weights_only=True)
            model.load_state_dict(state["params"], strict=False)
            model.eval()

            self._models[task_type] = (model, device)

        return self._models[task_type]

    # ------------------------------------------------------------------
    def process(self, input_path: str, output_path: str, task_type: str):
        """
        对单张图片执行 UHDRes 修复。

        返回 (success: bool, message: str)
        """
        if not os.path.isfile(input_path):
            return False, f"输入文件不存在: {input_path}"

        try:
            model, device = self.get_model(task_type)

            # 读取图片
            img = cv2.imread(input_path, cv2.IMREAD_COLOR)
            if img is None:
                return False, f"无法读取图片: {input_path}"

            h, w = img.shape[:2]

            # 预处理：BGR → RGB、归一化、加 batch 维度
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            tensor = img2tensor(img_rgb).to(device) / 255.0
            tensor = tensor.unsqueeze(0)  # (1, C, H, W)

            # ── 检查尺寸是否能被模型下采样倍数整除 ──────────────
            # 模型有 2 次 PixelUnshuffle(2) 下采样，宽高必须被 4 整除
            # 使用模型自带的 check_image_size（按 16 对齐，确保安全）
            _, _, h_in, w_in = tensor.shape
            mod_pad_h = (16 - h_in % 16) % 16
            mod_pad_w = (16 - w_in % 16) % 16
            if mod_pad_h > 0 or mod_pad_w > 0:
                tensor = torch.nn.functional.pad(
                    tensor, (0, mod_pad_w, 0, mod_pad_h), mode='reflect'
                )

            # 推理
            with torch.no_grad():
                output = model.test(tensor)

            # 裁回原图尺寸（去掉 padding）
            output = output[:, :, :h, :w]
            output_img = tensor2img(output)  # uint8 RGB

            # RGB → BGR 后保存
            output_bgr = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            cv2.imwrite(output_path, output_bgr)

            if not os.path.isfile(output_path):
                return False, "保存结果失败"

            return True, f"{TASK_NAMES[task_type]} 处理成功"

        except Exception as e:
            return False, f"处理异常: {str(e)}"
