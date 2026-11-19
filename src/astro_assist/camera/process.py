"""Manage the external rpicam-vid process."""

import queue
import subprocess
import threading
from typing import Optional

class CameraProcess:
    """Start, monitor, and stop a camera streaming process."""

    def __init__(self, command: list[str], frame_size: int) -> None:
        if frame_size <= 0:
            raise ValueError("Frame size must be positive.")

        self.command = command
        self.frame_size = frame_size

        self.process: Optional[subprocess.Popen[bytes]] = None
        self.frame_queue: queue.Queue[bytes] = queue.Queue(maxsize=1)

        self.reader_thread: Optional[threading.Thread] = None
        self.running = False
        self.error_message: Optional[str] = None

    def start(self) -> None:
        """Start the camera process and its frame reader."""
        if self.running:
            return

        self._clear_frame_queue()
        self.error_message = None

        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )

        if self.process.stdout is None:
            self.process.terminate()
            self.process.wait(timeout=3)
            self.process = None
            raise RuntimeError("Camera process did not provide stdout.")

        self.running = True
        self.reader_thread = threading.Thread(
            target=self._read_frames,
            name="CameraFrameReader",
            daemon=True,
        )
        self.reader_thread.start()

    def stop(self) -> None:
        """Terminate the process and wait for its reader thread."""
        self.running = False

        process = self.process

        if process is not None:
            if process.poll() is None:
                process.terminate()

                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)

            if process.stdout is not None:
                try:
                    process.stdout.close()
                except OSError:
                    pass

        if self.reader_thread is not None:
            self.reader_thread.join(timeout=3)

        self.process = None
        self.reader_thread = None
        self._clear_frame_queue()

    def get_frame(self) -> Optional[bytes]:
        """Return the newest available raw frame."""
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def wait_for_frame(self, timeout: float) -> Optional[bytes]:
        """Wait for a complete frame, up to the specified timeout."""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _read_exact(self, size: int) -> Optional[bytes]:
        """Read exactly one frame from the camera stream."""
        if self.process is None or self.process.stdout is None:
            return None

        data = bytearray()

        while self.running and len(data) < size:
            chunk = self.process.stdout.read(size - len(data))

            if not chunk:
                return None

            data.extend(chunk)

        if len(data) != size:
            return None

        return bytes(data)

    def _read_frames(self) -> None:
        """Continuously read frames into a one-frame queue."""
        while self.running:
            try:
                frame = self._read_exact(self.frame_size)

                if frame is None:
                    if self.running:
                        self.error_message = "Camera stream ended unexpectedly."
                    break

                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass

                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    pass

            except (OSError, ValueError) as exc:
                if self.running:
                    self.error_message = str(exc)
                break

        self.running = False

    def _clear_frame_queue(self) -> None:
        """Discard any frames left from an earlier stream."""
        while True:
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break