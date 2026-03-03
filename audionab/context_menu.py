"""Windows right-click context menu manager."""

import logging
import os
import sys

from . import SUPPORTED_ALL, REGISTRY_KEY_NAME, REGISTRY_LABEL, WIN11_CLASSIC_MENU_KEY

logger = logging.getLogger(__name__)


class ContextMenuManager:
    BAT_TEMPLATE = r'''@echo off
setlocal
chcp 65001 >nul 2>&1
title AudioNab
"{python_exe}" "{script_path}" --convert "%~1"
'''

    @staticmethod
    def is_admin():
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    @staticmethod
    def run_as_admin(args):
        if sys.platform != "win32":
            return False
        try:
            import ctypes
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(f'"{a}"' for a in args), None, 1
            )
            return ret > 32
        except Exception:
            logger.warning("Failed to elevate to admin", exc_info=True)
            return False

    @classmethod
    def install(cls, app_dir):
        if sys.platform != "win32":
            return False
        if not cls.is_admin():
            # Find the entry point script
            script_path = cls._find_script_path()
            return cls.run_as_admin([script_path, "--install"])
        try:
            import winreg
            bat_dir = os.path.join(app_dir, "launcher")
            os.makedirs(bat_dir, exist_ok=True)
            bat_path = os.path.join(bat_dir, "audionab.bat")
            script_path = cls._find_script_path()
            bat_content = cls.BAT_TEMPLATE.format(
                python_exe=sys.executable,
                script_path=script_path
            )
            with open(bat_path, "w") as f:
                f.write(bat_content)

            count = 0
            for ext in SUPPORTED_ALL:
                reg_paths = [
                    f"{ext}\\shell\\{REGISTRY_KEY_NAME}",
                    f"SystemFileAssociations\\{ext}\\shell\\{REGISTRY_KEY_NAME}"
                ]
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as k:
                        file_type = winreg.QueryValueEx(k, "")[0]
                        if file_type:
                            reg_paths.append(f"{file_type}\\shell\\{REGISTRY_KEY_NAME}")
                except Exception:
                    pass

                for rp in reg_paths:
                    try:
                        key = winreg.CreateKeyEx(
                            winreg.HKEY_CLASSES_ROOT, rp, 0, winreg.KEY_ALL_ACCESS
                        )
                        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, REGISTRY_LABEL)
                        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, "shell32.dll,168")
                        winreg.CloseKey(key)

                        cmd_key = winreg.CreateKeyEx(
                            winreg.HKEY_CLASSES_ROOT, f"{rp}\\command", 0, winreg.KEY_ALL_ACCESS
                        )
                        winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, f'"{bat_path}" "%1"')
                        winreg.CloseKey(cmd_key)
                        count += 1
                    except Exception:
                        pass
            logger.info("Installed context menu for %d extension registrations", count)
            return count > 0
        except ImportError:
            return False

    @classmethod
    def uninstall(cls):
        if sys.platform != "win32":
            return False
        if not cls.is_admin():
            script_path = cls._find_script_path()
            return cls.run_as_admin([script_path, "--uninstall"])
        try:
            import winreg
            removed = 0
            for ext in SUPPORTED_ALL:
                reg_paths = [
                    f"{ext}\\shell\\{REGISTRY_KEY_NAME}",
                    f"SystemFileAssociations\\{ext}\\shell\\{REGISTRY_KEY_NAME}"
                ]
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as k:
                        file_type = winreg.QueryValueEx(k, "")[0]
                        if file_type:
                            reg_paths.append(f"{file_type}\\shell\\{REGISTRY_KEY_NAME}")
                except Exception:
                    pass
                for rp in reg_paths:
                    try:
                        try:
                            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{rp}\\command")
                        except Exception:
                            pass
                        winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, rp)
                        removed += 1
                    except Exception:
                        pass
            logger.info("Uninstalled context menu (%d entries removed)", removed)
            return removed > 0
        except ImportError:
            return False

    @staticmethod
    def _find_script_path():
        """Find the main entry script path for context menu commands."""
        # When running as package, use __main__.py's parent
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(pkg_dir)

        # Check for shim first (audionab.py in project root)
        shim = os.path.join(parent_dir, "audionab.py")
        if os.path.exists(shim):
            return shim

        # Fall back to package __main__
        main_file = os.path.join(pkg_dir, "__main__.py")
        if os.path.exists(main_file):
            return main_file

        return os.path.abspath(sys.argv[0])

    @staticmethod
    def is_classic_menu_enabled():
        if sys.platform != "win32":
            return False
        try:
            import winreg
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN11_CLASSIC_MENU_KEY)
            return True
        except Exception:
            return False

    @staticmethod
    def enable_classic_menu():
        if sys.platform != "win32":
            return False
        try:
            import winreg
            key = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER, WIN11_CLASSIC_MENU_KEY,
                0, winreg.KEY_ALL_ACCESS
            )
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
            return True
        except Exception:
            logger.warning("Failed to enable classic menu", exc_info=True)
            return False

    @staticmethod
    def disable_classic_menu():
        if sys.platform != "win32":
            return False
        try:
            import winreg
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, WIN11_CLASSIC_MENU_KEY)
            try:
                winreg.DeleteKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}"
                )
            except Exception:
                pass
            return True
        except Exception:
            logger.warning("Failed to disable classic menu", exc_info=True)
            return False
