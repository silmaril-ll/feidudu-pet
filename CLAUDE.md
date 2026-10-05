# 肥嘟嘟桌宠：给 Claude Code 的说明

（给人看的介绍在 `README.md`。）

PyQt6 写的 Windows 桌宠。`feidudu.pyw` 是启动器（双击就开：先看文件齐不齐（`NEEDED`，缺了就直接说缺哪个），没有 PyQt6 会自己装、出错记到 `feidudu_error.log`、闪退（Python 接不住的）由 `faulthandler` 记到 `feidudu_crash.log`、
只开一只——再开会把已有的叫出来，见 `app.py`），程序在 `feidudu_pet/`，画面帧在 `sprites/`，清单 `sprites/sprites.json`。
请保持代码好读、注释用中文。

## 文件怎么分

| 文件 | 管什么 |
|---|---|
| `feidudu_pet/config.py` | 所有可调的数字（速度、大小、拉扯力度……）。用户自己调的写在根目录 `my_config.py`（不进 git），`feidudu_pet/__init__.py` 在别的模块读 config 之前把它盖上去 |
| `feidudu_pet/pet.py` | 肥嘟嘟本体窗口：位置、每一拍、画、鼠标、右键菜单 |
| `feidudu_pet/world.py` | 各个“面”：怎么沿着爬、到头怎么转弯、从哪吐丝、落在哪 |
| `feidudu_pet/behaviors/` | **一个动作一个文件**（idle、crawl、wave、wiggle、angry、snake、sleep、munch、nibble、refuse、frass、hang、lifted、tug、pupa、butterfly、approach、cling、comfy、look、peek） |
| `feidudu_pet/senses.py` | 肥嘟嘟的感觉：每拍看鼠标在哪、多快（`pet.senses.cursor` / `speed`），鼠标键按没按着（`pressed`、`pressed_at`），人多久没碰电脑（`idle`、`away`），在不在忙（`busy`、`busy_since`、`done_busy`） |
| `feidudu_pet/clock.py` | 肥嘟嘟看的钟（`config.TIMEZONE`）：按时间打招呼、晚上犯困 |
| `feidudu_pet/win32.py` | 只有这里碰 Windows API（找活动窗口、不抢焦点、伪装快捷键 `GlobalHotkey`、人多久没碰电脑 `idle_seconds`、鼠标键按没按着 `buttons_down`、最前面是哪个程序 `foreground_app`） |
| `feidudu_pet/silk.py` | 画那根丝的透明小窗口 |
| `feidudu_pet/silk_trail.py` | 丝垫：爬过的地方留下的丝（任务栏一条、活动窗口上沿一条，都点不到） |
| `feidudu_pet/disguise.py` | 伪装：卡通皮肤的输入法（没有框，蜡笔肥嘟嘟背上浮着小圆按钮；`sprites/skin.png`，画法在 `art-source/skin.js`） |
| `feidudu_pet/menu.py` | 蜡笔边框的菜单（`crayon_menu` / `add_submenu`）：QMenu + 样式表，画在 `art-source/menu.js`，字用系统的 |
| `feidudu_pet/shop.py` | 小卖部、衣柜的右键菜单，买东西、戴饰品 |
| `feidudu_pet/effects.py` | 特别叶子的效果，按名字找：吃完的（sparkle、scent、butterfly、tingly、plenty、sour、long_nap）；吃之前的 `refuses`（picky：枫叶这种不是芸香科的不吃，进 `refuse` 动作：叶子摆在嘴前、闻一闻、才不吃、我只吃芸香科，然后等你点叶子拿走（`pet.under_rect` 记着叶子在哪），`REFUSE_WAIT` 秒没人管就扭头；花肥不扣） |
| `art-source/items.js` | **货架**：饰品和叶子（样子、名字、价钱、抽到的机会、效果），加减东西只改这里再跑 runpet.py |
| `feidudu_pet/pellets.py` | 便便：一颗一个小窗口，往下掉、落在任务栏上，点一下捡起来 |
| `feidudu_pet/sprites.py`、`save.py`、`tray.py`、`app.py` | 读画面、存档、托盘、启动 |

## 加一个饰品 / 一种叶子

在 `art-source/items.js` 的 `ACCESSORIES` 或 `LEAVES` 里加一项（照着已有的抄），跑 `art-source/runpet.py`。
删掉一项同理。叶子想要新的特别效果：在 `feidudu_pet/effects.py` 写个函数加进 `EFFECTS`，叶子里写 `effect: '名字'`。

## 加一个新动作

1. 在 `feidudu_pet/behaviors/` 新建一个文件，写一个继承 `Behavior` 的类，加 `@register`（照着 `idle.py` 抄）。
   会自动被读进来，不用改别的文件。
2. 能改的地方：`anim`（用哪组画面）、`frame_every`、`duration`、`weight_for()`（多想做，0 = 只能被触发）、
   `enter()` / `tick()` / `exit()`、`menu_items()`（往右键菜单里加项）、`frame()`（不贴着面的动作自己决定怎么画）。
3. 在别处触发它：`pet.start("名字", 秒数, 其他参数=...)`。
4. 需要新画面：在 `art-source/pet.js` 里加一组帧，跑 `art-source/runpet.py`。

## 现在已经有的

- **位置模型**（`pet.py` 开头有说明）：用一个“支点”记位置（屏幕逻辑像素）。在地板/窗口上沿/墙/天花板上，支点是脚底中间；
  吊在丝上是嘴巴；被拎着是捏住的地方；被拉扯是后脚。每帧画面在 `sprites.json` 里有自己的 `anchor`，
  画的时候把帧的支点对准它，再按所在的面旋转 / 镜像（`world.pose_transform`）。
- **面**：任务栏（地板）、屏幕左右边（墙）、屏幕顶（天花板）、活动窗口的上沿（地板）和左右侧边（墙）。
  墙和天花板上用的是同一套爬行帧，程序里转 90° / 180°。
- **活动窗口**（`win32.ActiveWindow`，参考 Shimeji：只认活动窗口）：用 ctypes 调
  `GetForegroundWindow`、`DwmGetWindowAttribute(9)`（真实可见边框）、`IsIconic`/`IsZoomed`、`DWMWA_CLOAKED(14)`，
  跳过桌面、任务栏、最大化、全屏、太小的窗口；物理像素除以 `devicePixelRatio()` 换成 Qt 逻辑像素。
  活动窗口变成肥嘟嘟自己时（点它、开右键菜单）继续用上一个窗口。
- **不抢焦点**：`win32.no_activate()` 给窗口加 `WS_EX_NOACTIVATE`，不然一点它，活动窗口就变成它自己。
- **吐丝**：`behaviors/hang.py`，丝是单独一个点不到的透明小窗口 `silk.SilkThread`。
  脚下的窗口没了、被松手时走 `world.emergency_silk`（先快后慢），不会摔。
- **拉扯**（`behaviors/tug.py`）：按住拖动先进 `tug`，按拉力选 `tug` 帧、绕后脚转向鼠标；拉力 ≥ 0.9 坚持 `TUG_HOLD` 秒才松手变成 `lifted`。
- **拎起来**（`behaviors/lifted.py`）：`lifted` 帧（团成松松的 C 字，嘟嘴，偶尔冒角）。
- **探路**（`behaviors/wave.py`）：到了边上，`world.advance` 先调 `world.wave_first`，按 `config.WAVE_CHANCE` 的几率
  先做 `wave`（抬起前半身晃），晃完带着 `waved=True` 回到 `crawl`，下一拍才照原来的逻辑决定转弯/翻过去/吐丝。
  `wave` 帧：前 3 帧是抬起来（倒着放是放下），后 8 帧是晃。
- **丝垫**（`silk_trail.py`）：`crawl` 每拍调 `pet.silk_trail.lay`，按地方（`"floor"` 或窗口编号）记一根根丝；
  掉头、换地方就开新的一根。只记在这次运行里。
- **便便**（`behaviors/frass.py`、`pellets.py`）：吃一片叶子 `save["gut"]` 加 `FRASS_PER_LEAF`；有存货时 `frass`
  会被随机挑中（窗口上沿不拉），用 `strain` 帧抬尾巴，从尾巴尖掉一颗。捡起来记在 `save["frass"]`（以后可以拿来换东西）。
- **吃饱犯困**：吃完 `NAP_AFTER_MEAL` 秒之内白天也想睡；睡着一次就不困了（`sleep.enter` 把 `pet.fed_at` 清零）。
- **伪装**（`disguise.py`、`pet.disguise` / `pet.undisguise`）：停掉 `pet.timer`，藏起本体、丝、丝垫、便便、托盘图标，
  显示 `ImeBar`。还原时一切接着原来的状态走。状态栏拖过的位置存在 `save["ime_pos"]`。
  圆按钮、肥嘟嘟（双击还原）的位置都在 `sprites.json` 的 `skin` 里；按钮圆心在 `skin.js` 的 `SKIN_SPOTS`，顺着背的弧线。
  「中/英」「全半角」是单独的小图，程序贴上去才能切换。
- **小卖部**：饰品在 `pet.js` 的 `buildAnims(饰品部件, 饰品部件, true)` 里按身体同样的弯法画成每个动作的一层
  （`acc_名字_动作_帧.png`），`paintEvent` 画在身体上面；叶子是 4 个咬过的样子（`leaf_名字_几口.png`），
  `munch` 通过 `Behavior.under()` 垫在身体下面。梦蝶叶：`pupa` → `butterfly`（飞的时候点不到），时间到落地变回来。
  存档：`frass` 花肥、`owned` 买过的饰品、`wearing` 戴着的、`sparkle_until` 金叶子亮到什么时候。
- **吃饱了**（`behaviors/munch.py`）：`record_meal` 记最近几顿，`FULL_BOUT` 分钟里吃了 `FULL_AFTER` 片就设 `save["full_until"]`。
  能不能喂统一看 `refuse_reason(pet)`（睡着 / 吃饱 / 不在地上），右键喂叶子和小卖部抽叶子都用它，吃不了就不扣花肥。
  `nibble`：很少被随机挑中，啃一小口 `gut` 加 1，不算一顿。
- **蛇形警戒**（`behaviors/snake.py`）：`pet.poke` 记最近几次戳的时间，`SNAKE_WINDOW` 秒里戳了 `SNAKE_POKES` 下就进 `snake`。
- **人走开 / 回来**（`senses.py`、`sleep.nod_off` / `sleep.welcome`、`behaviors/approach.py`）：`win32.idle_seconds()`
  （`GetLastInputInfo`，别的系统上看鼠标有没有动）超过 `AWAY_AFTER` 秒算走开，它在地上闲着就睡（`pet.away_nap`，不自己醒）；
  人一碰电脑就醒，进 `approach`：说“你回来啦”，沿着脚下的面朝鼠标急急地爬（两倍速度，最多 15 秒）。
- **窗口被拖着跑**（`behaviors/cling.py`）：`world.check_window` 量窗口挪得多快（`pet.win_velocity`，只算整体平移、不算拖边改大小），
  `cling.hold_on` 看到快过 `CLING_SPEED` 就进 `cling`（压扁、嘟嘴、发抖），这时每拍都看窗口；停 `CLING_CALM` 秒说“呼～”；
  `FLING_WINDOW` 秒里快速掉头 `FLING_SHAKES` 次就被甩下来（`cling.fling`：丝粘在窗口边上，垂到下面去）。
- **摸摸**（`behaviors/comfy.py`）：`pet.feel_strokes` 每拍看鼠标（`senses.cursor`）是不是正在它画出来的身子上
  （`pet.touches`：把鼠标位置反算回这一帧画面，看那个像素透不透明）、没按键，是就交给 `comfy.stroke`。
  不用 `mouseMoveEvent`：Windows 上不抢焦点的窗口收不到不按键时的鼠标移动（实机试过没反应）。
  顺着身子方向（在墙上就是上下）来回划，每划够 `STROKE_LEN` 算一下，`PET_WINDOW` 秒里 `PET_STROKES` 下就进 `comfy`
  （瘫平一点、脸红、笑得更开）；停手 `PET_PAUSE` 秒回神，一直摸 `PET_SLEEPY` 秒就睡着。睡着的时候摸它不会醒。
- **看鼠标**（`behaviors/look.py`）：`look.notice` 每拍看要不要开始（在地上 idle/crawl、鼠标停 `LOOK_STILL` 秒、离它不到 `LOOK_RADIUS`、
  没按键、2 秒内没按过、不停在它身上、冷却完了；每停一次只掷一次 `LOOK_CHANCE`）。`look` 画面 9 帧是前半身抬起 0 → 1.35 弧度，
  按“弯的地方 → 鼠标”的仰角挑帧（`pet.look_idx` 慢慢转过去）；鼠标到身后就转身，在头前面慢慢挪远就进 `approach(then="look")`
  爬过去接着看；够不着说“够不着～”；鼠标快过 `FLINCH_SPEED` 从身上划过，`FLINCH_CHANCE` 几率吓一跳（`angry` + 吓！，五分之一装蛇）。
- **陪你忙**（`behaviors/peek.py`、`senses._track_busy`）：最近 60 秒里有动静（`idle < 1`）的秒数 ≥ `BUSY_LEVEL` 算忙，
  ≤ `BUSY_CALM` 算忙完（`senses.done_busy` = 忙了多久）。忙的时候 `pick_next` 去窗口的几率翻倍；在窗口上沿 `peek` 的想做程度是 `BUSY_PEEK`：
  正面的肥嘟嘟躲在窗口后面，只露出边线以上的脑袋和两只扒着边的小脚（`pet.js` 的 `peekFrame`，没有饰品层）。
  `peek.check_in` 每拍看：忙了 ≥ `DONE_AFTER` 秒停下来说“忙完啦？”；连着忙 `BREAK_AFTER` 秒说“歇一下？”，
  之后每 `BREAK_AGAIN` 秒一次（`save["break_reminder"]`，右键「提醒我歇一歇」开关，默认开）。
- **安静一会儿（暂停）**：`pet.pause(why)` 停掉 `pet.timer`、藏起本体 / 丝 / 丝垫 / 便便 / 输入法皮肤，只留托盘图标；
  `pet.unpause` 接着原来的状态走。`pet.paused` 是 None / "manual"（右键或托盘选的）/ "game"（自己发现在打游戏）。
  `config.GAMES`（程序名）/ `GAME_TITLES`（窗口标题里的字）写了东西才开 `pet.game_timer`，每 `GAME_CHECK_MS` 看一次
  `win32.foreground_app()`：是游戏就 `pause("game")`，切走就出来；"manual" 的不自动出来。暂停时伪装、快捷键都不藏，
  快捷键、再开一次 feidudu.pyw、单击托盘图标都会叫它出来。
- **快捷键**：`app.py` 装 `win32.GlobalHotkey(config.HOTKEY)`，按一下切换伪装；注册失败（被占了）右键菜单就不显示快捷键。
  `GlobalHotkey` 是一个藏起来的小窗口，`RegisterHotKey` 注册到它自己身上，只在它的 `nativeEvent` 里收 `WM_HOTKEY`
  （以前是全局 `nativeEventFilter`，每条 Windows 消息都要过一遍 Python，怀疑和右键菜单偶发闪退有关）。
- **右键菜单防闪退**：`pet.contextMenuEvent` 同时只开一个菜单，开着的时候留着引用、关了再 `deleteLater`；
  菜单样式表里的图片路径加了引号（路径里有空格也不出错）。
- **多屏幕**：`world.track_screen` 每拍看它身子在哪块屏幕，`world.area()` 用那块（不看鼠标）。
- **右键菜单**只留要人来做的事：喂叶子、捡便便、小卖部、衣柜、大小、安静一会儿、提醒我歇一歇、退出（藏起来 = 双击 / 快捷键，扭 = 单击，
  睡觉、去窗口它自己会）。托盘菜单：安静一会儿、回到任务栏上（救急）、退出；单击托盘图标扭一扭 / 暂停时叫它出来。所有菜单都用 `menu.crayon_menu()` 建
  （撕纸边卡片九宫格拉伸当底，字用系统字体、和平常的菜单一样大）。
- **启动器图标**：`feidudu.pyw` 每次启动都在后台用 PowerShell 在本文件夹生成 / 更新「肥嘟嘟.lnk」，图标是 `feidudu_icon.ico`
  （.pyw 文件本身换不了图标）。`.lnk` 里是这台电脑的路径，不进仓库。程序窗口图标也是这个 .ico；
  托盘图标是 `tray.py` 里用 QPainterPath 直接画的正面蝴蝶剪影（16–64 像素都清楚），颜色跟系统深色/浅色主题走。

## 只在 Linux 无头环境里测过，Windows 上需要实机确认

1. `win32.ActiveWindow` 这段 ctypes 能不能正常拿到窗口矩形，位置准不准（它应该正好站在窗口上沿）
2. `WS_EX_NOACTIVATE` 生效没有：点肥嘟嘟以后，原来的窗口还是不是活动窗口
3. 透明的地方鼠标能不能点穿（窗口是正方形的，比肥嘟嘟大不少）
4. 右键菜单在不抢焦点的窗口上能不能正常弹出、点选
5. 丝的小窗口、丝垫会不会挡住鼠标
6. 便便的小窗口能不能点到、点了会不会抢焦点
7. 输入法皮肤：点「中」、拖动、双击卡片上的肥嘟嘟会不会抢焦点
8. 蜡笔菜单：撕纸边的透明角在 Windows 上显示对不对（`WA_TranslucentBackground` + `NoDropShadowWindowHint`）
9. 打开一次以后文件夹里有没有带图标的「肥嘟嘟」快捷方式，点它能不能打开

10. 快捷键换了写法（藏起来的小窗口收 `WM_HOTKEY`），Ctrl+Alt+Z 还要再试一次
11. 右键菜单偶发闪退：改了以后乱点一阵还没出现，再观察一阵；再闪退就看 `feidudu_crash.log` 最后一段
12. 看鼠标：在别的程序里按着鼠标键的时候它不该看（`GetAsyncKeyState`）
13. 打游戏自己去睡：`foreground_app` 读不读得到游戏的程序名（反作弊可能挡住，就用 `GAME_TITLES`）

（摸摸、摸睡着、拖窗口抓紧、看鼠标、走开再回来（睡着的会醒、说“你回来啦”）已经在 Windows 上试过，能用。两块屏幕的情况暂时没法试。）

## 授权

代码（`feidudu.pyw`、`feidudu_pet/`、`art-source/lib_pet.js`、`runpet.py`）MIT；肥嘟嘟的形象和画（`sprites/`、`docs/`、
`feidudu_icon.ico`、`art-source/` 其余文件）CC BY-NC 4.0，见 `LICENSE`、`LICENSE-ART.md`。新加文件照这个分。

## 画新动作帧

`art-source/` 是蜡笔画笔（JS + 无头 Chromium）：`lib_pet.js` 画笔，`feidudu.js` 肥嘟嘟身体（侧面 / 正面）、叶子、蛹、蝴蝶，
`pet.js` 每个动作的弯法和泡泡，`items.js` 货架，`skin.js` 输入法皮肤，`menu.js` 菜单边框。先
`python -m pip install playwright pillow` 和 `python -m playwright install chromium`，
然后 `python art-source/runpet.py`，会重画整个 `sprites/`（固定随机种子，每次结果一样）。

## 待办

1. 叶子/蝴蝶图鉴（先不做）
