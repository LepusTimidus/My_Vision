import sys
from pathlib import Path
import torch
from PIL import Image
import os
import numpy as np

UHDRES_PATH = r"D:\Vision_Web\UHDRes"
sys.path.append(UHDRES_PATH)

# ======================
# 这里换成你模型的真实内容
# ======================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# 1. 加载模型（根据你的 UHDRes 改）
def load_uhdres_model():
    # 示例（你只需要改成你自己模型的加载方式）
    from model.module import SRModel  # 从 UHDRes 导入模型类
    model = SRModel()

    # 加载权重
    weight_path = os.path.join(UHDRES_PATH, "weights", "your_model.pth")
    model.load_state_dict(torch.load(weight_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model


# 全局只加载一次（提速）
model = load_uhdres_model()


# ======================
# 图像处理主函数
# ======================
def process_image_with_uhdres(image_path: str, output_dir: str = "results/"):
    """
    输入：图片路径
    输出：超分后的图片路径
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 1. 读取图片
    img = Image.open(image_path).convert("RGB")

    # 2. 预处理（按 UHDRes 要求）
    # --------------------------
    # 这里替换成你模型需要的预处理
    # --------------------------
    img_tensor = torch.from_numpy(np.array(img).transpose(2, 0, 1) / 255.0).float()
    img_tensor = img_tensor.unsqueeze(0).to(DEVICE)

    # 3. 模型推理
    with torch.no_grad():
        output_tensor = model(img_tensor)

    # 4. 后处理
    output_img = output_tensor.squeeze(0).cpu().numpy()
    output_img = (output_img.transpose(1, 2, 0) * 255.0).clip(0, 255).astype(np.uint8)
    output_img = Image.fromarray(output_img)

    # 5. 保存结果
    result_name = f"sr_{Path(image_path).stem}.png"
    result_path = os.path.join(output_dir, result_name)
    output_img.save(result_path)

    return result_path