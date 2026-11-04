from __future__ import annotations

from dataclasses import dataclass

import cv2

from astrocam.core.enums import PopupType
from astrocam.core.utils import (
    split_lines,
)


@dataclass(frozen=True)
class PopupResult:
    accepted: bool
    value: str | None = None


class MessagePopup:

    def __init__(
        self,
        title,
        message,
        popup_type=PopupType.INFO,
        options=None,
    ):

        self.title = title
        self.popup_type = (
            PopupType.from_value(
                popup_type
            )
        )

        if isinstance(
            message,
            str,
        ):
            message = [message]

        self.message = []

        for line in message:
            self.message.extend(
                split_lines(
                    str(line),
                    58,
                )
            )

        self.options = (
            options
            or ["OK"]
        )

        self.selected_index = 0
        self.finished = False

        self.result = PopupResult(
            accepted=False
        )

    def handle_key(
        self,
        key,
    ):

        if key == 27:
            self.finished = True

            self.result = PopupResult(
                accepted=False
            )

            return

        if key in (
            81,
            2424832,
        ):
            self.selected_index = max(
                0,
                self.selected_index - 1,
            )

            return

        if key in (
            83,
            2555904,
        ):
            self.selected_index = min(
                len(self.options) - 1,
                self.selected_index + 1,
            )

            return

        if key in (
            13,
            10,
            32,
        ):
            self._accept()

            return

        if (
            ord("1")
            <= key
            <= ord("9")
        ):

            index = (
                key
                - ord("1")
            )

            if (
                index
                < len(self.options)
            ):
                self.selected_index = index
                self._accept()

    def _accept(self):

        self.result = PopupResult(
            accepted=True,
            value=self.options[
                self.selected_index
            ],
        )

        self.finished = True

    def draw(
        self,
        frame,
    ):

        output = frame.copy()

        height, width = (
            output.shape[:2]
        )

        popup_width = int(
            width * 0.78
        )

        popup_height = int(
            height * 0.50
        )

        x1 = (
            width
            - popup_width
        ) // 2

        y1 = (
            height
            - popup_height
        ) // 2

        x2 = (
            x1
            + popup_width
        )

        y2 = (
            y1
            + popup_height
        )

        overlay = output.copy()

        cv2.rectangle(
            overlay,
            (0, 0),
            (width, height),
            (0, 0, 0),
            -1,
        )

        output = cv2.addWeighted(
            output,
            0.30,
            overlay,
            0.70,
            0,
        )

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (30, 30, 30),
            -1,
        )

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            (180, 180, 180),
            2,
        )

        cv2.putText(
            output,
            self.popup_type.value.upper(),
            (x1 + 20, y1 + 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.38,
            (180, 180, 180),
            1,
            cv2.LINE_AA,
        )

        cv2.putText(
            output,
            self.title,
            (x1 + 20, y1 + 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        text_y = y1 + 105

        for line in self.message:

            cv2.putText(
                output,
                line,
                (x1 + 20, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (225, 225, 225),
                1,
                cv2.LINE_AA,
            )

            text_y += 27

        option_y = y2 - 28
        current_x = x1 + 20

        for index, option in enumerate(
            self.options
        ):

            text = (
                f"{index + 1}: "
                f"{option}"
            )

            size, _ = cv2.getTextSize(
                text,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                1,
            )

            box_width = (
                size[0] + 30
            )

            if (
                index
                == self.selected_index
            ):

                cv2.rectangle(
                    output,
                    (
                        current_x,
                        option_y - 25,
                    ),
                    (
                        current_x
                        + box_width,
                        option_y + 7,
                    ),
                    (80, 80, 80),
                    -1,
                )

            cv2.putText(
                output,
                text,
                (
                    current_x + 8,
                    option_y,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            current_x += (
                box_width + 12
            )

        return output