# Removes autostart 
 
try:
    import winreg
except ImportError:
    raise SystemExit("Only  works on Windows.")

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "EyeProtector2020"

def main():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, VALUE_NAME)
        winreg.CloseKey(key)
        print("Removed from startup.")
    except FileNotFoundError:
        print("No autostart entry found.")


if __name__ == "__main__":
    main()   