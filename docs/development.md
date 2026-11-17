
# Development Guide

## Python version

Python 3.10 or newer.

## System dependencies

Install the following packages through Raspberry Pi OS:

- `rpicam-apps`
- `python3-opencv`
- `python3-numpy`
- `python3-pil`
- `python3-tk`

Installation command:

```bash
sudo apt update

sudo apt install -y \
    rpicam-apps \
    python3-opencv \
    python3-numpy \
    python3-pil \
    python3-tk
```

## Project structure

The project uses a `src` layout.

Application source code is stored in:

`src/astro_assist/`

Configuration files are stored in:

`config/`

Documentation is stored in:

`docs/`

Tests are stored in:

`tests/`

## Launching the application

From the repository root:

```bash
python3 run.py
```

Alternatively:

```bash
./scripts/run.sh
```

## Running tests

Run the complete test suite:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Run an individual test module:

```bash
PYTHONPATH=src python3 -m unittest tests.test_utils -v
```

## Coding conventions

- Type annotate function parameters and return values.
- Use descriptive variable and function names.
- Prefer named arguments for clarity.
- Keep shared enums in `common/enums.py`.
- Keep reusable functions in `common/utils.py`.
- Separate configuration from implementation.
- Keep camera operations out of UI classes.
- Keep UI updates on the Tkinter main thread.
- Group related methods logically.
- Place `__init__` first in classes.
- Place cleanup and termination methods last.
- Document larger classes and functions.
- Avoid unnecessary duplication of similar functionality.

## Architecture conventions

### Application

The application module coordinates initialization and shutdown.

It should not contain camera decoding or detailed UI layout logic.

### Camera

Camera modules manage the external camera process and frame conversion.

They should not depend on Tkinter widgets.

### UI

Tkinter owns the application window and event loop.

UI modules display frames and handle user interaction.

They should not directly manage the camera subprocess.

### Configuration

Hardware and UI defaults belong in `config/settings.json`.

Implementation code should not contain machine-specific paths, IP addresses, credentials, or hardware vendor assumptions.

### Threading

The camera reader runs in a background thread.

Tkinter widgets must only be modified from the main thread.

The preview should prioritize displaying the newest available frame rather than accumulating old frames.

## Git workflow

Use a separate branch for each substantial change.

Example:

```bash
git switch -c feature/fullscreen-ui
```

After implementation and testing:

```bash
git status
git add .
git commit -m "Stabilize full-screen application UI"
```

Use descriptive commit messages that identify the change.

Do not commit:

- Captured astronomy images
- Video recordings
- Credentials
- Machine-specific settings
- Temporary test output
- Python cache files

## Development priorities

The immediate priority is Milestone 1:

1. Establish a stable full-screen application.
2. Verify the camera preview.
3. Ensure all controls fit the display.
4. Verify camera startup and shutdown.
5. Verify calibration profile 0.
6. Complete documentation and initial tests.

Avoid adding advanced capture or processing functionality until the application shell is reliable.
