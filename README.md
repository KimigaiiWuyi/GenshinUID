# GenshinUID / 原神UID查询

​	一个HoshinoBot插件，用于查询原神UID信息。

​	注意：本插件不包含本体，您应该配合[Mrs4s](https://github.com/Mrs4s) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 和 [HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot) 使用，本插件的作用是利用米游社API查询指定原神UID信息（Cookies获取可前往[YuanShen_User_Info](https://github.com/Womsxd/YuanShen_User_Info)查看教程）

​	已完成：角色排序（星级>等级>好感），背景图自定义（通过传参形式）

​	未完成：深渊数据导出，角色详细信息列表（包括武器信息，和全角色）

​	示例：	![1](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/1.PNG)

- [安装](#安装)
- [更新记录](#更新记录)
- [指令](#指令)
- [相关仓库](#相关仓库)
- [其他](#其他)

## 安装

​	基于[Mrs4s](https://github.com/Mrs4s) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 和 [HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot) 的插件，请确保你知晓HoshinoBot的插件安装方法和go-cqhttp的使用方法。

1、在hoshino/modules目录下执行

```sh
$ git clone https://github.com/KimigaiiWuyi/GenshinUID.git
```

2、进入GenshinUID文件夹内，安装依赖库

```sh
$ pip3 install -r requirements.txt
```

3、在GenshinUID的文件夹下打开getData.py，添加自己的cookies到函数cache_Cookie()中的cookie_list中。

4、在hoshino/config的`__bot__.py`文件中，添加GenshinUID

## 更新记录

#### 2021-8-14

​	修复宵宫和早柚可能导致的输入错误bug。

​	增加了简易的cookies池，现在填写cookies的方法在函数cache_Cookie()中的cookie_list中，支持多个cookies共同使用。

​	增加了新功能（beta），使用uid+九位数字+角色的方式触发，获取全部角色+武器信息。

​	增加了新的默认随机图，简单修改了部分ui。

#### 2021-8-05

​	修复自定义图片时，竖屏图片可能造成黑边问题。

​	降低高斯模糊值。

#### 2021-8-01

​	添加自定义背景图。

#### 2021-7-29

​	优化排序算法。

#### 2021-7-28

​	添加排序算法。

#### 2021-7-26

​	完成主体。

#### 2021-7-18

​	本项目开坑。

## 指令

1、触发词uid后面跟九位uid即可。

![2](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/2.png)

2、触发词后跟九位uid后跟一张任意大小的图片（不能是GIF），可以自定义背景

![3](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/3.png)

![4](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/4.png)

## 相关仓库

- [PaimonBot](https://github.com/XiaoMiku01/PaimonBot) - 插件原始代码来自于它
- [YuanShen_User_Info](https://github.com/Womsxd/YuanShen_User_Info) - 米游社API来自于它

## 其他

​	代码写的很烂，勿喷，有问题可以发issues/Pull Requests~

​	顺便求个star~
