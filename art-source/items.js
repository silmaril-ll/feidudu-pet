// 小卖部的货架：饰品和叶子都写在这里。加一项、删一项，再跑一次 runpet.py 就行，程序那边会自己读 sprites.json。
//
// 饰品（ACCESSORIES）：label 名字、en 英文名字（config 里 LANGUAGE = "en" 时用）、price 几颗花肥、parts 怎么画。
//   坐标是肥嘟嘟身上的坐标（和 feidudu.js 的 fatParts 一样：头在左、脚底 y=0、背最高处大约在 (42, -55)）。
//   饰品单独画成一层，每个动作都用同样的弯曲，所以爬、探路、被拎、吊丝的时候都会贴着身体。
// 叶子（LEAVES）：label 名字、en 英文名字、weight 抽到的机会（0 = 不在抽奖里）、effect 吃完有什么特别、
//   minutes 特别效果持续多久、parts 怎么画（叶柄在 (0,0)，叶子朝 +x 长，长 100 左右）。
//   effect 的名字对应程序里 feidudu_pet/effects.py 的 EFFECTS；写了没有的名字就只是好吃，没有特别效果。
// 玩具（TOYS）：买一次永久拥有，在右键「玩具箱」里拿出来玩（玩法在 feidudu_pet/toys.py）。label、en、price、
//   kind（"hand" 拿在鼠标上）、parts 怎么画、points 几个要用到的点（都是画面坐标，单位和 parts 一样）：
//   拿在手上的：grip 鼠标箭头尖对着的地方、tip 叶子中间、end 树枝头。
const GACHA_PRICE = 5;          // 抽一片神秘叶子要几颗花肥

// 把一组部件挪到 (x, y)、转 a 弧度、放大 s 倍
function mapD(d, f){
  const tk = d.match(/[MLCQZ]|-?\d*\.?\d+(?:e[-+]?\d+)?/gi), out = []; let buf = [];
  tk.forEach(t => {
    if (/^[MLCQZ]$/i.test(t)) { out.push(t); return; }
    buf.push(parseFloat(t));
    if (buf.length === 2) { const q = f(buf); out.push(q[0].toFixed(2) + ',' + q[1].toFixed(2)); buf = []; }
  });
  return out.join(' ');
}
function place(parts, x, y, a, s){
  s = s || 1; const c = Math.cos(a || 0), n = Math.sin(a || 0);
  const f = p => [x + (p[0] * c - p[1] * n) * s, y + (p[0] * n + p[1] * c) * s];
  return parts.map(p => {
    const q = Object.assign({}, p);
    if (q.d) q.d = mapD(q.d, f);
    if (q.line) q.line = mapD(q.line, f);
    if (q.dot) { const m = f(q.dot); q.dot = [m[0], m[1], q.dot[2] * s]; }
    if (q.blush) { const m = f(q.blush); q.blush = [m[0], m[1], q.blush[2] * s, q.blush[3] * s]; }
    return q;
  });
}
function flower(col, r){
  r = r || 1; let d = '';
  for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2 - Math.PI / 2; d += E(Math.cos(a) * 2.7 * r, Math.sin(a) * 2.7 * r, 2.3 * r) + ' '; }
  return [{ d: d, fill: col, lw: 1, wob: .15 }, { dot: [0, 0, 1.3 * r], color: '#f3c64f', hl: false }];
}

const ACCESSORIES = {
  cat_ears: { label: '猫耳头箍', en: 'Cat ears', price: 12, parts: () => [
    { d: 'M45,-54 C47,-62 50.5,-69 55,-73 C57,-66 57.5,-59 56.5,-52 Z', fill: '#f6c9d6', lw: 1.3 },          // 后面那只耳朵
    { d: 'M48,-56.5 C49.5,-61 51.5,-65 53.8,-67.5 C54.6,-63 54.8,-59 54.4,-55 Z', fill: '#ec8fab', outline: false },
    { d: ART.limb([[43, -37], [42, -47], [40.5, -56]], 3), fill: '#ec8fab', lw: 1.1 },                    // 头箍
    { d: 'M25.5,-47.5 C25.5,-56 27.5,-64 31,-70 C35,-65 38,-59 39.5,-53.5 Z', fill: '#f6c9d6', lw: 1.3 },   // 前面那只耳朵
    { d: 'M28,-50 C28.2,-56 29.6,-61.5 31.4,-65 C33.6,-61.5 35.4,-57.5 36.6,-53.5 Z', fill: '#ec8fab', outline: false }
  ] },
  flowers: { label: '花环', en: 'Flower crown', price: 15, parts: () => {
    const spots = [[18, -45, '#f7b7c7'], [28, -51.5, '#fff1a6'], [39, -55, '#bcd6f5'], [50, -54, '#f7b7c7'], [60.5, -50, '#d9c6f0']];
    const P = [{ line: 'M13,-40 C22,-52 36,-58 50,-56 C56,-55 62,-52 67,-47', lw: 1.4, color: '#6f9f4a', double: false }];
    [[23, -50, .5], [45, -57.5, -.2], [56, -53.5, .5]].forEach(l => P.push(...place([{ d: E(0, 0, 3.4, 1.6), fill: '#86b865', lw: .9 }], l[0], l[1], l[2])));
    spots.forEach(s => P.push(...place(flower(s[2]), s[0], s[1] - 1.5, 0, 1)));
    return P;
  } },
  tophat: { label: '小礼帽', en: 'Top hat', price: 18, parts: () => place([
    { d: E(0, 0, 10.5, 2.4), fill: '#3a3330', lw: 1.2 },
    { d: 'M-6.5,-.5 C-6.6,-6 -6.2,-12 -5.6,-15.5 C-2,-16.8 2,-16.8 5.6,-15.5 C6.2,-12 6.6,-6 6.5,-.5 Z', fill: '#3a3330', lw: 1.2 },
    { d: 'M-6.5,-5 C-2,-6 2,-6 6.5,-5 L6.5,-2 C2,-3 -2,-3 -6.5,-2 Z', fill: '#d25a4a', outline: false },
    { line: 'M-4,-13 C-4.3,-10 -4.3,-8 -4,-6.5', lw: 1, color: 'rgba(255,255,255,.45)', double: false }
  ], 40, -54, -.3, 1.1) },
  bunny_ears: { label: '兔耳头箍', en: 'Bunny ears', price: 12, parts: () => [
    { d: 'M44.5,-54 C45.5,-66 48.5,-79 53.5,-84 C57.5,-79 57,-66 53,-52.5 Z', fill: '#fdf6f1', lw: 1.3 },
    { d: 'M47.5,-56 C48.5,-66 50.5,-75 53.3,-78.5 C55,-74 54.5,-65 52,-55 Z', fill: '#f4b9c8', outline: false },
    { d: ART.limb([[43, -37], [42, -47], [40.5, -56]], 3), fill: '#f4b9c8', lw: 1.1 },
    { d: 'M29.5,-49.5 C27.5,-63 28.5,-77 32.5,-83 C37.5,-78 40,-64 39.5,-52.5 Z', fill: '#fdf6f1', lw: 1.3 },
    { d: 'M31.5,-52 C30.5,-63 31.3,-73 33,-77.5 C35.8,-73 37.3,-63 37.3,-53.5 Z', fill: '#f4b9c8', outline: false }
  ] },
  bear_ears: { label: '熊耳头箍', en: 'Bear ears', price: 12, parts: () => [
    { d: E(52.5, -58.5, 7, 6.6), fill: '#8a6446', lw: 1.3 }, { d: E(52.5, -58.5, 3.8, 3.5), fill: '#c99f7a', outline: false },
    { d: ART.limb([[43, -37], [42, -47], [40.5, -56]], 3.2), fill: '#6b4a35', lw: 1.1 },
    { d: E(32.5, -55, 7, 6.6), fill: '#8a6446', lw: 1.3 }, { d: E(32.5, -55, 3.8, 3.5), fill: '#c99f7a', outline: false }
  ] },
  antennae: { label: '触角发箍', en: 'Bobble antennae', price: 10, parts: () => [                               // 真的触角其实很小，在头上
    { d: ART.limb([[43, -37], [42, -47], [40.5, -56]], 3), fill: '#3a3330', lw: 1 },
    { line: 'M40,-55 C37,-62 32,-68 33,-76 M42,-56 C47,-62 53,-67 55,-76', lw: 1.3, color: '#3a3330', double: false },
    { d: E(33, -78.5, 3.6), fill: '#f3c64f', lw: 1.1 }, { d: E(55, -78.5, 3.6), fill: '#f3c64f', lw: 1.1 }
  ] },
  glasses: { label: '玳瑁眼镜', en: 'Tortoiseshell glasses', price: 14, parts: () => {                             // 戴在假眼睛上（真眼睛是头上的小点点）；粗粗的玳瑁框
    const P = [
      { line: E(25, -33, 10.8, 10.2), lw: 3.6, color: '#7a4a28', double: false },
      { line: E(40.5, -41, 8.4, 8), lw: 3.6, color: '#7a4a28', double: false },
      { line: 'M34.8,-37.8 C35.6,-40 32.8,-40.2 33,-37', lw: 2.6, color: '#7a4a28', double: false }
    ];
    // 玳瑁的斑：沿着镜框撒一圈深浅不一的小点
    [[25, -33, 10.8, 10.2, 14], [40.5, -41, 8.4, 8, 11]].forEach(([cx, cy, rx, ry, n]) => {
      for (let k = 0; k < n; k++) {
        const a = k / n * Math.PI * 2 + .3;
        P.push({ dot: [cx + Math.cos(a) * rx, cy + Math.sin(a) * ry, k % 3 ? .9 : 1.2], color: ['#3e2413', '#d9a066', '#a8683a'][k % 3], hl: false });
      }
    });
    P.push({ line: 'M18,-37.5 C19,-40.5 21.5,-42 23.5,-42.3', lw: 1.1, color: 'rgba(255,255,255,.8)', double: false });
    return P;
  } },
  straw_hat: { label: '小草帽', en: 'Straw hat', price: 16, parts: () => place([
    { d: E(0, 0, 15, 3.2), fill: '#e9cf8a', lw: 1.2 },
    { d: 'M-7.5,-.5 C-7.8,-8 -4,-11 0,-11 C4,-11 7.8,-8 7.5,-.5 Z', fill: '#e9cf8a', lw: 1.2 },
    { d: 'M-7.6,-3.8 C-3,-4.8 3,-4.8 7.6,-3.8 L7.5,-1.2 C3,-2 -3,-2 -7.5,-1.2 Z', fill: '#d9483b', outline: false },
    { line: 'M-12,0 C-6,1 6,1 12,0 M-5,-7 L-3,-9 M2,-8 L4,-9.5', lw: .8, color: '#bda060', double: false }
  ], 40, -54, -.18, 1.1) },
  scarf: { label: '小围巾', en: 'Scarf', price: 14, parts: () => [                                   // 围在马鞍带那儿，侧面打个结，两条尾巴往后飘
    { d: ART.limb([[57, -25], [64, -21], [71, -16]], 5.5), fill: '#c93f33', lw: 1.1 },
    { d: ART.limb([[57, -23], [62, -14], [66, -5]], 5.5), fill: '#c93f33', lw: 1.1 },
    { d: ART.limb([[55.5, -2], [55, -27], [51.5, -53]], 9), fill: '#d9483b', lw: 1.2 },
    { line: 'M51.5,-49 L57,-48 M52.5,-40 L58,-39 M54.5,-15 L59.5,-14 M55,-7 L60,-6', lw: 1, color: '#f6e3c8', double: false },
    { d: E(56, -24, 4.2, 4.6), fill: '#b8362b', lw: 1.1 }
  ] },
  xmas_hat: { label: '圣诞帽', en: 'Christmas hat', price: 18, parts: () => place([
    { d: 'M-9,0 C-7,-9 0,-19 12,-21 C7,-14 7.5,-6 9,0 Z', fill: '#d9483b', lw: 1.2 },
    { d: E(0, 0, 11.5, 3.4), fill: '#fbf8f2', lw: 1.1 }, { d: E(12.5, -21, 3.6), fill: '#fbf8f2', lw: 1.1 }
  ], 40, -54, -.25, 1.1) },
  party_hat: { label: '生日帽', en: 'Party hat', price: 12, parts: () => place([
    { d: 'M-7.5,0 L0,-19 L7.5,0 Z', fill: '#8fb3d9', lw: 1.2 },
    { line: 'M-5.5,-5 L3,-12 M-3,-1 L5.8,-8 M1.5,-1 L6.8,-5', lw: 1.6, color: '#f3c64f', double: false },
    { d: E(0, -20, 3.2), fill: '#f4b9c8', lw: 1.1 }
  ], 41, -54, -.2, 1.05) },
  bow: { label: '蝴蝶结', en: 'Bow', price: 10, parts: () => place([
    { d: 'M0,0 C-5,-7 -12,-6 -11.5,0 C-12,6 -5,7 0,0 Z', fill: '#ec8fab', lw: 1.2 },
    { d: 'M0,0 C5,-7 12,-6 11.5,0 C12,6 5,7 0,0 Z', fill: '#ec8fab', lw: 1.2 },
    { d: E(0, 0, 2.8, 3.2), fill: '#d86b8c', lw: 1.1 }
  ], 47, -55, .35, 1) },
  orange_clip: { label: '小橘子发卡', en: 'Orange hair clip', price: 10, parts: () => place([                  // 柑橘凤蝶嘛：一颗小橘子别在头上
    { line: 'M-7,5.5 L7,5.5', lw: 2.2, color: '#b8b2a8', double: false },
    { d: E(0, 0, 5.8, 5.3), fill: '#f29c38', lw: 1.2 },
    { dot: [-1.8, -1.6, 1.1], color: 'rgba(255,255,255,.75)', hl: false },
    { d: 'M.5,-5 C2.5,-8.5 7,-9.5 9.5,-7.8 C7.5,-5.4 3.5,-4.4 .5,-5 Z', fill: '#6fae4f', lw: 1 },
    { dot: [.3, -5, .9], color: '#6b5a3a', hl: false }
  ], 45, -57, .3, 1) },
  lemon_clip: { label: '小柠檬发卡', en: 'Lemon hair clip', price: 10, parts: () => place([                   // 两头尖尖的小柠檬
    { line: 'M-7,5.5 L7,5.5', lw: 2.2, color: '#b8b2a8', double: false },
    { d: 'M-8,0 C-6.5,-4.5 -2.5,-5.4 0,-5.4 C2.5,-5.4 6.5,-4.5 8,0 C6.5,4.5 2.5,5.4 0,5.4 C-2.5,5.4 -6.5,4.5 -8,0 Z', fill: '#f5d949', lw: 1.2 },
    { dot: [-2.5, -2, 1.1], color: 'rgba(255,255,255,.75)', hl: false },
    { d: 'M1,-5 C3,-8.5 7.5,-9.5 10,-7.8 C8,-5.4 4,-4.4 1,-5 Z', fill: '#6fae4f', lw: 1 }
  ], 45, -57, .3, 1) },
  backpack: { label: '小书包', en: 'Backpack', price: 16, parts: () => [                                // 稳稳背在后背上：翻盖、扣子、提手
    { line: 'M91.5,-49.5 C91.5,-54.5 98.5,-54.5 98.5,-49.5', lw: 1.6, color: '#9b5b31', double: false },
    { d: 'M85,-35 C84,-43 86.5,-49.5 95,-50 C103,-50.5 106,-44.5 105.5,-35.5 C99,-33.5 91,-33.5 85,-35 Z', fill: '#e98a4a', lw: 1.3 },
    { d: 'M85.3,-41.5 C87,-47.5 101,-48.5 105,-42.5 C104,-39 96,-38 95,-38 C93,-38 87,-38.5 85.3,-41.5 Z', fill: '#c96f35', lw: 1.1 },
    { d: E(95, -38.5, 1.7), fill: '#f6d86b', outline: false }
  ] },
  crown: { label: '小王冠', en: 'Crown', price: 20, parts: () => place([
    { d: 'M-8,0 L-9.5,-10.5 L-4.5,-5 L0,-12.5 L4.5,-5 L9.5,-10.5 L8,0 Z', fill: '#f1cf62', lw: 1.2 },
    { d: 'M-8,0 L8,0 L8.4,-2.8 L-8.4,-2.8 Z', fill: '#e2b640', outline: false },
    { dot: [0, -4, 1.2], color: '#d9483b', hl: false }, { dot: [-4.8, -3.2, .95], color: '#7fa9d9', hl: false }, { dot: [4.8, -3.2, .95], color: '#7fa9d9', hl: false },
    { dot: [-9.5, -10.5, 1], color: '#fff3c2', hl: false }, { dot: [0, -12.5, 1], color: '#fff3c2', hl: false }, { dot: [9.5, -10.5, 1], color: '#fff3c2', hl: false }
  ], 41, -54, -.15, 1.1) }
};

function coloredLeaf(col, rib, vein){ return citrusLeaf(col, { rib: rib, vein: vein }); }
function leaflet(x, y, a, len, col){ return place([{ d: 'M0,0 C4,-5 12,-6 ' + len + ',0 C12,6 4,5 0,0 Z', fill: col, hatch: .25, lw: 1.1 }, { line: 'M0,0 L' + (len - 2) + ',0', lw: .7, color: '#a5d27f', double: false }], x, y, a); }

const LEAVES = {
  citrus: { label: '柑橘叶', en: 'Citrus leaf', weight: 0, parts: () => citrusLeaf() },               // 平时喂的，不花钱
  zanthoxylum: { label: '花椒叶', en: 'Sichuan pepper leaf', weight: 30, effect: 'tingly', parts: () => {        // 羽状复叶：一根叶轴，两边一对对小叶
    const P = [{ line: 'M-10,1.5 L96,0', lw: 1.6, color: '#6b8f45', double: false }];
    [14, 34, 54, 74].forEach((x, i) => { P.push(...leaflet(x, -1, -.9, 22 - i, '#5c9a45')); P.push(...leaflet(x + 3, 1, .9, 22 - i, '#5c9a45')); });
    P.push(...leaflet(92, 0, 0, 20, '#5c9a45'));
    return P;
  } },
  pomelo: { label: '柚子叶', en: 'Pomelo leaf', weight: 30, effect: 'plenty', parts: () =>                 // 叶柄上有一对“小翅膀”
    [{ d: 'M-2,0 C3,-7 10,-8.5 15,-2.5 C10,5 3,7 -2,0 Z', fill: '#3f7d36', lw: 1.1 }].concat(place(coloredLeaf('#3f7d36', '#8fc06a', '#6fa656'), 12, 0, 0, .86)) },
  kumquat: { label: '金橘叶', en: 'Kumquat leaf', weight: 25, parts: () =>                                // 小一点的叶子，带一颗小金橘
    place(coloredLeaf('#62a14a', '#b3dc8e', '#92c572'), 0, 0, 0, .85).concat([{ d: E(52, 10, 6.5, 5.8), fill: '#f29c38', lw: 1.1 }, { dot: [50, 8, 1.2], color: 'rgba(255,255,255,.7)', hl: false }]) },
  trifoliate: { label: '枳叶', en: 'Trifoliate orange leaf', weight: 20, parts: () =>                               // 三出复叶：三片小叶
    [{ line: 'M-10,1.5 L22,0', lw: 1.6, color: '#6b8f45', double: false }].concat(leaflet(22, 0, -.65, 38, '#78b04a'), leaflet(22, 0, .65, 38, '#78b04a'), leaflet(22, 0, 0, 58, '#78b04a')) },
  sansho: { label: '山椒叶', en: 'Japanese pepper leaf', weight: 20, effect: 'tingly', parts: () => {             // 山椒（日本花椒）：小叶更小更多
    const P = [{ line: 'M-10,1.5 L96,0', lw: 1.5, color: '#5d7f3c', double: false }];
    [12, 27, 42, 57, 72].forEach((x, i) => { P.push(...leaflet(x, -1, -.85, 17 - i, '#4d8c3a')); P.push(...leaflet(x + 2, 1, .85, 17 - i, '#4d8c3a')); });
    P.push(...leaflet(88, 0, 0, 15, '#4d8c3a'));
    return P;
  } },
  lemon: { label: '柠檬叶', en: 'Lemon leaf', weight: 20, effect: 'sour', parts: () =>                   // 带一颗小柠檬
    place(coloredLeaf('#6fae4f', '#c0e39c', '#9ccd78'), 0, 0, 0, .92).concat([{ d: 'M44,9 C44,4 50,2 55,3 C60,4 64,8 62,12 C60,16 52,17 48,15 C45,14 44,12 44,9 Z', fill: '#f5d949', lw: 1.1 }, { dot: [50, 6.5, 1.2], color: 'rgba(255,255,255,.75)', hl: false }]) },
  rue: { label: '芸香叶', en: 'Rue leaf', weight: 8, effect: 'scent', minutes: 30, parts: () => {       // 芸香：蓝绿色、深裂的小勺子叶，味道很冲
    const P = [{ line: 'M-10,1.5 L80,0 M30,0 C38,-10 46,-16 56,-20 M50,0 C58,9 66,13 76,15', lw: 1.4, color: '#6f8f82', double: false }];
    [[22, -6, -.9], [26, 6, .9], [40, -8, -.7], [44, 7, .8], [56, -21, -.3], [64, -17, .2], [76, 15, .3], [66, 12, .7], [84, 0, 0], [62, -3, -.6], [66, 4, .6]].forEach(l => P.push(...place([{ d: 'M0,0 C3,-3.5 9,-4.5 13,-1 C14,2 10,4 5,3.2 C2,2.6 .5,1.5 0,0 Z', fill: '#7fa39a', lw: .9, hatch: .3 }], l[0], l[1], l[2])));
    return P;
  } },
  phellodendron: { label: '黄檗叶', en: 'Cork tree leaf', weight: 15, effect: 'long_nap', parts: () => {   // 黄檗：尖尖的羽状复叶，有点黄
    const P = [{ line: 'M-10,1.5 L94,0', lw: 1.5, color: '#8a8f3c', double: false }];
    [16, 38, 60].forEach((x, i) => { P.push(...leaflet(x, -1, -.75, 26 - 2 * i, '#9dbb4a')); P.push(...leaflet(x + 3, 1, .75, 26 - 2 * i, '#9dbb4a')); });
    P.push(...leaflet(84, 0, 0, 26, '#9dbb4a'));
    return P;
  } },
  maple: { label: '枫叶', en: 'Maple leaf', weight: 10, effect: 'picky', parts: () => {                  // 陷阱：不是芸香科，它才不吃（花肥退回）
    const cx = 46, pts = [];                                                           // 掌状五裂：中间那片最长，边上有小锯齿
    const lobes = [[-110, 26], [-55, 35], [0, 40], [55, 35], [110, 26]], sinus = [[-145, 12], [-83, 20], [-28, 23], [28, 23], [83, 20], [145, 12]];
    const at = (deg, r) => [cx + Math.cos(deg * Math.PI / 180) * r, Math.sin(deg * Math.PI / 180) * r];
    pts.push(at(sinus[0][0], sinus[0][1]));
    lobes.forEach((l, k) => {
      const s0 = sinus[k], s1 = sinus[k + 1];
      pts.push(at((s0[0] + l[0]) / 2 + 3, l[1] * .62), at((s0[0] + l[0]) / 2 - 2, l[1] * .72));   // 小锯齿
      pts.push(at(l[0], l[1]));
      pts.push(at((s1[0] + l[0]) / 2 + 2, l[1] * .72), at((s1[0] + l[0]) / 2 - 3, l[1] * .62));
      pts.push(at(s1[0], s1[1]));
    });
    const d = 'M' + pts.map(p => p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' L') + ' Z';
    const veins = lobes.map(l => { const t = at(l[0], l[1] * .85); return 'M' + cx + ',0 L' + t[0].toFixed(1) + ',' + t[1].toFixed(1); }).join(' ');
    return [{ line: 'M-10,1.5 L' + (cx - 6) + ',0', lw: 1.6, color: '#9b5b31', double: false }, { d: d, fill: '#d9643a', hatch: .4, lw: 1.2 },
      { line: veins, lw: .9, color: '#f0a070', double: false }];
  } },
  gold: { label: '金叶子', en: 'Golden leaf', weight: 12, effect: 'sparkle', minutes: 60, parts: () => coloredLeaf('#e9c046', '#fff1b0', '#f5dc7a') },
  dream: { label: '梦蝶叶', en: 'Dream leaf', weight: 2, effect: 'butterfly', minutes: 10, parts: () => coloredLeaf('#a9b8e8', '#eef1ff', '#cdd6f5') }
};


// ---------------------------------------------------------------- 玩具
// 逗虫棒上的嫩叶（叶柄在原点，朝 +x 长）：挂在线上的、被它抢走趴着嚼的（pet.js 的 wand_leaf）都用这片
const WAND_LEAF = () => [{ d: 'M0,0 C5,-6 15,-8 26,0 C15,8 5,6 0,0 Z', fill: '#9fcf6e', hatch: .25, lw: 1.1 },
                         { line: 'M0,0 L23,0', lw: .7, color: '#d3eaa9', double: false }];
const TOYS = {
  // 逗虫棒：一根小树枝，头上一根线吊着一片嫩叶（拔河的时候叶子咬在它嘴里，线从树枝头牵过去）
  wand: { label: '逗虫棒', en: 'Leaf wand', price: 30, kind: 'hand',
    points: { grip: [0, 0], end: [-66, -52], tip: [-78, -30], stem: [-76, -36] },     // end：树枝头（线从这儿垂下去）；stem：线拴在叶柄上的地方；tip：它咬的地方
    parts: () => [
      { d: ART.limb([[0, 0], [-24, -24], [-50, -44], [-66, -52]], 2.6), fill: '#9b6b3e', hatch: -1.2, lw: 1.1 },
      { line: 'M-66,-52 C-70,-46 -74,-40 -76,-36', lw: 1, color: '#a08a6a', double: false },
      ...place(WAND_LEAF(), -76, -36, 1.75, 1)
    ] }
};
