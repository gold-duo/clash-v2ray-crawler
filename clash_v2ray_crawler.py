import logging
from pyquery import PyQuery as pq
from requests.packages import urllib3
import re

logging.basicConfig(level=logging.INFO,format="%(asctime)s:%(levelname)s - %(message)s")
sources=[{
        'name':'mibei77',
        'url':'https://www.mibei77.com/category/jiedian',
        #从列表页获取进入详情页url的selector
        'selector_entry':'#wrap > div > main > section > div.sec-panel-body > ul > li:nth-child(1) > div.item-img > a.item-img-inner',  
        #clash、v2ray连接共同所在父元素
        'selector_parent':'div.entry-main > div.entry-content',
        #clash url前的描述 selector
        'selector_clash_desc':'p:nth-child(15) > strong:contains(Clash)',
        #clash url selector（通常位于selector_clash_desc下一个）
        'selector_clash':'p:nth-child(16)',
        #v2ray url前的描述 selector
        'selector_v2ray_desc':'p:nth-child(13) > strong:contains(v2ray)',
        #v2ray url selector（通常位于selector_v2ray_desc下一个）
        'selector_v2ray':'p:nth-child(14)',
        #用来校验列表页第一项item的标题，并从标题中提取日期的正则表达式
        'reg_chk_title':r'.*?(\d{4})年(\d{2})月(\d{2})日免费.*?节点.+?v2ray.*',
    }
]

def req(url:str)->str:
    res=None
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"}
        res = urllib3.PoolManager(num_pools=1, headers=headers).request('GET', url, timeout=10)
        if not res or res.status!=200:
            logging.error("req %s status(%s)",url,res.status)
        return res.data.decode('utf-8')
    except Exception:
        logging.error("req error:%s",url,exc_info=True)
    finally:
        if res: res.close()

def checkTitleGetDate(title:str,reg:str)->str:
    """校验标题是否包含特定字符串,并返回日期""" 
    m=re.match(re.compile(reg),title)
    if not m : return None
    g=m.groups()
    if len(g)<=1: return g[0].strip()
    str=None
    for i in g:
        str = (str + '-' +i) if str else i
    return str

def parse_url(url:str,src:dict[str,str])->tuple[str, str]:
    """从详情页中的内容解析订阅url"""
    html=req(url)
    if not html: return None
    doc=pq(html)(src['selector_parent'])
    if not doc:
        logging.info("parse_url(%s):not entry(%s) found!", src['name'], src['selector_parent'])
        return (None, None)
    
    urls=[None,None]
    selector_desc=[src['selector_clash_desc'],src['selector_v2ray_desc']]
    selector_url=[src['selector_clash'],src['selector_v2ray']]
    for i in range(len(urls)):
        p=doc(selector_desc[i])
        if not p:
            logging.info("parse_url(%s):not desc(%s) found!", src['name'],selector_desc[i])
            continue
        p=doc(selector_url[i])
        if not p:
            logging.info("parse_url(%s):not url(%s) found!", src['name'],selector_url[i])
            continue
        urls[i]= p.text()

    return (urls[0],urls[1])

def parse_entry_url(src:dict[str,str]) -> tuple[str, str]:
    """从主页入口列表解析出跳转详情页的url"""
    html=req(src['url'])
    if not html: return (None, None)
    a=pq(html)(src['selector_entry'])
    if not a:
        logging.info("parse_entry_url(%s):not element(%s) found!", src['name'], src['selector_entry'])
        return (None, None)
    title = a.text()
    if not title: 
        title =a.attr('title')
    if not title:
        logging.info("parse_entry_url(%s):not title(%s) found!", src['name'], src['selector_entry'])
        return (None, None)
    date =checkTitleGetDate(title, src['reg_chk_title'])
    if not date:
        logging.info("parse_entry_url(%s):No date found in the title(%s -- %s).", src['name'], title, src['reg_chk_title'])
        return (None, None)
    return (date, a.attr('href'))

def main()->None:
    for src in sources:
        try:
            time,url=parse_entry_url(src)
            if url:
                clash,v2ray=parse_url(url,src)
                logging.info("\n【%s】:日期=%s,入口=%s\n\t%s\n\t%s\n",src['name'],time,url,clash,v2ray)
        except Exception:
            logging.error("main error:%s",src['name'],exc_info=True)   

if __name__=='__main__':main()