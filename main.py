import wx
from settings_dialog import SettingsDialog
from log_window import LogWindow

def main():
    app = wx.App(False)
    dlg = SettingsDialog(None)
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
