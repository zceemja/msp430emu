from threading import Thread
from os import path
import _msp430emu
import wx

source_dir = path.dirname(path.realpath(__file__))


class Emulator:
    EVENT_CONSOLE = 0
    EVENT_SERIAL = 1
    EVENT_GPIO = 2

    P1_0_ON_PACKET = 0x00
    P1_0_OFF_PACKET = 0x01
    P1_1_ON_PACKET = 0x02
    P1_1_OFF_PACKET = 0x03
    P1_2_ON_PACKET = 0x04
    P1_2_OFF_PACKET = 0x05
    P1_3_ON_PACKET = 0x06
    P1_3_OFF_PACKET = 0x07
    P1_4_ON_PACKET = 0x08
    P1_4_OFF_PACKET = 0x09
    P1_5_ON_PACKET = 0x0A
    P1_5_OFF_PACKET = 0x0B
    P1_6_ON_PACKET = 0x0C
    P1_6_OFF_PACKET = 0x0D
    P1_7_ON_PACKET = 0x0E
    P1_7_OFF_PACKET = 0x0F

    def __init__(self, load=None, callback=None):
        # self.process = Popen([path.join(emu_dir, 'MSP430'), str(ws_port)], stdout=PIPE, stderr=PIPE)
        # self.ws_port = ws_port
        # self._start_ws()
        self.load = load
        self.started = False
        self.callback = callback

        _msp430emu.on_serial(self._on_serial)
        _msp430emu.on_console(self._on_console)
        _msp430emu.on_control(self._on_control)

        if self.load is not None:
            self.process = Thread(target=self._start_emu, daemon=False)
            self.process.start()

    def _on_serial(self, s):
        self._cb(self.EVENT_SERIAL, s)

    def _on_console(self, s):
        self._cb(self.EVENT_CONSOLE, s)

    def _on_control(self, opcode, data):
        if opcode <= 0x0F:
            self._cb(self.EVENT_GPIO, opcode)

    def send_command(self, cmd):
        if self.started:
            _msp430emu.cmd(cmd)

    def reset(self):
        if self.started:
            _msp430emu.reset()

    def _start_emu(self):
        print("starting emulator...")
        self.started = True
        _msp430emu.init(self.load)
        print("stopping emulator...")

    # def _start_ws(self):
    #     self.ws = websocket.WebSocketApp(
    #         f"ws://127.0.0.1:{self.ws_port}",
    #         subprotocols={"emu-protocol"},
    #         on_open=self._ws_open,
    #         on_data=self._ws_msg,
    #         on_error=self._ws_err,
    #         on_close=self._ws_close
    #     )
    #     Thread(target=self.ws.run_forever).start()
    #
    def load_file(self, fname):
        print("loading " + fname)
        self.load = fname
        self.process = Thread(target=self._start_emu, daemon=False)
        self.process.start()
    #     with open(self.load, 'rb') as f:
    #         self.firmware = fname
    #         fdata = f.read()
    #         name = path.basename(fname)
    #         payload = b'\x00'  # opcode
    #         payload += len(fdata).to_bytes(2, byteorder='big')
    #         payload += len(name).to_bytes(2, byteorder='big')
    #         payload += name.encode() + fdata
    #         self.ws.send(payload, websocket.ABNF.OPCODE_BINARY)

    def _cb(self, ev, data):
        if callable(self.callback):
            self.callback(ev, data)

    # def _ws_open(self):
    #     self.started = True
    #     if self.load is not None:
    #         self.load_file(self.load)
    #
    # def _ws_msg(self, data, frame, x):
    #     opcode = data[0]
    #     if opcode == 0:
    #         if len(data) == 2 and data[1] <= 15:
    #             self._cb(self.EVENT_GPIO, data[1])
    #
    #     elif opcode == 1:
    #         message = data[1:-1].decode()
    #         self._cb(self.EVENT_CONSOLE, message)
    #         # print(message, end=None)
    #         return
    #     elif opcode == 2:
    #         message = data[1:-1].decode()
    #         self._cb(self.EVENT_SERIAL, message)
    #         return
    #     else:
    #         pass

    # def _ws_err(self, err):
    #     if not self.started:
    #         self.start_errors += 1
    #         if self.start_errors < 5:
    #             print(f"Failed to connect to emulator backend attempt {self.start_errors}")
    #             sleep(1)
    #             self._start_ws()
    #         raise ConnectionError("Failed to connect to emulation backend after 5 tries")
    #     raise err
    #
    # def _ws_close(self):
    #     if not self.started:
    #         return
    #     pass

    def __del__(self):
        self.close()

    def emulation_pause(self):
        if self.started:
            _msp430emu.pause()
        # if self.load is not None:
        #     self.ws.send(b'\x02', websocket.ABNF.OPCODE_BINARY)

    def emulation_start(self):
        if self.started:
            _msp430emu.play()
        # if self.load is not None:
        #     self.ws.send(b'\x01', websocket.ABNF.OPCODE_BINARY)

    def close(self):
        if self.started:
            _msp430emu.stop()
        # _msp430emu.stop()
            self.process.join(5)


class EmulatorWindow(wx.Frame):
    def __init__(self, parent, title, load=None):
        wx.Frame.__init__(self, parent, title=title)
        self.control = wx.TextCtrl(self, size=wx.Size(400, 450),
                                   style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.control.Hide()

        self.serial = wx.TextCtrl(self, size=wx.Size(400, 450), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.serial_input = wx.TextCtrl(self, style=wx.TE_DONTWRAP)

        self.CreateStatusBar()  # A Statusbar in the bottom of the window

        file_menu = wx.Menu()
        menuFile = file_menu.Append(wx.ID_OPEN, "&Firmware", " Open firmware")
        self.Bind(wx.EVT_MENU, self.OnOpen, menuFile)
        menuReset = file_menu.Append(wx.ID_CLOSE_ALL, "&Reset", " Reset Emulator")
        self.Bind(wx.EVT_MENU, self.RestartEmulator, menuReset)
        menuExit = file_menu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        view_menu = wx.Menu()
        view_console = view_menu.AppendCheckItem(101, "View Console", "Show/Hide Emulator debug console")
        self.Bind(wx.EVT_MENU, self.ToggleConsole, view_console)

        menuBar = wx.MenuBar()
        menuBar.Append(file_menu, "&File")
        menuBar.Append(view_menu, "&View")

        self.SetMenuBar(menuBar)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_start_emu = wx.Button(self, -1, "Start")
        self.Bind(wx.EVT_BUTTON, self.OnStart, btn_start_emu)
        btn_stop_emu = wx.Button(self, -1, "Pause")
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
        img = wx.Bitmap(path.join(source_dir, "msp430.png"), wx.BITMAP_TYPE_PNG)
        wx.StaticBitmap(panel, -1, img, (0, 0), (img.GetWidth(), img.GetHeight()))
        self.diagram = DrawRect(panel, -1, size=wx.Size(275, 375))
        #
        # dc = wx.WindowDC(panel)
        # dc.SetPen(wx.WHITE_PEN)
        # dc.SetBrush(wx.WHITE_BRUSH)
        # dc.DrawRectangle(50, 50, 500, 500)

        self.sizer_key_rst = wx.BoxSizer(wx.HORIZONTAL)
        btn_key = wx.Button(self, -1, "Press Key")
        self.Bind(wx.EVT_BUTTON, self.OnKeyPress, btn_key)
        btn_rst = wx.Button(self, -1, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnKeyReset, btn_rst)
        self.sizer_key_rst.Add(btn_key, 1, wx.EXPAND)
        self.sizer_key_rst.Add(btn_rst, 1, wx.EXPAND)

        self.sizer_diagram = wx.BoxSizer(wx.VERTICAL)
        self.sizer_diagram.Add(panel, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        #
        self.sizer_left = wx.BoxSizer(wx.VERTICAL)
        self.sizer_left.Add(self.sizer_diagram, 1, wx.EXPAND)
        self.sizer_left.Add(self.sizer_key_rst, 0, wx.ALIGN_BOTTOM)

        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(self.sizer_left, 0, wx.EXPAND)
        self.sizer1.Add(self.control, 1, wx.EXPAND)
        self.sizer1.Add(self.sizer0, 1, wx.EXPAND)

        self.sizer.Add(self.sizer1, 1, wx.EXPAND)
        self.sizer.Add(self.sizer2, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show()

        self.control.WriteText("Initialising Emulator..\n")
        self.load = load
        self.emu = Emulator(load=self.load, callback=self.callback)

    def callback(self, event, data):
        if event == Emulator.EVENT_CONSOLE:
            wx.CallAfter(self.control.AppendText, data)
        elif event == Emulator.EVENT_SERIAL:
            wx.CallAfter(self.serial.AppendText, data)
        elif event == Emulator.EVENT_GPIO:
            self.diagram.port1[data // 2] = data % 2 == 0
            wx.CallAfter(self.diagram.Refresh)

    def RestartEmulator(self, e):
        self.emu.close()
        self.control.Clear()
        self.serial.Clear()
        self.emu = Emulator(load=self.load, callback=self.callback)

    def ToggleConsole(self, e):
        if e.Int == 0:
            self.control.Hide()
            self.Layout()
        else:
            self.control.Show()
            self.Layout()

    def OnOpen(self, e):
        with wx.FileDialog(self, "Open Firmware File", wildcard="BIN files (*.bin)|*.bin",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.load = fileDialog.GetPath()
            self.emu.load_file(self.load)
            self.diagram.power = False
            # self.RestartEmulator(None)

    def OnPause(self, e):
        self.emu.emulation_pause()
        self.diagram.power = False
        self.diagram.Refresh()

    def OnStart(self, e):
        self.emu.emulation_start()
        self.diagram.power = True
        self.diagram.Refresh()

    def OnExit(self, e):
        self.emu.close()
        self.Close(True)

    def OnKeyPress(self, e):
        pass

    def OnKeyReset(self, e):
        self.emu.reset()


class DrawRect(wx.Panel):
    """ class MyPanel creates a panel to draw on, inherits wx.Panel """
    RED = wx.Colour(255, 0, 0, wx.ALPHA_OPAQUE)
    GREEN = wx.Colour(0, 255, 0, wx.ALPHA_OPAQUE)

    def __init__(self, parent, id, **kwargs):
        # create a panel
        wx.Panel.__init__(self, parent, id, **kwargs)
        # self.SetBackgroundColour("white")
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.power = False
        self.port1 = [False, False, False, False, False, False, False, False]

    def OnPaint(self, evt):
        """set up the device context (DC) for painting"""
        self.dc = wx.PaintDC(self)

        if self.power:
            self.dc.SetPen(wx.Pen(self.GREEN, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.GREEN, wx.SOLID))
            # set x, y, w, h for rectangle
            self.dc.DrawRectangle(39, 110, 8, 15)

        if self.port1[6]:
            self.dc.SetPen(wx.Pen(self.GREEN, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.GREEN, wx.SOLID))
            # set x, y, w, h for rectangle
            self.dc.DrawRectangle(83, 356, 8, 15)

        if self.port1[0]:
            self.dc.SetPen(wx.Pen(self.RED, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.RED, wx.SOLID))
            self.dc.DrawRectangle(70, 356, 8, 15)
        del self.dc
