import sys
# from http.server import BaseHTTPRequestHandler, HTTPServer
# from subprocess import PIPE, Popen
from threading import Thread
from time import sleep
import websocket
from os import path, chdir
import ctypes

import wx

pwd = path.dirname(path.realpath(__file__))
chdir(pwd)
libmsp430 = ctypes.cdll.LoadLibrary(path.join(pwd, "libmsp430.so"))
run_emu = libmsp430.run
run_emu.restype = ctypes.c_int
run_emu.argtypes = [ctypes.c_uint]


class Emulator:
    EVENT_CONSOLE = 0
    EVENT_SERIAL = 1

    def __init__(self, emu_dir, ws_port=59981, load=None, callback=None):
        # self.process = Popen([path.join(emu_dir, 'MSP430'), str(ws_port)], stdout=PIPE, stderr=PIPE)
        self.process = Thread(target=run_emu, args=(ws_port, ))
        self.process.start()
        sleep(3)
        self.ws = websocket.WebSocketApp(f"ws://127.0.0.1:{ws_port}",
                                         subprotocols={"emu-protocol"},
                                         on_open=self._ws_open,
                                         on_data=self._ws_msg,
                                         on_error=self._ws_err,
                                         on_close=self._ws_close
                                        )
        self.load = load
        self.started = False
        self.start_errors = 0
        self.callback = callback
        Thread(target=self.ws.run_forever).start()

    def wait(self):
        self.process.wait()

    def load_file(self, fname):
        with open(fname, 'rb') as f:
            fdata = f.read()
            name = path.basename(fname)
            payload = b'\x00'  # opcode
            payload += len(fdata).to_bytes(2, byteorder='big')
            payload += len(name).to_bytes(2, byteorder='big')
            payload += name.encode() + fdata
            self.ws.send(payload, websocket.ABNF.OPCODE_BINARY)

    def _ws_open(self):
        self.started = True
        if self.load is not None:
            self.load_file(self.load)

    def _ws_msg(self, data, frame, x):
        opcode = data[0]
        if opcode == 0:
            return
        elif opcode == 1:
            message = data[1:-1].decode()
            if "Type 'h' for" in message:
                return
            if callable(self.callback):
                self.callback(self.EVENT_CONSOLE, message)
            print(message, end=None)
            return
        elif opcode == 2:
            message = data[1:-1].decode()
            if callable(self.callback):
                self.callback(self.EVENT_SERIAL, message)
            return
        else:
            pass

    def _ws_err(self, err):
        if not self.started:
            self.start_errors += 1
            if self.start_errors < 5:
                print(f"Failed to connect to emulator backend attempt {self.start_errors}")
                sleep(1)
                self.ws.run_forever()
            raise ConnectionError("Failed to connect to emulation backend after 5 tries")
        raise err

    def _ws_close(self):
        if not self.started:
            return
        pass

    def __del__(self):
        self.close()

    def emulation_pause(self):
        self.ws.send(b'\x02', websocket.ABNF.OPCODE_BINARY)

    def emulation_start(self):
        self.ws.send(b'\x01', websocket.ABNF.OPCODE_BINARY)

    def close(self):
        self.ws.close()
        self.process.join()


class EmulatorWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)
        self.control = wx.TextCtrl(self, size=wx.Size(400, 450),
                                   style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.serial = wx.TextCtrl(self, size=wx.Size(400, 450), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.serial_input = wx.TextCtrl(self, style=wx.TE_DONTWRAP)

        self.CreateStatusBar()  # A Statusbar in the bottom of the window

        filemenu = wx.Menu()

        menuFile = filemenu.Append(wx.ID_OPEN, "&Firmware", " Open firmware")
        menuReset = filemenu.Append(wx.ID_CLOSE_ALL, "&Reset", " Reset Emulator")
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnOpen, menuFile)
        self.Bind(wx.EVT_MENU, self.RestartEmulator, menuReset)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_start_emu = wx.Button(self, -1, "S&tart")
        self.Bind(wx.EVT_BUTTON, self.OnStart, btn_start_emu)
        btn_stop_emu = wx.Button(self, -1, "P&ause")
        self.Bind(wx.EVT_BUTTON, self.OnPause, btn_stop_emu)
        self.sizer2.Add(btn_start_emu, 1, wx.EXPAND)
        self.sizer2.Add(btn_stop_emu, 1, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        btn_start_emu = wx.Button(self, -1, "Send")
        self.sizer3.Add(self.serial_input, 1, wx.EXPAND)
        self.sizer3.Add(btn_start_emu, 0)

        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer0.Add(self.serial, 1, wx.EXPAND)
        self.sizer0.Add(self.sizer3, 0, wx.EXPAND)

        panel = wx.Panel(self, size=wx.Size(275, 375))
        img = wx.Bitmap("msp430.png", wx.BITMAP_TYPE_PNG)
        wx.StaticBitmap(panel, -1, img, (0, 0), (img.GetWidth(), img.GetHeight()))
        self.diagram = DrawRect(panel, -1, size=wx.Size(275, 375))
        #
        # dc = wx.WindowDC(panel)
        # dc.SetPen(wx.WHITE_PEN)
        # dc.SetBrush(wx.WHITE_BRUSH)
        # dc.DrawRectangle(50, 50, 500, 500)


        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(panel, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        self.sizer1.Add(self.control, 1, wx.EXPAND)
        self.sizer1.Add(self.sizer0, 1, wx.EXPAND)

        self.sizer.Add(self.sizer1, 1, wx.EXPAND)
        self.sizer.Add(self.sizer2, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show()

        self.control.WriteText("Initialising Emulator..\n")
        self.load = None
        if len(sys.argv) >= 2:
            if path.exists(sys.argv[1]):
                self.load = sys.argv[1]
        self.emu = Emulator('emulator', load=self.load, callback=self.callback)

    def callback(self, event, data):
        if event == Emulator.EVENT_CONSOLE:
            wx.CallAfter(self.control.AppendText, data)
        if event == Emulator.EVENT_SERIAL:
            wx.CallAfter(self.serial.AppendText, data)

    def RestartEmulator(self, e):
        self.control.AppendText("Stopping Emulator..")
        self.emu.close()
        self.control.Clear()
        self.serial.Clear()
        self.control.WriteText("Initialising Emulator..\n")
        self.emu = Emulator('emulator', load=self.load, callback=self.callback)

    def OnOpen(self, e):
        with wx.FileDialog(self, "Open Firmware", wildcard="ELF files (*.elf)|*.elf",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.load = fileDialog.GetPath()
            self.RestartEmulator(None)

    def OnPause(self, e):
        self.emu.emulation_pause()

    def OnStart(self, e):
        self.emu.emulation_start()

    def OnExit(self, e):
        self.emu.close()
        self.Close(True)


class DrawRect(wx.Panel):
    """ class MyPanel creates a panel to draw on, inherits wx.Panel """
    def __init__(self, parent, id, **kwargs):
        # create a panel
        wx.Panel.__init__(self, parent, id, **kwargs)
        # self.SetBackgroundColour("white")
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        """set up the device context (DC) for painting"""
        self.dc = wx.PaintDC(self)
        self.dc.SetPen(wx.Pen("green",style=wx.TRANSPARENT))
        self.dc.SetBrush(wx.Brush("green", wx.SOLID))
        # set x, y, w, h for rectangle
        self.dc.DrawRectangle(83, 356, 8, 15)

        self.dc.SetPen(wx.Pen("red",style=wx.TRANSPARENT))
        self.dc.SetBrush(wx.Brush("red", wx.SOLID))
        self.dc.DrawRectangle(70, 356, 8, 15)
        del self.dc


if __name__ == '__main__':
    app = wx.App(False)
    frame = EmulatorWindow(None, "MSP430 Emulator")
    app.MainLoop()
