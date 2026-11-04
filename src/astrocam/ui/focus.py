import cv2


class FocusAssist:

    def __init__(self):
        self.enabled = False
        self.roi_fraction = 0.25

    def configure(
        self,
        config,
    ):

        self.enabled = bool(
            config.get(
                "enabled",
                False,
            )
        )

        self.roi_fraction = float(
            config.get(
                "roi_fraction",
                0.25,
            )
        )

    def toggle(self):
        self.enabled = not self.enabled

    def calculate_score(
        self,
        frame,
    ):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY,
        )

        height, width = (
            gray.shape[:2]
        )

        fraction = max(
            0.05,
            min(
                0.90,
                self.roi_fraction,
            ),
        )

        roi_width = int(
            width * fraction
        )

        roi_height = int(
            height * fraction
        )

        x1 = (
            width - roi_width
        ) // 2

        y1 = (
            height - roi_height
        ) // 2

        roi = gray[
            y1:y1 + roi_height,
            x1:x1 + roi_width,
        ]

        score = cv2.Laplacian(
            roi,
            cv2.CV_64F,
        ).var()

        return score

    def draw(
        self,
        frame,
    ):

        if not self.enabled:
            return frame

        height, width = (
            frame.shape[:2]
        )

        fraction = max(
            0.05,
            min(
                0.90,
                self.roi_fraction,
            ),
        )

        roi_width = int(
            width * fraction
        )

        roi_height = int(
            height * fraction
        )

        x1 = (
            width - roi_width
        ) // 2

        y1 = (
            height - roi_height
        ) // 2

        x2 = (
            x1 + roi_width
        )

        y2 = (
            y1 + roi_height
        )

        score = (
            self.calculate_score(
                frame
            )
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (255, 255, 255),
            1,
        )

        cv2.putText(
            frame,
            f"FOCUS {score:.1f}",
            (
                x1 + 5,
                y1 + 20,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        return frame