from typing import List

from gsuid_core.models import Message

CK_QRCODE_LOGIN = '''先发送【绑定uidxxx】绑定UID,
然后发送【扫码登陆】, 使用米游社APP扫码完成绑定, [或者]选择以下方法
'''

CK_CONSOLE = '''var cookie = document.cookie;
var Str_Num = cookie.indexOf('_MHYUUID=');
cookie = '添加 ' + cookie.substring(Str_Num);
var ask = confirm('Cookie:' + cookie + '\\n\\n按确认，然后粘贴发送给机器人');
if (ask == true) {
    copy(cookie);
    msg = cookie
} else {
    msg = 'Cancel'
}
'''

CK_URL = '''1.复制上面全部代码，然后打开下面的网站
https://bbs.mihoyo.com/ys/obc/?bbs_presentation_style=no_header(国服)
https://www.hoyolab.com/home(国际服)
2.在页面上右键检查或者Ctrl+Shift+i
3.选择控制台(Console)，粘贴，回车，在弹出的窗口点确认(点完自动复制)
4.然后在和机器人的私聊窗口，粘贴发送即可
'''

SK_URL = '''如果想获取SK,操作方法和上面一致,网址更换为
http://user.mihoyo.com/(国服)
登陆后,进入控制台粘贴代码
然后在和机器人的私聊窗口，粘贴发送即可
'''


async def get_ck_help() -> List[Message]:
    msg_list = []
    msg_list.append(Message('text', '请先添加bot为好友'))
    msg_list.append(Message('text', CK_QRCODE_LOGIN))
    msg_list.append(Message('text', CK_CONSOLE))
    msg_list.append(Message('text', CK_URL))
    msg_list.append(Message('text', SK_URL))
    return msg_list
