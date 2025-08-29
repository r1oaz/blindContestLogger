import wx
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# PyInstaller
output/
dist/
build/
*.spec

# VS Code
.vscode/

# System
*.log
*.tmp
.DS_Store
Thumbs.db# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# PyInstaller
output/
dist/
build/
*.spec

# VS Code
.vscode/

# System
*.log
*.tmp
.DS_Store
Thumbs.dbfrom settings_dialog import SettingsDialog
from log_window import LogWindow

def main():
    app = wx.App(False)
    dlg =    # Python
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    
    # PyInstaller
    output/
    dist/
    build/
    *.spec
    
    # VS Code
    .vscode/
    
    # System
    *.log
    *.tmp
    .DS_Store
    Thumbs.db    # Python
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    
    # PyInstaller
    output/
    dist/
    build/
    *.spec
    
    # VS Code
    .vscode/
    
    # System
    *.log
    *.tmp
    .DS_Store
    Thumbs.db SettingsDialog(None)
    if dlg.ShowModal() == wx.ID_OK:
        settings = dlg.get_settings()
        dlg.Destroy()
        frame = LogWindow(None, settings)
        frame.Show()
        app.MainLoop()
    else:
        dlg.Destroy()

if __name__ == "__main__":
    main()
