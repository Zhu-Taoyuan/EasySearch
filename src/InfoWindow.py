from PyQt5.QtWidgets import QPushButton, QWidget, QTabBar, QVBoxLayout, QTabWidget, QHBoxLayout, QListWidget,\
    QStackedWidget, QListWidgetItem, QProgressBar, QGridLayout, QLabel, QSizePolicy, QSpacerItem,\
    QLineEdit, QAction, QApplication, QFileDialog, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal, QTimer,  QMarginsF, QSize, QModelIndex
from PyQt5.QtGui import  QIcon, QPageLayout, QPageSize, QColor
from PyQt5.QtWebEngineWidgets import QWebEngineView
import datetime
from pathlib import Path
import icons

class InfoWindow(QWidget):
    """显示查询结果的窗口类
    """
    def __init__(self):
        super().__init__()
        self._resultDict = None
        self.setupUi()

    def setupUi(self):
        self.setAttribute(Qt.WA_QuitOnClose, False)#用于解决此窗口关闭后，整个程序都关闭的问题
        self.setWindowIcon(QIcon(":/src/engineIcon/searchAll.ico"))
        self.resize(1000, 600)
        #进度条的显示页
        self._processPage = ProcessPage("爬虫正在运行中...")
        #搜索结果的显示页
        self._searchPage = SearchPage()
        self.previewNeed = self._searchPage.previewNeed
        #第一个主标签页
        self._mainTab = QStackedWidget()
        self._mainTab.addWidget(self._processPage)
        self._mainTab.addWidget(self._searchPage)
        self._mainTab.setCurrentWidget(self._processPage)
        #添加标签组件
        self._tabWidget = QTabWidget(self)
        self._tabWidget.setElideMode(Qt.ElideRight)
        self._tabWidget.setDocumentMode(False)
        self._tabWidget.setTabsClosable(True)
        self._tabWidget.setTabBarAutoHide(True)
        self._tabWidget.addTab(self._mainTab, "搜索结果")
        self._tabWidget.setCurrentIndex(0)
        self._tabWidget.tabBar().setTabButton(0, QTabBar.RightSide, None)#去除第一个标签页的关闭按钮
        self._tabWidget.tabBar().setTabTextColor(0,QColor(255,0,0,255))
        self._tabWidget.tabCloseRequested.connect(self._tableCloseHandle)#能够关闭标签页
        #主窗口的布局
        self._verticalLayout = QVBoxLayout(self)
        self._verticalLayout.setContentsMargins(0, 0, 0, 0)
        self._verticalLayout.addWidget(self._tabWidget)

    def showSearchPage(self, resultDict):
        """显示查询到的结果

        Args:
            resultDict (dict): 查询到的结果字典
        """
        self._resultDict = resultDict
        self._searchPage.showDate(resultDict)
        self._mainTab.setCurrentWidget(self._searchPage)
    
    def showPreview(self, title, href, htmlCode, config):
        """显示预览页面

        Args:
            title (str): 标签页标题
            href (str): 文章超链接
            htmlCode (str): 文章HTML源代码
            config (str): 系统默认配置
        """
        tab = PreviewTab(self, href, htmlCode, config)
        self._tabWidget.addTab(tab, title)
        self._tabWidget.setCurrentWidget(tab)

    def _tableCloseHandle(self, currentIndex):
        """标签页的关闭的槽函数

        Args:
            currentIndex (int): 关闭标签的索引
        """
        self._tabWidget.removeTab(currentIndex)


class SearchPage(QWidget):
    """结果显示页
    """
    previewNeed = pyqtSignal(tuple) #选项被单击，需要预览的信号

    def __init__(self):
        super().__init__()
        self._resultDict = None
        self._engineIDs = None
        self._engineNow = None
        self.setupUi()

    def setupUi(self):
        self._resultListWidget = QListWidget(self)#结果的列出框
        self._resultListWidget.setStyleSheet("font-size:20px;")
        self._engineListWidget = QListWidget(self)#引擎的选择框
        self._engineListWidget.setIconSize(QSize(30,30))
        self._engineListWidget.setStyleSheet("font-size:20px;outline: 0px;border:0px;")
        self._horizontalLayout = QHBoxLayout(self)
        self._horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self._horizontalLayout.addWidget(self._engineListWidget)
        self._horizontalLayout.addWidget(self._resultListWidget)
        self._horizontalLayout.setStretch(1, 10)
        #数据显示操作            
        self._engineListWidget.itemClicked.connect(self._engineChooseHandle)
        self._resultListWidget.itemClicked.connect(self._previewHandle)

    def showDate(self, resultDict):
        """显示查询到的结果

        Args:
            resultDict (dict): 存储结果的字典
        """
        self._resultDict = resultDict
        self._engineIDs = list(resultDict.keys())
        for engineID in self._resultDict:
            icon = self._resultDict[engineID]["icon"]
            engineName = self._resultDict[engineID]["engineName"]
            engineItem = QListWidgetItem(icon,engineName,self._engineListWidget)
            self._engineListWidget.addItem(engineItem)
        self._engineListWidget.setCurrentRow(0)
        self._engineListWidget.itemClicked.emit(self._engineListWidget.item(0))

    def _engineChooseHandle(self,item):
        self._resultListWidget.clear()
        index = self._engineListWidget.indexFromItem(item).row()
        engineID = self._engineIDs[index]
        results = self._resultDict[engineID]["results"]
        for result in results:
            item = QListWidgetItem(result["title"],self._resultListWidget)
            item.setToolTip(result["desc"])
            self._resultListWidget.addItem(item)
        self._engineNow = engineID


    def _previewHandle(self, item):
        index = self._resultListWidget.indexFromItem(item).row()
        self.previewNeed.emit((self._engineNow, index))

class ProcessPage(QWidget):
    """等待页
    """
    def __init__(self, tips):
        super().__init__()
        self._tips = tips
        self.setupUi()
    
    def setupUi(self):
        #进度条
        self._processBar = QProgressBar()
        self._processBar.setMinimum(0)
        self._processBar.setMaximum(0)#使其成跑马灯的效果
        self._processBar.setTextVisible(False)
        #标签
        self._label = QLabel(self._tips,self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self._label.sizePolicy().hasHeightForWidth())
        self._label.setSizePolicy(sizePolicy)
        self._label.setAlignment(Qt.AlignCenter)
        #站空元素
        spacerItemUp = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        spacerItemLeft = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItemRight = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        spacerItemDown = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        #布局
        self._gridLayout = QGridLayout(self)
        self._gridLayout.addItem(spacerItemUp, 0, 1, 1, 1)
        self._gridLayout.addItem(spacerItemLeft, 1, 0, 1, 1)
        self._gridLayout.addWidget(self._label, 1, 1, 1, 1)
        self._gridLayout.addItem(spacerItemRight, 1, 2, 1, 1)
        self._gridLayout.addWidget(self._processBar, 2, 1, 1, 1)
        self._gridLayout.addItem(spacerItemDown, 3, 1, 1, 1)
        self._gridLayout.setColumnStretch(0, 1)
        self._gridLayout.setColumnStretch(1, 1)
        self._gridLayout.setColumnStretch(2, 1)
        self._gridLayout.setRowStretch(0, 1)
        self._gridLayout.setRowStretch(1, 1)
        self._gridLayout.setRowStretch(2, 1)
        self._gridLayout.setRowStretch(3, 1)
        self._gridLayout.setContentsMargins(0, 0, 0, 0)

class PreviewTab(QWidget):
    """预览标签页
    """
    def __init__(self, parent, href, htmlCode, config):
        super().__init__(parent)
        self._href = href
        self._htmlCode = htmlCode
        self._path = config["defaultExportPath"]
        self._config = config
        self.setUpUi()

    def setUpUi(self):
        self._webWidget = QWebEngineView(self) # 用于浏览网页
        self._webWidget.setHtml(self._htmlCode)
        self._webWidget.setContentsMargins(10,10,10,10)

        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        label = QLabel("网页地址：")
        urlLineEdit = QLineEdit(self._href)#显示超链接
        urlLineEdit.home(False)#光标回到第一个位置
        urlLineEdit.setReadOnly(True)#不可编辑
        icon = QIcon(":/src/icon/copyIcon.ico")
        copyAction = QAction(urlLineEdit)
        copyAction.setIcon(icon)
        copyAction.setToolTip("复制链接")
        copyAction.triggered.connect(self._copyHandle)
        urlLineEdit.addAction(copyAction, QLineEdit.TrailingPosition)
        self._pathLineEdit = QLineEdit(self._path)
        self._pathLineEdit.home(False)#光标回到第一个位置
        self._pathLineEdit.setReadOnly(True)#不可编辑
        pathAction = QAction(self._pathLineEdit)
        icon = QIcon(":/src/icon/fileOpen.ico")
        pathAction.setIcon(icon)
        pathAction.setToolTip("更改导出文件路径")
        pathAction.triggered.connect(self._pathHandle)
        self._pathLineEdit.addAction(pathAction, QLineEdit.TrailingPosition)
        exportButton = QPushButton("导出为PDF")
        exportButton.clicked.connect(self._export)
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setContentsMargins(0,0,0,0)
        horizontalLayout.addItem(spacerItem)
        horizontalLayout.addWidget(label)
        horizontalLayout.addWidget(urlLineEdit)
        horizontalLayout.addWidget(self._pathLineEdit)
        horizontalLayout.addWidget(exportButton)
    
        verticalLayout = QVBoxLayout(self)
        #verticalLayout.setContentsMargins(0,0,0,0)
        verticalLayout.addWidget(self._webWidget)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.setStretch(0, 10)
        verticalLayout.setStretch(1, 1)


    def _copyHandle(self):
        """复制超链接
        """
        clipboard = QApplication.clipboard()
        clipboard.setText(self._href)
        #汉化提示框
        messageBox = QMessageBox(self)
        messageBox.setIcon(QMessageBox.Information)
        messageBox.setWindowTitle("提示")
        messageBox.setText("已复制到粘贴板")
        messageBox.addButton("确定",QMessageBox.AcceptRole)
        messageBox.exec_()
    
    def _pathHandle(self):
        """修改路径
        """
        filePath = QFileDialog.getExistingDirectory(self,"请选择需要导出的文件夹",self._path)
        self._path = filePath if filePath else self._path
        self._pathLineEdit.setText(self._path)
        self._pathLineEdit.home(False)#光标回到第一个位置
    
    def _export(self):
        """打印为pdf
        """
        self._page = self._webWidget.page()
        fileName = "Export_" + datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f')[:-3] + ".pdf" #用时间命名
        path = str(Path(self._path).joinpath(fileName)) 
        layout = QPageLayout(QPageSize(QPageSize.A4),QPageLayout.Portrait, QMarginsF(31.8,25.4,31.8,25.4))#打印的纸张设置,页边距
        self._printProcess = PrintProcess(self)
        self._printProcess.startExport()
        self._page.pdfPrintingFinished.connect(lambda: self._printProcess.endExport())
        self._page.printToPdf(path, layout)
        self._printProcess.exec_()
        self._config["defaultExportPath"] = self._path

class PrintProcess(QDialog):
    """pdf导出进程提示程序

    Args:
        QDialog ([type]): [description]
    """
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(":/src/engineIcon/searchAll.ico"))
        self.setFixedSize(200,105)
        self.setWindowTitle("提示")
        self.setWindowFlags(self.windowFlags()&~(Qt.WindowContextHelpButtonHint | Qt.WindowCloseButtonHint))#禁用关闭和帮助按钮
        verticalLayout = QVBoxLayout(self)
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        verticalLayout.addWidget(self._label)
        self._progressBar = QProgressBar(self)
        self._progressBar.setTextVisible(False)
        verticalLayout.addWidget(self._progressBar)
        self._buttonBox = QDialogButtonBox(self)
        self._buttonBox.setOrientation(Qt.Horizontal)
        self._buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self._buttonBox.button(QDialogButtonBox.Ok).setText("确定")
        self._buttonBox.setCenterButtons(True)
        self._buttonBox.accepted.connect(lambda : self.close())
        verticalLayout.addWidget(self._buttonBox)
    
    def startExport(self):
        self._label.setText("PDF导出中...")
        self._progressBar.setMaximum(0)
        self._progressBar.setValue(-1)
        self._buttonBox.setEnabled(False)
    
    def endExport(self):
        self._label.setText("PDF导出完成！")
        self._progressBar.setMaximum(100)
        self._progressBar.setValue(100)
        self._buttonBox.setEnabled(True)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    icon1 = QIcon(":/src/engineIcon/csdn.ico")
    icon2 = QIcon(":/src/engineIcon/cnblogs.ico")
    resultDict = {"csdn":{"engineName":"CSDN","icon":icon1,"results":[{"title":"测试标题1","desc":"测试说明1"},{"title":"测试标题2","desc":"测试说明2"}]}}
    resultDict["cnblogs"] = {"engineName":"博客园","icon":icon2,"results":[{"title":"测试标题3","desc":"测试说明3"},{"title":"测试标题4","desc":"测试说明4"}]}
    
    config = {"passageNum":30,"defaultExportPath":"C:\\Users\\ZhuTaoyuan\\Documents"}

    infoWindow = InfoWindow()
    infoWindow.showPreview("测试","www.baidu.com","""
    <!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>菜鸟教程(runoob.com)</title>
</head>
<body>

<h1>我的第一个标题</h1>
<p>我的第一个段落。</p>

</body>
</html>
    """,config)
    infoWindow.show()

    timer = QTimer()
    def timeOutHandle():
        infoWindow.showSearchPage(resultDict)
        timer.stop()
    timer.timeout.connect(timeOutHandle)
    timer.start(2000)
    app.exec_()
    print(config)
    sys.exit()