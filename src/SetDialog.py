from PyQt5.QtWidgets import QDialog, QLabel, QKeySequenceEdit, QRadioButton, QLineEdit, QDialogButtonBox, QGridLayout
from PyQt5.QtCore import  Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence, QIcon
import icons

class SetDialog(QDialog):
    updateNeed = pyqtSignal()
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._numValid = False
        self._replaceList = [("control","Ctrl"),("alt","Alt"),("shift","Shift")]#两个包之间快捷键有出入的列表
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon(":/src/engineIcon/searchAll.ico"))
        self.setWindowTitle("设置")
        self.setWindowFlags(self.windowFlags()&~Qt.WindowContextHelpButtonHint)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setupUi()
    
    def setupUi(self):
        label1 = QLabel("唤醒热键", self)
        label2 = QLabel("每个引擎搜索文章数", self)
        label3 = QLabel("失去焦点后自动隐藏", self)
        
        #快捷键转换
        keyStr = ""
        for key in self._config["hotkey"]:
            keyStr += (key + "+")
        keyStr = keyStr[:-1]
        for param in self._replaceList:
            keyStr = keyStr.replace(param[0], param[1])
        #快捷键输入
        keySequence = QKeySequence(keyStr)
        self._keySequenceEdit = QKeySequenceEdit(keySequence,self)

        self._lineEdit = QLineEdit(self)
        self._lineEdit.setText(str(self._config["passageNum"]))
        self._lineEdit.setPlaceholderText("1至20的整数")
        self._lineEdit.textEdited.connect(self._textEditedHandle)

        #选择框
        self._radioButtonYes = QRadioButton("是", self)

        self._radioButtonNo = QRadioButton("否", self)

        if self._config["loseFocusHidden"]:
            self._radioButtonYes.setChecked(True)
        else:
            self._radioButtonNo.setChecked(True)

        self._buttonBox = QDialogButtonBox(self)
        self._buttonBox.setOrientation(Qt.Horizontal)
        self._buttonBox.addButton("确定",QDialogButtonBox.AcceptRole)
        self._buttonBox.addButton("取消",QDialogButtonBox.RejectRole)
        self._buttonBox.accepted.connect(self._acceptedHandle)
        self._buttonBox.rejected.connect(self.close)

        gridLayout = QGridLayout(self)
        gridLayout.addWidget(label1,0,0,1,1)
        gridLayout.addWidget(label2,1,0,1,1)
        gridLayout.addWidget(label3,2,0,1,1)
        gridLayout.addWidget(self._keySequenceEdit,0,1,1,2)
        gridLayout.addWidget(self._lineEdit,1,1,1,2)
        gridLayout.addWidget(self._radioButtonYes,2,1,1,1)
        gridLayout.addWidget(self._radioButtonNo,2,2,1,1)
        gridLayout.addWidget(self._buttonBox,3,0,1,3)
        gridLayout.setColumnStretch(0, 2)
        gridLayout.setColumnStretch(1, 1)
        gridLayout.setColumnStretch(2, 1)
    

    def _textEditedHandle(self, text):
        """文字改变时的槽函数，此处用来判定输入的合法性

        Args:
            text : 当前文字
        """
        text = str(text)
        try:
            num = int(text)
            if num < 1 :
                self._lineEdit.setText("1")
            elif num > 20:
                self._lineEdit.setText("20")
        except ValueError:
            self._lineEdit.setText(text[:-1])

    def _acceptedHandle(self):
        """确定被按下时的槽函数
        """
        self._config["passageNum"] = int(self._lineEdit.text())
        self._config["loseFocusHidden"] = self._radioButtonYes.isChecked()
        keyStr = self._keySequenceEdit.keySequence().toString()
        for param in self._replaceList:
            keyStr = keyStr.replace(param[1], param[0])
        keyStr = keyStr.lower()
        keyTuple = tuple(keyStr.split("+"))
        self._config["hotkey"] = keyTuple
        self.updateNeed.emit()
        self.close()
            

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    setDialog = SetDialog({"passageNum":10,"defaultExportPath":"C:\\Users\\ZhuTaoyuan\\Documents","loseFocusHidden":True,"hotkey":("control","alt","S")})
    setDialog.show()
    sys.exit(app.exec_())