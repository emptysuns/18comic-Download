
```
```
# 18comic-Download(禁漫天堂)
### python多线程下载禁漫天堂comic 18comic.vip

*本脚本仅作学习交流，不能用于任何侵犯它人权益的行为。侵删！*

如果您觉得侵犯您合法权益后，请联系TG: [@Core_i0](https://t.me/Core_i0)

我会进行删库操作，永不更新。或者您使用过程中遇到某些问题也请发issue或者直接去联系TG~~（~~因为作者一般不会在github闲逛，一般在水TG群~~）~~。


***请使用2.2之后的版本进行下载。其之前的版本由于多进程引发的一系列的问题，最严重的会使操作系统死锁！***


```
2021/01/20更新:version：2.0 解决了下载图片被分割的问题,原网站对源图片资源进行了反爬虫，现在下载comic images正常了。
2021/01/31更新:version：2.1 增加下载多章节功能。
2021/02/08更新:version：2.2 将多进程下载改成多线程下载。解决多进程闪退，error，因过密集io操作使系统发生死锁问题。进一步提高下载速度。
```



终于到这个时间了

养兵千日，用兵一时

学了这么久python了终于到它用武之地了

学习之余，写了这个下载脚本，用来下载18comic.vip的images

同时该脚本开启多线程下载（默认64线程），基本能跑满宽带

如果对您有那么一点点的帮助请帮我点个**★**，如果有问题请在issue内提出

***更加详细的介绍地址***: https://blog.acglove.cloud/?p=35


##### windows exe 使用展示

可直接去release里下载打包好的exe文件

或者自己打包
```
pyinstaller --onefile Catch18comic.py
```


![image](https://blog.acglove.cloud/wp-content/uploads/2021/01/Screenshot_2.png)
##### 直接py脚本运行展示
![image](https://blog.acglove.cloud/wp-content/uploads/2021/02/Screenshot_3.png)


## 必看声明:
- 安装所需依赖库(直接运行脚本的话，打包好的exe可执行文件不需要安装依赖库)
```
pip3 install bs4 Pillow
```
- 传入url地址格式: 
您应该传入url应为如下举例
1. 
https://18comic.org/album/232758/%E7%B4%97%E5%A4%9C%E8%88%87%E6%97%A5%E8%8F%9C-bang-dream-ezr%E5%80%8B%E4%BA%BA%E6%BC%A2%E5%8C%96-ryu-minbs-%E6%B5%81%E6%B0%91-%E7%B4%97%E5%A4%9C%E3%81%95%E3%82%93%E3%81%A8%E6%97%A5%E8%8F%9C%E3%81%A1%E3%82%83%E3%82%93-bang-dream

![image](https://blog.acglove.cloud/wp-content/uploads/2021/01/Screenshot_3.png)


2. 
https://18comic.org/photo/232758/
![image](https://blog.acglove.cloud/wp-content/uploads/2021/01/Screenshot_4.png)


!仅支持这两种url，不支持其他形式url！
