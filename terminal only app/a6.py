"""
qtpyTerminal is a Qt widget that runs a Bash shell. 

qtpyTerminal VT100 emulation is powered by Pyte,
(https://github.com/selectel/pyte).
"""

import collections
import fcntl
import functools
import html
import os
import pty
import signal
import sys

import pyte
from pyte.screens import History
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Property as pyqtProperty
from qtpy.QtCore import QSize, QSocketNotifier, Qt, QTimer
from qtpy.QtCore import Signal as pyqtSignal, Slot as pyqtSlot
from qtpy.QtGui import QClipboard, QColor, QPalette, QTextCursor
from qtpy.QtWidgets import QApplication, QHBoxLayout, QScrollBar, QSizePolicy

if sys.platform != "win32":
    import fcntl
    import pty
else:
    # Windows doesn't have these modules
    # You'll need to use the Windows Console API or a different approach
    print("This terminal emulator is not supported on Windows.")
    print("Please use Linux or macOS.")
    sys.exit(1)


def SafeSlot(*slot_args, **slot_kwargs):  # pylint: disable=invalid-name
    """Function with args, acting like a decorator, to display errors instead of raising an exception
    """
    def error_managed(method):
        @pyqtSlot(*slot_args, **slot_kwargs)
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except Exception:
                sys.excepthook(*sys.exc_info())

        return wrapper

    return error_managed


ansi_colors = {
    "black": "#000000",
    "red": "#CD0000",
    "green": "#00CD00",
    "brown": "#996633",  # Brown, replacing the yellow
    "blue": "#0000EE",
    "magenta": "#CD00CD",
    "cyan": "#00CDCD",
    "white": "#E5E5E5",
    "brightblack": "#7F7F7F",
    "brightred": "#FF0000",
    "brightgreen": "#00FF00",
    "brightyellow": "#FFFF00",
    "brightblue": "#5C5CFF",
    "brightmagenta": "#FF00FF",
    "brightcyan": "#00FFFF",
    "brightwhite": "#FFFFFF",
}

control_keys_mapping = {
    QtCore.Qt.Key_A: b"\x01",  # Ctrl-A
    QtCore.Qt.Key_B: b"\x02",  # Ctrl-B
    QtCore.Qt.Key_C: b"\x03",  # Ctrl-C
    QtCore.Qt.Key_D: b"\x04",  # Ctrl-D
    QtCore.Qt.Key_E: b"\x05",  # Ctrl-E
    QtCore.Qt.Key_F: b"\x06",  # Ctrl-F
    QtCore.Qt.Key_G: b"\x07",  # Ctrl-G (Bell)
    QtCore.Qt.Key_H: b"\x08",  # Ctrl-H (Backspace)
    QtCore.Qt.Key_I: b"\x09",  # Ctrl-I (Tab)
    QtCore.Qt.Key_J: b"\x0A",  # Ctrl-J (Line Feed)
    QtCore.Qt.Key_K: b"\x0B",  # Ctrl-K (Vertical Tab)
    QtCore.Qt.Key_L: b"\x0C",  # Ctrl-L (Form Feed)
    QtCore.Qt.Key_M: b"\x0D",  # Ctrl-M (Carriage Return)
    QtCore.Qt.Key_N: b"\x0E",  # Ctrl-N
    QtCore.Qt.Key_O: b"\x0F",  # Ctrl-O
    QtCore.Qt.Key_P: b"\x10",  # Ctrl-P
    QtCore.Qt.Key_Q: b"\x11",  # Ctrl-Q
    QtCore.Qt.Key_R: b"\x12",  # Ctrl-R
    QtCore.Qt.Key_S: b"\x13",  # Ctrl-S
    QtCore.Qt.Key_T: b"\x14",  # Ctrl-T
    QtCore.Qt.Key_U: b"\x15",  # Ctrl-U
    QtCore.Qt.Key_V: b"\x16",  # Ctrl-V
    QtCore.Qt.Key_W: b"\x17",  # Ctrl-W
    QtCore.Qt.Key_X: b"\x18",  # Ctrl-X
    QtCore.Qt.Key_Y: b"\x19",  # Ctrl-Y
    QtCore.Qt.Key_Z: b"\x1A",  # Ctrl-Z
    QtCore.Qt.Key_Escape: b"\x1B",  # Ctrl-Escape
    QtCore.Qt.Key_Backslash: b"\x1C",  # Ctrl-\
    QtCore.Qt.Key_Underscore: b"\x1F",  # Ctrl-_
}

normal_keys_mapping = {
    QtCore.Qt.Key_Return: b"\n",
    QtCore.Qt.Key_Space: b" ",
    QtCore.Qt.Key_Enter: b"\n",
    QtCore.Qt.Key_Tab: b"\t",
    QtCore.Qt.Key_Backspace: b"\x08",
    QtCore.Qt.Key_Home: b"\x47",
    QtCore.Qt.Key_End: b"\x4f",
    QtCore.Qt.Key_Left: b"\x02",
    QtCore.Qt.Key_Up: b"\x10",
    QtCore.Qt.Key_Right: b"\x06",
    QtCore.Qt.Key_Down: b"\x0E",
    QtCore.Qt.Key_PageUp: b"\x49",
    QtCore.Qt.Key_PageDown: b"\x51",
    QtCore.Qt.Key_F1: b"\x1b\x31",
    QtCore.Qt.Key_F2: b"\x1b\x32",
    QtCore.Qt.Key_F3: b"\x1b\x33",
    QtCore.Qt.Key_F4: b"\x1b\x34",
    QtCore.Qt.Key_F5: b"\x1b\x35",
    QtCore.Qt.Key_F6: b"\x1b\x36",
    QtCore.Qt.Key_F7: b"\x1b\x37",
    QtCore.Qt.Key_F8: b"\x1b\x38",
    QtCore.Qt.Key_F9: b"\x1b\x39",
    QtCore.Qt.Key_F10: b"\x1b\x30",
    QtCore.Qt.Key_F11: b"\x45",
    QtCore.Qt.Key_F12: b"\x46",
}


def QtKeyToAscii(event):
    """
    Convert the Qt key event to the corresponding ASCII sequence for
    the terminal. This works fine for standard alphanumerical characters, but
    most other characters require terminal specific control sequences.
    """
    if sys.platform == "darwin":
        # special case for MacOS
        # /!\ Qt maps ControlModifier to CMD
        # CMD-C, CMD-V for copy/paste
        # CTRL-C and other modifiers -> key mapping
        if event.modifiers() == QtCore.Qt.MetaModifier:
            if event.key() == Qt.Key_Backspace:
                return control_keys_mapping.get(Qt.Key_W)
            return control_keys_mapping.get(event.key())
        elif event.modifiers() == QtCore.Qt.ControlModifier:
            if event.key() == Qt.Key_C:
                # copy
                return "copy"
            elif event.key() == Qt.Key_V:
                # paste
                return "paste"
            return None
        else:
            return normal_keys_mapping.get(event.key(), event.text().encode("utf8"))
    if event.modifiers() == QtCore.Qt.ControlModifier:
        return control_keys_mapping.get(event.key())
    else:
        return normal_keys_mapping.get(event.key(), event.text().encode("utf8"))


class Screen(pyte.HistoryScreen):
    def __init__(self, stdin_fd, cols, rows, historyLength):
        super().__init__(cols, rows, historyLength, ratio=1 / rows)
        self._fd = stdin_fd

    def write_process_input(self, data):
        """Response to CPR request (for example),
        this can be for other requests
        """
        try:
            os.write(self._fd, data.encode("utf-8"))
        except (IOError, OSError):
            pass

    def resize(self, lines, columns):
        lines = lines or self.lines
        columns = columns or self.columns

        if lines == self.lines and columns == self.columns:
            return  # No changes.

        self.dirty.clear()
        self.dirty.update(range(lines))

        self.save_cursor()
        if lines < self.lines:
            if lines <= self.cursor.y:
                nlines_to_move_up = self.lines - lines
                for i in range(nlines_to_move_up):
                    line = self.buffer[i]  # .pop(0)
                    self.history.top.append(line)
                self.cursor_position(0, 0)
                self.delete_lines(nlines_to_move_up)
                self.restore_cursor()
                self.cursor.y -= nlines_to_move_up
        else:
            self.restore_cursor()

        self.lines, self.columns = lines, columns
        self.history = History(
            self.history.top,
            self.history.bottom,
            1 / self.lines,
            self.history.size,
            self.history.position,
        )
        self.set_margins()


class Backend(QtCore.QObject):
    """
    This class will run as a qsocketnotifier (started in ``_TerminalWidget``) and poll the
    file descriptor of the underlying executed program.
    """

    # Signals to communicate with ``_TerminalWidget``.
    dataReady = pyqtSignal(object)
    processExited = pyqtSignal()

    def __init__(self, fd, cols, rows):
        super().__init__()

        # File descriptor that connects to the process.
        self.fd = fd

        self.screen = Screen(self.fd, cols, rows, 10000)
        self.stream = pyte.ByteStream()
        self.stream.attach(self.screen)

        self.notifier = QSocketNotifier(fd, QSocketNotifier.Read)
        self.notifier.activated.connect(self._fd_readable)

    def _fd_readable(self):
        """
        Poll the Bash output, run it through Pyte, and notify
        """
        # Read the shell output until the file descriptor is closed.
        try:
            out = os.read(self.fd, 2**16)
        except OSError:
            self.processExited.emit()
            self.notifier.setEnabled(False)
            return

        # Feed output into Pyte's state machine and send the new screen
        # output to the GUI
        self.stream.feed(out)
        self.dataReady.emit(self.screen)


class qtpyTerminal(QtWidgets.QWidget):
    """Container widget for the terminal text area"""
    def __init__(self, parent=None, cols=132):
        super().__init__(parent)

        self.term = _TerminalWidget(self, cols, rows=25)
        self.scroll_bar = QScrollBar(Qt.Vertical, self)
        # self.scroll_bar.hide()
        layout = QHBoxLayout(self)
        layout.addWidget(self.term)
        layout.addWidget(self.scroll_bar)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)

        pal = QPalette()
        self.set_bgcolor(pal.window().color())
        self.set_fgcolor(pal.windowText().color())
        self.term.set_scroll_bar(self.scroll_bar)
        self.set_cmd("") # will execute the default shell

    def minimumSizeHint(self):
        size = self.term.sizeHint()
        size.setWidth(size.width() + self.scroll_bar.width())
        return size

    def sizeHint(self):
        return self.minimumSizeHint()

    def get_rows(self):
        return self.term.rows

    def set_rows(self, rows):
        self.term.rows = rows
        self.adjustSize()
        self.updateGeometry()

    def get_cols(self):
        return self.term.cols

    def set_cols(self, cols):
        self.term.cols = cols
        self.adjustSize()
        self.updateGeometry()

    def get_bgcolor(self):
        return QColor.fromString(self.term.bg_color)

    def set_bgcolor(self, color):
        self.term.bg_color = color.name(QColor.HexRgb)

    def get_fgcolor(self):
        return QColor.fromString(self.term.fg_color)

    def set_fgcolor(self, color):
        self.term.fg_color = color.name(QColor.HexRgb)

    def get_cmd(self):
        return self.term._cmd

    def set_cmd(self, cmd):
        if not cmd:
            cmd = os.environ["SHELL"]
        self.term._cmd = cmd
        if self.term.fd is None:
            # not started yet
            self.term.clear()
            self.term.appendHtml(f"<h2>qtpyTerminal - {repr(cmd)}</h2>")

    @SafeSlot(bool)
    def start(self, deactivate_ctrl_d=True):
        self.term.start(deactivate_ctrl_d=deactivate_ctrl_d)

    @SafeSlot()
    def stop(self):
        self.term.stop()

    @SafeSlot(str)
    def push(self, text):
        """Push some text to the terminal"""
        return self.term.push(text)

    cols = pyqtProperty(int, get_cols, set_cols)
    rows = pyqtProperty(int, get_rows, set_rows)
    bgcolor = pyqtProperty(QColor, get_bgcolor, set_bgcolor)
    fgcolor = pyqtProperty(QColor, get_fgcolor, set_fgcolor)
    cmd = pyqtProperty(str, get_cmd, set_cmd)


class _TerminalWidget(QtWidgets.QPlainTextEdit):
    """
    Start ``Backend`` process and render Pyte output as text.
    """
    def __init__(self, parent, cols=125, rows=50, **kwargs):
        # file descriptor to communicate with the subprocess
        self.fd = None
        self.pid = None
        self.backend = None
        # command to execute
        self._cmd = ""
        # should ctrl-d be deactivated ? (prevent Python exit)
        self._deactivate_ctrl_d = False

        # Default colors
        pal = QPalette()
        self._fg_color = pal.text().color().name()
        self._bg_color = pal.base().color().name()

        # Specify the terminal size in terms of lines and columns.
        self._rows = rows
        self._cols = cols
        self.output = collections.deque()

        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        # Disable default scrollbars (we use our own, to be set via .set_scroll_bar())
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_bar = None

        # Use Monospace fonts and disable line wrapping.
        self.setFont(QtGui.QFont("Courier", 9))
        self.setFont(QtGui.QFont("Monospace"))
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        fmt = QtGui.QFontMetrics(self.font())
        char_width = fmt.width("w")
        self.setCursorWidth(char_width)

        self.adjustSize()
        self.updateGeometry()
        self.update_stylesheet()

    @property
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, hexcolor):
        self._bg_color = hexcolor
        self.update_stylesheet()

    @property
    def fg_color(self):
        return self._fg_color

    @fg_color.setter
    def fg_color(self, hexcolor):
        self._fg_color = hexcolor
        self.update_stylesheet()

    def update_stylesheet(self):
        self.setStyleSheet(
            f"QPlainTextEdit {{ border: 0; color: {self._fg_color}; background-color: {self._bg_color}; }} "
        )

    @property
    def rows(self):
        return self._rows

    @rows.setter
    def rows(self, rows: int):
        if self.backend is None:
            # not initialized yet, ok to change
            self._rows = rows
            self.adjustSize()
            self.updateGeometry()
        else:
            raise RuntimeError("Cannot change rows after console is started.")

    @property
    def cols(self):
        return self._cols

    @cols.setter
    def cols(self, cols: int):
        if self.fd is None:
            # not initialized yet, ok to change
            self._cols = cols
            self.adjustSize()
            self.updateGeometry()
        else:
            raise RuntimeError("Cannot change cols after console is started.")

    def stop(self):
        if self.fd:
            os.kill(self.pid, signal.SIGTERM)
            os.waitpid(self.pid, os.WNOHANG)

    def start(self, deactivate_ctrl_d: bool = False):
        self._deactivate_ctrl_d = deactivate_ctrl_d

        self.update_term_size()

        # Start the process
        self.fd, self.pid = self.fork_shell()

        if self.fd:
            # Create the ``Backend`` object
            self.backend = Backend(self.fd, self.cols, self.rows)
            self.backend.dataReady.connect(self.data_ready)
            self.backend.processExited.connect(self.process_exited)
        else:
            self.process_exited()

    @SafeSlot()
    def process_exited(self):
        self.fd = None
        self.clear()
        self.appendHtml(f"<br><h2>{repr(self._cmd)} - Process exited.</h2>")
        self.setReadOnly(True)

    @SafeSlot(object)
    def data_ready(self, screen):
        """Handle new screen: redraw, set scroll bar max and slider, move cursor to its position

        This method is triggered via a signal from ``Backend``.
        """
        self.redraw_screen()
        self.adjust_scroll_bar()
        self.move_cursor()

    def minimumSizeHint(self):
        """Return minimum size for current cols and rows"""
        fmt = QtGui.QFontMetrics(self.font())
        char_width = fmt.width("w")
        char_height = fmt.height()
        width = char_width * self.cols
        height = char_height * self.rows
        return QSize(width, height)

    def sizeHint(self):
        return self.minimumSizeHint()

    def set_scroll_bar(self, scroll_bar):
        self.scroll_bar = scroll_bar
        self.scroll_bar.setMinimum(0)
        self.scroll_bar.valueChanged.connect(self.scroll_value_change)

    def scroll_value_change(self, value, old={"value": -1}):
        if self.backend is None:
            return
        if old["value"] == -1:
            old["value"] = self.scroll_bar.maximum()
        if value <= old["value"]:
            # scroll up
            # value is number of lines from the start
            nlines = old["value"] - value
            # history ratio gives prev_page == 1 line
            for i in range(nlines):
                self.backend.screen.prev_page()
        else:
            # scroll down
            nlines = value - old["value"]
            for i in range(nlines):
                self.backend.screen.next_page()
        old["value"] = value
        self.redraw_screen()

    def adjust_scroll_bar(self):
        sb = self.scroll_bar
        sb.valueChanged.disconnect(self.scroll_value_change)
        tmp = len(self.backend.screen.history.top) + len(self.backend.screen.history.bottom)
        sb.setMaximum(tmp if tmp > 0 else 0)
        sb.setSliderPosition(tmp if tmp > 0 else 0)
        # if tmp > 0:
        #    # show scrollbar, but delayed - prevent recursion with widget size change
        #    QTimer.singleShot(0, scrollbar.show)
        # else:
        #    QTimer.singleShot(0, scrollbar.hide)
        sb.valueChanged.connect(self.scroll_value_change)

    def write(self, data):
        try:
            os.write(self.fd, data)
        except (IOError, OSError):
            self.process_exited()

    @SafeSlot(object)
    def keyPressEvent(self, event):
        """
        Redirect all keystrokes to the terminal process.
        """
        if self.fd is None:
            # not started
            return
        # Convert the Qt key to the correct ASCII code.
        if (
            self._deactivate_ctrl_d
            and event.modifiers() == QtCore.Qt.ControlModifier
            and event.key() == QtCore.Qt.Key_D
        ):
            return None

        code = QtKeyToAscii(event)
        if code == "copy":
            # MacOS only: CMD-C handling
            self.copy()
        elif code == "paste":
            # MacOS only: CMD-V handling
            self._push_clipboard()
        elif code is not None:
            self.write(code)

    def push(self, text):
        """
        Write 'text' to terminal
        """
        self.write(text.encode("utf-8"))

    def contextMenuEvent(self, event):
        if self.fd is None:
            return
        menu = self.createStandardContextMenu()
        for action in menu.actions():
            # remove all actions except copy and paste
            if "opy" in action.text():
                # redefine text without shortcut
                # since it probably clashes with control codes (like CTRL-C etc)
                action.setText("Copy")
                continue
            if "aste" in action.text():
                # redefine text without shortcut
                action.setText("Paste")
                # paste -> have to insert with self.push
                action.triggered.connect(self._push_clipboard)
                continue
            menu.removeAction(action)
        menu.exec_(event.globalPos())

    @SafeSlot()
    def _push_clipboard(self):
        clipboard = QApplication.instance().clipboard()
        self.push(clipboard.text())

    def move_cursor(self):
        textCursor = self.textCursor()
        textCursor.setPosition(0)
        textCursor.movePosition(
            QTextCursor.Down, QTextCursor.MoveAnchor, self.backend.screen.cursor.y
        )
        textCursor.movePosition(
            QTextCursor.Right, QTextCursor.MoveAnchor, self.backend.screen.cursor.x
        )
        self.setTextCursor(textCursor)

    def mouseReleaseEvent(self, event):
        if self.fd is None:
            return
        if event.button() == Qt.MiddleButton:
            # push primary selection buffer ("mouse clipboard") to terminal
            clipboard = QApplication.instance().clipboard()
            if clipboard.supportsSelection():
                self.push(clipboard.text(QClipboard.Selection))
            return None
        elif event.button() == Qt.LeftButton:
            # left button click
            textCursor = self.textCursor()
            if textCursor.selectedText():
                # mouse was used to select text -> nothing to do
                pass
            else:
                # a simple 'click', move scrollbar to end
                self.scroll_bar.setSliderPosition(self.scroll_bar.maximum())
                self.move_cursor()
                return None
        return super().mouseReleaseEvent(event)

    def redraw_screen(self):
        """
        Render the screen as formatted text into the widget.
        """
        screen = self.backend.screen

        # Clear the widget
        if screen.dirty:
            self.clear()
            while len(self.output) < (max(screen.dirty) + 1):
                self.output.append("")
            while len(self.output) > (max(screen.dirty) + 1):
                self.output.pop()

            # Prepare the HTML output
            for line_no in screen.dirty:
                line = text = ""
                style = old_style = ""
                old_idx = 0
                for idx, ch in screen.buffer[line_no].items():
                    text += " " * (idx - old_idx - 1)
                    old_idx = idx
                    style = f"{'background-color:%s;' % ansi_colors.get(ch.bg, ansi_colors['black']) if ch.bg!='default' else ''}{'color:%s;' % ansi_colors.get(ch.fg, ansi_colors['white']) if ch.fg!='default' else ''}{'font-weight:bold;' if ch.bold else ''}{'font-style:italic;' if ch.italics else ''}"
                    if style != old_style:
                        if old_style:
                            line += f"<span style={repr(old_style)}>{html.escape(text, quote=True)}</span>"
                        else:
                            line += html.escape(text, quote=True)
                        text = ""
                        old_style = style
                    text += ch.data
                if style:
                    line += f"<span style={repr(style)}>{html.escape(text, quote=True)}</span>"
                else:
                    line += html.escape(text, quote=True)
                # do a check at the cursor position:
                # it is possible x pos > output line length,
                # for example if last escape codes are "cursor forward" past end of text,
                # like IPython does for "..." prompt (in a block, like "for" loop or "while" for example)
                # In this case, cursor is at 12 but last text output is at 8 -> insert spaces
                if line_no == screen.cursor.y:
                    llen = len(screen.buffer[line_no])
                    if llen < screen.cursor.x:
                        line += " " * (screen.cursor.x - llen)
                self.output[line_no] = line
            # fill the text area with HTML contents in one go
            self.appendHtml(f"<pre>{chr(10).join(self.output)}</pre>")
            # did updates, all clean
            screen.dirty.clear()

    def update_term_size(self):
        fmt = QtGui.QFontMetrics(self.font())
        char_width = fmt.width("w")
        char_height = fmt.height()
        self._cols = int(self.width() / char_width)
        self._rows = int(self.height() / char_height)

    def resizeEvent(self, event):
        self.update_term_size()
        if self.fd:
            self.backend.screen.resize(self._rows, self._cols)
            self.redraw_screen()
            self.adjust_scroll_bar()
            self.move_cursor()

    def wheelEvent(self, event):
        if not self.fd:
            return
        y = event.angleDelta().y()
        if y > 0:
            self.backend.screen.prev_page()
        else:
            self.backend.screen.next_page()
        self.redraw_screen()

    def fork_shell(self):
        """
        Fork the current process and execute in shell.
        """
        try:
            pid, fd = pty.fork()
        except (IOError, OSError):
            return False
        if pid == 0:
            try:
                ls = os.environ["LANG"].split(".")
            except KeyError:
                ls = []
            if len(ls) < 2:
                ls = ["en_US", "UTF-8"]
            os.putenv("COLUMNS", str(self.cols))
            os.putenv("LINES", str(self.rows))
            os.putenv("TERM", "linux")
            os.putenv("LANG", ls[0] + ".UTF-8")
            if not self._cmd:
                self._cmd = os.environ["SHELL"]
            cmd = self._cmd
            if isinstance(cmd, str):
                cmd = cmd.split()
            try:
                os.execvp(cmd[0], cmd)
            except (IOError, OSError):
                pass
            os._exit(0)
        else:
            # We are in the parent process.
            # Set file control
            fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
            return fd, pid


if __name__ == "__main__":
    import argparse
    from qtpy import QtWidgets

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='qtpyTerminal - A Qt-based terminal emulator')
    parser.add_argument('--cols', type=int, default=132, help='Number of columns (default: 132)')
    parser.add_argument('--rows', type=int, default=25, help='Number of rows (default: 25)')
    parser.add_argument('--cmd', type=str, default='', help='Command to run (default: system shell)')
    args = parser.parse_args()

    # Create the Qt application and console
    app = QtWidgets.QApplication([])
    mainwin = QtWidgets.QMainWindow()
    title = "qtpyTerminal"
    mainwin.setWindowTitle(title)

    # Create terminal widget with specified settings
    console = qtpyTerminal(mainwin, cols=args.cols)
    console.rows = args.rows
    if args.cmd:
        console.cmd = args.cmd
    mainwin.setCentralWidget(console)
    
    # Set a reasonable default size
    mainwin.resize(1024, 768)
    
    # Start the terminal
    console.start()

    # Show widget and launch Qt's event loop
    mainwin.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        console.stop()
        sys.exit(0)
