#!/usr/bin/env python3

import subprocess
import winreg
from pathlib import Path

def run(version):
    registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
    registry_key = r"SOFTWARE\Microsoft\VisualStudio\Setup"

    if version == "2017" or version == 2017:
        version_range = "[15.0,16.0)"
    elif version == "2019" or version == 2019:
        version_range = "[16.0,17.0)"
    else:
        assert False, "unknown Visual Studio version {}".format(version)

    registry_key = winreg.OpenKey(registry, registry_key)
    for i in range(0, winreg.QueryInfoKey(registry_key)[1]):
        sub_value = winreg.EnumValue(registry_key, i)
        if sub_value[0] == "SharedInstallationPath":
            shared_install_dir = Path(sub_value[1])
            vswhere_path = Path(shared_install_dir).parent.absolute() / Path("Installer/vswhere.exe")
            if vswhere_path.exists():
                vs_path = Path(subprocess.check_output([vswhere_path, "-version", version_range, "-property", "installationPath"]).decode("utf-8").splitlines()[0])
                return vs_path
