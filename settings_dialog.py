import wx
import wx.adv
import datetime
import webbrowser
import os

class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Настройки контеста", size=(400, 400))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        # Кнопка справки
        btn_help = wx.Button(panel, label="Справка")
        vbox.Add(btn_help, 0, wx.ALL | wx.ALIGN_LEFT, 10)
        btn_help.SetFocus()
        btn_help.Bind(wx.EVT_BUTTON, self.on_help)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)

        # Подписи и поля
        label_callsign = wx.StaticText(panel, label="Позывной:")
        self.callsign = wx.TextCtrl(panel)
        self.callsign.SetName("Позывной")

        label_qth = wx.StaticText(panel, label="QTH локатор:")
        self.qth = wx.TextCtrl(panel)
        self.qth.SetName("QTH локатор")

        label_grid = wx.StaticText(panel, label="Grid-локатор:")
        self.grid = wx.TextCtrl(panel)
        self.grid.SetName("Grid-локатор")

        label_contest_name = wx.StaticText(panel, label="Название контеста:")
        self.contest_name = wx.TextCtrl(panel)
        self.contest_name.SetName("Название контеста")

        label_contest_type = wx.StaticText(panel, label="Тип контеста:")
        self.contest_type = wx.ComboBox(panel, choices=["КВ", "УКВ"], style=wx.CB_READONLY)
        self.contest_type.SetName("Тип контеста")

        label_band = wx.StaticText(panel, label="Начальный диапазон:")
        self.band_choices_kv = ["1.8 МГц", "3.5 МГц", "7 МГц", "14 МГц", "21 МГц", "28 МГц"]
        self.band_choices_ukv = ["144 МГц", "430 МГц", "1200 МГц"]
        self.band_choice = wx.ComboBox(panel, choices=self.band_choices_kv, style=wx.CB_READONLY)
        self.band_choice.SetName("Начальный диапазон")

        label_mode = wx.StaticText(panel, label="Режим:")
        self.mode_choice = wx.ComboBox(panel, choices=["SSB", "CW", "FM", "DIGI"], style=wx.CB_READONLY)
        self.mode_choice.SetName("Режим")
        self.mode_choice.SetSelection(0)

        label_tz = wx.StaticText(panel, label="Часовой пояс:")
        self.tz_choice = wx.ComboBox(panel, choices=[f"UTC{('+' if i>=0 else '')}{i}" for i in range(-12, 13)], style=wx.CB_READONLY)
        self.tz_choice.SetName("Часовой пояс")
        self.tz_choice.SetSelection(12)  # UTC+0 по умолчанию

        label_end_date = wx.StaticText(panel, label="Время окончания (дата):")
        self.end_time = wx.adv.DatePickerCtrl(panel)
        self.end_time.SetName("Время окончания (дата)")

        label_end_time = wx.StaticText(panel, label="Время окончания (время):")
        self.end_clock = wx.adv.TimePickerCtrl(panel)
        self.end_clock.SetName("Время окончания (время)")

        self.tours = wx.CheckBox(panel, label="Контест разделён на туры")
        self.tours.SetName("Контест разделён на туры")
        label_tour_interval = wx.StaticText(panel, label="Интервал туров (мин):")
        self.tour_interval = wx.ComboBox(panel, choices=["2", "5", "10", "15", "30", "60", "120", "240"], style=wx.CB_READONLY)
        self.tour_interval.SetName("Интервал туров (мин)")
        self.tour_interval.Hide()
        label_tour_interval.Hide()
        self.label_tour_interval = label_tour_interval

        grid = wx.FlexGridSizer(0, 2, 5, 5)
        grid.AddMany([
            (label_callsign, 0, wx.ALIGN_CENTER_VERTICAL), (self.callsign, 1, wx.EXPAND),
            (label_qth, 0, wx.ALIGN_CENTER_VERTICAL), (self.qth, 1, wx.EXPAND),
            (label_grid, 0, wx.ALIGN_CENTER_VERTICAL), (self.grid, 1, wx.EXPAND),
            (label_contest_name, 0, wx.ALIGN_CENTER_VERTICAL), (self.contest_name, 1, wx.EXPAND),
            (label_contest_type, 0, wx.ALIGN_CENTER_VERTICAL), (self.contest_type, 1, wx.EXPAND),
            (label_band, 0, wx.ALIGN_CENTER_VERTICAL), (self.band_choice, 1, wx.EXPAND),
            (label_mode, 0, wx.ALIGN_CENTER_VERTICAL), (self.mode_choice, 1, wx.EXPAND),
            (label_tz, 0, wx.ALIGN_CENTER_VERTICAL), (self.tz_choice, 1, wx.EXPAND),
            (label_end_date, 0, wx.ALIGN_CENTER_VERTICAL), (self.end_time, 1, wx.EXPAND),
            (label_end_time, 0, wx.ALIGN_CENTER_VERTICAL), (self.end_clock, 1, wx.EXPAND),
            (self.tours, 0, wx.ALIGN_CENTER_VERTICAL), (wx.Panel(panel), 1),
            (self.label_tour_interval, 0, wx.ALIGN_CENTER_VERTICAL), (self.tour_interval, 1, wx.EXPAND),
        ])
        grid.AddGrowableCol(1, 1)
        vbox.Add(grid, 1, wx.ALL | wx.EXPAND, 10)
        # Кнопки OK/Cancel с правильным parent
        hbox_btns = wx.BoxSizer(wx.HORIZONTAL)
        btn_ok = wx.Button(panel, wx.ID_OK)
        btn_cancel = wx.Button(panel, wx.ID_CANCEL)
        hbox_btns.Add(btn_ok, 0, wx.RIGHT, 10)
        hbox_btns.Add(btn_cancel, 0)
        vbox.Add(hbox_btns, 0, wx.ALL | wx.ALIGN_CENTER, 10)
        panel.SetSizer(vbox)
        self.tours.Bind(wx.EVT_CHECKBOX, self.on_tours)
        self.contest_type.Bind(wx.EVT_COMBOBOX, self.on_contest_type)

    def on_tours(self, event):
        if self.tours.IsChecked():
            self.tour_interval.Show()
            self.label_tour_interval.Show()
        else:
            self.tour_interval.Hide()
            self.label_tour_interval.Hide()
        self.Layout()

    def on_contest_type(self, event):
        t = self.contest_type.GetValue()
        if t == "УКВ":
            self.band_choice.SetItems(self.band_choices_ukv)
            self.band_choice.SetSelection(0)
        else:
            self.band_choice.SetItems(self.band_choices_kv)
            self.band_choice.SetSelection(0)

    def get_settings(self):
        # Преобразуем wx.DateTime в datetime.date и datetime.time
        def wxdate_to_pydate(wxdate):
            return datetime.date(wxdate.GetYear(), wxdate.GetMonth() + 1, wxdate.GetDay())
        def wxtime_to_pytime(wxtime):
            return datetime.time(wxtime.GetHour(), wxtime.GetMinute(), wxtime.GetSecond())
        end_date = wxdate_to_pydate(self.end_time.GetValue())
        end_time = wxtime_to_pytime(self.end_clock.GetValue())
        return {
            "callsign": self.callsign.GetValue(),
            "qth": self.qth.GetValue(),
            "grid": self.grid.GetValue(),
            "contest_name": self.contest_name.GetValue(),
            "contest_type": self.contest_type.GetValue(),
            "band": self.band_choice.GetValue(),
            "mode": self.mode_choice.GetValue(),
            "tz": self.tz_choice.GetValue(),
            "end": datetime.datetime.combine(end_date, end_time),
            "tours": self.tours.IsChecked(),
            "tour_interval": self.tour_interval.GetValue() if self.tours.IsChecked() else None
        }

    def on_help(self, event=None):
        help_path = os.path.join(os.path.dirname(__file__), 'help.html')
        webbrowser.open_new_tab('file://' + help_path)

    def show_about(self):
        from log_window import AboutDialog
        dlg = AboutDialog(self)
        dlg.ShowModal()

    def on_key(self, event):
        key = event.GetKeyCode()
        shift = event.ShiftDown()
        if key == wx.WXK_F1 and not shift:
            self.on_help()
        elif key == wx.WXK_F1 and shift:
            self.show_about()
        else:
            event.Skip()
