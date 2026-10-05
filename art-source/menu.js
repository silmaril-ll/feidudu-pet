// 右键菜单的蜡笔皮肤：一张撕纸边的小卡片当底（程序里九宫格拉伸）、鼠标停着时的一抹绿蜡笔、小箭头、勾、波浪分隔线。
// 都画成 1 倍图，因为 Qt 的样式表（QSS）按图片像素来拉伸。字用系统的（清楚、大小和平常的菜单一样）。
const MENU = { W: 48, H: 48, CUT: 11 };           // CUT：九宫格四边各留多少像素不拉伸（撕纸边 + 圆角）

function menuRect(x0, y0, x1, y1, r){
  return 'M' + (x0 + r) + ',' + y0 + ' L' + (x1 - r) + ',' + y0 + ' Q' + x1 + ',' + y0 + ' ' + x1 + ',' + (y0 + r) +
    ' L' + x1 + ',' + (y1 - r) + ' Q' + x1 + ',' + y1 + ' ' + (x1 - r) + ',' + y1 + ' L' + (x0 + r) + ',' + y1 +
    ' Q' + x0 + ',' + y1 + ' ' + x0 + ',' + (y1 - r) + ' L' + x0 + ',' + (y0 + r) + ' Q' + x0 + ',' + y0 + ' ' + (x0 + r) + ',' + y0 + ' Z';
}

function menuPiece(w, h, parts, opts){
  const c = ART.mk(w, h);
  ART.figure(c.getContext('2d'), parts, { x: 0, y: 0, s: 1, r: 0 }, Object.assign({}, PO, { lineS: 1.9, minDot: 0 }, opts));
  return c.toDataURL('image/png');
}

function renderMenu(){
  const T0 = { x: 0, y: 0, s: 1, r: 0 };
  return {
    cut: MENU.CUT,
    bg: menuPiece(MENU.W, MENU.H, [{ d: menuRect(5, 5, MENU.W - 5, MENU.H - 5, 7), fill: '#fffaf0', hatchK: .35, lw: 1.2, step: .6 }], { seed: 210, border: 3.5, lineS: 1.6 }),
    hover: menuPiece(120, 24, [{ d: 'M6,5 C30,2 90,3 114,5 C118,10 118,15 114,19 C80,22 34,22 7,20 C2,15 2,10 6,5 Z', fill: '#d3e8b6', hatch: -.2, hatchK: .8, outline: false }], { seed: 211, cut: false }),
    arrow: menuPiece(12, 12, [{ d: 'M3.5,2.5 L9,6 L3.5,9.5 Z', fill: '#9a8a78', lw: 1 }], { seed: 212, cut: false, lineS: 1.2 }),
    check: menuPiece(14, 14, [{ line: 'M2.5,7.5 L5.8,10.8 L11.5,3.5', lw: 2.2, color: '#4f8a3e', double: false }], { seed: 213, cut: false, lineS: 1.3 }),
    sep: menuPiece(120, 6, [{ line: 'M4,3 C20,1.8 36,4.2 52,3 C68,1.8 84,4.2 100,3 C106,2.6 111,2.9 116,3', lw: 1, color: '#bdb2a2', double: false }], { seed: 214, cut: false, lineS: 1.2 })
  };
}
