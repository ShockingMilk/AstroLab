from __future__ import annotations

import os
from pathlib import Path

from astrocam.camera.controller import CameraController
from astrocam.config.presets import PresetManager
from astrocam.devices.display import DisplayController
from astrocam.devices.manager import DeviceManager
from astrocam.storage.manager import StorageManager
from astrocam.ui.controller import UIController


def project_root() -> Path:
    '''
        Provides the root path of the project

        :rtype: Path
        :returns: Path to root of project
    '''
    return Path(__file__).resolve().parents[3]


def configuration_path() -> Path:
    '''
        Provides the path to the Configuration .json of project

        :rtype: Path
        :returns: Path to project's config file
    '''
    configured = os.environ.get('ASTROCAM_CONFIG')

    if configured:
        return Path(configured).expanduser()

    return f'{project_root()}/config/presets.json'


def main() -> None:
    '''
        Main function to run entire camera program
    '''
    print('Starting AstroCam...')

    config_path = configuration_path()
    
    presets = PresetManager(path=config_path)
    device_manager = DeviceManager(camera_config=presets.camera)
    
    inventory = device_manager.detect()
    device_manager.print_summary(inventory)
    camera_info = device_manager.select_camera(inventory)
    
    camera = CameraController(
        camera_info,
        config=presets.camera
    )
    
    display = DisplayController(
        displays=inventory.displays,
        config=presets.display
    )
    
    storage = StorageManager(config=presets.storage)
    storage.refresh(force=True)

    ui = UIController(
        camera=camera,
        display=display,
        presets=presets,
        storage=storage
    )

    ui.run()

if __name__ == "__main__":
    main()