import io
from typing import Optional

import matplotlib.pyplot as plt
from PIL import Image


def matplotlib_to_image(
    fig: Optional[plt.Figure] = None,
    dpi: int = 100,
    close_fig: bool = True
) -> Image.Image:
    """
    Matplotlib Figure를 PIL Image로 변환하는 공통 유틸

    Args:
        fig (plt.Figure, optional): 변환할 Figure 객체, None이면 현재 fig 사용
        dpi (int): 이미지 DPI
        close_fig (bool): 변환 후 fig 닫기 여부

    Returns:
        PIL.Image.Image: 이미지 객체
    """
    fig = fig or plt.gcf()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
    buf.seek(0)

    if close_fig:
        plt.close(fig)

    return Image.open(buf)
