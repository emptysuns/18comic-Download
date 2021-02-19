from requests import *
from bs4 import BeautifulSoup
from PIL import Image ##调用image库对有反转的图片进行转换
from io import BytesIO
import os #创建文件夹，保存下载好的图片
import re
import threading #多线程支持库，对于这种io密集操作相对于多进程还是换成多线程比较好
import time
'''
基于BeautifulSoup解析库的py爬虫爬取18comic
'''
public_headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}

ERROR_PAGE_LIST = [] #声明一个全局变量，用来储存因诸如网络等不可抗元素导致的下载失败，从而进行重新下载！（这个变量只是存储单次下载的错误）
WARNING_PAGE_LIST = [] #存储有问题但不需要处理的图片。有些图片经过人工验证发现在服务器上就是0字节，记录到这里但不处理

def checkImgConvert(url): #判断图片是否做过反爬机制，比较狂野的使用id分析,没有对前端进行分析来判断
    pass

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



def get_url_list(url): #得到图片的下载链接
    response = get(url, headers=public_headers)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    if soup.find_all("a",class_="prevnext") != [] :  #网页存在下一页按钮
        # print("发现多个页面")
        max_web_page_num = 2  # 默认只有两页
        max_web_page_url = url + "?page=" + str(max_web_page_num)
        last_web_page_num = int(soup.find_all("ul",class_="pagination")[0](string=True)[-2])  #最后一个是下一页按钮，倒数第二个是当前跳转最大页面
        while last_web_page_num > max_web_page_num : #可跳转的最后页面大于记录的最大页数时，修正最大页数并检查
            max_web_page_num = last_web_page_num
            max_web_page_url = url + "?page=" + str(max_web_page_num)
            # print("正在读取",max_web_page_url)
            last_html = get(max_web_page_url, headers=public_headers).text
            soup_lastpage = BeautifulSoup(last_html, 'lxml')
            last_web_page_num = int(soup_lastpage.find_all("ul",class_="pagination")[0](string=True)[-2])  
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
    return comic_page_urls

def makeDir(url): # 根据传入的url创建以名称为根据的文件夹，返回文件夹路径
    response = get(url, headers=public_headers)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title.string
    dir_name = title.split('|')[0]
    path = r'download/' + dir_name
    path = re.sub('[:*?"<>|]', '' ,path) # 去除特殊字符
    # print(path)
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    return path

def download_image(url_path , timeout = 30):# 下载图片,定义一个方法方便开启多线程,返回下载该图片的相对路径
    url = url_path[0]
    path = url_path[1]
    convert_status = url_path[2]
    comic_name = url.split('/')[-1].split('?')[0]
    comic_local_position = path + '/' + comic_name
    global ERROR_PAGE_LIST #全局变量
    try:
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
            # raise Exception("0字节图片")  # 后来发现没必要处理0k图片
            WARNING_PAGE_LIST.append(url_path) #额外记录，后续不处理
        if convert_status:
            convertImg(comic_local_position) # 对“无耻”的以修改图片的反爬虫机制进行反制！
    except Exception:
        # print('Download Error')
        pass
    if url_path in ERROR_PAGE_LIST: # 如果下载成功就再下载列表删除它
        ERROR_PAGE_LIST.remove(url_path)

def checkPluralPage(url): #判断是不是有复数章节需要下载，有返回True，无返回False
    response = get(url)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    switch_btn_class = soup.find_all(name='a', attrs={'class': 'switch_btn'})
    if switch_btn_class:
        flag = True
    else:
        flag = False
    return flag

# 得到多章节comic所有的url返回一个列表
def getChapterList(url):
    response = get(url)
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

# 调用此方法来判断开启多线程程的个数
def downloadByThread(comic_num, url_path_list):
    thread_list = []  # 用于存放线程的列表
    print('正在开始多线程下载（线程数量:' + str(comic_num) + ')请稍后......')
    start_time = time.time()
    for num in range(comic_num):
        # 根据页数动态创建线程
        thread_one = threading.Thread(target=download_image, name='DownloadPageIs' + str(num), args=(url_path_list[num],))
        thread_list.append(thread_one)
    for thread in thread_list:
        thread.start()  # 开始线程
    for thread in thread_list:
        thread.join()  # 同步线程

def main(id):
    convert_status = False #设置处理反爬机制的问题,False为未对comic进行切割
    id = int(id)
    comic_num = 0 # 根据下载的页数决定线程数量
    if id >= 220971:# 静态检测检测!!!有必要再改成动态
        convert_status = True
    url = 'https://18comic.org/photo/' + str(id)
    re_download_count = 1 #由于网络等种种原因而重新下载次数
    print('解析成功,开始下载',url)
    path = makeDir(url)
    print('成功创建目录', path)
    url_list = get_url_list(url)
    url_path_list = [] # 里面加入path等传入下载方法的信息
    for url_in_list in url_list:
        url_path_list.append((url_in_list, path, convert_status))
    comic_num = len(url_path_list)
    start_time = time.time()  # 开始执行时间
    downloadByThread(comic_num, url_path_list)
    while ERROR_PAGE_LIST:
        ERROR_PAGE_LIST = list( set (ERROR_PAGE_LIST))  #对错误记录去重
        print('当前有' + str(len(ERROR_PAGE_LIST)) + '张comic image由于不可抗网络因素下载失败，正在第' + str(
            re_download_count) + '次重新下载...')
        re_download_count += 1
        comic_num = len(ERROR_PAGE_LIST)
        downloadByThread(comic_num, ERROR_PAGE_LIST)
    download_time = float(time.time() - start_time)
    print("所有comic image下载成功，共" + str(len(url_path_list)) + "张（含0字节图片", str(len(WARNING_PAGE_LIST)),"张）,下载用时:%.1fS。enjoy!\n\n" % download_time)

if __name__ == '__main__':
    print('18comic.vip Downloader by emptysuns.\n请不要用于任何非法用途，仅作学习交流\n版本:Version 2.2\n下载链接格式请参照：\nhttps://github.com/emptysuns/18comic-Download\thttps://blog.acglove.cloud/?p=35\n')
    download_count = 1
    while(1):
        url = input('第'+str(download_count)+'次下载,请输入您想要下载comic的下载链接:\n')
        flag = checkPluralPage(url)
        if flag: #有就进行解析，无就直接下载
            id = url.split('/')[4]
            check_all_download = input('Tips:检测到您输入的链接是包括多个章节的，请判断是否将所有章节都下载：\n输入数字1:下载全部章节\t输入数字0:只下载当前章节\n')
            if check_all_download == '1' or check_all_download == '0':
                if check_all_download == '1':
                    chapter_list = getChapterList(url)
                    # print(chapter_list) # 调试输出是否得到所有下载id
                    print('当前共有'+str(len(chapter_list))+'话需下载\n')
                    chapter_count = 1
                    for id in chapter_list:
                        print('正在下载第'+str(chapter_count)+'话，请稍后...')
                        main(id)
                        chapter_count += 1
                    print('共'+str(len(chapter_list))+'话下载完毕！\n')
                    download_count += 1
                else:
                    id = url.split('/')[4]
                    main(id)
                    download_count += 1
            else:
                print("请输入的合法字符")
                download_count += 1
                continue
        else:
            id = url.split('/')[4]
            main(id)
            download_count += 1
