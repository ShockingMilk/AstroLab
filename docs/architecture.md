
# Architecture

## Overview

Astro Assist separates application startup, camera management,
device discovery, configuration, and UI responsibilities.

## Application flow

run.py
  |
  v
Application
  |
  +-- ConfigLoader
  |
  +-- DeviceManager
  |
  +-- CameraManager
  |     |
  |     +-- CameraProcess
  |
  +-- MainWindow
        |
        +-- CameraPreview
        |
        +-- ControlPanel
        |
        +-- StatusBar

## Camera data flow

IMX477
  |
  v
rpicam-vid
  |
  v
YUV420 stdout stream
  |
  v
CameraProcess background reader
  |
  v
Latest-frame queue
  |
  v
CameraManager
  |
  v
OpenCV YUV420 to BGR conversion
  |
  v
CameraPreview
  |
  v
Tkinter display

## UI ownership

Tkinter owns the application window and event loop.

OpenCV is used for image processing only. It must not create
a second preview window.

## Threading

The camera reader runs in a background thread.

The Tkinter main thread retrieves the newest available frame
and updates the UI.

Tkinter widgets must only be modified from the main thread.

The frame queue holds at most one frame. Older frames are
discarded if the UI cannot keep up.

## Configuration

Hardware and UI defaults are stored in config/settings.json.

Implementation code should not contain machine-specific paths,
IP addresses, credentials, or hardware vendor assumptions.
