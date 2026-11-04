from __future__ import annotations

import cv2


class HUD:

    def __init__(
        self,
        storage=None,
    ):
        self.storage = storage

    def draw(
        self,
        frame,
        profile_name,
        fps,
        metadata=None,
        show_crosshair=True,
        show_legend=True,
        commands=None,
    ):

        output = frame.copy()

        height, width = (
            output.shape[:2]
        )

        exposure = "--"
        gain = "--"

        if metadata:

            if "ExposureTime" in metadata:
                exposure = str(
                    metadata[
                        "ExposureTime"
                    ]
                )

            if "AnalogueGain" in metadata:
                gain = f"{metadata['AnalogueGain']:.2f}"

        storage_text = ""

        if self.storage:
            storage_text = (
                self.storage.status_text()
            )

        top_text = (
            f"{profile_name} | "
            f"FPS {fps:.1f} | "
            f"EXP {exposure} | "
            f"GAIN {gain}"
        )

        if storage_text:
            top_text += (
                f" | {storage_text}"
            )

        cv2.putText(
            output,
            top_text,
            (12, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        if show_crosshair:

            center_x = width // 2
            center_y = height // 2

            cv2.line(
                output,
                (
                    center_x - 20,
                    center_y,
                ),
                (
                    center_x + 20,
                    center_y,
                ),
                (255, 255, 255),
                1,
            )

            cv2.line(
                output,
                (
                    center_x,
                    center_y - 20,
                ),
                (
                    center_x,
                    center_y + 20,
                ),
                (255, 255, 255),
                1,
            )

        if (
            show_legend
            and commands
        ):

            self._draw_legend(
                output,
                commands,
            )

        return output

    def _draw_legend(
        self,
        frame,
        commands,
    ):

        height, width = (
            frame.shape[:2]
        )

        row1 = []
        row2 = []
        row3 = []

        for key, name in commands:

            if key == "0":
                row3.append(
                    f"{key}:{name}"
                )

            elif key in (
                "1",
                "2",
                "3",
                "4",
                "5",
            ):
                row1.append(
                    f"{key}:{name}"
                )

            elif key in (
                "6",
                "7",
                "8",
                "9",
            ):
                row2.append(
                    f"{key}:{name}"
                )

            else:
                row3.append(
                    f"{key}:{name}"
                )

        rows = [
            row1,
            row2,
            row3,
        ]

        y = height - 48

        for row in rows:

            if not row:
                continue

            text = "  ".join(row)

            cv2.putText(
                frame,
                text,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.38,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

            y += 18