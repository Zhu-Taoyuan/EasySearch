import sys,json
sys.path.append("./src")
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QAction, QMenu, qApp
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, QThreadPool, QRunnable, Qt, QTimer, pyqtSignal
from src.SearchBar import SearchBar, Engine
from src.InfoWindow import InfoWindow
from src.CrawlerFactory import CrawlerFactory
from src.SetDialog import SetDialog
from system_hotkey import SystemHotkey
import src.icons
from pathlib import Path

class EasySearch(object):
    def __init__(self, configuration):
        self._config = configuration
        self._searchBar = SearchBar()
        self._searchBar.show()
        self._timer = QTimer() #用于解决托盘和失去焦点相互影响
        self._timer.timeout.connect(self._hideHandle)
        if self._config["loseFocusHidden"]: #是否启用失去焦点自动隐藏
            self._searchBar.activationChange.connect(lambda: self._timer.start(200))
        for engineID in CrawlerFactory.getCrawlerList(): #添加搜索引擎选项
            engine = Engine(QIcon(CrawlerFactory.ENGINES[engineID]["icon"]),engineID,CrawlerFactory.ENGINES[engineID]["searchEngineName"])
            self._searchBar.addSearchEngine(engine)
        self._searchBar.comfirmSearch.connect(self._showSearchResults) #关键词确定后开启爬虫
        self._tray = Tray(self._searchBar)#创建托盘图标
        self._tray.setNeed.connect(self._setNeedHandle)
        self._hotkey = HotKeyThread(self._config["hotkey"], self._searchBar)

    def _showSearchResults(self,param):
        """创建爬虫

        Args:
            param (tuple): (搜索引擎,搜索文本)
        """
        self._infoWindow = InfoWindow() #必须设置成对象字段
        self._infoWindow.show()
        self._crawlers = {}
        searchEngineID,text = param 
        if searchEngineID == "":
            for engineID in CrawlerFactory.getCrawlerList():
                crawler = CrawlerFactory.getCrawler(engineID)
                crawler.setParam(text,self._config["passageNum"])
                self._crawlers[engineID] = crawler
        else:
            crawler = CrawlerFactory.getCrawler(searchEngineID)
            crawler.setParam(text,self._config["passageNum"])
            self._crawlers[searchEngineID] = crawler
        
        self._crawlerManage = CrawlerManage(list(self._crawlers.values()))
        self._crawlerManage.start()
        self._crawlerManage.finished.connect(self._crawlerFinshedHandle)

    def _crawlerFinshedHandle(self):
        """爬虫完成后的槽函数
        """
        self._resultDict = {}
        for id in self._crawlers:
            results = []
            icon = QIcon(CrawlerFactory.ENGINES[id]["icon"])
            engineName = CrawlerFactory.ENGINES[id]["searchEngineName"]
            titleList = self._crawlers[id].getTitleList()
            descTextList = self._crawlers[id].getDescTextList()
            for index in range(self._config["passageNum"]):
                results.append({"title":titleList[index],"desc":descTextList[index]})
            self._resultDict[id] = {"engineName":engineName,"icon":icon,"results":results}
        self._infoWindow.showSearchPage(self._resultDict)
        self._infoWindow.previewNeed.connect(self._previewNeedHandle)
    
    def _previewNeedHandle(self, param):
        """需要预览的槽函数

        Args:
            param (预览所需要的参数): (搜索引擎,预览的索引)
        """
        engineID, index = param
        href = self._crawlers[engineID].getHrefList()[index]
        title = self._crawlers[engineID].getTitleList()[index]
        htmlCode = self._crawlers[engineID].getPassage(index)        
        self._infoWindow.showPreview(title,href, htmlCode, self._config)

    def _hideHandle(self):
        """对窗口进行隐藏
        """
        self._timer.stop()
        if not self._searchBar.isActiveWindow():
            self._searchBar.hide()
    
    def _updateHandle(self):
        """热键更新的槽函数
        """
        self._hotkey.updateKeys(self._config["hotkey"])#更新热键
        #更新失去焦点
        try:
            self._searchBar.activationChange.disconnect()
            if self._config["loseFocusHidden"]: #是否启用失去焦点自动隐藏
                self._searchBar.activationChange.connect(lambda: self._timer.start(200))
        except TypeError:
            if self._config["loseFocusHidden"]: #是否启用失去焦点自动隐藏
                self._searchBar.activationChange.connect(lambda: self._timer.start(200))
    
    def _setNeedHandle(self):
        """设置菜单被点击时的槽函数
        """
        self._setDialog = SetDialog(self._config)
        self._setDialog.updateNeed.connect(self._updateHandle)
        self._setDialog.show()

class CrawlerTask(QRunnable):
    """线程池中需要完成的任务
    """
    def __init__(self, crawlerObject):
        super().__init__()
        self._crawlerObject = crawlerObject

    def run(self):
        self._crawlerObject.run()

class CrawlerManage(QThread):
    """管理爬虫线程池的类
    """
    def __init__(self, crawlers):
        super().__init__()
        self._crawlers = crawlers
    
    def run(self):
        pool = QThreadPool()
        pool.setMaxThreadCount(10)
        for crawler in self._crawlers:
            crawlerTask = CrawlerTask(crawler)
            pool.start(crawlerTask)
        pool.waitForDone()

class Tray(QSystemTrayIcon):
    """托盘类
    """
    setNeed = pyqtSignal()
    def __init__(self, widget):
        self._widget = widget
        super().__init__()
        self.setIcon(QIcon(":/src/engineIcon/searchAll.ico"))
        self.activated.connect(self._trayActiveHandle)#单击托盘显示
        self._menu = QMenu()
        showHiddenAction = QAction("显示/隐藏", self._menu, triggered = self._showHidden)
        quitAction = QAction("退出", self._menu, triggered=self._quitHandle)
        setAction = QAction("设置", self._menu, triggered=self.setNeed.emit)
        self._menu.addAction(showHiddenAction)
        self._menu.addAction(setAction)
        self._menu.addSeparator()
        self._menu.addAction(quitAction)
        self.setContextMenu(self._menu)
        self.show()

    def _showHidden(self):
        """窗口隐藏/显示函数
        """
        if self._widget.isVisible():
            self._widget.hide()
        else:
            self._widget.show()
            self._widget.activateWindow()

    def _quitHandle(self):
        """托盘退出槽函数
        """
        self.deleteLater()
        qApp.quit()
    
    def _trayActiveHandle(self, reason):
        """托盘被激活的槽函数

        Args:
            reason : 被激活的原因
        """
        if reason == QSystemTrayIcon.Trigger :
            self._showHidden()

class HotKeyThread(SystemHotkey, QThread):
    """用于监控全局热键
    """
    keyCatch = pyqtSignal()
    def __init__(self, keys, widget):
        SystemHotkey.__init__(self)
        QThread.__init__(self)
        self._keys = keys
        self._widget = widget
        self.register(keys,callback=lambda x:self.start())
        self.keyCatch.connect(self._keyCatchHandle)

    def updateKeys(self, keys):
        """更新热键

        Args:
            keys (tuple): 需要更新的热键
        """
        self.unregister(self._keys)
        self.register(keys,callback=lambda x: self.start())
        self._keys = keys

    def run(self):
        """热键回调函数
        """
        self.keyCatch.emit()#防止直接修改造成线程卡死

    def _keyCatchHandle(self):
        """热键被捕获的槽函数
        """
        if self._widget.isVisible():
            self._widget.hide()
        else:
            self._widget.show()
            self._widget.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    path = Path.cwd().joinpath("src","settings.json")
    try:
        with open(str(path),"r") as fp:
            configuration = json.load(fp)
    except Exception:#恢复默认配置
        configuration = {}
        configuration["passageNum"] = 10 
        configuration["defaultExportPath"] = str(Path.home().joinpath("Documents"))
        configuration["loseFocusHidden"] = True
        configuration["hotkey"] = ("control","alt","s")
    easySearch = EasySearch(configuration)
    app.exec_()
    with open(str(path),"w") as fp:
        json.dump(configuration,fp)
    sys.exit()