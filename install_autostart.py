# Adds pyw to HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run

import os
import sys
try:
    import winreg
except ImportError:
    raise SystemExit("Only works on Windows.")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "EyeProtector2020"

def find_pythonw():
    candidate = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if os.path.exists(candidate):
        return candidate
    return sys.executable

def main():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "eye_protector.pyw"))
    if not os.path.exists(script_path):
        raise SystemExit(f"Couldnt find eye_protector.pyw. " f"(looked in {script_path}).")
    
    pythonw = find_pythonw()
    command = f'"{pythonw}" "{script_path}"'

    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
    winreg.CloseKey(key)

    print("Added to startup.")
    print(f"  Registry key: HKEY_CURRENT_USER\\{RUN_KEY}")
    print(f"  Value name:   {VALUE_NAME}")
    print(f"  Command:      {command}")
    print("\neye_protector will launch automatically.")

    if __name__ == "__main__":
            main()