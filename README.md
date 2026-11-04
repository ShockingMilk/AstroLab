# AstroCam

Raspberry Pi astronomy camera interface designed for live telescope
observation, planetary imaging, lunar imaging, bright-star imaging,
star-field imaging, and future astrophotography automation.

## Hardware

The project is designed around:

- Raspberry Pi 5
- Raspberry Pi-compatible CSI camera
- Raspberry Pi HQ Camera / IMX477 or another Picamera2-compatible camera
- HDMI display
- Optional external storage

The application attempts to discover hardware dynamically rather than
requiring a specific camera, display, or storage-device model.

## Current Features

- Full-screen live camera preview
- Keyboard-driven interface
- Automatic camera discovery
- Automatic display-resolution discovery
- Picamera2 sensor-mode discovery
- Automatic sensor-mode selection
- Explicit sensor-mode configuration
- Calibration profile
- Moon profile
- Planetary profile
- Bright-planet profile
- Bright-star profile
- Star-field profile
- Screenshot capture
- Video recording
- Histogram
- Focus assist
- Exposure adjustment
- Gain adjustment
- Clean-view mode
- Runtime configuration reload
- Dynamic storage selection
- Internal/external storage selection
- External storage auto-detection
- Free-space checking
- Storage recommendation
- Low-space indication
- Insufficient-storage popup
- Reusable popup system
- Vendor/model-independent storage handling

## Keyboard Controls

| Key | Function |
|---|---|
| 0 | Calibration |
| 1-9 | Observation profiles |
| S | Screenshot |
| C | Clean View |
| H | Histogram |
| F | Focus Assist |
| E | Exposure adjustment |
| G | Gain adjustment |
| Up/Down | Adjust selected exposure/gain |
| V | Video recording |
| L | Storage location |
| R | Reload configuration |
| Q | Exit |

The command legend is generated from the configuration file.

## Clean View

Clean View hides:

- Crosshair
- Command legend

The camera image remains full-screen.

The top HUD remains visible.

## Camera Modes

The application uses the sensor modes exposed by Picamera2.

It does not assume that a camera provides arbitrary sensor resolutions.

For example, if an IMX477 reports:

- 1332x990
- 2028x1080
- 2028x1520
- 4056x2160
- 4056x3040

those are the available sensor modes used for automatic selection.

A requested stream resolution may still be smaller than the sensor mode,
but that is treated as an output stream resolution rather than falsely
representing it as a native sensor mode.

## Storage

Storage is vendor/model independent.

The application does not look for a specific manufacturer or drive name.

Storage discovery uses mounted filesystem information and identifies
potential external storage using:

- USB transport
- removable-device status
- common removable mount locations

The application can operate in:

- Auto
- External
- Internal

mode.

### Auto

The application evaluates available storage and chooses an appropriate
location.

### External

External storage is required.

If no suitable external storage is available, the application displays
an error rather than silently saving somewhere else.

### Internal

The application uses internal storage.

## Storage Recommendation

Before captures or recordings, the application evaluates available
storage.

The recommendation considers:

- Required estimated space
- Available free space
- Configured safety margin
- Internal storage
- External storage

If neither location has enough available space, the operation is
blocked and a popup is displayed.

## Recording Safeguard

An active recording is never silently moved between storage devices.

If the storage device being used for an active recording disappears,
the recording is stopped and the user is notified.

## Directory Structure

External storage:

    Astronomy/
    ├── Images/
    ├── Videos/
    └── Logs/

Internal fallback:

    ~/Pictures/Astronomy/
    ├── Images/
    ├── Videos/
    └── Logs/

## Raspberry Pi Setup

Install the Raspberry Pi camera stack first.

Picamera2 is normally installed through the Raspberry Pi/Debian
package system rather than through this project's Python requirements.

Example:

    sudo apt update
    sudo apt install -y python3-picamera2 python3-opencv

Then install the Python dependencies:

    python3 -m pip install -r requirements.txt

Depending on the Raspberry Pi OS configuration, using the system Python
packages may be preferable to a virtual environment for Picamera2.

## Test Camera Discovery

Before launching AstroCam:

    rpicam-hello --list-cameras

The application itself uses Picamera2 to discover camera information
and sensor modes.

## Run

From the repository root:

    python3 run.py

## Configuration

The main configuration is:

    config/presets.json

The configuration controls:

- Camera selection
- Display resolution
- Storage behavior
- Profiles
- Camera controls
- Commands

The application can reload configuration using `R`.

## Project Layout

Source code is under:

    src/astrocam/

Subsystems are separated into:

    core/
    app/
    camera/
    capture/
    config/
    devices/
    storage/
    ui/

Enums are centralized in:

    src/astrocam/core/enums.py

Generic reusable functions are centralized in:

    src/astrocam/core/utils.py

## Future Expansion

The architecture is intended to support future additions such as:

- Additional observation profiles
- More cameras
- Additional storage formats
- FITS capture
- Planetary capture sequences
- Automated centering
- Telescope-control integration
- Calibration workflows
- Cluster-based astrophotography processing
- Additional astronomy-specific tools
