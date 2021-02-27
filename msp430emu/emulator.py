from threading import Thread, Event, RLock
import queue
from os import path
import sys
import _msp430emu
from . import version
import wx
from wx.adv import RichToolTip
import time

source_dir = path.dirname(path.realpath(__file__))


class Emulator:
    EVENT_CONSOLE = 0
    EVENT_SERIAL = 1
    EVENT_GPIO = 2

    REG_NAMES_PORT1 = ['P1OUT', 'P1DIR', 'P1IFG', 'P1IES', 'P1IE', 'P1SEL', 'P1SEL2', 'P1REN', 'P1IN']
    REG_NAMES_BCM = ['DCOCTL', 'BCSCTL1', 'BCSCTL2', 'BCSCTL3', 'IE1', 'IFG1']
    REG_NAMES_TIMER_A = [
        'TA0CTL', 'TA0R', 'TA0CCTL0', 'TA0CCR0', 'TA0CCTL1', 'TA0CCR1', 'TA0CCTL2', 'TA0CCR2', 'TA0IV',
        'TA1CTL', 'TA1R', 'TA1CCTL0', 'TA1CCR0', 'TA1CCTL1', 'TA1CCR1', 'TA1CCTL2', 'TA1CCR2', 'TA1IV'
    ]
    REG_NAMES_USCI = [
        'UCA0CTL0', 'UCA0CTL1', 'UCA0BR0', 'UCA0BR1', 'UCA0MCTL', 'UCA0STAT',
        'UCA0RXBUF', 'UCA0TXBUF', 'UCA0ABCTL', 'UCA0IRTCTL', 'UCA0IRRCTL', 'IFG2'
    ]
    REG_NAMES_CPU = [
        'PC', 'SP', 'SR', 'CG2', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14', 'R15'
    ]

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
            self.load_file(self.load)

    def _on_serial(self, s):
        print("received " + s)
        self._cb(self.EVENT_SERIAL, s)

    def _on_console(self, s):
        self._cb(self.EVENT_CONSOLE, s)

    def _on_control(self, opcode, data):
        if opcode <= 0x0F:
            self._cb(self.EVENT_GPIO, opcode)

    def send_command(self, cmd):
        if self.started:
            _msp430emu.cmd(cmd)

    def write_serial(self, value):
        try:
            # self._serial_queue.put_nowait(value)
            cmd_val = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            self._cb(self.EVENT_CONSOLE, f"[UART TX] {cmd_val}\n")
        except queue.Full:
            self._cb(self.EVENT_CONSOLE, "UART TX queue is full, this value will not be sent\n")

    def get_port1_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x05)

    def get_bcm_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x03)

    def get_cpu_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x04)

    def get_timer_a_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x07)

    def get_usci_regs(self):
        if self.started:
            return _msp430emu.get_regs(0x08)

    def set_port1_en(self, value):
        if 255 >= value >= 0 and self.started:
            return _msp430emu.set_regs(0x05, value)

    def set_port1_dir(self, value):
        if 255 >= value >= 0 and self.started:
            return _msp430emu.set_regs(0x06, value)

    def reset(self):
        if self.started:
            _msp430emu.reset()

    def _start_emu(self):
        print("starting emulator...")
        self.started = True
        _msp430emu.init(self.load)
        self.started = False
        print("stopping emulator...")

    def _serial_writer(self):
        pass
        # while self.started:
        #     message = self._serial_queue.get()
        #     if message is None:
        #         break
        #     _msp430emu.write_serial(message)
        #     self._serial_queue.task_done()
        # print("stopping writer...")

    def load_file(self, fname):
        self.close()
        if not path.exists(fname):
            self._cb(self.EVENT_CONSOLE, f"Firmware file '{fname}' does not exist\n")
            return
        print("loading " + fname)
        self.load = fname
        # self._serial_queue = queue.Queue(maxsize=2)
        self._process = Thread(target=self._start_emu, daemon=False)
        # self._writer = Thread(target=self._serial_writer, daemon=False)
        self._process.start()
        # self._writer.start()

    def _cb(self, ev, data):
        if callable(self.callback):
            self.callback(ev, data)

    def __del__(self):
        self.close()

    def emulation_pause(self):
        if self.started:
            _msp430emu.pause()

    def emulation_start(self):
        if self.started:
            _msp430emu.play()

    def close(self):
        if self.started:
            self.started = False
            try:
                _msp430emu.stop()
            except SystemError:
                print("Failed gradually stop emulator")
            # if self._serial_queue.empty():
            #     self._serial_queue.put_nowait(None)
            # self._writer.join(1)
            self._process.join(1)


class EmulatorWindow(wx.Frame):
    def __init__(self, parent, title, load=None, update_fps=25):
        wx.Frame.__init__(self, parent, title=title)
        self.update_delay = 1 / update_fps

        self.control = wx.TextCtrl(self, size=wx.Size(400, 450),
                                   style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.control.Hide()

        self.control.WriteText("Initialising Emulator..\n")

        self.load = load
        self.emu = Emulator(load=self.load, callback=self.callback)

        self.serial = wx.TextCtrl(self, size=wx.Size(400, 450), style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.serial_input = wx.TextCtrl(self)
        self.statusBar = self.CreateStatusBar()  # A Statusbar in the bottom of the window

        file_menu = wx.Menu()
        view_menu = wx.Menu()
        debug_menu = wx.Menu()

        self.menu_navigation = {
            "&Firmware": (file_menu, 0, wx.ID_OPEN, "Open firmware", self.OnOpen),
            "&Reload\tCtrl+R": (file_menu, 0, wx.ID_RESET, "Reopen the same firmware file", self.OnLoad),
            "About": (file_menu, 0, wx.ID_ABOUT, "About", self.OnAbout),
            "E&xit": (file_menu, 0, wx.ID_EXIT, " Terminate the program", self.OnClose),

            "View Console": (view_menu, 1, wx.NewId(), "Show/Hide Emulator debug console", self.ToggleConsole),
            "Port1 Registers": (view_menu, 1, wx.NewId(), "Show/Hide Emulator Port1 register table", self.ToggleRegisters),
            "BCM Registers": (view_menu, 1, wx.NewId(), "Show/Hide Emulator BCM register table", self.ToggleRegisters),
            "TimerA Registers": (view_menu, 1, wx.NewId(), "Show/Hide Emulator TimerA register table", self.ToggleRegisters),
            "USCI Registers": (view_menu, 1, wx.NewId(), "Show/Hide Emulator USCI register table", self.ToggleRegisters),
            "CPU Registers": (view_menu, 1, wx.NewId(), "Show/Hide Emulator CPU register table", self.ToggleRegisters),
            "Clear serial": (view_menu, 0, wx.NewId(), "Clean text in serial window", lambda e: self.serial.Clear()),
            "Clear console": (view_menu, 0, wx.NewId(), "Clean text in console window", lambda e: self.control.Clear()),

            "Step\tCtrl+N": (debug_menu, 0, wx.NewId(), "Step single instruction", self.OnStep),
            "Registers": (debug_menu, 0, wx.NewId(), "Print registers in console", lambda e: self.emu.send_command("regs")),
        }

        for name, (menu, typ, wx_id, desc, action) in self.menu_navigation.items():
            if typ == 0:
                button = menu.Append(wx_id, name, desc)
            elif typ == 1:
                button = menu.AppendCheckItem(wx_id, name, desc)
            else:
                continue
            self.Bind(wx.EVT_MENU, action, button)

        menuBar = wx.MenuBar()
        menuBar.Append(file_menu, "&File")
        menuBar.Append(view_menu, "&View")
        menuBar.Append(debug_menu, "&Debug")
        self.SetMenuBar(menuBar)

        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('R'), wx.ID_RESET),
            (wx.ACCEL_CTRL, ord('N'), self.menu_navigation["Step\tCtrl+N"][2]),
        ])
        self.SetAcceleratorTable(accel_tbl)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_start_emu = wx.Button(self, -1, "Start")
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.btn_start_emu)
        self.btn_stop_emu = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.OnPause, self.btn_stop_emu)

        self.btn_key = wx.Button(self, -1, "Press P1.3 Key")
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
        self.btn_send_serial = wx.Button(self, -1, "Send")
        self.Bind(wx.EVT_BUTTON, self.SendSerial, self.btn_send_serial)
        self.sizer3.Add(self.serial_input, 1)
        self.sizer3.Add(self.btn_send_serial, 0)

        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer0.Add(self.serial, 1, wx.EXPAND)
        self.sizer0.Add(self.sizer3, 0, wx.EXPAND)

        panel = wx.Panel(self, size=wx.Size(275, 375))
        # img =
        # wx.StaticBitmap(panel, -1, img, (0, 0), (img.GetWidth(), img.GetHeight()))
        self.diagram = DrawRect(panel, -1, size=wx.Size(275, 375))

        self.sizer_diagram = wx.BoxSizer(wx.VERTICAL)
        self.sizer_diagram.Add(panel, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL)

        self.registers = RegisterPanel(self, self.emu)

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

        self.btn_key.Disable()
        self.btn_send_serial.Disable()

        self.emu_paused = True
        self.timer_running = Event()
        self.timer = Thread(target=self.OnTimer)
        self.timer.start()

        self.serial_buffer = ""
        self.serial_buffer_lock = RLock()

        if not self.emu.started:
            self.serial_input.Disable()
            self.serial.Disable()
            self.btn_rst.Disable()
            self.btn_start_emu.Disable()
            self.btn_stop_emu.Disable()
            self.statusBar.SetStatusText("Open firmware file to start simulation")
        else:
            self.statusBar.SetStatusText("Press start to run emulation")

    def callback(self, event, data):
        if event == Emulator.EVENT_CONSOLE:
            wx.CallAfter(self.control.AppendText, data)
        elif event == Emulator.EVENT_SERIAL:
            self.serial_buffer_lock.acquire()
            self.serial_buffer += data
            self.serial_buffer_lock.release()
            # wx.CallAfter(self.serial.AppendText, data)
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
        self.diagram.reset()
        self.btn_key.Disable()
        self.btn_send_serial.Disable()
        self.emu_paused = True
        if not self.emu.started:
            self.statusBar.SetStatusText("Open firmware file to start simulation")
            return

        self.serial_input.Enable()
        self.serial.Enable()
        self.btn_rst.Enable()
        self.btn_start_emu.Enable()
        self.btn_stop_emu.Enable()
        self.statusBar.SetStatusText("Press start to run emulation")

    def OnTimer(self):
        while 1:
            try:
                if self.timer_running.wait(self.update_delay):
                    break
            except TimeoutError:
                pass
            if self.emu_paused:
                continue
            port1 = self.emu.get_port1_regs()
            if port1 is not None and self.diagram.port1 != port1[0]:
                self.diagram.port1 = port1[0]
                wx.CallAfter(self.diagram.Refresh)

            self.serial_buffer_lock.acquire()
            if len(self.serial_buffer) > 0:
                wx.CallAfter(self.serial.AppendText, self.serial_buffer)
                self.serial_buffer = ""
            self.serial_buffer_lock.release()
            wx.CallAfter(self.registers.update_values)

    def OnPause(self, e):
        self.emu.emulation_pause()
        self.diagram.power = False
        self.diagram.Refresh()
        self.emu.get_port1_regs()
        self.btn_key.Disable()
        self.btn_send_serial.Disable()
        self.emu_paused = True

    def OnStart(self, e):
        if self.load is None:
            self.OnOpen(e)
        else:
            self.statusBar.SetStatusText("")
            self.emu.emulation_start()
            self.diagram.power = True
            self.diagram.Refresh()
            self.btn_key.Enable()
            self.btn_send_serial.Enable()
            self.emu_paused = False

    def OnClose(self, e):
        self.Close(True)

    def OnExit(self, e):
        self.emu.close()
        self.timer_running.set()
        e.Skip()

    def OnAbout(self, e):
        AboutWindow(self)

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
            self.emu.set_port1_en(8)  # P1.3 to ground
        e.Skip()

    def OnMouseUp(self, e):
        if self.btn_key_down:
            self.emu.set_port1_en(0)  # P1.3 to high z
            self.btn_key_down = False
        e.Skip()

    def OnKeyReset(self, e):
        self.diagram.reset()
        self.emu.reset()

    def SendSerial(self, e):
        text = self.serial_input.GetValue()
        self.emu.write_serial(text)
        self.serial_input.Clear()

    def OnStep(self, e):
        self.emu.send_command("step")
        self.registers.update_values()

    def ToggleRegisters(self, e):
        if e.Id == self.menu_navigation["Port1 Registers"][2]:
            panel = self.registers.panel_port1
        elif e.Id == self.menu_navigation["BCM Registers"][2]:
            panel = self.registers.panel_bmc
        elif e.Id == self.menu_navigation["TimerA Registers"][2]:
            panel = self.registers.panel_timer_a
        elif e.Id == self.menu_navigation["USCI Registers"][2]:
            panel = self.registers.panel_usci
        elif e.Id == self.menu_navigation["CPU Registers"][2]:
            panel = self.registers.panel_cpu
        else:
            return
        if e.Int == 0:
            panel.Hide()
        else:
            panel.Show()
        self.sizer.Fit(self)
        self.Layout()


class RegisterPanel(wx.Panel):
    def __init__(self, parent, emu: Emulator):
        wx.Panel.__init__(self, parent)
        self.font = wx.Font(wx.FontInfo(11).Family(wx.FONTFAMILY_TELETYPE))
        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.emu = emu
        self.regs_port1 = {name: None for name in emu.REG_NAMES_PORT1}
        self.regs_bcm = {name: None for name in emu.REG_NAMES_BCM + ["MCLK"]}
        self.regs_timer_a = {name: None for name in emu.REG_NAMES_TIMER_A}
        self.regs_usci = {name: None for name in emu.REG_NAMES_USCI}
        self.regs_cpu = {name: None for name in emu.REG_NAMES_CPU}

        self.grid_port1 = wx.FlexGridSizer(len(self.regs_port1), 2, 0, 10)
        self.grid_bmc = wx.FlexGridSizer(len(self.regs_bcm), 2, 0, 10)
        self.grid_timer_a = wx.FlexGridSizer(len(self.regs_timer_a), 2, 0, 10)
        self.grid_usci = wx.FlexGridSizer(len(self.regs_usci), 2, 0, 10)
        self.grid_cpu = wx.FlexGridSizer(len(self.regs_cpu), 2, 0, 5)

        self.panel_port1 = wx.Panel(self)
        self.panel_bmc = wx.Panel(self)
        self.panel_timer_a = wx.Panel(self)
        self.panel_usci = wx.Panel(self)
        self.panel_cpu = wx.Panel(self)

        # Stucture map of [panel, grid, regs, emu func]
        self.__struc = [
            (self.panel_port1, self.grid_port1, self.regs_port1, emu.get_port1_regs),
            (self.panel_bmc, self.grid_bmc, self.regs_bcm, emu.get_bcm_regs),
            (self.panel_timer_a, self.grid_timer_a, self.regs_timer_a, emu.get_timer_a_regs),
            (self.panel_usci, self.grid_usci, self.regs_usci, emu.get_usci_regs),
            (self.panel_cpu, self.grid_cpu, self.regs_cpu, emu.get_cpu_regs),
        ]

        for panel, grid, regs, _ in self.__struc:
            gridvals = []
            for name in regs.keys():
                text = wx.TextCtrl(panel, style=wx.TE_READONLY | wx.TE_NO_VSCROLL)
                text.SetMinSize((90, 15))
                text.SetFont(self.font)
                gridvals.append((wx.StaticText(panel, label=name),))
                gridvals.append((text, 1, wx.EXPAND))
                regs[name] = text
            grid.AddMany(gridvals)
            panel.SetSizer(grid)
            panel.Hide()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.panel_port1, proportion=1, flag=wx.ALL | wx.EXPAND)
        vbox.Add(self.panel_bmc, proportion=1, flag=wx.ALL | wx.EXPAND)
        self.box.Add(vbox, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        self.box.Add(self.panel_timer_a, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        self.box.Add(self.panel_cpu, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        self.box.Add(self.panel_usci, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        self.SetSizer(self.box)
        self.Center()
        self.Show()
        self.Fit()
        self.Layout()

    def _map(self, func, panel):
        values = func()
        if values is None:
            return None
        if panel == self.panel_bmc:
            formatted = [f"{value:08b}" for value in values]
            freq = "x"
            if values[0] == 96 and values[1] == 135:
                freq = "1.03"
            elif values[0] == 0b11010001 and values[1] == 0b10000110:
                freq = "1.00"
            elif values[0] == 0b10010010 and values[1] == 0b10001101:
                freq = "8.00"
            elif values[0] == 0b10011110 and values[1] == 0b10001110:
                freq = "12.0"
            elif values[0] == 0b10010101 and values[1] == 0b10001111:
                freq = "16.0"
            formatted.append(freq + " MHz")
        elif panel == self.panel_cpu:
            formatted = ["0x%0.4X" % int.from_bytes(values[i:i+2], sys.byteorder) for i in range(0, len(values), 2)]
        else:
            formatted = [f"{value:08b}" for value in values]
        return formatted

    def update_values(self):
        for panel, _, regs, emu_func in self.__struc:
            if not panel.IsShown():
                continue
            values = self._map(emu_func, panel)
            if values is None:
                continue
            if len(values) != len(regs):
                continue
            for i, reg in enumerate(regs.values()):
                if reg.GetValue() != values[i]:
                    reg.SetValue(values[i])


class AboutWindow(wx.Frame):
    def __init__(self, parent, title="About"):
        super().__init__(parent, title=title)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self._add_text(version.description)
        self._add_text("version: " + version.__version__, 20)
        self._add_text("wx version: " + wx.VERSION_STRING)
        self._add_text("python: " + sys.version)
        box = wx.BoxSizer()
        box.Add(self.vbox, 1, wx.ALL | wx.EXPAND, border=20)
        self.SetSizer(box)
        self.Layout()
        self.Fit()
        self.Center()
        self.Show()

    def _add_text(self, text, bottom=0):
        stext = wx.StaticText(self, label=text, style=wx.ALIGN_CENTRE_HORIZONTAL)
        if bottom > 0:
            self.vbox.Add(stext, 0, wx.BOTTOM | wx.EXPAND, border=bottom)
        else:
            self.vbox.Add(stext, 0, wx.EXPAND)


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
        self.port1 = 0
        self.image = wx.Bitmap(path.join(source_dir, "msp430.png"), wx.BITMAP_TYPE_PNG)

    def reset(self):
        self.power = False
        self.port1 = 0
        wx.CallAfter(self.Refresh)

    def OnPaint(self, evt):
        """set up the device context (DC) for painting"""
        self.dc = wx.PaintDC(self)
        self.dc.DrawBitmap(self.image, 0, 0, True)
        if self.power:
            self.dc.SetPen(wx.Pen(self.GREEN, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.GREEN, wx.SOLID))
            # set x, y, w, h for rectangle
            self.dc.DrawRectangle(39, 110, 8, 15)

        if self.port1 & 1 << 6:
            self.dc.SetPen(wx.Pen(self.GREEN, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.GREEN, wx.SOLID))
            # set x, y, w, h for rectangle
            self.dc.DrawRectangle(83, 356, 8, 15)

        if self.port1 & 1:
            self.dc.SetPen(wx.Pen(self.RED, style=wx.TRANSPARENT))
            self.dc.SetBrush(wx.Brush(self.RED, wx.SOLID))
            self.dc.DrawRectangle(70, 356, 8, 15)
        del self.dc


def run(load=None):
    app = wx.App(False)
    frame = EmulatorWindow(None, "MSP430 Emulator", load)
    app.MainLoop()
