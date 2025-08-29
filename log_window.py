import wx
import wx.adv
import datetime
import nvda_notify
import exporter
import os
import threading
import winsound

class QSOManager:
    def __init__(self):
        self.qso_list = []

    def add_qso(self, qso):
        self.qso_list.append(qso)

class SettingsManager:
    def __init__(self, settings=None):
        self.settings = settings or {}

class LogWindow(wx.Frame):
    def __init__(self, parent, settings):
        super().__init__(parent, title="Логирование QSO", size=(800, 600))
        self.settings_manager = SettingsManager(settings)
        self.qso_manager = QSOManager()
        self.exporter = exporter.Exporter(self.qso_manager, self.settings_manager)
        self.init_ui()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        # Таймеры для контеста и туров
        self.tour_timer = None
        self.contest_timer = None
        self.tour_end_time = None
        self.contest_end_time = None
        self.tour_interval_sec = None
        self.sounds_path = os.path.join(os.path.dirname(__file__), 'sounds')
        self.tour_warning_played = False
        self.setup_timers_from_settings()

    def setup_timers_from_settings(self):
        import time
        settings = self.settings_manager.settings
        now = datetime.datetime.now()
        self.contest_end_time = settings.get('end')
        if isinstance(self.contest_end_time, str):
            self.contest_end_time = datetime.datetime.fromisoformat(self.contest_end_time)
        self.tour_interval_sec = None
        self.tours_enabled = bool(settings.get('tours') and settings.get('tour_interval'))
        if self.tours_enabled:
            self.tour_interval_sec = int(settings['tour_interval']) * 60
            self.tour_end_time = now + datetime.timedelta(seconds=self.tour_interval_sec)
        else:
            self.tour_end_time = None
        # Запуск таймеров
        self.start_timers()

    def start_timers(self):
        if self.contest_timer:
            self.contest_timer.Stop()
        if self.tour_timer:
            self.tour_timer.Stop()
        # Всегда запускаем общий таймер
        self.contest_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_contest_timer, self.contest_timer)
        self.contest_timer.Start(1000)
        # Таймер тура только если включено разделение и до конца контеста больше длительности тура
        if self.tours_enabled and self.tour_end_time and self.contest_end_time:
            now = datetime.datetime.now()
            contest_left = (self.contest_end_time - now).total_seconds()
            if contest_left > self.tour_interval_sec:
                self.tour_timer = wx.Timer(self)
                self.Bind(wx.EVT_TIMER, self.on_tour_timer, self.tour_timer)
                self.tour_timer.Start(1000)
            else:
                self.tour_timer = None
                self.tour_end_time = None
    def announce_tour_time_left(self):
        if self.tours_enabled:
            if self.tour_end_time:
                now = datetime.datetime.now()
                left = int((self.tour_end_time - now).total_seconds())
                if left < 0:
                    left = 0
                m, s = divmod(left, 60)
                nvda_notify.nvda_notify(f"До конца тура {m} минут {s} секунд")
            else:
                nvda_notify.nvda_notify("Тур завершён")
        else:
            nvda_notify.nvda_notify("Разделение на туры не включено")

    def announce_contest_time_left(self):
        if self.contest_end_time:
            now = datetime.datetime.now()
            left = int((self.contest_end_time - now).total_seconds())
            if left < 0:
                left = 0
            m, s = divmod(left, 60)
            nvda_notify.nvda_notify(f"До конца контеста {m} минут {s} секунд")
        else:
            nvda_notify.nvda_notify("Время окончания контеста не задано")

    def on_contest_timer(self, event):
        now = datetime.datetime.now()
        # За 30 секунд до конца контеста проигрываем 1.wav, если осталось <= 30 секунд и ещё не проигрывали
        if self.contest_end_time:
            left_contest = (self.contest_end_time - now).total_seconds()
            if left_contest <= 30 and not hasattr(self, 'contest_warning_played'):
                # Если до конца контеста меньше или столько же, сколько до конца тура, то предупреждение только по контесту
                left_tour = (self.tour_end_time - now).total_seconds() if self.tour_end_time else 999999
                if left_contest <= left_tour:
                    self.play_sound('1.wav')
                    self.contest_warning_played = True
        if now >= self.contest_end_time:
            self.play_sound('3.wav')
            if self.tour_timer:
                self.tour_timer.Stop()
            self.contest_timer.Stop()
            nvda_notify.nvda_notify("Контест завершён")
            self.contest_warning_played = False

    def on_tour_timer(self, event):
        now = datetime.datetime.now()
        if self.tour_end_time and self.contest_end_time:
            left = (self.tour_end_time - now).total_seconds()
            left_contest = (self.contest_end_time - now).total_seconds()
            # Если до конца контеста меньше или равно, чем до конца тура, не озвучивать тур
            if left_contest <= left:
                return
            if left <= 0:
                if left_contest > 0:
                    self.play_sound('2.wav')
                    nvda_notify.nvda_notify("Тур завершён")
                # Если до конца контеста осталось больше длительности тура — запускаем новый тур, иначе не запускаем
                if left_contest > self.tour_interval_sec:
                    self.tour_end_time = now + datetime.timedelta(seconds=self.tour_interval_sec)
                    self.tour_warning_played = False
                else:
                    self.tour_end_time = None
            elif left <= 30 and not self.tour_warning_played:
                self.play_sound('1.wav')
                nvda_notify.nvda_notify("До конца тура 30 секунд")
                self.tour_warning_played = True

    def play_sound(self, filename):
        path = os.path.join(self.sounds_path, filename)
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            nvda_notify.nvda_notify(f"Ошибка воспроизведения звука: {e}")

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Поле ввода позывного корреспондента
        hbox_callsign = wx.BoxSizer(wx.HORIZONTAL)
        hbox_callsign.Add(wx.StaticText(panel, label="Позывной корреспондента:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.callsign_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        hbox_callsign.Add(self.callsign_ctrl, 1, wx.EXPAND)
        vbox.Add(hbox_callsign, 0, wx.EXPAND|wx.ALL, 5)

        # Поле комментария
        hbox_comment = wx.BoxSizer(wx.HORIZONTAL)
        hbox_comment.Add(wx.StaticText(panel, label="Комментарий:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.comment_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        hbox_comment.Add(self.comment_ctrl, 1, wx.EXPAND)
        vbox.Add(hbox_comment, 0, wx.EXPAND|wx.ALL, 5)

        # Таблица QSO
        self.qso_list = wx.ListCtrl(panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.qso_list.InsertColumn(0, "Время", width=120)
        self.qso_list.InsertColumn(1, "Позывной", width=100)
        self.qso_list.InsertColumn(2, "RST", width=50)
        self.qso_list.InsertColumn(3, "Диапазон", width=80)
        self.qso_list.InsertColumn(4, "Частота", width=80)
        self.qso_list.InsertColumn(5, "Комментарий", width=200)
        vbox.Add(self.qso_list, 1, wx.EXPAND|wx.ALL, 5)

        # Горячие клавиши
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('1'), 1001),
            (wx.ACCEL_CTRL, ord('2'), 1002),
            (wx.ACCEL_CTRL, ord('3'), 1003),
            (wx.ACCEL_ALT, ord('3'), 1005),  # Alt+3 - предыдущий диапазон
            (wx.ACCEL_ALT, ord('4'), 1004),  # Alt+4 - следующий диапазон
            (wx.ACCEL_ALT, ord('1'), 1006),  # Alt+1 - предыдущий режим
            (wx.ACCEL_ALT, ord('2'), 1007),  # Alt+2 - следующий режим
            (wx.ACCEL_CTRL, ord('F'), 1008),
            (wx.ACCEL_CTRL, ord('Q'), 1009),
            (wx.ACCEL_CTRL, wx.WXK_RETURN, 1010),
        ])
        self.SetAcceleratorTable(accel_tbl)
        self.Bind(wx.EVT_MENU, self.focus_callsign, id=1001)
        self.Bind(wx.EVT_MENU, self.focus_comment, id=1002)
        self.Bind(wx.EVT_MENU, self.focus_table, id=1003)
        self.Bind(wx.EVT_MENU, self.next_band, id=1004)
        self.Bind(wx.EVT_MENU, self.prev_band, id=1005)
        self.Bind(wx.EVT_MENU, self.prev_mode, id=1006)
        self.Bind(wx.EVT_MENU, self.next_mode, id=1007)
        self.Bind(wx.EVT_MENU, self.input_freq, id=1008)
        self.Bind(wx.EVT_MENU, self.on_close, id=1009)
        self.Bind(wx.EVT_MENU, self.save_qso, id=1010)

        # Enter и Ctrl+Enter
        self.callsign_ctrl.Bind(wx.EVT_TEXT_ENTER, self.goto_comment)
        self.callsign_ctrl.SetWindowStyleFlag(wx.TE_PROCESS_ENTER)
        self.comment_ctrl.Bind(wx.EVT_TEXT_ENTER, self.save_qso)
        self.comment_ctrl.SetWindowStyleFlag(wx.TE_PROCESS_ENTER)

        panel.SetSizer(vbox)

        # Значения по умолчанию
        self.rst_default = "59"
        self.band_list = self.get_band_list()
        # Учитываем стартовый диапазон из настроек
        start_band = self.settings_manager.settings.get("band")
        if start_band in self.band_list:
            self.band_index = self.band_list.index(start_band)
        else:
            self.band_index = 0
        self.current_band = self.band_list[self.band_index]
        self.current_freq = ""
        self.mode_list = ["SSB", "CW", "FM", "DIGI"]
        mode_from_settings = self.settings_manager.settings.get("mode", "SSB")
        if mode_from_settings in self.mode_list:
            self.mode_index = self.mode_list.index(mode_from_settings)
        else:
            self.mode_index = 0
        self.current_mode = self.mode_list[self.mode_index]
        self.tz_offset = self.parse_tz(self.settings_manager.settings.get("tz", "UTC+0"))

        self.band_history = []  # Для хранения истории диапазонов

    def parse_tz(self, tz_str):
        # Преобразует строку UTC+3 в int 3
        try:
            return int(tz_str.replace("UTC", ""))
        except Exception:
            return 0

    def focus_callsign(self, event):
        self.callsign_ctrl.SetFocus()
    def focus_comment(self, event):
        self.comment_ctrl.SetFocus()
    def focus_table(self, event):
        self.qso_list.SetFocus()

    def goto_comment(self, event):
        self.comment_ctrl.SetFocus()

    def save_qso(self, event):
        # Запрет добавления после завершения контеста
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=self.tz_offset)
        if self.contest_end_time and datetime.datetime.now() >= self.contest_end_time:
            nvda_notify.nvda_notify("Контест завершён, новые записи не могут быть приняты.")
            return
        callsign = self.callsign_ctrl.GetValue().strip()
        comment = self.comment_ctrl.GetValue().strip()
        if not callsign:
            nvda_notify.nvda_notify("Введите позывной корреспондента")
            return
        now_str = now.strftime("%Y-%m-%d %H:%M")
        qso = {
            "datetime": now_str,
            "call": callsign,
            "rst_sent": self.rst_default,
            "rst_received": self.rst_default,
            "band": self.current_band,
            "freq": self.current_freq,
            "mode": self.current_mode,
            "comment": comment
        }
        self.qso_manager.add_qso(qso)
        idx = self.qso_list.InsertItem(self.qso_list.GetItemCount(), now_str)
        self.qso_list.SetItem(idx, 1, callsign)
        self.qso_list.SetItem(idx, 2, self.rst_default)
        self.qso_list.SetItem(idx, 3, self.current_band)
        self.qso_list.SetItem(idx, 4, self.current_freq)
        self.qso_list.SetItem(idx, 5, comment)
        nvda_notify.nvda_notify("Запись добавлена")
        self.callsign_ctrl.SetValue("")
        self.comment_ctrl.SetValue("")
        self.callsign_ctrl.SetFocus()

    def get_band_list(self):
        t = self.settings_manager.settings.get("contest_type", "КВ")
        if t == "УКВ":
            return ["144 МГц", "430 МГц", "1200 МГц"]
        return ["1.8 МГц", "3.5 МГц", "7 МГц", "14 МГц", "21 МГц", "28 МГц"]

    def next_band(self, event):
        self.band_index = (self.band_index + 1) % len(self.band_list)
        self.current_band = self.band_list[self.band_index]
        self.current_freq = ""  # Сброс частоты при смене диапазона
        self.band_history.append(self.current_band)
        nvda_notify.nvda_notify(f"Диапазон: {self.current_band}")

    def prev_band(self, event):
        self.band_index = (self.band_index - 1) % len(self.band_list)
        self.current_band = self.band_list[self.band_index]
        self.current_freq = ""  # Сброс частоты при смене диапазона
        self.band_history.append(self.current_band)
        nvda_notify.nvda_notify(f"Диапазон: {self.current_band}")
        

    def input_freq(self, event):
        dlg = wx.TextEntryDialog(self, "Введите рабочую частоту:", "Частота")
        if dlg.ShowModal() == wx.ID_OK:
            self.current_freq = dlg.GetValue()
            nvda_notify.nvda_notify(f"Частота: {self.current_freq}")
        dlg.Destroy()

    def on_close(self, event):
        dlg = wx.MessageDialog(self, "Сохранить лог перед выходом?", "Выход", wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        if res == wx.ID_YES:
            self.exporter.on_export(event)
            self.Destroy()
        elif res == wx.ID_NO:
            self.Destroy()
        else:
            event.Veto()

    def on_key_down(self, event):
        key = event.GetKeyCode()
        ctrl = event.ControlDown()
        alt = event.AltDown()
        shift = event.ShiftDown()
        if key == wx.WXK_F1 and not shift:
            self.show_help()
        elif key == wx.WXK_F1 and shift:
            self.show_about()
        elif key == wx.WXK_F2:
            self.announce_tour_time_left()
        elif key == wx.WXK_F3:
            self.announce_contest_time_left()
        elif (ctrl and key == ord('Q')) or (alt and key == wx.WXK_F4):
            self.Close()
        else:
            event.Skip()
    def show_help(self):
        import webbrowser, os
        help_path = os.path.join(os.path.dirname(__file__), 'help.html')
        webbrowser.open_new_tab('file://' + help_path)
    def show_about(self):
        dlg = AboutDialog(self)
        dlg.ShowModal()

    def prev_mode(self, event):
        self.mode_index = (self.mode_index - 1) % len(self.mode_list)
        self.current_mode = self.mode_list[self.mode_index]
        nvda_notify.nvda_notify(f"Режим: {self.current_mode}")

    def next_mode(self, event):
        self.mode_index = (self.mode_index + 1) % len(self.mode_list)
        self.current_mode = self.mode_list[self.mode_index]
        nvda_notify.nvda_notify(f"Режим: {self.current_mode}")

class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="О программе", size=(420, 220))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.text = wx.TextCtrl(panel, value="программа для ведения лога контеста от незрячего радиолюбителя R1BQE", style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.text.SetFocus()
        vbox.Add(self.text, 1, wx.EXPAND|wx.ALL, 10)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_site = wx.Button(panel, label="Перейти на сайт")
        btn_close = wx.Button(panel, label="Закрыть")
        hbox.Add(btn_site, 0, wx.RIGHT, 10)
        hbox.Add(btn_close, 0)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER|wx.BOTTOM, 10)
        panel.SetSizer(vbox)
        btn_site.Bind(wx.EVT_BUTTON, lambda e: wx.LaunchDefaultBrowser("https://r1oaz.ru"))
        btn_close.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)
        self.Bind(wx.EVT_CLOSE, lambda e: self.Destroy())
    def on_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE or (event.AltDown() and key == wx.WXK_F4):
            self.Close()
        else:
            event.Skip()
