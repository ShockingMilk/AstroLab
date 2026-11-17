# Astro Assist

Astro Assist is a Raspberry Pi-based telescope camera application.

The initial goal is to provide a stable, full-screen camera preview and a foundation for later astrophotography capture and processing.

## Hardware

Current target hardware:

- Raspberry Pi 5
- Raspberry Pi touchscreen display
- Raspberry Pi HQ Camera with IMX477 sensor
- Gskyer manual telescope
- Optional 3x Barlow lens

The application is designed to avoid hard-coded assumptions about specific camera models, display sizes, or external storage devices.

## Milestone 1

The first milestone establishes:

- Full-screen Tkinter application window
- Responsive camera preview
- Managed `rpicam-vid` camera process
- Keyboard controls
- Calibration profile 0
- Configurable camera rotation
- Clean startup and shutdown
- Basic device discovery
- Initial documentation and tests

## Installation

Install Raspberry Pi OS packages:

```bash
sudo apt update

sudo apt install -y \
    rpicam-apps \
    python3-opencv \
    python3-numpy \
    python3-pil \
    python3-tk
```

Clone the repository:

```bash
git clone <repository-url>
cd astro-assist
```

Make the launcher executable:

```bash
chmod +x run.py
chmod +x scripts/run.sh
```

Start the application:

```bash
python3 run.py
```

Alternatively:

```bash
./scripts/run.sh
```

## Keyboard controls

| Key | Action |
| --- | --- |
| 0 | Calibration profile |
| C | Toggle crosshair |
| F11 | Toggle full-screen |
| Q | Exit |
| Escape | Exit |

## Configuration

Default settings are stored in:

`config/settings.json`

Camera output dimensions, frame rate, rotation, UI colors, and keyboard controls are configured there.

The configuration is intended to keep hardware-specific settings separate from application implementation.

## Camera architecture

Astro Assist uses one managed `rpicam-vid` process.

The process outputs YUV420 frames through standard output. The application reads those frames in a background thread and uses OpenCV to convert them for display.

Tkinter owns the application window.

OpenCV does not create a separate preview window.

## Development

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run the application:

```bash
python3 run.py
```

See `docs/development.md` for development conventions and workflow.

## Current limitations

Milestone 1 does not yet implement:

- Multiple observing profiles
- Exposure and gain adjustment
- Histogram display
- Focus assistance
- Image or video capture
- External storage selection
- Image stacking
- Distributed processing

These are planned for later milestones.

## Project direction

See `docs/project-roadmap.md` for the planned development phases.
