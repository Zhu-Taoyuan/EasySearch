from Crawler import *
class CrawlerFactory(object):
    #支持的搜索引擎
    CSDN = "CSDN"
    CNBLOG = "CNBLOG"
    ELECFANS = "ELECFANS"
    ENGINES = {
        CSDN:{"searchEngineName":"CSDN","class":CSDNCrawler,"passagePerPage":25, "icon":":/src/engineIcon/csdn.ico"},
        CNBLOG:{"searchEngineName":"博客园","class":CNBLOGCrawler,"passagePerPage":10, "icon":":/src/engineIcon/cnblogs.ico"},
        ELECFANS:{"searchEngineName":"电子发烧友","class":ELECFANSCrawler,"passagePerPage":10, "icon":":/src/engineIcon/elecfans.ico"}
        }#爬虫的中文名，构造对象，每页爬取的文章数
    @classmethod
    def getCrawler(cls, searchEngineID):
        """根据输入构造相应爬虫

        Args:
            searchEngineID (str): 爬虫对应的ID

        Returns:
            AbstractCrawler: 构造的爬虫对象
        """
        return cls.ENGINES[searchEngineID]["class"]() #利用字典实现switch case语句
    @classmethod
    def getCrawlerList(cls):
        """返回支持的引擎

        Returns:
            list: 引擎id
        """
        return [cls.CSDN, cls.CNBLOG, cls.ELECFANS]

if __name__ == '__main__':
    crawler = CrawlerFactory.getCrawler(CrawlerFactory.ELECFANS)
    crawler.setParam("python",10)
    crawler.run()
    print(crawler.getTitleList())