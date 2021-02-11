from threading import Thread, Event
from os import path
import _msp430emu
import wx
from wx.adv import RichToolTip

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

    SET_REG_P1_IN = 0x05

    def __init__(self, load=None, callback=None):
        # self.process = Popen([path.join(emu_dir, 'MSP430'), str(ws_port)], stdout=PIPE, stderr=PIPE)
        # self.ws_port = ws_port
        # self._start_ws()
        self.load = load
        self.started = False
        self.callback = callback

        _msp430emu.on_serial(self._on_serial)
        _msp430emu.on_console(self._on_console)
        # _msp430emu.on_control(self._on_control)

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

    def get_port1_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x05)

    def set_port1_in(self, value):
        if 255 >= value >= 0 and self.started:
            return _msp430emu.set_regs(0x05, value)

    def reset(self):
        if self.started:
            _msp430emu.reset()

    def _start_emu(self):
        print("starting emulator...")
        self.started = True
        _msp430emu.init(self.load)
        print("stopping emulator...")

    def load_file(self, fname):
        self.close()
        print("loading " + fname)
        self.load = fname
        self.process = Thread(target=self._start_emu, daemon=False)
        self.process.start()

    def _cb(self, ev, data):
        if callable(self.callback):
            self.callback(ev, data)

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
            try:
                _msp430emu.stop()
            except SystemError:
                print("Failed gradually stop emulator")
            self.process.join(2)


class EmulatorWindow(wx.Frame):
    def __init__(self, parent, title, load=None):
        wx.Frame.__init__(self, parent, title=title)
        self.control = wx.TextCtrl(self, size=wx.Size(400, 450),
                                   style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.control.Hide()

        self.serial = wx.TextCtrl(self, size=wx.Size(400, 450), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.serial_input = wx.TextCtrl(self)

        self.statusBar = self.CreateStatusBar()  # A Statusbar in the bottom of the window

        file_menu = wx.Menu()
        menuFile = file_menu.Append(wx.ID_OPEN, "&Firmware", " Open firmware")
        self.Bind(wx.EVT_MENU, self.OnOpen, menuFile)
        menuReload = file_menu.Append(wx.ID_RESET, "Reload", " Reopen the same firmware file")
        self.Bind(wx.EVT_MENU, self.OnLoad, menuReload)
        # menuReset = file_menu.Append(wx.ID_CLOSE_ALL, "&Reset", " Reset Emulator")
        # self.Bind(wx.EVT_MENU, self.RestartEmulator, menuReset)
        menuExit = file_menu.Append(wx.ID_EXIT, "E&xit", " Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnClose, menuExit)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        view_menu = wx.Menu()
        self.view_console = view_menu.AppendCheckItem(101, "View Console", "Show/Hide Emulator debug console")
        self.view_registers = view_menu.AppendCheckItem(102, "View Registers", "Show/Hide Emulator registers table")
        self.Bind(wx.EVT_MENU, self.ToggleConsole, self.view_console)
        self.Bind(wx.EVT_MENU, self.ToggleRegisters, self.view_registers)
        self.registers = RegisterPanel(self)
        self.registers.Hide()

        menuBar = wx.MenuBar()
        menuBar.Append(file_menu, "&File")
        menuBar.Append(view_menu, "&View")

        self.SetMenuBar(menuBar)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_start_emu = wx.Button(self, -1, "Start")
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.btn_start_emu)
        self.btn_stop_emu = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.OnPause, self.btn_stop_emu)

        self.btn_key = wx.Button(self, -1, "Press Key")
        self.btn_key.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.btn_key.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.btn_key_down = False
        self.btn_rst = wx.Button(self, -1, "Reset")
        self.Bind(wx.EVT_BUTTON, self.OnKeyReset, self.btn_rst)

        self.sizer2.Add(self.btn_key, 1, wx.EXPAND)
        self.sizer2.Add(self.btn_start_emu, 1, wx.EXPAND)
        self.sizer2.Add(self.btn_stop_emu, 1, wx.EXPAND)
        self.sizer2.Add(self.btn_rst, 1, wx.EXPAND)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_start_emu = wx.Button(self, -1, "Send")
        self.Bind(wx.EVT_BUTTON, self.SendSerial, self.btn_start_emu)
        self.sizer3.Add(self.serial_input, 1)
        self.sizer3.Add(self.btn_start_emu, 0)

        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer0.Add(self.serial, 1, wx.EXPAND)
        self.sizer0.Add(self.sizer3, 0, wx.EXPAND)

        panel = wx.Panel(self, size=wx.Size(275, 375))
        # img =
        # wx.StaticBitmap(panel, -1, img, (0, 0), (img.GetWidth(), img.GetHeight()))
        self.diagram = DrawRect(panel, -1, size=wx.Size(275, 375))
        #
        # dc = wx.WindowDC(panel)
        # dc.SetPen(wx.WHITE_PEN)
        # dc.SetBrush(wx.WHITE_BRUSH)
        # dc.DrawRectangle(50, 50, 500, 500)

        # self.sizer_key_rst = wx.BoxSizer(wx.HORIZONTAL)
        # btn_key = wx.Button(self, -1, "Press Key")
        # self.Bind(wx.EVT_BUTTON, self.OnKeyPress, btn_key)
        # btn_rst = wx.Button(self, -1, "Reset")
        # self.Bind(wx.EVT_BUTTON, self.OnKeyReset, btn_rst)
        # self.sizer_key_rst.Add(btn_key, 1, wx.EXPAND)
        # self.sizer_key_rst.Add(btn_rst, 1, wx.EXPAND)

        self.sizer_diagram = wx.BoxSizer(wx.VERTICAL)
        self.sizer_diagram.Add(panel, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)
        #
        # self.sizer_left = wx.BoxSizer(wx.VERTICAL)
        # self.sizer_left.Add(self.sizer_diagram, 1, wx.EXPAND)
        # self.sizer_left.Add(self.sizer_key_rst, 0, wx.ALIGN_BOTTOM)

        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(self.sizer_diagram, 0, wx.EXPAND)
        self.sizer1.Add(self.registers, 0, wx.EXPAND)
        self.sizer1.Add(self.control, 0, wx.EXPAND)
        self.sizer1.Add(self.sizer0, 1, wx.EXPAND)

        self.sizer.Add(self.sizer1, 1, wx.EXPAND)
        self.sizer.Add(self.sizer2, 0, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.Show()

        self.emu_paused = True
        self.timer_running = Event()
        self.timer = Thread(target=self.OnTimer)
        self.timer.start()

        self.control.WriteText("Initialising Emulator..\n")
        self.load = load
        self.emu = Emulator(load=self.load, callback=self.callback)
        if self.load is None:
            self.serial_input.Disable()
            self.serial.Disable()
            self.btn_rst.Disable()
            self.btn_key.Disable()
            self.btn_start_emu.Disable()
            self.btn_stop_emu.Disable()
        else:
            self.statusBar.SetStatusText("Press start to run emulation")

    def callback(self, event, data):
        if event == Emulator.EVENT_CONSOLE:
            wx.CallAfter(self.control.AppendText, data)
        elif event == Emulator.EVENT_SERIAL:
            wx.CallAfter(self.serial.AppendText, data)
        # elif event == Emulator.EVENT_GPIO:
        #     self.diagram.port1[data // 2] = data % 2 == 0
        #     wx.CallAfter(self.diagram.Refresh)

    def RestartEmulator(self, e):
        self.emu.close()
        self.control.Clear()
        self.serial.Clear()
        self.emu = Emulator(load=self.load, callback=self.callback)

    def ToggleConsole(self, e):
        if e.Int == 0:
            self.control.Hide()
            self.sizer.Fit(self)
            self.Layout()
        else:
            self.control.Show()
            self.sizer.Fit(self)
            self.Layout()


    def OnOpen(self, e):
        with wx.FileDialog(self, "Open Firmware File", wildcard="BIN files (*.bin)|*.bin",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            self.load = fileDialog.GetPath()
            self.OnLoad(None)


    def OnLoad(self, e):
        if self.load is None:
            return
        self.emu.load_file(self.load)
        self.diagram.power = False
        self.emu_paused = True

        self.serial_input.Enable()
        self.serial.Enable()
        self.btn_rst.Enable()
        self.btn_key.Enable()
        self.btn_start_emu.Enable()
        self.btn_stop_emu.Enable()
        self.statusBar.SetStatusText("Press start to run emulation")

    def OnTimer(self):
        while 1:
            try:
                if self.timer_running.wait(0.04):
                    break
            except TimeoutError:
                pass
            if self.emu_paused:
                continue
            ports = self.emu.get_port1_regs()
            if ports is not None:
                for i in range(8):
                    self.diagram.port1[i] = (ports[0] >> i) & 1 == 1
            if not self.btn_key_down and ports[0] & 8 and ports[7] & 8 and not ports[1] & 8:
                self.emu.set_port1_in(8)  # P1.3 high
            wx.CallAfter(self.diagram.Refresh)
            if self.view_registers.IsChecked():
                wx.CallAfter(self.registers.set_values, self.emu)

    def OnPause(self, e):
        self.emu.emulation_pause()
        self.diagram.power = False
        self.diagram.Refresh()
        self.emu.get_port1_regs()
        self.emu_paused = True

    def OnStart(self, e):
        if self.load is None:
            self.OnOpen(e)
        else:
            self.statusBar.SetStatusText("")
            self.emu.emulation_start()
            self.diagram.power = True
            self.diagram.Refresh()
            self.emu_paused = False

    def OnClose(self, e):
        self.Close(True)

    def OnExit(self, e):
        self.emu.close()
        self.timer_running.set()
        e.Skip()

    def OnMouseDown(self, e):
        if self.emu_paused:
            e.Skip()
            return
        regs = self.emu.get_port1_regs()
        err = []
        if regs[1] & 8:
            err.append("P1DIR is set as output")
        if regs[5] & 8:
            err.append("P1SEL is not set to I/O function")
        if regs[6] & 8:
            err.append("P1SEL2 is not set to I/O function")
        if not regs[7] & 8:
            err.append("P1REN has pullup/pulldown resistor disabled")
        if regs[7] & 8 and not regs[0] & 8:
            err.append("P1OUT is set with pull down resistor")
        if len(err) > 0:
            tip = RichToolTip("Invalid configuration", '\n'.join(err))
            tip.SetIcon(wx.ICON_WARNING)
            tip.ShowFor(self.btn_key)
        else:
            self.btn_key_down = True
            self.emu.set_port1_in(0)  # P1.3 low
        e.Skip()

    def OnMouseUp(self, e):
        if self.btn_key_down:
            self.emu.set_port1_in(8)  # P1.3 high
            self.btn_key_down = False
        e.Skip()

    def OnKeyReset(self, e):
        self.diagram.port1 = [False, False, False, False, False, False, False, False]
        self.emu.reset()

    def SendSerial(self, e):
        text = self.serial_input.GetValue()
        print(text)
        self.serial_input.Clear()

    def ToggleRegisters(self, e):
        if e.Int == 0:
            # self.registers.Close()
            self.registers.Hide()
        else:
            self.registers.Show()
        self.sizer.Fit(self)
        self.Layout()

            # self.registers = RegisterPanel(self)
            # self.registers.Bind(wx.EVT_CLOSE, self.OnRegistersClose)
            # self.registers.set_values(self.emu)

    # def OnRegistersClose(self, e):
    #     self.view_registers.Check(False)
    #     e.Skip()


class RegisterPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.grid = wx.FlexGridSizer(9, 2, 0, 10)
        self.p1_registers = {
            'P1OUT': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1DIR': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1IFG': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1IES': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1IE': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1SEL': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1SEL2': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1REN': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
            'P1IN': wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_NO_VSCROLL),
        }
        gridvals = []
        for name, text in self.p1_registers.items():
            text.SetMinSize((80, 15))
            text.SetValue("00000000")
            gridvals.append((wx.StaticText(self, label=name),))
            gridvals.append((text, 1, wx.EXPAND))
        self.grid.AddMany(gridvals)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.grid, proportion=1, flag=wx.ALL | wx.EXPAND, border=15)
        self.SetSizer(box)
        self.Center()
        self.Show()
        self.Fit()
        self.Layout()

    def set_values(self, emu):
        p1regs = emu.get_port1_regs()
        if p1regs is not None:
            for i, reg in enumerate(self.p1_registers.values()):
                reg.SetValue(f"{p1regs[i]:08b}")


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
        self.image = wx.Bitmap(path.join(source_dir, "msp430.png"), wx.BITMAP_TYPE_PNG)

    def OnPaint(self, evt):
        """set up the device context (DC) for painting"""
        self.dc = wx.PaintDC(self)

        self.dc.DrawBitmap(self.image, 0, 0, True)
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


def run(load=None):
    app = wx.App(False)
    frame = EmulatorWindow(None, "MSP430 Emulator", load)
    app.MainLoop()
