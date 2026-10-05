// 伪装用的输入法皮肤：没有框，只有肥嘟嘟，顺着它背上的弧线浮着几个蜡笔小圆按钮（中/英、全半角、表情、设置）。
// 故意不显眼：同事看了只会觉得“输入法皮肤上的小虫子”，也正好解释平时桌面上爬的是什么。
// 「中/英」「全半角」要能切换，所以单独画成小图，程序里贴到按钮上；表情和齿轮直接画在皮肤里。
const SK = { W: 256, H: 176, OX: 24, GY: 150, S: 1.6, R: 10.5, ink: '#5a5046', green: '#4f8a3e', moon: '#f1cf62' };
const SKIN_ORDER = ['lang', 'width', 'emoji', 'settings'];
const SKIN_SPOTS = [[13, -61], [44, -70], [77, -59], [106, -52]];     // 按钮圆心（肥嘟嘟身上的坐标），顺着背的弧线

function skinCenter(i){ const p = SKIN_SPOTS[i]; return [SK.OX + p[0] * SK.S, SK.GY + p[1] * SK.S]; }
function skinCell(i){ const c = skinCenter(i), r = SK.R * SK.S; return [c[0] - r, c[1] - r, c[0] + r, c[1] + r]; }

function gearD(){
  let d = '';
  for (let k = 0; k < 16; k++) {
    const a0 = k / 16 * Math.PI * 2, a1 = (k + 1) / 16 * Math.PI * 2, r = k % 2 ? 7.2 : 10;
    d += (k ? ' L' : 'M') + (Math.cos(a0) * r).toFixed(2) + ',' + (Math.sin(a0) * r).toFixed(2) + ' L' + (Math.cos(a1) * r).toFixed(2) + ',' + (Math.sin(a1) * r).toFixed(2);
  }
  return d + ' Z';
}
const SKIN_ICONS = {
  emoji: () => [{ d: E(0, 0, 9.5), fill: '#ffe39a', lw: 1.5 }, { dot: [-3.3, -2.2, 1.3], color: SK.ink, hl: false }, { dot: [3.3, -2.2, 1.3], color: SK.ink, hl: false },
    { line: 'M-4.2,2.2 Q0,6.4 4.2,2.2', lw: 1.4, color: SK.ink, double: false }, { blush: [-5.6, 2, 2.4, 1.5] }, { blush: [5.6, 2, 2.4, 1.5] }],
  settings: () => [{ d: gearD(), fill: '#cfd8c4', lw: 1.4, step: .4 }, { d: E(0, 0, 3.2), fill: '#fdfbf4', lw: 1.2 }]
};
const CRESCENT = 'M2,-7.5 C-6,-7.5 -9.5,2 -3.5,6.2 C0,8.6 5,7.6 7.2,4 C1.2,5.6 -3,1 -2.6,-3 C-2.3,-5.6 -.2,-7.1 2,-7.5 Z';

function glyphCanvas(){ return ART.mk(48, 48); }
function textGlyph(text, color, size){
  const c = glyphCanvas(), x = c.getContext('2d');
  x.font = size + 'px "Long Cang"'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = color;
  for (const o of [[0, 0], [.7, 0], [0, .6]]) x.fillText(text, 24 + o[0], 26 + o[1]);     // 描两遍，笔画粗一点
  return c.toDataURL('image/png');
}
function partsGlyph(parts, k, seed){
  const c = glyphCanvas();
  ART.figure(c.getContext('2d'), parts, { x: 24, y: 24, s: SK.S * k, r: 0 }, Object.assign({}, PO, { seed: seed, cut: false, lineS: 1.2, minDot: 0 }));
  return c.toDataURL('image/png');
}

function renderSkin(){
  const cv = ART.mk(SK.W, SK.H), ctx = cv.getContext('2d');
  // 肥嘟嘟（侧面，趴着）
  ART.figure(ctx, fatParts(), { x: SK.OX, y: SK.GY, s: SK.S, r: 0 }, Object.assign({}, PO, { seed: 185, border: 7 }));
  // 顺着背浮着的小圆按钮：白色小纸片，表情和齿轮直接画上去
  SKIN_ORDER.forEach((name, i) => {
    const c = skinCenter(i);
    ART.figure(ctx, [{ d: E(0, 0, SK.R), fill: '#fffdf4', hatchK: .3, lw: 1.5 }], { x: c[0], y: c[1], s: SK.S, r: 0 }, Object.assign({}, PO, { seed: 186 + i, border: 5 }));
    if (SKIN_ICONS[name]) ART.figure(ctx, SKIN_ICONS[name](), { x: c[0], y: c[1], s: SK.S * .7, r: 0 }, Object.assign({}, PO, { seed: 190 + i, cut: false, lineS: 1.2, minDot: 0 }));
  });
  const half = v => v.map(n => Math.round(n / 2 * 10) / 10);            // 画布是 2 倍图，程序里用一半
  return {
    card: cv.toDataURL('image/png'), w: SK.W / 2, h: SK.H / 2, order: SKIN_ORDER,
    cells: SKIN_ORDER.map((_, i) => half(skinCell(i))),
    pet: half([SK.OX, SK.GY - 57 * SK.S, SK.OX + 132 * SK.S, SK.GY + 6]),     // 双击肥嘟嘟就还原
    glyphs: {
      lang_zh: textGlyph('中', SK.green, 24), lang_en: textGlyph('英', SK.green, 24),
      width_half: partsGlyph([{ d: CRESCENT, fill: SK.moon, lw: 1.4 }], .78, 201),                 // 半角：弯月亮
      width_full: partsGlyph([{ d: E(0, 0, 6.8), fill: SK.moon, lw: 1.4 }], .78, 202)              // 全角：圆圆的
    }
  };
}
