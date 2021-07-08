from abc import ABC,abstractmethod
import requests
from lxml import etree

class AbstractCrawler(ABC):
    """爬虫的抽象类，用于统一爬虫的接口
    """
    @abstractmethod
    def setParam(self, keyword, passageNum):
        """设置爬虫参数

        Args:
            keyword (str): 检索词
            passageNum (int): 查询的文章数
        """
        pass

    @abstractmethod
    def run(self):
        """爬虫启动程序
        """
        pass

    @abstractmethod
    def getPassage(self, index):
        """获取索引对应的文章的HTML代码

        Args:
            index (int): 文章索引
        """
        pass

    @abstractmethod
    def getTitleList(self):
        """获取检索到的文章标题列表
        """
        pass
    
    @abstractmethod
    def getDescTextList(self):
        """获取检索到的文章简述列表
        """
        pass

    @abstractmethod
    def getHrefList(self):
        """获取检索到的文章的超链接列表
        """
        pass

class CSDNCrawler(AbstractCrawler):
    """CSDN爬虫
    """
    def __init__(self):
        super().__init__()
        self._responseText = ""
        self._titleList = []
        self._descTextList = []
        self._hrefList = []
        self._passagePerPage = 25
    
    def setParam(self, keyword, passageNum):
        self._keyword = keyword
        self._passageNum = passageNum
        self._pageNum = passageNum//self._passagePerPage
        self._pageNum = self._pageNum+1 if passageNum % self._passagePerPage else self._pageNum
        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "accept": "application/json, text/plain, */*"
            }
    
    def run(self):
        for pageNum in range(self._pageNum):
            self._url = "https://so.csdn.net/api/v3/search?q="+self._keyword+"&t=all&p="+str(pageNum+1)+"&s=0&tm=0&lv=-1&ft=0&l=&u=&ct=-1&pnt=-1&ry=-1&ss=-1&dct=-1&vco=-1&cc=-1&sc=-1&akt=-1&art=-1&ca=-1&prs=&pre=&ecc=-1&ebc=-1&platform=pc"
            # self._url = self._url.encode("utf-8").decode("latin1")
            self.__getPage()
            self.__getInfo()
        self._titleList = self._titleList[:self._passageNum]
        self._descTextList = self._descTextList[:self._passageNum]
        self._hrefList = self._hrefList[:self._passageNum]

    def getPassage(self,index):
        htmlResponse = requests.get(self._hrefList[index], headers=self._headers).text
        htmlTree = etree.HTML(htmlResponse)
        postBody = htmlTree.xpath('//div[@id="article_content"]')[0]
        htmlTtml = etree.tostring(postBody, method='html', with_tail=False).decode('UTF-8')
        return htmlTtml
    
    def getTitleList(self):
        return self._titleList
    
    def getDescTextList(self):
        return self._descTextList
    
    def getHrefList(self):
        return self._hrefList

    def __getPage(self):
        self._responseText = requests.post(self._url, headers=self._headers).json()
    
    def __getInfo(self):
        items = dict(self._responseText)['result_vos']
        for item in items:
            # 获取 title
            title = str(item['title']).replace('<em>', '')
            title = title.replace('</em>', '')
            self._titleList.append(title)
            # 获取 desc
            desc = str(item['description']).replace('<em>', '')
            desc = desc.replace('</em>', '')
            self._descTextList.append(desc)
            # 获取 href
            href = str(item['url'])
            self._hrefList.append(href)

class CNBLOGCrawler(AbstractCrawler):
    """博客园爬虫
    """
    def __init__(self):
        super().__init__()
        self._responseText = ""
        self._titleList = []
        self._descTextList = []
        self._hrefList = []
        self._passagePerPage = 10

    def setParam(self, keyword, passageNum):
        self._keyword = keyword
        self._passageNum = passageNum
        self._pageNum = passageNum//self._passagePerPage
        self._pageNum = self._pageNum+1 if passageNum % self._passagePerPage else self._pageNum
        self._headers = {
                'user-agent': 'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.'
                              '36(KHTML,likeGecko)Chrome/90.0.4430.93 Safari/537.36',
                'cookie': '_ga=GA1.2.119028761.1619010923; is-side-open=open; theme=light; UM_distinctid=17910d3e5a2268-08537109682ccf-d7e163f-13c680-17910d3e5a3284; _gid=GA1.2.508121567.1619794817; __utmz=59123430.1619799574.1.1.utmcsr=cnblogs.com|utmccn=(referral)|utmcmd=referral|utmcct=/; ShitNoRobotCookie=CfDJ8L-rpLgFVEJMgssCVvNUAjvY50IQtGLoLSL77V7sLBNi9i-7q1haepEJ7RVzvnbDvqLh91A4KewjDSpqd6jdwV9a6CyONjkq8pUY2VzAYVcOX_YBkKx4oUHzuWQ1Gj6GFA; DetectCookieSupport=OK; __utmc=59123430; __utmt=1; __utma=59123430.119028761.1619010923.1619799573.1619876071.2; __utmb=59123430.3.10.1619876072'
        }

    def run(self):
        for pageNum in range(self._pageNum):
            self._url = 'https://zzk.cnblogs.com/s/blogpost?Keywords=' + self._keyword + '&pageindex=' + str(pageNum)
            self.__getPage()
            self.__getInfo()
        self._titleList = self._titleList[:self._passageNum]
        self._descTextList = self._descTextList[:self._passageNum]
        self._hrefList = self._hrefList[:self._passageNum]

    def getPassage(self, index):
        htmlResponse = requests.get(self._hrefList[index], headers=self._headers).text
        htmlTree = etree.HTML(htmlResponse)
        postBody = htmlTree.xpath('//div[@id="cnblogs_post_body"]')[0]

        htmlHtml = etree.tostring(postBody, method='html', with_tail=False).decode('UTF-8')

        return htmlHtml

    def getTitleList(self):
        return self._titleList
    
    def getDescTextList(self):
        return self._descTextList
    
    def getHrefList(self):
        return self._hrefList
    
    def __getPage(self):
        response = requests.get(self._url, headers=self._headers)
        self._responseText = response.text
        self._tree = etree.HTML(self._responseText)

    def __getInfo(self):
        items = self._tree.xpath(".//div[@class='forflow']/div[@class='searchItem']")
        for item in items:
            # 获取 title
            title = str(item.xpath("./h3//text()"))
            title = title.split(',')
            titleName = ''
            for i in range(1, len(title)-1):
                titleName += title[i]
                titleName = titleName.replace("'", "")
                titleName = titleName.replace(" ", "")
            self._titleList.append(titleName)
            # 获取 desc
            desc = str(item.xpath("./span[@class='searchCon']/text()"))

            desc = desc.replace(r"\n", "")
            desc = desc.replace(" ", '')
            self._descTextList.append(desc)
            # 获取 href
            href = str(item.xpath("./h3/a/@href")[0])
            href = href.replace("'", "")
            self._hrefList.append(href)

class ELECFANSCrawler(AbstractCrawler):
    """电子发烧友爬虫
    """
    def __init__(self):
        super().__init__()
        self._responseText = ""
        self._titleList = []
        self._descTextList = []
        self._hrefList = []
        self._passagePerPage = 10

    def setParam(self, keyword, passageNum):
        self._keyword = keyword
        self._passageNum = passageNum
        self._pageNum = passageNum//self._passagePerPage
        self._pageNum = self._pageNum+1 if passageNum % self._passagePerPage else self._pageNum
        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            }

    def run(self):
        for pageNum in range(self._pageNum):
            self._url = 'https://s.elecfans.com/s?type=0&keyword=' + self._keyword + '&page=' + str(pageNum)
            self.__getPage()
            self.__getInfo()
        self._titleList = self._titleList[:self._passageNum]
        self._descTextList = self._descTextList[:self._passageNum]
        self._hrefList = self._hrefList[:self._passageNum]

    def getPassage(self, index):
        htmlResponse = requests.get(self._hrefList[index], headers=self._headers).text
        htmlTree = etree.HTML(htmlResponse)
        try:
            postBody = htmlTree.xpath('//div[@class="simditor-body clearfix"]')[0]
            htmlHtml = etree.tostring(postBody, method='html', with_tail=False).decode('UTF-8')
        except:
            postBody = htmlTree.xpath('//div[@id ="mainContent"]')[0]
            htmlHtml = etree.tostring(postBody, method='html', with_tail=False).decode('UTF-8')
        return htmlHtml

    def getTitleList(self):
        return self._titleList
    
    def getDescTextList(self):
        return self._descTextList
    
    def getHrefList(self):
        return self._hrefList
    
    def __getPage(self):
        response = requests.get(self._url, headers=self._headers)
        self._responseText = response.text
        self._tree = etree.HTML(self._responseText)

    def __getInfo(self):
        items = self._tree.xpath('//div[@class="list"]/ul/li')
        for item in items:
            # 获取 title
            title = str(item.xpath("./h2/a//text()")).replace('[', '').replace(']', '').replace("'", '').replace(',', '').replace(' ', '')
            self._titleList.append(title)
            # 获取 desc
            desc = str(item.xpath('./div/p[1]//text()')).replace('[', '').replace(']', '').replace("'", '').replace(',', '').replace(' ', '')
            self._descTextList.append(desc)
            # 获取 href
            href = str(item.xpath("./h2/a/@href")[0])
            self._hrefList.append(href)

