# 适配器端变更：`recall_message_id` 回执 与 `meta` 元事件

> 日期：2026-06-11
> 分支：`v4-nonebot2`
> 影响文件：`GenshinUID/models.py`、`GenshinUID/client.py`、`GenshinUID/__init__.py`
> 关联设计（在 gsuid_core 仓库）：
> - `gsuid_core/plans/recall_message_id_design_20260610.md`
> - `gsuid_core/plans/meta_event_trigger_design_20260610.md`

本插件是 gsuid_core（SayuCore）的「适配器组件」：把各平台事件归一化后转发给 core，并把 core
下发的统一消息派发到对应平台发送。本次在适配器端落地两项 core 已完成的能力。

---

## 一、`recall_message_id` 回执机制（OneBot V11）

### 1.1 目标

core 侧已支持 `await bot.send(msg, wait_recall=True) -> Optional[str]`，返回平台真实出站消息 id，
供后续撤回 / 编辑 / 表情回应。适配器端需要：**发送平台消息成功后，把平台返回的 message_id 回传
给 core**，core 据此唤醒对应的 future。

### 1.2 协议

- **下行（core → adapter）**：`MessageSend` 新增 `echo: Optional[str]` 字段。
  - `echo is None` ⇒ 不需要回执（fire-and-forget，旧行为，零回程流量）。
  - `echo` 非空 ⇒ 发送成功后必须回执；core 只把 `echo` 盖在一次 `send()` 的**第一帧**上，
    因此适配器对每次调用**至多回执一次**，天然坍缩为单个 `Optional[str]`。
- **上行（adapter → core）**：复用 `MessageReceive` 承载回执，`content` 仅含单段：

  ```python
  Message(type="recall_message_id", data={"echo": "<原样回传>", "id": "<平台出站msg_id>"})
  ```

### 1.3 实现要点

| 位置 | 改动 |
|---|---|
| `models.py` | `MessageSend` 增加 `echo: Optional[str] = None`。msgspec 默认忽略未知字段，对旧 core 无影响。 |
| `client.py` `GsClient.recv_msg` | 在派发循环前初始化 `recall_id`；`onebot` 分支捕获 `onebot_send` 的返回值；循环结束后 `if msg.echo and recall_id:` 调用 `self._send_recall_receipt(msg, recall_id)`。 |
| `client.py` `GsClient._send_recall_receipt` | 新增方法：构造单段 `recall_message_id` 的 `MessageReceive`，经 `self._input()` 入发送队列。 |
| `client.py` `onebot_send` | 返回类型改为 `Optional[str]`；发送成功后 `return str(recall['message_id'])`，否则 `return None`。原 TODO 占位删除。 |

### 1.4 关键设计：回执为什么走 `self`，而非模块全局 `gsclient`

原本曾把 `gsclient` 全局移入 `client.py` 以便发送函数访问。但 `connect()/repeat_connect()` 的
`global gsclient` 位于 `__init__.py`，重绑定的是 `__init__` 的名字，**不会**同步到 `client.py` 的
同名全局 —— 这正是「init 与 client 循环设计」的隐患（两个模块各持一份会发散）。

本次的解法是**根本上不跨模块共享该全局**：

- `gsclient` 全局回归 `__init__.py`（连接生命周期 connect/重连/心跳/各 handler 都在此，`global`
  重绑定就地生效，单一可信来源）。
- 回执发送发生在 `GsClient.recv_msg` 内，它是实例方法，直接用 `self._input()` 即可，**无需**任何
  模块全局。`GsClient` 是单例，`self` 永远是当前连接实例。

因此既消除了发散隐患，又让回执路径与连接管理彻底解耦。

### 1.5 撤回执行（`excute_delete_message`）

`onebot_send` 的 `to_msg` 中新增对 `excute_delete_message` 段的处理：core 下发该段时调用
`bot.delete_msg(message_id=int(data))` 执行平台撤回。这是与 recall id 对称的「撤回」执行通道
（普通文本/图片不受影响；该段不产生可发送内容，故不触发回执）。

### 1.6 扩展到其它平台

让对应 `*_send` 函数返回平台 message_id（`Optional[str]`），并在 `recv_msg` 派发分支里用
`recall_id = await xxx_send(...)` 捕获即可。未改造的平台返回 `None` ⇒ 不回执 ⇒ core 端超时降级返回
`None`，安全。

---

## 二、`meta` 元事件监听（OneBot V11）

### 2.1 目标

core 已支持 `@sv.on_meta("user_exit_group")` 触发器，识别 `content` 中 `type` 以 `"meta-"` 开头的
段并走独立分发路径（不进文本/AI/历史/记忆管道，但完整继承 pm/黑白名单/area/enabled）。适配器端
需要：**监听平台通知/请求类事件，转成 `meta-*` 段上报 core**。

### 2.2 协议

适配器构造 `MessageReceive`：

- 顶层照常填 `bot_id`、`bot_self_id`、`user_type`、尽量填 `user_id`/`group_id`（用于鉴权/黑白名单）。
- `content` 放**单段** `Message(type="meta-<事件名>", data={...})`，`data` 为该事件特有字段 dict。

### 2.3 实现要点

| 位置 | 改动 |
|---|---|
| `__init__.py` 导入 | 新增 `on_request`（nonebot 核心匹配器）、`Dict`/`Tuple` 类型。 |
| `__init__.py` 匹配器 | 新增 `get_meta = on_notice(...)` 与 `get_meta_request = on_request(...)`。 |
| `__init__.py` `_ob11_event_to_meta` | 纯函数：把 OneBot V11 的 `ev.dict()` 映射为 `(事件名, data)`，无法识别返回 `None`。 |
| `__init__.py` `get_meta_message` | 处理器（同时挂在 notice/request 两个匹配器上）：连接检查 → 仅 OneBot V11 → 映射 → 构造 `meta-*` 的 `MessageReceive` → `gsclient._input()`。 |

与既有 `get_notice_message` 不冲突：OneBot V11 的非文件类通知在 `get_notice_message` 中本就
`return` 空操作；`get_meta_message` 对 `group_upload` 等返回 `None` 同样空操作，二者不会重复处理。

### 2.4 已映射的事件（OneBot V11）

| 平台事件 | meta 事件名 | user_type | data 字段 |
|---|---|---|---|
| notice `group_increase` | `user_join_group` | group | user_id, group_id, operator_id, sub_type |
| notice `group_decrease` | `user_exit_group` | group | user_id, group_id, operator_id, sub_type |
| notice `group_admin` | `group_admin_change` | group | user_id, group_id, sub_type(set/unset) |
| notice `group_ban` | `group_ban` | group | user_id, group_id, operator_id, duration, sub_type |
| notice `group_recall` | `group_recall` | group | user_id, group_id, operator_id, message_id |
| notice `friend_recall` | `friend_recall` | direct | user_id, message_id |
| notice `friend_add` | `friend_add` | direct | user_id |
| notice `notify`/`poke` | `poke` | group/direct | user_id, target_id, group_id? |
| request `friend` | `friend_request` | direct | user_id, comment, flag |
| request `group` | `group_request` | group | user_id, group_id, comment, flag, sub_type |

### 2.5 扩展到其它平台

在 `get_meta_message` 中放开 `bot.adapter.get_name()` 判断，为新平台编写各自的「事件 → (事件名,
data)」映射（参照 `_ob11_event_to_meta`），其余转发逻辑可复用。

---

## 三、向后兼容

- **旧 core**：不下发 `echo` 字段 ⇒ `msg.echo` 为 `None` ⇒ 适配器永不回执；不消费 `meta-*` ⇒
  无影响。
- **普通消息收发**：未触及，逐字节不变。
- **未改造的发送平台 / 未映射的元事件**：分别走「不回执」「`None` 忽略」路径，静默降级，不报错。

## 四、自测建议

1. OneBot V11 下，core 用 `wait_recall=True` 发送一条群消息，断言能拿到非空 message_id，且二次发送
   返回值不同。
2. core 不带 `echo` 正常发送，断言适配器无回执、行为同旧版。
3. 触发进群 / 退群 / 撤回 / 戳一戳 / 加好友 / 加群申请，断言 core 端对应 `@sv.on_meta(...)` 命中、
   `ev.meta_event_data` 字段正确。
4. 普通文本消息，断言不会误进 meta 路径。
