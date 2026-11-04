from __future__ import annotations

from pathlib import Path

import cv2

from astrocam.core.utils import (
    estimate_image_size,
    estimate_video_size,
    filename_safe,
    now_timestamp,
)
from astrocam.storage.manager import (
    StorageUnavailableError,
)


class CaptureManager:

    def __init__(
        self,
        camera,
        storage,
        config,
    ):
        self.camera = camera
        self.storage = storage
        self.config = config

        self.video_writer = None
        self.video_directory = None
        self.video_path = None

        self.recording = False

    # ----------------------------------------------------------
    # Images
    # ----------------------------------------------------------

    def capture_image(
        self,
        frame,
        profile_name,
    ):

        height, width = (
            frame.shape[:2]
        )

        required_bytes = (
            estimate_image_size(
                width,
                height,
            )
        )

        recommendation = (
            self.storage.recommend_storage(
                required_bytes
            )
        )

        if not recommendation.sufficient:
            raise StorageUnavailableError(
                "There is not enough "
                "storage available for "
                "this image."
            )

        try:
            directory = (
                self.storage.get_directory(
                    "images"
                )
            )

        except StorageUnavailableError:
            raise

        timestamp = (
            now_timestamp()
        )

        safe_name = filename_safe(
            profile_name
        )

        filename = (
            f"astro_"
            f"{timestamp}_"
            f"{safe_name}.png"
        )

        path = (
            directory
            / filename
        )

        if not cv2.imwrite(
            str(path),
            frame,
        ):
            raise IOError(
                "OpenCV could not save "
                "the image."
            )

        return path

    # ----------------------------------------------------------
    # Video
    # ----------------------------------------------------------

    def start_video(
        self,
        width,
        height,
        fps,
        profile_name,
    ):

        if self.recording:
            return self.video_path

        minutes = float(
            self.config.get(
                "estimated_video_minutes",
                10,
            )
        )

        required_bytes = (
            estimate_video_size(
                width,
                height,
                fps,
                minutes * 60,
            )
        )

        recommendation = (
            self.storage.recommend_storage(
                required_bytes
            )
        )

        if not recommendation.sufficient:
            raise StorageUnavailableError(
                "There is not enough "
                "storage available for "
                "the configured recording "
                f"estimate of {minutes:g} "
                "minutes."
            )

        directory = (
            self.storage.get_directory(
                "videos"
            )
        )

        timestamp = (
            now_timestamp()
        )

        safe_name = filename_safe(
            profile_name
        )

        path = (
            directory
            / (
                f"astro_"
                f"{timestamp}_"
                f"{safe_name}.mp4"
            )
        )

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        writer = cv2.VideoWriter(
            str(path),
            fourcc,
            fps,
            (width, height),
        )

        if not writer.isOpened():
            raise IOError(
                "Unable to open video "
                "writer."
            )

        self.video_writer = writer
        self.video_directory = directory
        self.video_path = path
        self.recording = True

        return path

    def write_video_frame(
        self,
        frame,
    ):

        if not self.recording:
            return

        if not self.storage.is_path_available(
            self.video_directory
        ):
            self.stop_video()
            raise StorageUnavailableError(
                "The recording storage "
                "device is no longer "
                "available."
            )

        self.video_writer.write(
            frame
        )

    def stop_video(self):

        if self.video_writer:
            self.video_writer.release()

        self.video_writer = None
        self.video_directory = None
        self.video_path = None
        self.recording = False