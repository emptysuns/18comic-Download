from requests import *
from bs4 import BeautifulSoup
from PIL import Image ##调用image库对有反转的图片进行转换
from io import BytesIO
from tqdm import tqdm #进度条
import os #创建文件夹，保存下载好的图片
import re
# import threading #多线程支持库，对于这种io密集操作相对于多进程还是换成多线程比较好
from concurrent import futures #异步执行模块。【警告】需求python版本 3.2以上！
import time
'''
基于BeautifulSoup解析库的py爬虫爬取18comic
'''
public_headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}

ERROR_PAGE_LIST = [] #声明一个全局变量，用来储存因诸如网络等不可抗元素导致的下载失败，从而进行重新下载！（这个变量只是存储单次下载的错误）
WARNING_PAGE_LIST = [] #存储有问题但不需要处理的图片。有些图片经过人工验证发现在服务器上就是0字节，记录到这里但不处理
# semaphore = threading.Semaphore(30)  #下载同时执行的线程数。已用ThreadPoolExecutor取代semaphore控制并行线程数
## semaphore是用阻塞acquire()的方式限制同时执行的线程数。简单方便但无法显示进度。留着这个说不定以后同时下载多本的时候限流
MAX_WORKERS = 50 #通过concurrent模块的线程池中控制最大下载数的变量

def checkImgConvert(url): #判断图片是否做过反爬机制，比较狂野的使用id分析,没有对前端进行分析来判断
    pass

def getMirror(): #获取镜像列表，以防网址无法访问
        mirrors = []
        html = get("http://jmcomic.xyz/", headers=public_headers).text
        soup = BeautifulSoup(html, 'lxml')
        for i in soup.find_all("span",class_="has-luminous-vivid-orange-color"):
            try :
                home = get("http://" + i.text +"/templates/frontend/airav/css/toastr.min.css", headers=public_headers).text
                if len(home) >1: 
                    mirrors.append(i.text)
            except Exception:
                pass
        # mirrors 的默认排序就是发布页的排序。即JM主站、JM海外分流1、JM中国、JM中国分流1、JM中国分流2
        # 没必要引入ping，否则会引入很多网络相关的模块，增加打包大小。这里直接粗暴下载首页面，失败踢掉。默认使用第一个能用的，即mirror[0]
        # 该方法未使用，当今镜像为采纳输入下载地址时的url ！！！
        # 考虑后续可能加入自动抓取更新，需要尽量直连，因此加入这个功能（不需要直连时，经梯子主站能访问则默认从主站下载）
        return mirrors

def mkIndex( path , imgs, preLinks, nextLinks):
    #imgs可以是数字（图片总数），也可以是列表（图片名，包含扩展名）
    # title文本，preLinks和nextLinks是上下集链接中的文件夹名(列表）
    body = "<!DOCTYPE html> <html lang='en'> <head> <title>" +path.split("/")[1] + \
                 '''</title><style type="text/css">
.button {
    position: relative;
    overflow: visible;
    display: inline-block;
    padding: 0.5em 1em;
    border: 1px solid #3072b3;
    border-bottom-color: #2a65a0;
    color: #fff;
    margin: 0;
    text-decoration: none;
    text-shadow: -1px -1px 0 rgba(0,0,0,0.3);
    text-align: center;
    font:15px/normal sans-serif;
    white-space: nowrap;
    cursor: pointer;
    outline: none;
    background-color: #dc5f59;
    background-image: -webkit-gradient(linear, 0 0, 0 100%, from(#599bdc), to(#3072b3));
    background-image: -moz-linear-gradient(#599bdc, #3072b3);
    background-image: -ms-linear-gradient(#599bdc, #3072b3);
    background-image: -o-linear-gradient(#599bdc, #3072b3);
    background-image: linear-gradient(#599bdc, #3072b3);
    -moz-background-clip: padding; /* for Firefox 3.6 */
    background-clip: padding-box;
    border-radius: 0.2em;
    /* IE hacks */
    zoom: 1;
    *display: inline;
}
.button:active,
.button.active {
    border-color: #2a65a0;
    border-bottom-color: #3884cd;
    background-color: #3072b3;
    background-image: -webkit-gradient(linear, 0 0, 0 100%, from(#3072b3), to(#599bdc));
    background-image: -moz-linear-gradient(#3072b3, #599bdc);
    background-image: -ms-linear-gradient(#3072b3, #599bdc);
    background-image: -o-linear-gradient(#3072b3, #599bdc);
    background-image: linear-gradient(#3072b3, #599bdc);
}
/* overrides extra padding on button elements in Firefox */
.button::-moz-focus-inner {
    padding: 0;
    border: 0;
}
</style></head>\n<body style='text-align: center;'> <div>'''   #html正文部分
    if isinstance( imgs, int ) : #是数字
        for i in range(1, imgs + 1):  #图片文件的编号
            body += "<img src=%05d.jpg> "%i  #5位数字用0补齐
    else:
        for i in imgs:  #图片文件的列表
            body = body + "<img src=" + i + "> "
    #添加之前章节的目录
    if preLinks == [] :  #当前是第一话，没有前文章节
        body += "</div>\n"    #只添加图片容器的结尾标签
    else :
        body = body + "</div>\n <div style='position: fixed ; left: 5px; top: 100px; background:#F0F0F0'><a href='..\\"    \
                              + preLinks[-1] + "\\index.html' class='button'>←上一话</a></br>"   #添加“上一话”的链接
        for j in range( len(preLinks) ):  #前文页面的目录序号
            if (len(preLinks) - j) < 5 :  #前5话有连续的目录
                body = body + "<a href='..\\" + preLinks[j] + "\\index.html'>第" + str(j+1) + "话</a></br>"
            elif (len(preLinks) - j)%5 == 0 and (len(preLinks) - j) <30 :  #前5-30话的每5话添加到目录
                body = body + "<a href='..\\" + preLinks[j] + "\\index.html'>第" + str(j+1) + "话&lt;</a></br>"
            elif  j == 0 :  #  当preLinks >30 太多的时候，前30以外的直接只留第一话(j=0)到目录
                body = body + "<a href='..\\" + preLinks[j] + "\\index.html'>第1话&lt;&lt;</a></br>"
    #添加后文章节的目录
    if nextLinks == [] :  #当前是最新一话，没有后文章节
        body += "</div>\n"    #只添加前文目录容器的结尾标签
    else :
        body = body + "</div>\n <div style='position: fixed ; right: 5px; top: 100px; background:#F0F0F0'><a href='..\\"     \
                              + nextLinks[0] + "\\index.html' class='button'>下一话→</a></br>"   #添加“下一话”的链接
        for k in range( len(nextLinks) ):  #后文页面的目录序号
            if k <5  :  #仅仅接下来5话有连续的目录
                body = body + "<a href='..\\" + nextLinks[k] + "\\index.html'>第" + str(k+len(preLinks) + 2) + "话</a></br>"
            elif  k%5 == 0 and k < 30  :  #5话之后的每5话添加到目录
                body = body + "<a href='..\\" + nextLinks[k] + "\\index.html'>&gt;第" + str(k+len(preLinks) + 2) + "话</a></br>"
            elif  k == len(nextLinks) - 1 :   # k>=30 太多的时候，直接只留最后一话到目录
                body = body + "<a href='..\\" + nextLinks[k] + "\\index.html'>&gt;&gt;第" + str(k+len(preLinks) + 2) + "话</a></br>"
    #收尾标签
    body += "\n</div></body></html>"  #前文目录、body、html的结束标签
    #写入文件
    fileName = path + '/index.html'  
    with open( fileName , "w",encoding='utf-8' ) as file :     #覆盖已存在的文件以更新目录
        file.write ( body )  #尝试写入文件
    
    

def convertImg(img_url):
        img = Image.open(img_url)
        img_size = img.size
        img_crop_size = int(img_size[1] / 10)
        img_crop_size_last = (img_size[1] / 10) - img_crop_size  # 解决图片height不能被10整除导致拼接后下方黑条
        img_crop_size_last = round(img_crop_size_last, 1)
        if img_crop_size_last > 0:  # 只有无法整除时才将新建图片进行画布纵向减小
            img_crop_size_last_sum = int(img_crop_size_last * 10)
        else:
            img_crop_size_last_sum = 0
        img_width = int(img_size[0])
        img_block_list = [] #定义一个列表用来存切割后图片
        for img_count in range(10):
            img_crop_box = (0, img_crop_size*img_count, img_width, img_crop_size*(img_count+1))
            img_crop_area = img.crop(img_crop_box)
            img_block_list.append(img_crop_area)
        img_new = Image.new('RGB', (img_size[0], img_size[1]-img_crop_size_last_sum))
        count = 0
        for img_block in reversed(img_block_list):
            img_new.paste(img_block, (0, count*img_crop_size))
            count += 1
        # img_new.show() # 调试显示转化后的图片
        img_new.save(img_url)

def get_url_list2(url): #原get_url_list方法采用编号推算，对编号断层没有办法处理，这是新的试验办法
    '''新方法的原理为，<script>中有一个段存储了各种变量。（不论第几页都有）格式如下：
    var scramble_id = 220980;    #都是这个数，不知道干什么用
    var series_id = 0;  
    var aid = 147643;                  #这是 photo的 id
    var sort = 2;                          #集数
    var speed = '';
    var nb_path = 'e1a88-69_a1';
    var readmode = "read-by-full";
    var page_initial = '03001';   #当前页面从多少页开始显示的
    var page_arr = ["00001.jpg","00002.jpg","00003.jpg","00004.jpg","00005.jpg",……   #所有photo的编号，貌似有显示上限
    '''
    i = 5   #重试次数   #前面的mkDir之前部分和get_url_list一致
    while i>0:
        try:
            response = get(url, headers=public_headers, timeout = (5, 10))   #连接超时5s，读取超时10s
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            i = 0  #能正确获取网页，则排除网络问题，其他问题（比如新建目录权限不够）不需要重试（也不需要捕捉错误）
        except exceptions.RequestException as e:
            print( e , "正在重新访问网址" )
            i -= 1  #剩余重试计数器
    #创建目录：原mkDir()的功能
    title = soup.title.string
    dir_name = title.split('|')[0]
    dir_name = re.sub('/', '' ,dir_name) # 去除反斜杠，以免产生不必要的子文件夹
    path = r'download/' + dir_name
    path = re.sub('[:*?"<>|]', '' ,path) # 去除特殊字符
    # print(path)
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    print('成功创建目录', path)
    #mkDir()结束，后续path作为元组的一部分在return输出
    #查找下载链接
    rawText = str(soup.find_all('div',id="wrapper")[0].find_all('script')[2]).split("\n")    #soup搜索到的scripts不知道怎么导出文本代码
    # rawText[2].split("=")[1][1:-1]   # var series_id = xxxxxx 是记录的简介目录的id，格式如下: /album/xxxxxx/
    # rawText[3].split("=")[1][1:-1]   # var aid = xxxxxx 是记录的该图集的id，格式如下: /photo/xxxxxx/
    rawList = rawText[9].split("[")[1][:-2].split(",")  #处理后的图片编号，但包含引号
    comic_page_urls = []     # 设置一个列表用来存储所有的最终url
    anyJpgNum = 1
    anyJpg = soup.find(id='album_photo_%05d.jpg'%anyJpgNum)  #随便找一个页面，从album_photo_00001.jpg开始
    while anyJpg is None :    #  恰好00001缺失，导致无法获取图片地址cdn形式的前缀
        anyJpgNum += 1  # 找下一个图片
        anyJpg = soup.find(id='album_photo_%05d.jpg'%anyJpgNum)
    comic_page_url_head = '/'.join(anyJpg['data-original'].split('/')[:-1])  #图片网址前缀
    comic_page_id_tail = anyJpg['data-original'].split('?')[-1]                   #图片网址后缀
    for page in rawList :
        comic_page_urls.append( comic_page_url_head + "/" +page[1:-1] + "?" + comic_page_id_tail )  #前缀加上去引号的图片名
    return (comic_page_urls, path)

def get_url_list(url): #得到图片的下载链接
    i = 5   #重试次数
    while i>0:
        try:
            response = get(url, headers=public_headers, timeout = (5, 10))   #连接超时5s，读取超时10s
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            i = 0  #能正确获取网页，则排除网络问题，其他问题（比如新建目录权限不够）不需要重试（也不需要捕捉错误）
        except exceptions.RequestException as e:
            print( e , "正在重新访问网址" )
            i -= 1  #剩余重试计数器
    #创建目录：原mkDir()的功能
    title = soup.title.string
    dir_name = title.split('|')[0]
    dir_name = re.sub('/', '' ,dir_name) # 去除反斜杠，以免产生不必要的子文件夹
    path = r'download/' + dir_name
    path = re.sub('[:*?"<>|]', '' ,path) # 去除特殊字符
    # print(path)
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    print('成功创建目录', path)
    #mkDir()结束，后续path作为元组的一部分在return输出
    #查找下载链接
    if soup.find_all("a",class_="prevnext") != [] :  #网页存在下一页按钮
        # print("发现多个页面")
        max_web_page_num = 1  # 因为有多页，所以最少2页，取初始值为1以便第一个while循环正常执行
        max_web_page_url = url + "?page=" + str(max_web_page_num)
        last_web_page_num = int(soup.find_all("ul",class_="pagination")[0](string=True)[-2])#最后一个是下一页按钮，倒数第二个是当前跳转最大页面
        while last_web_page_num > max_web_page_num : #可跳转的最后页面大于记录的最大页数时，修正最大页数并检查
            max_web_page_num = last_web_page_num
            max_web_page_url = url + "?page=" + str(max_web_page_num)
            # print("正在读取",max_web_page_url)
            last_html = get(max_web_page_url, headers=public_headers).text
            soup_lastpage = BeautifulSoup(last_html, 'lxml')
            last_web_page_num = int(soup_lastpage.find_all("ul",class_="pagination")[0](string=True)[-2])  
    else: #无翻页的情况
        soup_lastpage = soup
        max_web_page_num = 1
    options_list = soup_lastpage.find_all('select')[2].find_all('option') # 用来取出存放页数select中的option标签数量来计算页数
    pages = len(options_list) + (max_web_page_num - 1 ) * 500 # 设置一个变量表征页数
    print("页数位于", str(max_web_page_num), "网页文件内，共计 ", pages , "页")
    comic_page_urls = []     # 设置一个列表用来存储所有的最终url
    comic_page1_id = soup.find(id='album_photo_00001.jpg')['data-original']    # 存放每一页page图片 ## 取出第一页的页数根据页数的命名规则来自己计算出后面的页数的url，减少用库进行查的时间
    comic_page_url_head_temp = '/'.join(comic_page1_id.split('/')[:-1])     # 取出页数url判断之前的服务器路径
    comic_page_id_tail_temp = comic_page1_id.split('/')[-1].split('.')[-1]     # 用split取出判断页数的后半段url地址例如jpg?v=1602070382暂存
    for page in range(1, pages + 1):     # 对url地址后面的判断页数的url进行根据页数递增的规则进行拼接
        if page < 10:
            comic_page_url = comic_page_url_head_temp + '/0000' + str(page) + '.' + comic_page_id_tail_temp
        elif page >= 10 and page < 100:
            comic_page_url = comic_page_url_head_temp + '/000' + str(page) + '.' + comic_page_id_tail_temp
        elif page >= 100 and page < 1000:
            comic_page_url = comic_page_url_head_temp + '/00' + str(page) + '.' + comic_page_id_tail_temp
        elif page >= 1000 and page < 10000:
            comic_page_url = comic_page_url_head_temp + '/0' + str(page) + '.' + comic_page_id_tail_temp
        elif page >= 10000:
            comic_page_url = comic_page_url_head_temp + '/' + str(page) + '.' + comic_page_id_tail_temp
        #print(comic_page_url + '\n')         # 测试每个url是否正正常输出
        comic_page_urls.append(comic_page_url)         # 将每一个url加入到存储的列表中
    # print(comic_page_urls)     # 测试存储url的列表是否正常输出
    return (comic_page_urls, path)

def makeDir(url): # 根据传入的url创建以名称为根据的文件夹，返回文件夹路径
    #该方法已整合入get_url_list，但尚未删除
    i = 5   #重试次数
    while i>0:
        try:
            response = get(url, headers=public_headers, timeout = (5, 10))   #连接超时5s，读取超时10s
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            title = soup.title.string
            dir_name = title.split('|')[0]
            dir_name = re.sub('/', '' ,dir_name) # 去除反斜杠，以免产生不必要的子文件夹
            path = r'download/' + dir_name
            path = re.sub('[:*?"<>|]', '' ,path) # 去除特殊字符
            # print(path)
            folder = os.path.exists(path)
            if not folder:
                os.makedirs(path)
            return path
        except exceptions.RequestException as e:
            print( e , "正在重新访问网址" )
            i -= 1  #剩余重试计数器
        except Exception: 
            print( "无法建立文件夹，请检查权限" )
            i = 0  #重试计数器清零


def download_image(url_path , timeout = (5, 20)):# 下载图片,定义一个方法方便开启多线程,返回下载该图片的相对路径
    #semaphore.acquire()  #执行中的线程计数器+1。已被ThreadPoolExecutor取代
    url = url_path[0]
    path = url_path[1]
    convert_status = url_path[2]
    comic_name = url.split('/')[-1].split('?')[0]
    comic_local_position = path + '/' + comic_name
    global ERROR_PAGE_LIST #全局变量
    global WARNING_PAGE_LIST 
    try:
        if not url_path in ERROR_PAGE_LIST:  
            ERROR_PAGE_LIST.append(url_path) # 先把网页加入错误列表，以防网络错误、I/O错误引发中断造成遗漏
        #注意：如果上一次没有解决的错误网页，会再次重复记录。所以重试下载时需要去重。
        comic_page = get(url, headers=public_headers, timeout = timeout) #可从传入timeout参数防止网络问题阻塞
        # if comic_page.status_code != 200:
            # print('!= 200')
        image_bytes = BytesIO(comic_page.content)
        if image_bytes.__sizeof__() >= 1: #防止下载的图片为0kb，玄学？！
            image_source = Image.open(image_bytes)
            image_source.save(comic_local_position)
        else:
            # print('content is lost')
            # raise Exception("0字节图片")  # 后来发现没必要处理0k图片。是服务器的问题，重试也没用，过几天服务器就好了
            WARNING_PAGE_LIST.append(url_path) #额外记录，后续不处理
        if convert_status:
            convertImg(comic_local_position) # 对“无耻”的以修改图片的反爬虫机制进行反制！
        if url_path in ERROR_PAGE_LIST: # 如果下载成功就再下载列表删除它
            ERROR_PAGE_LIST.remove(url_path)
            # semaphore.release()  #执行中的线程计数器-1。已被ThreadPoolExecutor取代
            # print ("【下载完成】 ", url_path[0])
            return url_path #下载完成后返回url地址，完成的地址记录在进程池中，用于标记下载进度，或可取代ERROR_PAGE_LIST的记录动作
    except Exception:
        # print('Download Error, File', url_path)
        # semaphore.release()  #执行中的线程计数器-1。已被ThreadPoolExecutor取代
        pass


def checkPluralPage(url): #判断是不是有复数章节需要下载，有返回True，无返回False
    i = 5   #重试次数
    while i>0:
        try:
            response = get(url, timeout = (5, 10))   #连接超时5s，读取超时10s
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            switch_btn_class = soup.find_all(name='a', attrs={'class': 'switch_btn'})
            if switch_btn_class:
                flag = True
            else:
                flag = False
            return flag
        except exceptions.RequestException as e:
            print( e, "正在重新访问网址"  )
            i -= 1  #剩余重试计数器



# 得到多章节comic所有的url返回一个列表
def getChapterList(url):
    i = 5   #重试次数
    while i>0:
        try:
            response = get(url, timeout = (5, 10))   #连接超时5s，读取超时10s
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            btn_toolbar_class = soup.find_all(name='ul', attrs={'class': 'btn-toolbar'})
            pattern = re.compile('<a href="/photo/(.*?)">.*?</a>', re.S)
            chapter_find = []
            for a in btn_toolbar_class[0].contents:
                id = re.findall(pattern, str(a))
                if id:
                    chapter_find.append(id)
            last_chapter = []
            for chapter in chapter_find:  # findall查找的出的是返回列表，"暂时"这么让它返回列表，便于后续操作
                last_chapter.append(chapter[0])
            return last_chapter
        except exceptions.RequestException as e:
            print( e , "正在重新访问网址" )
            i -= 1  #剩余重试计数器

# 调用此方法来判断开启多线程程的个数
def downloadByThread(comic_num, url_path_list):
    workers = min(MAX_WORKERS, comic_num) #确定线程池数量，避免超出页数
    print(' ===> 正在开始多线程下载（线程数量:' + str(workers) + ')请稍后......')
    with futures.ThreadPoolExecutor(workers) as executor: #启动线程池
        results = list(tqdm(executor.map(download_image, url_path_list), total = comic_num, ncols=75, leave=True)) #加入线程池并记录结果
        #上面tqdm记录进度条的参数是：executor中成果的结果数、最大结果数、指定列宽(防止cmd中超过)、防止多行(cmd的锅))
    # return results #返回已下载的地址
    
    """ #原处理方法无法正确显示进度条，会在一瞬间跑满然后继续等待
    thread_list = []  # 用于存放线程的列表
    for num in range(comic_num):
        # 根据页数动态创建线程
        thread_one = threading.Thread(target=download_image, name='DownloadPageIs' + str(num), args=(url_path_list[num],))
        thread_list.append(thread_one)
    for thread in thread_list:
        thread.start()  # 开始线程
    for thread in thread_list:
        thread.join()  # 同步线程
     """

def main(mirror, id):
    convert_status = False #设置处理反爬机制的问题,False为未对comic进行切割
    id = int(id)
    comic_num = 0 # 根据下载的页数决定线程数量
    if id >= 220971:# 静态检测检测!!!有必要再改成动态
        convert_status = True
    url = 'https://' + mirror +'/photo/' + str(id)
    re_download_count = 1 #由于网络等种种原因而重新下载次数
    print('解析成功,开始下载',url)
    #path = makeDir(url)
    (url_list,path) = get_url_list2(url)   #改用新方法获取图片地址
    url_path_list = [] # 里面加入path等，用于把多个变量传入download_image方法的信息
    for url_in_list in url_list:
        url_path_list.append((url_in_list, path, convert_status))
    comic_num = len(url_path_list)
    start_time = time.time()  # 开始执行时间
    downloadByThread(comic_num, url_path_list)  #多线程下载
    while ERROR_PAGE_LIST:
        print('当前有' + str(len(ERROR_PAGE_LIST)) + '张comic image由于不可抗网络因素下载失败，')
        for i in ERROR_PAGE_LIST:    #显示失败的图片编号用于debug
            print(i[0].split('/')[-1].split('?')[0], " ", end = "")
        print('\n正在第' + str(re_download_count) + '次重新下载...')
        re_download_count += 1
        comic_num = len(ERROR_PAGE_LIST)
        downloadByThread(comic_num, ERROR_PAGE_LIST)
        if re_download_count > 10 :  #连续10次出错，可能是页码编号断层，尝试处理
            print ("连续10次出错，可能存在页码编号断层。当前剩余" , len(ERROR_PAGE_LIST) ,  "个图片，尝试处理中…")
            #处理方式没有写，计划直接下载 "总编号+1.jpg"，然后反复尝试。但是现在用了新方法获取url_path_list
    download_time = float(time.time() - start_time)
    print("所有comic image下载成功，共" + str(len(url_path_list)) + "张（含0字节图片"+ str(len(WARNING_PAGE_LIST))+"张）,下载用时:%.1fS。enjoy!\n\n" % download_time)
    return (path, len(url_path_list) ) #把地址传出去，用于生成index.html的上下页链接。传递变量避免重复读取网页


if __name__ == '__main__':
    print('18comic.vip Downloader by emptysuns.\n请不要用于任何非法用途，仅作学习交流\n版本:Version 2.2\n下载链接格式请参照：\nhttps://github.com/emptysuns/18comic-Download\thttps://blog.acglove.cloud/?p=35\n')
    download_count = 1
    while(1):
        url = input('第'+str(download_count)+'次下载,请输入您想要下载comic的下载链接:\n')
        id = url.split('/')[4]
        mirror = url.split('/')[2]
        flag = checkPluralPage(url)
        if flag: #有就进行解析，无就直接下载
            check_all_download = input('Tips:检测到您输入的链接是包括多个章节的，请判断是否将所有章节都下载：\n输入数字1:下载全部章节\t输入数字0:只下载当前章节\n')
            if check_all_download == '1' or check_all_download == '0':
                if check_all_download == '1':
                    chapter_list = getChapterList(url)
                    # print(chapter_list) # 调试输出是否得到所有下载id
                    print('当前共有'+str(len(chapter_list))+'话需下载\n')
                    chapter_count = 1
                    path_list = []  #存储已经下载章节的存储位置和图片数
                    for id in chapter_list:
                        print('正在下载第'+str(chapter_count)+ '话/共'+ str(len(chapter_list))+ '话，请稍后...')
                        (path,comic_num) = main(mirror, id) #记录该章节的保存位置。
                        path_list.append((path,comic_num))  #保存到列表便于下载完成后生成目录
                        chapter_count += 1
                    print('共'+str(len(chapter_list))+'话下载完毕！')
                    download_count += 1
                    # print('正在生成index.html文件，以便于\n')
                    #print(path_list)  #测试是否正确记录了图片数
                    for i in range(len(path_list)) :  #i是当前章节的序号，便于查找上一章和下一章
                        (path , comic_num) = path_list[i]
                        preLinks = []  #章节的之前目录清零
                        nextLinks = []  #章节的后续目录清零
                        for j in range( i ): #生成之前章节的目录(从起始章到 i 的前一章)
                            preLinks.append( path_list[j][0].split("/")[1] )
                        for k in range( i+1, len(path_list) ): #生成之后章节的目录（从 i+1 章到最后一章）
                            nextLinks.append( path_list[k][0].split("/")[1] )
                        mkIndex( path , comic_num , preLinks, nextLinks) #path包含“/download”前缀，preLinks和nextLinks只有目录
                    print("生成了", len(path_list) , "个html文件，便于浏览\n" )
                else:
                    (path,comic_num) = main(mirror, id)
                    download_count += 1
            else:
                print("请输入的合法字符")
                download_count += 1
                continue
        else:
            (path,comic_num) = main(mirror, id)
            #单个合集的形式，就不生成index.html了。一般需要网页的韩漫都是连载的、分很多集
            download_count += 1
