from __future__ import annotations

import time

import cv2

from astrocam.capture.manager import (
    CaptureManager,
)
from astrocam.core.enums import (
    AdjustmentMode,
    CommandAction,
    PopupType,
)
from astrocam.core.utils import (
    switch,
)
from astrocam.storage.manager import (
    StorageUnavailableError,
)
from astrocam.ui.exposure import (
    ExposureController,
)
from astrocam.ui.focus import (
    FocusAssist,
)
from astrocam.ui.histogram import (
    Histogram,
)
from astrocam.ui.hud import (
    HUD,
)
from astrocam.ui.popup import (
    MessagePopup,
)


class UIController:

    def __init__(
        self,
        camera,
        display,
        presets,
        storage,
    ):

        self.camera = camera
        self.display = display
        self.presets = presets
        self.storage = storage

        self.capture = (
            CaptureManager(
                camera,
                storage,
                presets.data.get(
                    "capture",
                    {},
                ),
            )
        )

        self.histogram = Histogram()

        self.focus = FocusAssist()

        self.exposure = (
            ExposureController(
                camera
            )
        )

        self.hud = HUD(
            storage
        )

        self.active_profile = "0"
        self.active_profile_name = (
            self.presets.get_profile_name(
                "0"
            )
        )

        self.clean_view = False

        self.running = True

        self.popup = None

        self.last_frame_time = (
            time.monotonic()
        )

        self.fps = 0.0

    # ----------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------

    def run(self):

        self.apply_profile(
            "0"
        )

        while self.running:

            frame = (
                self.camera.capture_frame()
            )

            self._update_fps()

            metadata = (
                self.camera.capture_metadata()
            )

            if self.capture.recording:

                try:
                    self.capture.write_video_frame(
                        frame
                    )

                except StorageUnavailableError as exc:

                    self.show_popup(
                        "Recording Stopped",
                        str(exc),
                        PopupType.ERROR,
                    )

            display_frame = (
                self.display.resize_frame(
                    frame
                )
            )

            display_frame = (
                self.histogram.draw(
                    display_frame
                )
            )

            display_frame = (
                self.focus.draw(
                    display_frame
                )
            )

            commands = (
                self._legend_commands()
            )

            display_frame = (
                self.hud.draw(
                    display_frame,
                    self.active_profile_name,
                    self.fps,
                    metadata,
                    show_crosshair=(
                        not self.clean_view
                    ),
                    show_legend=(
                        not self.clean_view
                    ),
                    commands=commands,
                )
            )

            if self.popup:
                display_frame = (
                    self.popup.draw(
                        display_frame
                    )
                )

            cv2.imshow(
                "AstroCam",
                display_frame,
            )

            key = cv2.waitKeyEx(1)

            if key != -1:
                self.handle_key(
                    key
                )

            if (
                self.popup
                and self.popup.finished
            ):
                result = (
                    self.popup.get_result()
                )

                self.handle_popup_result(
                    result
                )

                self.popup = None

        self.shutdown()

    def _update_fps(self):

        now = time.monotonic()

        delta = (
            now
            - self.last_frame_time
        )

        if delta > 0:
            current = 1.0 / delta

            self.fps = (
                self.fps * 0.90
                + current * 0.10
            )

        self.last_frame_time = now

    # ----------------------------------------------------------
    # Keyboard
    # ----------------------------------------------------------

    def handle_key(
        self,
        key,
    ):

        if self.popup:

            self.popup.handle_key(
                key
            )

            return

        if key == ord("q"):
            self.running = False
            return

        if key == ord("c"):
            self.clean_view = (
                not self.clean_view
            )
            return

        if key == ord("h"):
            self.histogram.toggle()
            return

        if key == ord("f"):
            self.focus.toggle()
            return

        if key == ord("s"):
            self.take_screenshot()
            return

        if key == ord("v"):
            self.toggle_video()
            return

        if key == ord("r"):
            self.reload()
            return

        if key == ord("l"):
            self.show_storage_selector()
            return

        if key == ord("e"):
            self.exposure.set_mode(
                AdjustmentMode.EXPOSURE
            )
            return

        if key == ord("g"):
            self.exposure.set_mode(
                AdjustmentMode.GAIN
            )
            return

        if key == 82:
            self.exposure.adjust(1)
            return

        if key == 84:
            self.exposure.adjust(-1)
            return

        if ord("0") <= key <= ord("9"):

            profile_number = (
                chr(key)
            )

            if (
                self.presets.get_profile(
                    profile_number
                )
                is not None
            ):
                self.apply_profile(
                    profile_number
                )

    # ----------------------------------------------------------
    # Profiles
    # ----------------------------------------------------------

    def apply_profile(
        self,
        profile_number,
    ):

        profile = (
            self.presets.get_profile(
                profile_number
            )
        )

        if not profile:
            return

        camera_config = (
            profile.get(
                "camera",
                {},
            )
        )

        controls = (
            profile.get(
                "controls",
                {},
            )
        )

        focus_config = (
            profile.get(
                "focus",
                {},
            )
        )

        self.camera.set_camera_mode(
            camera_config
        )

        self.camera.set_controls(
            controls
        )

        self.focus.configure(
            focus_config
        )

        self.active_profile = (
            str(profile_number)
        )

        self.active_profile_name = (
            self.presets.get_profile_name(
                profile_number
            )
        )

    # ----------------------------------------------------------
    # Commands
    # ----------------------------------------------------------

    def execute_action(
        self,
        action,
        options=None,
    ):

        action = (
            CommandAction.from_value(
                action
            )
        )

        handlers = {

            CommandAction.SCREENSHOT:
                self.take_screenshot,

            CommandAction.CLEAN_VIEW:
                self.toggle_clean_view,

            CommandAction.HISTOGRAM:
                self.histogram.toggle,

            CommandAction.FOCUS_ASSIST:
                self.focus.toggle,

            CommandAction.RECORD_VIDEO:
                self.toggle_video,

            CommandAction.STORAGE_LOCATION:
                self.show_storage_selector,

            CommandAction.RELOAD:
                self.reload,

            CommandAction.EXIT:
                self.request_exit,
        }

        handler = handlers.get(
            action
        )

        if handler:
            return handler()

    # ----------------------------------------------------------
    # Capture
    # ----------------------------------------------------------

    def take_screenshot(self):

        frame = (
            self.camera.capture_frame()
        )

        try:

            path = (
                self.capture.capture_image(
                    frame,
                    self.active_profile_name,
                )
            )

            self.show_popup(
                "Screenshot Saved",
                str(path),
                PopupType.SUCCESS,
            )

        except (
            StorageUnavailableError,
            IOError,
        ) as exc:

            self.show_popup(
                "Unable to Save Image",
                str(exc),
                PopupType.ERROR,
            )

    def toggle_video(self):

        if self.capture.recording:

            self.capture.stop_video()

            self.show_popup(
                "Recording Stopped",
                "The video recording has been saved.",
                PopupType.SUCCESS,
            )

            return

        width, height = (
            self.camera.active_stream_size
        )

        fps = (
            self.camera.active_sensor_mode.fps
            if self.camera.active_sensor_mode
            else 30.0
        )

        try:

            path = (
                self.capture.start_video(
                    width,
                    height,
                    fps,
                    self.active_profile_name,
                )
            )

            self.show_popup(
                "Recording Started",
                str(path),
                PopupType.INFO,
            )

        except (
            StorageUnavailableError,
            IOError,
        ) as exc:

            self.show_popup(
                "Unable to Start Recording",
                str(exc),
                PopupType.ERROR,
            )

    # ----------------------------------------------------------
    # Storage selection
    # ----------------------------------------------------------

    def show_storage_selector(
        self,
    ):

        self.storage.refresh(
            force=True
        )

        external = (
            self.storage.get_best_external()
        )

        internal = (
            self.storage.get_internal_storage()
        )

        external_text = (
            f"External: "
            f"{external.free_gb:.1f} GB free"
            if external
            else
            "External: unavailable"
        )

        internal_text = (
            f"Internal: "
            f"{internal.free_gb:.1f} GB free"
            if internal
            else
            "Internal: unavailable"
        )

        recommendation = (
            self.storage.recommend_storage(
                0
            )
        )

        recommendation_text = (
            f"Recommended: "
            f"{recommendation.location.upper()}\n"
            f"{recommendation.reason}"
        )

        self.popup = MessagePopup(
            "Storage Location",
            [
                external_text,
                internal_text,
                recommendation_text,
            ],
            PopupType.SELECTION,
            [
                "Auto",
                "External",
                "Internal",
            ],
        )

    def handle_popup_result(
        self,
        result,
    ):

        if not result.accepted:
            return

        if result.value == "Auto":
            self.storage.set_selection(
                "auto"
            )

        elif result.value == "External":
            self.storage.set_selection(
                "external"
            )

        elif result.value == "Internal":
            self.storage.set_selection(
                "internal"
            )

    # ----------------------------------------------------------
    # Popups
    # ----------------------------------------------------------

    def show_popup(
        self,
        title,
        message,
        popup_type=PopupType.INFO,
        options=None,
    ):

        self.popup = MessagePopup(
            title,
            message,
            popup_type,
            options,
        )

    # ----------------------------------------------------------

    def toggle_clean_view(self):
        self.clean_view = (
            not self.clean_view
        )

    def request_exit(self):
        self.running = False

    def reload(self):

        try:

            self.presets.reload()

            self.storage.update_config(
                self.presets.storage
            )

            self.show_popup(
                "Configuration Reloaded",
                "Configuration was successfully reloaded.",
                PopupType.SUCCESS,
            )

        except Exception as exc:

            self.show_popup(
                "Reload Failed",
                str(exc),
                PopupType.ERROR,
            )

    def _legend_commands(self):

        commands = []

        for key, name, _, _ in (
            self.presets.get_command_items()
        ):

            commands.append(
                (
                    key,
                    name,
                )
            )

        for number in (
            "0",
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
        ):

            if (
                self.presets.get_profile(
                    number
                )
                is not None
            ):

                commands.append(
                    (
                        number,
                        self.presets.get_profile_name(
                            number
                        ),
                    )
                )

        return commands

    def shutdown(self):

        if self.capture.recording:
            self.capture.stop_video()

        self.camera.close()

        cv2.destroyAllWindows()