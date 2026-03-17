import ctypes
import os
import winreg


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Default opener used when double-clicking a .noui file.
DEFAULT_OPEN_APP = os.path.join(BASE_DIR, "gameEngine", "main.dist", "main.exe")
# Default filetype icon shown by Windows Explorer.
DEFAULT_ICON = os.path.join(BASE_DIR, "systemTrayDesktopApp", "icon.png")

def register_noui_filetype(
    app_exe_path: str = DEFAULT_OPEN_APP,
    icon_path: str = DEFAULT_ICON,
    prog_id: str = "AIAutostart.noui",
    extension: str = ".noui",
) -> None:
    """
    Register .noui as a Windows file type in HKCU (no admin required).

    - Associates .noui with a ProgID
    - Sets default open command to *app_exe_path*
    - Sets file icon to *icon_path*
    """
    # Normalize incoming paths
    app_exe_path = os.path.abspath(app_exe_path)
    icon_path = os.path.abspath(icon_path)

    # Validate required assets before touching registry.
    if not os.path.exists(app_exe_path):
        raise FileNotFoundError(f"No .noui opener app found: {app_exe_path}")
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"No icon file found: {icon_path}")

    # Use per-user Classes branch (HKCU) so admin rights are not required.
    root = winreg.HKEY_CURRENT_USER
    classes_root = r"Software\Classes"

    # Extension key: maps .noui -> ProgID.
    ext_key_path = f"{classes_root}\\{extension}"

    # ProgID key: the file type identity and metadata bucket.
    progid_key_path = f"{classes_root}\\{prog_id}"

    # Open command key: command used on double-click/open.
    command_key_path = f"{progid_key_path}\\shell\\open\\command"

    # DefaultIcon key: icon shown for .noui files in Explorer.
    default_icon_key_path = f"{progid_key_path}\\DefaultIcon"

    # Write extension -> ProgID association.
    with winreg.CreateKeyEx(root, ext_key_path, 0, winreg.KEY_WRITE) as ext_key:
        winreg.SetValueEx(ext_key, None, 0, winreg.REG_SZ, prog_id)

    # Write user-friendly display name for this file type.
    with winreg.CreateKeyEx(root, progid_key_path, 0, winreg.KEY_WRITE) as progid_key:
        winreg.SetValueEx(progid_key, None, 0, winreg.REG_SZ, "No UI Game File")

    # "%1" is replaced by the clicked .noui file path by Windows.
    open_command = f'"{app_exe_path}" "%1"'
    with winreg.CreateKeyEx(root, command_key_path, 0, winreg.KEY_WRITE) as cmd_key:
        winreg.SetValueEx(cmd_key, None, 0, winreg.REG_SZ, open_command)

    # Setting the icon - ",0" refers to "first icon resource" in the file.
    with winreg.CreateKeyEx(root, default_icon_key_path, 0, winreg.KEY_WRITE) as icon_key:
        winreg.SetValueEx(icon_key, None, 0, winreg.REG_SZ, f'"{icon_path}",0')

    # Notify Explorer that file associations changed (refresh icon/open behavior).
    SHCNE_ASSOCCHANGED = 0x08000000
    SHCNF_IDLIST = 0x0000
    ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)