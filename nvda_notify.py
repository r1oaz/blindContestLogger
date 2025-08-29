# nvda_notify.py
"""
Модуль для озвучивания сообщений через NVDA с помощью controllerClient.dll.
"""
import sys
import ctypes
import os
import wx
import logging

class NVDAController:
    def __init__(self):
        self.dll = None
        self.available = False
        try:
            # Поиск DLL: сначала внутри PyInstaller (_MEIPASS), затем рядом с exe, затем рядом с исходным файлом
            dll_path = None
            if getattr(sys, 'frozen', False):
                # PyInstaller: DLL будет распакована во временную папку _MEIPASS
                candidate = os.path.join(sys._MEIPASS, 'nvdaControllerClient64.dll')
                if os.path.exists(candidate):
                    dll_path = candidate
            if dll_path is None:
                # Рядом с exe
                candidate = os.path.join(os.path.dirname(sys.executable), 'nvdaControllerClient64.dll')
                if os.path.exists(candidate):
                    dll_path = candidate
            if dll_path is None:
                # Рядом с исходным файлом
                candidate = os.path.join(os.path.dirname(__file__), 'nvdaControllerClient64.dll')
                if os.path.exists(candidate):
                    dll_path = candidate
            if dll_path:
                self.dll = ctypes.WinDLL(dll_path)
                self.dll.nvdaController_speakText.argtypes = [ctypes.c_wchar_p]
                self.dll.nvdaController_speakText.restype = ctypes.c_int
                self.available = True
            else:
                self.available = False
        except Exception as e:
            print(f"Ошибка загрузки NVDA DLL: {e}")
            logging.error(f"Ошибка загрузки NVDA DLL: {e}")
            self.available = False

    def speak(self, message: str, interrupt: bool = True):
        if self.available and self.dll:
            try:
                res = self.dll.nvdaController_speakText(message)
                if res != 0:
                    print(f"Ошибка NVDA speakText: код {res}")
                    logging.error(f"Ошибка NVDA speakText: код {res}")
            except Exception as e:
                print(f"Ошибка вызова nvdaController_speakText: {e}")
                logging.error(f"Ошибка вызова nvdaController_speakText: {e}")
        else:
            print("NVDA DLL недоступна, fallback на wx.adv.NotificationMessage")
            wx.adv.NotificationMessage("Blind_Log", message).Show()
            logging.warning("NVDA DLL недоступна, fallback на wx.adv.NotificationMessage")

# Глобальный экземпляр для использования в других модулях
nvda_controller = NVDAController()

def nvda_notify(message: str, interrupt: bool = True):
    """
    Озвучить сообщение через NVDA, если controllerClient.dll доступен.
    """
    nvda_controller.speak(message, interrupt)
    # Для отладки также выводим в консоль
    print(f"NVDA_NOTIFY: {message}")
    logging.info(f"NVDA_NOTIFY: {message}")
