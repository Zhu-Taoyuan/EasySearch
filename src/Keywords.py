import requests as rq
import re
import json
def getKeywordsList(keyword):
    """根据输入的关键词进行关键词提示

    Args:
        keyword (str): 用户输入的关键词

    Returns:
        list: 百度提示的关键词列表
    """
    url = "http://suggestion.baidu.com/su?wd={0}&cb=window.baidu.sug".format(keyword)
    response = rq.get(url)
    responseText = response.content.decode("gbk")
    keywordsJson = re.findall(r'\[.*\]',responseText)[0]
    keywordsList = json.loads(keywordsJson)
    return keywordsList

if __name__ == '__main__':
    print(getKeywordsList("python"))