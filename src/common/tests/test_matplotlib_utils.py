import matplotlib.pyplot as plt
from PIL import Image
from django.test.testcases import TestCase

from common.matplotlib_util import matplotlib_to_image


class MatplotlibUtilsTestDrive(TestCase):
    def test_matplotlib_to_image_returns_image(self):
        fig, ax = plt.subplots()
        ax.plot([0, 1, 2], [10, 20, 30])
        ax.set_title("Test Plot")

        img = matplotlib_to_image(fig, dpi=80, close_fig=True)

        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.format, 'PNG')

    def test_matplotlib_to_image_default_fig(self):
        plt.plot([1, 2, 3], [4, 5, 6])
        img = matplotlib_to_image()
        self.assertIsInstance(img, Image.Image)
