"""Application command controls and live camera adjustments."""

import tkinter as tk

from collections.abc import Callable
from typing import Any

from astro_assist.common.exceptions import CameraError

class ControlPanel(tk.Frame):
    """Display profile selection and application commands."""

    def __init__(
        self,
        parent: tk.Misc,
        settings: dict,
        profiles: dict[str, dict[str, Any]],
        callbacks: dict[str, Callable[[], None]],
        allow_windowed_mode: bool = True,
    ) -> None:
        super().__init__(
            parent,
            bg=settings.get("background", "#101010"),
            height=settings.get("controls_height", 76),
        )

        self.pack_propagate(False)

        self.background = settings.get("background", "#101010")
        self.foreground = settings.get("foreground", "#FFFFFF")
        self.accent = settings.get("accent", "#36A3FF")

        self.live_controls_button: tk.Button | None = None

        profile_row = tk.Frame(self, bg=self.background)
        profile_row.pack(
            side="top",
            fill="both",
            expand=True,
            padx=4,
            pady=(3, 0),
        )

        action_row = tk.Frame(self, bg=self.background)
        action_row.pack(
            side="bottom",
            fill="both",
            expand=True,
            padx=4,
            pady=(0, 3),
        )

        for profile_id, profile in profiles.items():
            if not profile.get("enabled", True):
                continue

            name = profile.get("name", profile_id)

            self._create_button(
                parent=profile_row,
                text=f"{profile_id}  {name}",
                command=callbacks[f"profile:{profile_id}"],
                expand=True,
            )

        self._create_button(
            parent=action_row,
            text="Crosshair",
            command=callbacks["crosshair"],
        )

        self.live_controls_button = self._create_button(
            parent=action_row,
            text="Live Controls",
            command=callbacks["live_controls"],
        )

        if allow_windowed_mode:
            self._create_button(
                parent=action_row,
                text="Display Mode",
                command=callbacks["display_mode"],
            )

        self._create_button(
            parent=action_row,
            text="Exit",
            command=callbacks["exit"],
        )

    def set_live_controls_open(self, is_open: bool) -> None:
        """Update the live-controls button label."""
        if self.live_controls_button is not None:
            label = "Hide Adjustments" if is_open else "Live Controls"
            self.live_controls_button.configure(text=label)

    def _create_button(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        expand: bool = False,
    ) -> tk.Button:
        """Create a consistently styled command button."""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg="#202020",
            fg=self.foreground,
            activebackground=self.accent,
            activeforeground="#FFFFFF",
            relief="flat",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=5,
            takefocus=True,
        )

        button.pack(
            side="left",
            padx=3,
            pady=2,
            fill="both",
            expand=expand,
        )

        return button


class LiveControlsPanel(tk.Frame):
    """Provide touch- and mouse-friendly live camera adjustments."""

    def __init__(
        self,
        parent: tk.Misc,
        camera: Any,
        settings: dict,
        on_status: Callable[[str], None],
    ) -> None:
        self.background = settings.get("background", "#101010")
        self.foreground = settings.get("foreground", "#FFFFFF")
        self.accent = settings.get("accent", "#36A3FF")

        super().__init__(
            parent,
            bg=self.background,
            height=205,
            highlightthickness=1,
            highlightbackground="#333333",
        )

        self.camera = camera
        self.on_status = on_status

        self.supported = camera.camera_controls
        self.current = self._read_current_controls()

        self._scales: dict[str, tk.Scale] = {}
        self._value_labels: dict[str, tk.Label] = {}
        self._auto_variables: dict[str, tk.BooleanVar] = {}
        self._dependent_controls: dict[str, list[tk.Widget]] = {
            "AeEnable": [],
            "AwbEnable": [],
        }

        self.pack_propagate(False)

        self._create_groups()

    def _read_current_controls(self) -> dict[str, Any]:
        """Read current metadata, falling back gracefully if unavailable."""
        try:
            return self.camera.get_controls()
        except CameraError:
            return {}

    def _create_groups(self) -> None:
        """Create the three live-adjustment groups."""
        container = tk.Frame(self, bg=self.background)
        container.pack(fill="both", expand=True, padx=6, pady=4)

        for column in range(3):
            container.grid_columnconfigure(column, weight=1, uniform="group")

        self._create_exposure_group(container)
        self._create_white_balance_group(container)
        self._create_image_group(container)

    def _create_group(
        self,
        parent: tk.Misc,
        column: int,
        title: str,
    ) -> tk.Frame:
        """Create a consistently styled control group."""
        group = tk.Frame(
            parent,
            bg="#181818",
            padx=7,
            pady=4,
        )
        group.grid(
            row=0,
            column=column,
            sticky="nsew",
            padx=3,
        )

        tk.Label(
            group,
            text=title,
            bg="#181818",
            fg=self.accent,
            font=("Arial", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 2))

        return group

    def _create_exposure_group(self, parent: tk.Misc) -> None:
        """Create automatic and manual exposure controls."""
        group = self._create_group(parent, 0, "EXPOSURE")

        if "AeEnable" in self.supported:
            self._add_auto_toggle(
                group,
                "AeEnable",
                "Auto exposure",
            )

        self._add_scalar_control(
            group,
            "ExposureTime",
            "Exposure (µs)",
            self._exposure_value,
        )

        self._add_scalar_control(
            group,
            "AnalogueGain",
            "Analogue gain",
            self._decimal_value,
        )

    def _create_white_balance_group(self, parent: tk.Misc) -> None:
        """Create automatic and manual white-balance controls."""
        group = self._create_group(parent, 1, "WHITE BALANCE")

        if "AwbEnable" in self.supported:
            self._add_auto_toggle(
                group,
                "AwbEnable",
                "Auto white balance",
            )

        self._add_scalar_control(
            group,
            "ColourTemperature",
            "Temperature (K)",
            self._integer_value,
        )

        self._add_colour_gains(group)

    def _create_image_group(self, parent: tk.Misc) -> None:
        """Create image appearance controls."""
        group = self._create_group(parent, 2, "IMAGE")

        controls = (
            ("Brightness", "Brightness"),
            ("Contrast", "Contrast"),
            ("Saturation", "Saturation"),
            ("Sharpness", "Sharpness"),
        )

        for name, label in controls:
            self._add_scalar_control(
                group,
                name,
                label,
                self._decimal_value,
            )

    def _add_auto_toggle(
        self,
        parent: tk.Misc,
        name: str,
        label: str,
    ) -> None:
        """Add an automatic-mode checkbox."""
        limits = self.supported[name]
        default = limits[2] if len(limits) == 3 else True
        current = self.current.get(name, default)

        variable = tk.BooleanVar(value=bool(current))
        self._auto_variables[name] = variable

        checkbox = tk.Checkbutton(
            parent,
            text=label,
            variable=variable,
            command=lambda key=name: self._toggle_auto(key),
            bg="#181818",
            fg=self.foreground,
            activebackground="#181818",
            activeforeground=self.foreground,
            selectcolor="#303030",
            font=("Arial", 9),
            anchor="w",
            padx=2,
            pady=1,
        )
        checkbox.pack(fill="x")

    def _add_scalar_control(
        self,
        parent: tk.Misc,
        name: str,
        label: str,
        formatter: Callable[[float], str],
    ) -> None:
        """Add a range-based slider when the camera supports the control."""
        if name not in self.supported:
            return

        limits = self.supported[name]

        if not isinstance(limits, (tuple, list)) or len(limits) != 3:
            return

        minimum, maximum, default = limits

        if not isinstance(minimum, (int, float)):
            return

        if not isinstance(maximum, (int, float)):
            return

        current = self.current.get(name, default)

        if current is None:
            current = default if default is not None else minimum

        if isinstance(current, bool) or not isinstance(current, (int, float)):
            current = minimum

        row = tk.Frame(parent, bg="#181818")
        row.pack(fill="x", pady=1)

        value_label = tk.Label(
            row,
            text=formatter(float(current)),
            bg="#181818",
            fg=self.foreground,
            font=("Arial", 8),
            width=9,
            anchor="e",
        )
        value_label.pack(side="right")

        tk.Label(
            row,
            text=label,
            bg="#181818",
            fg=self.foreground,
            font=("Arial", 8),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        is_integer = (
            isinstance(minimum, int)
            and isinstance(maximum, int)
        )

        resolution = 1 if is_integer else max(
            (maximum - minimum) / 200,
            0.01,
        )

        scale = tk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            resolution=resolution,
            orient="horizontal",
            showvalue=False,
            length=210,
            sliderlength=22,
            width=16,
            bg="#181818",
            fg=self.foreground,
            troughcolor="#383838",
            activebackground=self.accent,
            highlightthickness=0,
            bd=0,
            command=lambda value, key=name, fmt=formatter:
                self._on_scalar_change(key, value, fmt),
        )
        scale.set(current)
        scale.pack(fill="x", padx=2)

        self._scales[name] = scale
        self._value_labels[name] = value_label

        if name in ("ExposureTime", "AnalogueGain"):
            self._dependent_controls["AeEnable"].append(scale)

        if name in ("ColourTemperature",):
            self._dependent_controls["AwbEnable"].append(scale)

        self._apply_auto_states()

    def _add_colour_gains(self, parent: tk.Misc) -> None:
        """Add separate red and blue controls for ColourGains."""
        if "ColourGains" not in self.supported:
            return

        limits = self.supported["ColourGains"]
        if not isinstance(limits, (tuple, list)) or len(limits) != 3:
            return

        minimum, maximum, default = limits

        if not isinstance(minimum, (int, float)):
            return

        if not isinstance(maximum, (int, float)):
            return

        current = self.current.get("ColourGains", default)

        if not isinstance(current, (tuple, list)) or len(current) != 2:
            current = (1.0, 1.0)

        self._colour_gain_values = [
            float(current[0]),
            float(current[1]),
        ]

        for index, channel in enumerate(("Red gain", "Blue gain")):
            row = tk.Frame(parent, bg="#181818")
            row.pack(fill="x", pady=1)

            value_label = tk.Label(
                row,
                text=f"{self._colour_gain_values[index]:.2f}",
                bg="#181818",
                fg=self.foreground,
                font=("Arial", 8),
                width=9,
                anchor="e",
            )
            value_label.pack(side="right")

            tk.Label(
                row,
                text=channel,
                bg="#181818",
                fg=self.foreground,
                font=("Arial", 8),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            scale = tk.Scale(
                parent,
                from_=minimum,
                to=maximum,
                resolution=0.05,
                orient="horizontal",
                showvalue=False,
                length=210,
                sliderlength=22,
                width=16,
                bg="#181818",
                fg=self.foreground,
                troughcolor="#383838",
                activebackground=self.accent,
                highlightthickness=0,
                bd=0,
                command=lambda value, i=index:
                    self._on_colour_gain_change(i, value),
            )
            scale.set(self._colour_gain_values[index])
            scale.pack(fill="x", padx=2)

            self._value_labels[f"ColourGains:{index}"] = value_label
            self._dependent_controls["AwbEnable"].append(scale)

    @staticmethod
    def _integer_value(value: float) -> str:
        return f"{int(value)}"

    @staticmethod
    def _decimal_value(value: float) -> str:
        return f"{value:.2f}"

    @staticmethod
    def _exposure_value(value: float) -> str:
        return f"{int(value)}"

    def _on_scalar_change(
        self,
        name: str,
        raw_value: str,
        formatter: Callable[[float], str],
    ) -> None:
        """Apply a slider adjustment immediately."""
        value = float(raw_value)

        limits = self.supported[name]
        if (
            isinstance(limits[0], int)
            and isinstance(limits[1], int)
        ):
            value = int(round(value))

        self._value_labels[name].configure(
            text=formatter(float(value))
        )

        self._apply_controls({name: value})

    def _on_colour_gain_change(
        self,
        index: int,
        raw_value: str,
    ) -> None:
        """Apply one white-balance channel while preserving the other."""
        value = float(raw_value)
        self._colour_gain_values[index] = value

        self._value_labels[f"ColourGains:{index}"].configure(
            text=f"{value:.2f}"
        )

        self._apply_controls(
            {"ColourGains": tuple(self._colour_gain_values)}
        )

    def _toggle_auto(self, name: str) -> None:
        """Enable or disable the selected automatic camera mode."""
        enabled = self._auto_variables[name].get()

        self._apply_controls({name: enabled})
        self._apply_auto_states()

    def _apply_auto_states(self) -> None:
        """Enable manual sliders only when their automatic mode is off."""
        for auto_name, widgets in self._dependent_controls.items():
            automatic = self._auto_variables.get(auto_name)

            if automatic is None:
                continue

            state = tk.DISABLED if automatic.get() else tk.NORMAL

            for widget in widgets:
                widget.configure(state=state)

    def _apply_controls(self, values: dict[str, Any]) -> None:
        """Send validated control changes to the camera."""
        try:
            self.camera.set_controls(values)
            self.on_status("Camera adjustments updated")
        except CameraError as exc:
            self.on_status(f"Adjustment failed: {exc}")
