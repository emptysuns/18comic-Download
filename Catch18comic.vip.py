from requests import *
from bs4 import BeautifulSoup
from multiprocessing import Pool
'''
基于BeautifulSoup解析库的py爬虫爬取18comic
'''
def get_url_list(url):
    response = get(url)
    # print(response.text)
    html = response.text
    # 用BeautifulSoup解析
    soup = BeautifulSoup(html, 'lxml')
    # 用来取出存放页数select中的option标签数量来计算页数
    options_list = soup.find_all('select')[2].find_all('option')
    # 设置一个变量表征页数
    pages = len(options_list)
    # 设置一个列表用来存储所有的最终url
    comic_page_urls = []
    # 存放每一页page图片
    # 取出第一页的页数根据页数的命名规则来自己计算出后面的页数的url，减少用库进行查的时间
    comic_page1_id = soup.find(id='album_photo_00001.jpg')['data-original']
    # 取出页数url判断之前的服务器路径
    comic_page_url_head_temp = '/'.join(comic_page1_id.split('/')[:-1])
    # 用split取出判断页数的后半段url地址例如jpg?v=1602070382暂存
    comic_page_id_tail_temp = comic_page1_id.split('/')[-1].split('.')[-1]
    # 对url地址后面的判断页数的url进行根据页数递增的规则进行拼接
    for page in range(1, pages + 1):
        if(page < 10):
            comic_page_url = comic_page_url_head_temp + '/0000' + str(page) + '.' + comic_page_id_tail_temp
        elif (page >= 10 and page < 100):
            comic_page_url = comic_page_url_head_temp + '/000' + str(page) + '.' + comic_page_id_tail_temp
        elif (page >= 100 and page < 1000):
            comic_page_url = comic_page_url_head_temp + '/00' + str(page) + '.' + comic_page_id_tail_temp
        elif (page >= 1000 and page < 10000):
            comic_page_url = comic_page_url_head_temp + '/0' + str(page) + '.' + comic_page_id_tail_temp
        elif (page >= 10000):
            comic_page_url = comic_page_url_head_temp + '/' + str(page) + '.' + comic_page_id_tail_temp
        # 测试每个url是否正正常输出
        #print(comic_page_url + '\n')
        # 将每一个url加入到存储的列表中
        comic_page_urls.append(comic_page_url)

    # 测试存储url的列表是否正常输出
    print(comic_page_urls)
    return comic_page_urls
'''
# 普通下载方式
# for comic_page_url in comic_page_urls:
#     # comic_page = get(comic_page_url)
#     print(comic_page_url,'\n')
#     comic_page = get(comic_page_url)
#     comic_name = comic_page_url.split('/')[-1].split('?')[0]
#     comic_local_position = r'./img download/' + comic_name
#     with open(comic_local_position, 'wb') as comic_img:
#         comic_img.write(comic_page.content)
#         comic_img.close()
#     print(comic_name + " This image DownLoad Successfully\n")
# print("\n*******DownLoad Successfully*******\n")
'''
# 下载图片,定义一个方法方便开启多线程
def download_image(url):
    comic_page = get(url)
    comic_name = url.split('/')[-1].split('?')[0]
    comic_local_position = r'./img download/' + comic_name
    with open(comic_local_position, 'wb') as comic_img:
        comic_img.write(comic_page.content)
        comic_img.close()
def main():
    url = 'https://18comic.org/photo/2394/'
    url_list = get_url_list(url)
    pool = Pool(processes = 64)
    pool.map(download_image, url_list)
    print("image DownLoad Successfully\n")
if __name__ == '__main__':
    main()