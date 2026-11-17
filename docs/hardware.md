# Hardware Baseline

## Main computer

- Raspberry Pi 5

## Display

- Raspberry Pi touchscreen
- Target resolution: 1024x600
- HDMI connection

The application should detect the active display dimensions
rather than assume that every installation uses 1024x600.

## Camera

- Raspberry Pi HQ Camera
- Sony IMX477 sensor

The application currently uses rpicam-vid.

The selected output dimensions are separate from the camera's
native sensor modes.

## Telescope

- Gskyer manual telescope
- Optional 3x Barlow lens

The telescope is manually adjusted and does not currently
provide motorized tracking.

## Camera orientation

The initial calibration setting uses 180-degree rotation
based on the previous daytime camera test.

This setting is configurable.
