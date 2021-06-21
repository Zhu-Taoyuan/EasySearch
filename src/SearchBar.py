from typing import Text
from PyQt5.QtWidgets import QAction, QWidget, QLineEdit, QHBoxLayout, QSizePolicy, QApplication, QPushButton, QMenu, QCompleter
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer, QThread, QEvent
from PyQt5.QtGui import QFont, QIcon, QStandardItemModel
from Keywords import getKeywordsList
import icons

class SearchBar(QWidget):
    """自定义搜索框组件，其主体是一个无边框窗口，由一个切换搜索引擎的菜单按钮和输入关键字的编辑框构成，并提供了关键字补全的接口
    """
    comfirmSearch = pyqtSignal(tuple) #回车键按下时会发送该信号
    activationChange = pyqtSignal() #活动窗口改变
    def __init__(self, width=1000, height=50, checkTime = 500):
        super().__init__()
        self.setWindowIcon(QIcon(":/src/engineIcon/searchAll.ico"))
        self._width = width #窗口宽度
        self._height = height #窗口高度
        self._checkTime = checkTime #关键字提示刷新事件
        self._timer = QTimer()
        self._timer.start()
        self._timer.timeout.connect(self._timer.stop)
        self._setupUi()

    def _setupUi(self):
        """初始化UI界面
        """
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.SplashScreen) #无边框 
        self.setFixedSize(1000, 50) #固定窗口大小
        #调整窗口初始位置
        desktop = QApplication.desktop()
        screen_rect = desktop.availableGeometry(0) #解决双屏问题，使其初始化到主屏幕上
        self.move((screen_rect.width()-self._width)//2, screen_rect.height()//5) #水平居中，竖直1/5处
        #增加布局
        self._horizontalLayout = QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0,0,0,0) #使布局紧贴窗口
        self._horizontalLayout.setSpacing(0)
        #添加引擎按钮
        self._button = EngineButton(QIcon(":/src/engineIcon/searchAll.ico"),self)
        #添加编辑框编辑框
        self._searchLineEdit = SearchLineEdit(self)
        self._searchLineEdit.setFocus()
        self._searchLineEdit.returnPressed.connect(self._returnPressedHandle) 
        self._searchLineEdit.textEdited.connect(self._textEditedHandle)
        #补全
        self._task = GetKeywords()
        self._task.keywordsGot.connect(self.setCompleterString)

        #添加控件
        self._horizontalLayout.addWidget(self._button)
        self._horizontalLayout.addWidget(self._searchLineEdit)

    def addSearchEngine(self, engine):
        """添加搜索引擎

        Args:
            engine (Engine): 需要添加的引擎
        """
        self._button.addSearchEngine(engine)

    def _getSearchEngine(self):
        """获取当前搜索引擎

        Returns:
            str: 当前搜索引擎，如果为""，则是启用所有搜索引擎
        """
        return self._button.searchEngineID

    def setCompleterString(self, stringList):
        """设置补全的字符串数组

        Args:
            stringList (list): 字符串数组
        """
        self._searchLineEdit.setCompleterString(stringList)

    def _textEditedHandle(self, text):
        """编辑框的文字被修改时的槽函数，如果程序修改不会接收到

        Args:
            text (QString): 当前的文本
        """
        if not self._timer.isActive():
            self._task.getKeywords(str(text))
            self._timer.start(self._checkTime)
    
    def _clearText(self):
        """清除编辑框的文字
        """
        self._searchLineEdit.setText("")

    def _returnPressedHandle(self):
        """回车按下的槽函数
        """
        text = self._searchLineEdit.text() 
        self._clearText()
        self.comfirmSearch.emit((self._getSearchEngine(),text))
    
    def changeEvent(self, event):
        """活动窗口改变的槽函数

        Args:
            event : 事件
        """
        if event.type() == QEvent.ActivationChange:
            self.activationChange.emit()
    
    def keyPressEvent(self, QKeyEvent):
        """按下ESC的槽函数

        Args:
            QKeyEvent : 事件
        """
        if QKeyEvent.key() == Qt.Key_Escape:
            self.hide()

class EngineButton(QPushButton):
    """实现菜单按钮，用于切换搜索引擎，初始化时可以设置默认全部搜索的图标
    """
    def __init__(self, icon, parent=None):
        super().__init__(parent)
        self._defaultIcon = icon
        self.searchEngineID = "" #储存当前搜索引擎，当为""时，使用所有搜索引擎
        self.setupUi()

    def setupUi(self):
        """初始化UI
        """
        self.setIcon(self._defaultIcon)
        self.setIconSize(QSize(40,40))
        self.resize(50,50)
        self.setStyleSheet("QPushButton{border-width:0px;border-style:groove;margin:0px;padding:0px;}QPushButton::menu-indicator{image:none;}")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self._menu = QMenu()
        self._menu.triggered.connect(self._menuTriggeredHandle)
        self.setMenu(self._menu)
        #添加全部搜索引擎
        engine = Engine(self._defaultIcon,"","聚合搜索")
        self.addSearchEngine(engine)
    
    def _menuTriggeredHandle(self, engine):
        """按钮菜单的槽函数

        Args:
            engine (Engine): 触发的搜索引擎
        """
        icon = engine.icon()
        self.setIcon(icon)
        self.searchEngineID = engine.searchEngineID
    
    def addSearchEngine(self, engine):
        """添加搜索引擎

        Args:
            engine (Engine): 需要添加的引擎
        """
        engine.setParent(self._menu)
        self._menu.addAction(engine)


class SearchLineEdit(QLineEdit):
    """搜索的编辑器，具体实现了鼠标的窗口拖动，关键词补全的接口
    """
    def __init__(self,parent):
        super().__init__(parent)
        self._parent = parent #使得可以操纵窗口的移动
        self.setupUi() #对QLineEdit的样式进行修改
        #重写鼠标图样需要的变量
        self._isTracking = False
        self._startPos = None
    
    def setupUi(self):
        """UI的设置
        """
        #边框设置
        self.setStyleSheet("border-width:0px;border-style:groove;")#消除边框
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        #字体
        font = QFont()
        font.setPointSize(18)
        self.setFont(font)
        self.setText("")
        #对齐
        self.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        #关键词提示
        self._model = QStandardItemModel(0,1,self)
        self._completer = QCompleter(self._model,self)
        self._completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self._completer.popup().setStyleSheet("font-family:SimSun;font-size:18pt;")
        self.setCompleter(self._completer)
    
    def setCompleterString(self, stringList):
        """设置补全的字符串数组

        Args:
            stringList (list): 字符串数组
        """
        self._model.removeRows(0,self._model.rowCount())
        self._model.insertRows(0,len(stringList))
        [self._model.setData(self._model.index(index,0),stringList[index]) for index in range(len(stringList))]

    def mousePressEvent(self, event):
        """重写鼠标点击事件

        Args:
            event : 事件对象
        """
        if event.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = event.globalPos() - self._parent.pos() #获取当前鼠标相对于窗口的坐标
            self.setCursor(Qt.SizeAllCursor)
            event.accept()
    
    def mouseMoveEvent(self, event):
        """重写鼠标移动函数，实现窗口拖动

        Args:
            event : 事件对象
        """
        if self._isTracking and self._startPos:
            self._parent.move(event.globalPos()-self._startPos) # 实际就是窗口以前的坐标加上坐标的偏移量
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """重写鼠标释放事件

        Args:
            event : 事件对象
        """
        self._isTracking = False
        self._startPos = None
        self.setCursor(Qt.IBeamCursor)
        event.accept()

class Engine(QAction):
    """搜索引擎类，用于用户添加搜索引擎
    """
    def __init__(self, icon, searchEngineID, searchEngineName):
        super().__init__()
        self.setIcon(icon)
        self.setText(searchEngineName)
        self.searchEngineID = searchEngineID
        self.searchEngineName = searchEngineName

class GetKeywords(QThread):
    """多线程爬取关键词，爬取完成后会发射信号
    """
    keywordsGot = pyqtSignal(list)
    def __init__(self):
        super().__init__()

    def getKeywords(self,text):
        self._text = text
        self.start()

    def run(self):
        keywords = getKeywordsList(self._text)
        self.keywordsGot.emit(keywords)



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from pathlib import Path
    app = QApplication(sys.argv)
    searchBar = SearchBar()
    # path = Path(__file__).parent.joinpath("baidu.ico")
    # searchBar.addSearchEngine(Engine(QIcon(str(path)),"baidu","百度"))
    path = Path(__file__).parent.joinpath("csdn.ico")
    searchBar.addSearchEngine(Engine(QIcon(str(path)),"csdn","CSDN"))
    searchBar.comfirmSearch.connect(lambda text: print(text))
    # task = GetKeywords()
    # task.keywordsGot.connect(searchBar.setCompleterString)
    # searchBar.searchTextChanged.connect(task.getKeywords)

    searchBar.show()
    sys.exit(app.exec_())


