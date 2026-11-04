import cv2
import numpy as np


class Histogram:

    def __init__(self):
        self.enabled = False

    def toggle(self):
        self.enabled = not self.enabled

    def draw(
        self,
        frame,
    ):

        if not self.enabled:
            return frame

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

        histogram = cv2.calcHist(
            [gray],
            [0],
            None,
            [256],
            [0, 256],
        )

        histogram = cv2.normalize(
            histogram,
            histogram,
            0,
            120,
            cv2.NORM_MINMAX,
        )

        height = 130
        width = 256

        canvas = np.zeros(
            (
                height,
                width,
                3,
            ),
            dtype=np.uint8,
        )

        for x in range(256):

            value = int(
                histogram[x][0]
            )

            cv2.line(
                canvas,
                (
                    x,
                    height,
                ),
                (
                    x,
                    height - value,
                ),
                (255, 255, 255),
                1,
            )

        frame[
            10:10 + height,
            10:10 + width,
        ] = canvas

        return frame