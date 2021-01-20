from requests import *
from bs4 import BeautifulSoup
from multiprocessing import Pool
from PIL import Image ##调用image库对有反转的图片进行转换
from io import BytesIO
import os #创建文件夹，保存下载好的图片
import re
import multiprocessing
'''
基于BeautifulSoup解析库的py爬虫爬取18comic
'''
public_headers = {
    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36'
}
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
    options_list = soup.find_all('select')[2].find_all('option') # 用来取出存放页数select中的option标签数量来计算页数
    pages = len(options_list) # 设置一个变量表征页数
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

def download_image(url_path):# 下载图片,定义一个方法方便开启多线程,返回下载该图片的相对路径
    url = url_path[0]
    path = url_path[1]
    convert_status = url_path[2]
    try:
        comic_page = get(url, headers=public_headers)
        if comic_page.status_code != 200:
            # print('!= 200')
            return url_path
    except Exception:
        # print('Download Error')
        return url_path
    comic_name = url.split('/')[-1].split('?')[0]
    comic_local_position = path + '/' + comic_name
    image_bytes = BytesIO(comic_page.content)
    if image_bytes.__sizeof__() >= 1:
        image_source = Image.open(image_bytes)
        image_source.save(comic_local_position)
    else:
        # print('content is lost')
        return url_path
    if convert_status:
        convertImg(comic_local_position)
    return None # 成功返回None


def main(id):
    convert_status = False
    id = int(id)
    if id >= 220971:
        convert_status = True
    url = 'https://18comic.org/photo/' + str(id)
    print('解析成功,开始下载',url)
    path = makeDir(url)
    print('成功创建目录', path)
    url_list = get_url_list(url)
    url_path_list = [] # 这里创建一个列表作为传入map的值，里面加入path，屏蔽map只支持传入一个参数的问题
    for url_in_list in url_list:
        url_path_list.append((url_in_list, path, convert_status))
    print('正在开始多线程下载(默认64线程)请稍后......')
    pool = Pool(processes = 64) #改变下载进程数
    un_successful_list = pool.map(download_image, url_path_list) # 用于存放未下载成功图片路径
    while None in un_successful_list:
        un_successful_list.remove(None) #清洗None成功的下载
    while un_successful_list:
        re_download_count = 1
        print('当前有'+str(len(un_successful_list))+'张comic image由于不可抗网络因素下载失败，正在第'+str(re_download_count)+'次重新下载...')
        un_successful_list = pool.map(download_image, un_successful_list) #再进行下载
        while None in un_successful_list:
            un_successful_list.remove(None)
        re_download_count += 1
    print("所有comic image下载成功，共" + str(len(url_path_list)) + "张。enjoy!\n\n")

if __name__ == '__main__':
    multiprocessing.freeze_support() #防止pyinstaller()打包过程中出现由于开启多进程打包错误
    print('18comic.vip Downloader by emptysuns.\n请不要用于任何非法用途，仅作学习交流\n版本:Version 2.0\n下载链接格式请参照：\nhttps://github.com/emptysuns/18comic-Download\thttps://blog.acglove.cloud/?p=35\n')
    download_count = 1
    while(1):
        url = input('第'+str(download_count)+'次下载,请输入您想要下载comic的下载链接:\n')
        id = url.split('/')[4]
        main(id)
        download_count += 1