from PyQt5.QtCore import QProcess, QStandardPaths, Qt, QEvent, QSettings, QPoint, QSize
from PyQt5.QtWidgets import QWidget, QApplication, QPlainTextEdit, QVBoxLayout, QMainWindow
from PyQt5.QtGui import QTextCursor
import sys
import shlex
import getpass
import socket
import os


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.cmdlist = []
        self.track = 0
        os.chdir(os.path.expanduser("~"))
        self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                + ":" + str(os.getcwd()) + "$ ")
        self.setWindowTitle('Terminal')
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.readyRead.connect(self.dataReady)
        self.proc.finished.connect(self.isFinished)
        self.proc.setWorkingDirectory(os.getcwd())
        self.cmdWindow = QPlainTextEdit()
        self.cmdWindow.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.cmdWindow.setFixedHeight(55)
        self.cmdWindow.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cmdWindow.setAcceptDrops(True)
        self.cursor = self.cmdWindow.textCursor()

        self.textWindow = QPlainTextEdit(self)
        self.setStyleSheet(stylesheet(self))

        self.textWindow.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.cmdWindow)
        layout.addWidget(self.textWindow)
        
        self.wid = QWidget()
        self.wid.setLayout(layout)
        self.setCentralWidget(self.wid)
        self.setGeometry(0, 0, 640, 480)
        self.cmdWindow.setPlainText(self.name)
        self.cursorEnd()
        self.cmdWindow.setFocus()

        self.cmdWindow.installEventFilter(self)
        QApplication.setCursorFlashTime(1000)
        self.cursorEnd()
        print(self.proc.workingDirectory())
        self.settings = QSettings("QTerminal", "QTerminal")
        self.readSettings()

    def closeEvent(self, e):
        self.writeSettings()

    def cursorEnd(self):
        self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                + ":" + str(os.getcwd()) + "$ ")
        self.cmdWindow.setPlainText(self.name)
        cursor = self.cmdWindow.textCursor()
        cursor.movePosition(11, 0)
        self.cmdWindow.setTextCursor(cursor)
        self.cmdWindow.setFocus()

    def eventFilter(self, source, event):
        if source == self.cmdWindow:
            if (event.type() == QEvent.DragEnter):
                event.accept()
                return True
            elif (event.type() == QEvent.Drop):
                print ('Drop')
                self.setDropEvent(event)
                return True
            elif (event.type() == QEvent.KeyPress):
                cursor = self.cmdWindow.textCursor()
                if event.key() == Qt.Key_Backspace:
                    if cursor.positionInBlock() <= len(self.name):
                        return True
                    else:
                        return False
        
                elif event.key() == Qt.Key_Return:
                    self.run_command()
                    return True
        
                elif event.key() == Qt.Key_Left:
                    if cursor.positionInBlock() <= len(self.name):
                        return True
                    else:
                        return False
            
                elif event.key() == Qt.Key_Delete:
                    if cursor.positionInBlock() <= len(self.name) - 1:
                        return True
                    else:
                        return False

                elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
                    
                    return True

                elif event.key() == Qt.Key_Up:
                    try:
                        if self.track != 0:
                            cursor.select(QTextCursor.BlockUnderCursor)
                            cursor.removeSelectedText()
                            self.cmdWindow.appendPlainText(self.name)
        
                        self.cmdWindow.insertPlainText(self.cmdlist[self.track])
                        self.track -= 1
        
                    except IndexError:
                        self.track = 0
                    return True

                elif event.key() == Qt.Key_Down:
                    try:
                        if self.track != 0:
                            cursor.select(QTextCursor.BlockUnderCursor)
                            cursor.removeSelectedText()
                            self.cmdWindow.appendPlainText(self.name)
        
                        self.cmdWindow.insertPlainText(self.cmdlist[self.track])
                        self.track += 1
        
                    except IndexError:
                        self.track = 0
                    return True

                else:
                    return False
            else:
                return False
        else:
            return False
        

    def copyText(self):
        self.textWindow.copy()

    def pasteText(self):
        self.cmdWindow.paste()

    def setDropEvent(self, event):
        self.cmdWindow.setFocus()
        if event.mimeData().hasUrls():
            f = str(event.mimeData().urls()[0].toLocalFile())
            print("is file:", f)
            if " " in f:
                self.cmdWindow.insertPlainText("'{}'".format(f))
            else:
                self.cmdWindow.insertPlainText(f)
            event.accept()
        elif event.mimeData().hasText():
            ft = event.mimeData().text()
            print("is text:", ft)
            if " " in ft:
                self.cmdWindow.insertPlainText("'{}'".format(ft))
            else:
                self.cmdWindow.insertPlainText(ft)
        else:
            event.ignore()

    def run_command(self):
        """This function will be called once a command is written and the Enter key is pressed.
        """
        print("started")
        cli = []
        cmd = ""
        t = ""
        self.textWindow.setFocus()
        self.textWindow.appendPlainText(self.cmdWindow.toPlainText())
        cli = shlex.split(self.cmdWindow.toPlainText().replace(self.name, '').replace("'", '"'), posix=False)
        cmd = str(cli[0]) 

        if cmd == "exit":
            quit()

        elif cmd == "cd":
            del cli[0]
            path = " ".join(cli)
            os.chdir(os.path.abspath(path))
            self.proc.setWorkingDirectory(os.getcwd())
            print("Directory:", self.proc.workingDirectory())
            self.cursorEnd()
        else:
            self.proc.setWorkingDirectory(os.getcwd())
            print("Directory", self.proc.workingDirectory())
            del cli[0]
            if (QStandardPaths.findExecutable(cmd)):
                self.cmdlist.append(self.cmdWindow.toPlainText().replace(self.name, ""))
                print("Command", cmd,  "found")
                t = " ".join(cli)
                if self.proc.state() != 2:
                    self.proc.waitForStarted()
                    self.proc.waitForFinished()
                    if "|" in t or ">" in t or "<" in t:
                        print("special characters")
                        self.proc.start('sh -c "' + cmd + ' ' + t + '"')
                        print("running",('sh -c "' + cmd + ' ' + t + '"'))
                    else:
                        self.proc.start(cmd + " " + t)
                        print("running", (cmd + " " + t))
            else:
                print("Command not found ...")
                self.textWindow.appendPlainText("Command not found ...")
                self.cursorEnd()

    def dataReady(self):
        out = ""
        try:
            out = str(self.proc.readAll(), encoding = 'utf8').rstrip()
        except TypeError:
            out = str(self.proc.readAll()).rstrip()
            self.textWindow.moveCursor(self.cursor.Start) 
        self.textWindow.appendPlainText(out)    


    def isFinished(self):
        self.name = (str(getpass.getuser()) + "@" + str(socket.gethostname()) 
                                + ":" + str(os.getcwd()) + "$ ")
        self.cmdWindow.setPlainText(self.name)
        self.cursorEnd()

    def readSettings(self):
        if self.settings.contains("commands"):
            self.cmdlist = self.settings.value("commands")
        if self.settings.contains("pos"):
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        if self.settings.contains("size"):
            size = self.settings.value("size", QSize(400, 400))
            self.resize(size)

    def writeSettings(self):
        self.settings.setValue("commands", self.cmdlist)
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())
        
def stylesheet(self):
    """Here you can set the fond color of the text and the background"""

    return """
    QMainWindow{
    background-color: #FFFFFF; }

    QMainWindow:title
    {
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #ca0619);
    color: #3465a4;
    }

    QPlainTextEdit
    {font-family: Noto Sans Mono; 
    font-size: 10pt; 
    background-color: #000000; 
    color: #1aee30; padding: 2; 
    border: none;}

    QPlainTextEdit:focus { 
    border: none; }

    QScrollBar {            
    border: 1px solid #2e3436;
    background: #292929;
    width:8px;
    height: 8px;
    margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle {
    background: #2e3436;
    min-height: 0px;
    min-width: 0px;
    }
    QScrollBar::add-line {
    background: #2e3436;
    height: 0px;
    width: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
    }
    QScrollBar::sub-line {
    background: #2e3436;
    height: 0px;
    width: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
    }

    QStatusBar {
    font-family: Noto Sans Mono; 
    font-size: 7pt; 
    color:  #1aee30;}

"""

def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    ex.raise_()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
    

