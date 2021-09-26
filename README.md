# GenshinUID / 原神UID查询

​	一个HoshinoBot插件，用于查询原神UID信息。

​	注意：本插件不包含本体，您应该配合[Mrs4s](https://github.com/Mrs4s) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp) 和 [HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot) 使用，本插件的作用是利用米游社API查询指定原神UID信息（Cookies获取可前往[YuanShen_User_Info](https://github.com/Womsxd/YuanShen_User_Info)查看教程）

​	已完成：角色排序（星级>等级>好感），mysid/uid查询，mysid/uid绑定qq号，cookies池，每日自动记录uid查询使用的cookies，下次再查询时仍然调用该cookies（防止浪费），mysid/uid查询深渊单独层数，以上所有输出图片均可支持背景图片自定义。

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

3、在hoshino/config的`__bot__.py`文件中，添加GenshinUID

4、启动HoshinoBot后，私聊机器人，发送

```sh
添加 cookies
```

注意事项：可以添加多条，但一次只能添加一条，添加两个字的之后必须带有空格，cookies填入你自己的，并且不要泄露给任何人，如果添加了错误的cookies，会导致一系列问题，如果想删除错误的cookies，请操作sqlite数据库完成。

5、进入机器人在的群聊，即可正常使用本插件。

## 更新记录

#### 2021-9-27

​	新增：Cookies次数防浪费机制（查过的mysid/uid会锁定使用过的cookies，当天再查时会使用同样的cookies防止次数浪费，每日零点清空。）

​	优化：Cookies填入现在需要私聊bot，可以设置多条，并且不会随着git pull而需要重新设置。

​	优化：白色底图现在的透明度会更高。

​	修复：使用心海刷新深渊记录时，尝试查询深渊时无法输出正确的结果。

#### 2021-9-20

​	新增：米游社id查询（指令示例：mys123456789），该方法同样支持深渊查询，（指令示例：mys123456789深渊12）.

​	新增：支持绑定（指令示例：绑定uid123456789；指令示例：绑定mys123456789），二选一绑定或者都绑定也可，自动优先调用mys命令。

​	新增：绑定后可查询（指令示例：查询），同时支持深渊查询（指令示例：查询深渊12），该指令同时支持自定义图片，（指令示例：查询[此处应有图片]）

​	修复：修复图片拉伸比例不正确等问题。

​	优化：现在输出的图片质量默认为90%，优化发送速度。

​	优化：文件夹目录的bg文件夹可自由添加背景随机图库。

​	优化：优化代码结构

#### 2021-9-7

​	修改了米游社的salt值[@Azure](https://github.com/Azure99)，修复了米游社ds算法[@lulu666lululu](https://github.com/lulu666lulu)

​	更换了新ui+新背景画面。

​	添加了自动下载拼接头像、武器的程序，以后理论上游戏更新也通用。

​	uid命令现在可以根据角色数量自动设定长宽，并且自定义背景仍然适用！并且添加了角色当前携带的武器ui界面。

​	![8](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/8.PNG)

​	UID命令在uid命令的基础上删除了武器的ui界面。

​	![7](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/7.PNG)

​	添加了深渊查询，指令：uidxxxxxx深渊xx，例如uid123456789深渊12，只能查指定楼层（beta）

​	![9](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/9.PNG)

​	删除角色命令。

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

1、仅私聊状态下生效，触发词添加 后跟cookies即可添加Cookies（添加两字后需要带空格）

![10](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/10.png)

2、群聊状态下生效，绑定uid/绑定mys后跟uid/mysid即可完成绑定

![11](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/11.png)

3、群聊状态下生效，而且必须绑定过uid/mysid才可生效，输出查询可以获取角色图

![12](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/12.png)

4、群聊状态下生效，而且必须绑定过uid/mysid才可生效，输出查询深渊xx可以获取当期深渊层数图

![13](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/13.png)

5、群聊状态下生效，触发词uid后面跟九位uid即可/触发词mys后面跟米游社通行证即可。

![2](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/2.png)

6、群聊状态下生效，mysid/uid后跟相应数字后跟深渊后跟相应层数即可。

![14](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/14.png)

7、以上所有可输出图片的触发词后跟一张任意大小的图片（不能是GIF），可以自定义背景

![3](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/3.png)

![4](https://raw.githubusercontent.com/KimigaiiWuyi/GenshinUID/main/readme/4.png)



## 相关仓库

- [PaimonBot](https://github.com/XiaoMiku01/PaimonBot) - 插件原始代码来自于它
- [YuanShen_User_Info](https://github.com/Womsxd/YuanShen_User_Info) - 米游社API来自于它

## 其他

​	代码写的很烂，勿喷，有问题可以发issues/Pull Requests~

​	顺便求个star~
