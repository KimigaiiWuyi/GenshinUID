# Enka Effect DSL 速查

用于 `weapon_effect.json` / `artifact_effect.json` / `char_effect.json`。

## 基本格式

```
属性+数值
```

多段用 `;` 连接：

```
addAtk+20;critRate+12
```

## 条件前缀（技能限制）

| 前缀 | 含义 |
|------|------|
| `A:` | 仅普攻 |
| `B:` | 仅重击 |
| `C:` | 仅下落 |
| `E:` | 仅元素战技 |
| `Q:` | 仅元素爆发 |
| `EQ:` | 战技+爆发 |
| `AB:` | 普攻+重击 |
| `ABCEQ:` | 全技能 |

例：`E:dmgBonus+40`、`Q:critRate+28`

## 常见属性名

| DSL | 含义 |
|-----|------|
| `addAtk` | 攻击力% |
| `addHp` | 生命% |
| `addDef` | 防御% |
| `exAtk` / `exHp` / `exDef` | 固定攻击/生命/防御（或转化结果） |
| `critRate` | 暴击率% |
| `critDmg` | 暴击伤害% |
| `energyRecharge` | 充能效率% |
| `elementalMastery` | 元素精通（点数） |
| `dmgBonus` | 伤害加成% |
| `physicalDmgBonus` | 物理伤害加成% |
| `healBonus` | 治疗加成% |
| `*DmgBonus` | 如 `CryoDmgBonus`、`GeoDmgBonus` |
| `lunarDmgBonus` 等 | 月曜类（见下文，**无冒号**） |

## 基于其它属性转化

```
目标属性+数值%基数
目标属性+上限%数值%基数
```

例：

- `exAtk+0.8%hp` — 生命的 0.8% 转化为攻击
- `dmgBonus+12%0.03%hp` — 基于生命转化伤害，上限 12%，每 1 生命贡献 0.03%（见 Character.py 解析）

## 文件职责

| 文件 | 用途 | 自动程度 |
|------|------|----------|
| `skill_add.json` | C3/C5 加 E/Q/A 等级 | 全自动 |
| `weapon_effect.json` | 武器精炼 buff | 半自动 |
| `artifact_effect.json` | 圣遗物 2/4 件 | 半自动 |
| `char_effect.json` | 角色固有/命座 buff | 空壳+人工 |
| `char_action.json` | 技能倍率表 | 从天赋 promote 生成 |
| `value_attr.json` | 圣遗物副词条权重 | 启发式 |
| `dmg_map.json` | 参考面板 | 仅空列表占位 |

## weapon_effect 结构

```json
{
  "武器名": {
    "normal": { "normal_effect": { "1": "...", "2": "...", "3": "...", "4": "...", "5": "..." } },
    "fight": {
      "fight_effect": { "1": "", "2": "", "3": "", "4": "", "5": "" },
      "group_effect": { "1": "", "2": "", "3": "", "4": "", "5": "" },
      "time": 0,
      "extra": {}
    }
  }
}
```

- `normal`：常驻、无条件
- `fight`：开战/条件触发
- `group`：组队计算用
- key `1`–`5`：精炼等级

## artifact_effect 结构

```json
{
  "套装名": {
    "normal_effect": { "2": "", "4": "" },
    "fight_effect": { "2": "", "4": "" },
    "group_effect": { "2": "", "4": "" }
  }
}
```

## skill_add

```json
{ "角色名": ["E", "Q"] }
```

数组两项对应 **三命、五命**（不是六命）分别给哪条技能 +3 级。  
取值：`A` / `E` / `Q`。

## 取值策略（最高）

- 区间 buff：取 **最高**（如最低 18% / 最高 36% → `addAtk+36`）
- 叠层：取 **满层**（3 层 × 8% → `addAtk+24`）
- 可并行条件：全部叠上（反应攻击 + 星烁伤害）
- 角色/武器限定：默认视为满足
- **互斥**（只能选一条）：默认给一条主线，备选写 `fight.extra`

## 新反应 DSL（7.0）

**禁止用冒号**写反应属性（`:` 在本项目里表示技能限制前缀如 `E:`/`Q:`）。

| 文案 | DSL |
|------|-----|
| 星烁反应伤害提高（通用，星超导+星扩散都吃） | `stellarDmgBonus+32` |
| 仅星超导反应伤害 | `stellarSuperconductDmgBonus+xx` |
| 仅星扩散反应伤害 | `stellarSpreadDmgBonus+40` |
| 星烁反应暴击伤害 | `stellarCritDmg+110` |
| 星烁基础增伤 | `stellarBaseDmgBonus+14` |
| 星烁擢升 | `stellarElevate+10` |

计算时：`增伤 = stellarDmgBonus + (星扩散?spread:0) + (星超导?super:0)`。
| 月曜增伤（通用） | `lunarDmgBonus+60` |
| 月曜基础增伤 | `lunarBaseDmgBonus+14` |
| 月感电增伤 | `lunarElectroDmgBonus+48` |
| 月绽放增伤 | `lunarBloomDmgBonus+80` |
| 月结晶增伤 | `lunarCrystallizeDmgBonus+128` |
| 月曜暴伤 | `lunarCritDmg+140` |
| 月曜擢升 | `lunarElevate+10` |
| 月曜大权区 | `lunarBaseArea`（默认 1，加算） |
| 月曜羽毛 | `lunarAddDmg+…` |

月曜公式见 `Fight.get_lunar_dmg`（meropide）：

- 基础系数：月感电 **3** / 月绽放 **1** / 月结晶 **1.6**
- 直伤：`属性×倍率×基础系数×(1+基础增伤)×(1+6×精通/(精通+2000)+月曜增伤)×大权区 + 羽毛` × 抗性 × 暴击期望 × (1+擢升)
- 反应：等级基础值×同上（无技能倍率时）
- **擢升**（命座「擢升」）：抗性后 ×`(1+擢升)`，加算；**不是** `lunarDmgBonus` 增伤
  - 通用：`lunarElevate` / `stellarElevate`
  - 分反应：`lunarElectroElevate` / `lunarBloomElevate` / `lunarCrystallizeElevate`
  - 来源在 `char_effect.json` 的 `fight_talent` / `group_talent`（按命座 1–6）

### 三套月曜圣遗物（最高）

| 套装 | 2 件 | 4 件（默认最高） |
|------|------|------------------|
| 晨星与月的晓歌 | `elementalMastery+80` | `lunarDmgBonus+60`（后台20+满辉40） |
| 穹境示现之夜 | `elementalMastery+80` | `critRate+30;lunarDmgBonus+20`（满辉暴击 + 两种月辉明光×10%） |
| 纺月的夜歌 | `energyRecharge+20` | `elementalMastery+120;lunarDmgBonus+20`（满辉全队精通 + 月辉明光） |

注意：纺月 **没有** 暴击率；暴击是穹境的。

### 武器核查要点

1. **月兆·满辉**：默认已满辉，数值 = 基础 + 额外。
2. **全队 buff** 必须同时写入 `fight_effect`（装备者单人面板）和 `group_effect`（组队）。
3. `a+xx` = 剧变反应增伤（感电/绽放等，`get_transform_dmg` 用 `prop["a"]`）。
4. `stellarDmgBonus` = 通用星烁；`stellarSpreadDmgBonus` / `stellarSuperconductDmgBonus` 分反应。
5. `lunarElectro/Bloom/CrystallizeDmgBonus` 分月感电/月绽放/月结晶。
6. 常驻词条放 `normal_effect`；条件触发放 `fight_effect`。

星烁公式见 `Fight.get_stellar_dmg`：

**直伤星超导**：基础系数满层 **2**（层数表 0→1 / 1~12→0.05n+1.4 / >12→2）  
**直伤星扩散**：基础倍率 **1**  
**反应星扩散·风**：等级基础值 × **0.75** × 精通项…  
**反应星扩散·冰**：等级基础值 × **3**（风涡满 3~6）× 精通项…（默认取冰满涡作最高）

```
直伤 = (属性×倍率×基础系数×(1+基础提升)×(1+6×精通/(精通+2000)+增伤)×大权区 + 羽毛)
       ×抗性×(1+暴击率×暴击伤害)×(1+擢升)

反应星扩散 = 等级基础值×基础倍率×(1+基础提升)×(1+6×精通/(精通+2000)+星扩散增伤)
            ×抗性×暴击区×擢升
```
