# Testing

## Milestone 1 acceptance

- [ ] Application launches.
- [ ] Application requests true full-screen mode.
- [ ] Taskbar is not visible during normal full-screen operation.
- [ ] Header remains visible.
- [ ] Preview remains visible.
- [ ] Controls remain visible.
- [ ] Layout works at 1024x600.
- [ ] Layout works when running windowed.
- [ ] Camera process starts.
- [ ] Camera frames reach the preview.
- [ ] Camera process stops on exit.
- [ ] Calibration profile 0 can be selected.
- [ ] Crosshair can be toggled.
- [ ] Camera rotation is configurable.
- [ ] Unit tests pass.
- [ ] Documentation is current.

## Camera testing

Test the application in daylight first.

Verify that the image orientation is correct before testing
through the telescope.

Confirm that the camera preview does not accumulate latency
when the application is left running.

## Full-screen testing

Test both:

1. Full-screen mode.
2. Windowed mode using F11.

Record the active desktop session type and display resolution
if the taskbar remains visible.

## Shutdown testing

Exit using:

- Escape
- Q
- Window close button

Verify that no rpicam-vid process remains running.
