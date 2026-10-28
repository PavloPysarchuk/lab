// ===== bedtime story cast: layered SVG, every animatable part has a class =====
// Style: storybook flat vector, soft shading, warm/night palette, thick-ish rounded shapes, no outlines.
(function () {
  const A = (window.ART = window.ART || {});
  const P = A.pal = {
    skin: '#FFD8BD', skinSh: '#F2B99A', blush: '#FF8F7E', hair: '#E2572B', hairSh: '#B9401C', hairHi: '#F27A45',
    tie: '#4FB7A8', iris: '#3A2618', pj: '#F6C9D8', pjSh: '#E7A9BF', quilt: '#4E6BC9', quiltSh: '#3C55A8', quiltStar: '#FFD36B',
    pillow: '#F6EFE6', pillowSh: '#E3D6C6', wood: '#9A6440', woodSh: '#7A4B2E',
    fox: '#EE7A3A', foxSh: '#C95E25', foxW: '#FFF3E4', foxD: '#3B2A2E', brass: '#C9974A', brassSh: '#9C7234', flame: '#FFD36B', glow: '#FFC45A',
    night: '#141A3A', night2: '#1E2752', ink: '#15131A', gold: '#F2B544', paper: '#F1EADF',
  };

  // ---------- Mia: head (expressions) ----------
  // groups: .mia-eyes (blink: scaleY), .mia-pupils (look: translate), .m-<expr> mouths, .brow-l/.brow-r
  A.miaHead = (id = 'mia') => `
<svg class="${id}" viewBox="0 0 400 420" width="400" height="420" overflow="visible">
  <defs>
    <radialGradient id="${id}-face" cx="45%" cy="40%" r="65%"><stop offset="0" stop-color="#FFE3CF"/><stop offset="1" stop-color="${P.skin}"/></radialGradient>
    <linearGradient id="${id}-hair" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${P.hairHi}"/><stop offset=".55" stop-color="${P.hair}"/><stop offset="1" stop-color="${P.hairSh}"/></linearGradient>
  </defs>
  <g class="mia-pig-l" style="transform-origin:80px 200px">
    <path d="M86 196 C30 190 8 250 22 300 C30 330 58 338 70 318 C58 296 66 262 96 238 Z" fill="url(#${id}-hair)"/>
    <path d="M40 268 C36 292 44 314 58 322" stroke="${P.hairSh}" stroke-width="6" fill="none" stroke-linecap="round" opacity=".5"/>
    <circle cx="88" cy="214" r="15" fill="${P.tie}"/><circle cx="84" cy="209" r="5" fill="#8EE0D3"/>
  </g>
  <g class="mia-pig-r" style="transform-origin:320px 200px">
    <path d="M314 196 C370 190 392 250 378 300 C370 330 342 338 330 318 C342 296 334 262 304 238 Z" fill="url(#${id}-hair)"/>
    <path d="M360 268 C364 292 356 314 342 322" stroke="${P.hairSh}" stroke-width="6" fill="none" stroke-linecap="round" opacity=".5"/>
    <circle cx="312" cy="214" r="15" fill="${P.tie}"/><circle cx="308" cy="209" r="5" fill="#8EE0D3"/>
  </g>
  <path d="M70 210 C64 110 130 52 200 52 C270 52 336 110 330 210 C330 260 300 300 290 300 L110 300 C100 300 70 260 70 210 Z" fill="${P.hairSh}"/>
  <ellipse cx="82" cy="236" rx="18" ry="22" fill="${P.skinSh}"/><ellipse cx="318" cy="236" rx="18" ry="22" fill="${P.skinSh}"/>
  <path d="M86 220 C86 140 136 96 200 96 C264 96 314 140 314 220 C314 300 262 350 200 350 C138 350 86 300 86 220 Z" fill="url(#${id}-face)"/>
  <path d="M200 350 C150 350 112 322 96 280 C120 318 158 334 200 334 C242 334 280 318 304 280 C288 322 250 350 200 350Z" fill="${P.skinSh}" opacity=".45"/>
  <!-- bangs -->
  <path d="M78 196 C70 112 130 60 200 60 C272 60 332 112 322 196 C306 170 296 150 286 136 C280 162 262 176 246 182 C250 160 246 144 238 132 C224 158 196 172 170 176 C178 160 180 146 176 134 C160 162 132 182 104 186 C108 170 110 156 108 146 C96 160 86 178 78 196 Z" fill="url(#${id}-hair)"/>
  <path d="M150 80 C176 70 214 68 244 78" stroke="#FF9A63" stroke-width="7" stroke-linecap="round" fill="none" opacity=".7"/>
  <!-- cheeks + freckles -->
  <ellipse class="mia-cheek" cx="128" cy="270" rx="26" ry="15" fill="${P.blush}" opacity=".45"/>
  <ellipse class="mia-cheek" cx="272" cy="270" rx="26" ry="15" fill="${P.blush}" opacity=".45"/>
  <g fill="#E0946A" opacity=".8"><circle cx="150" cy="254" r="3.2"/><circle cx="162" cy="262" r="2.6"/><circle cx="142" cy="266" r="2.4"/><circle cx="250" cy="254" r="3.2"/><circle cx="238" cy="262" r="2.6"/><circle cx="258" cy="266" r="2.4"/></g>
  <!-- brows -->
  <path class="brow-l" style="transform-origin:150px 190px;transform-box:view-box" d="M128 192 C140 184 158 182 170 188" stroke="${P.hairSh}" stroke-width="7" stroke-linecap="round" fill="none"/>
  <path class="brow-r" style="transform-origin:250px 190px;transform-box:view-box" d="M230 188 C242 182 260 184 272 192" stroke="${P.hairSh}" stroke-width="7" stroke-linecap="round" fill="none"/>
  <!-- eyes -->
  <g class="mia-eyes" style="transform-origin:200px 228px;transform-box:view-box">
    <ellipse cx="150" cy="228" rx="25" ry="29" fill="#fff"/><ellipse cx="250" cy="228" rx="25" ry="29" fill="#fff"/>
    <g class="mia-pupils">
      <circle cx="150" cy="232" r="18" fill="${P.iris}"/><circle cx="250" cy="232" r="18" fill="${P.iris}"/>
      <circle cx="150" cy="232" r="9" fill="#0E0906"/><circle cx="250" cy="232" r="9" fill="#0E0906"/>
      <circle class="mia-glint" cx="157" cy="223" r="6.5" fill="#fff"/><circle class="mia-glint" cx="257" cy="223" r="6.5" fill="#fff"/>
      <circle cx="144" cy="240" r="3" fill="#fff" opacity=".8"/><circle cx="244" cy="240" r="3" fill="#fff" opacity=".8"/>
    </g>
    <path d="M124 214 C134 200 166 198 176 214" stroke="${P.iris}" stroke-width="5" fill="none" stroke-linecap="round"/>
    <path d="M224 214 C234 200 266 198 276 214" stroke="${P.iris}" stroke-width="5" fill="none" stroke-linecap="round"/>
  </g>
  <g class="mia-closed" style="display:none">
    <path d="M126 232 C138 246 162 246 174 232" stroke="${P.iris}" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M226 232 C238 246 262 246 274 232" stroke="${P.iris}" stroke-width="6" fill="none" stroke-linecap="round"/>
  </g>
  <path d="M194 262 C198 268 204 268 208 262" stroke="${P.skinSh}" stroke-width="5" fill="none" stroke-linecap="round"/>
  <!-- mouths -->
  <g class="m-scared" style="display:none"><path d="M182 300 C186 288 214 288 218 300 C214 312 186 312 182 300Z" fill="#7A2E2E"/><path d="M188 304 C196 300 204 300 212 304" stroke="#FF8F8F" stroke-width="4" fill="none"/></g>
  <g class="m-smile" style="display:none"><path d="M168 290 C180 312 220 312 232 290" stroke="#7A2E2E" stroke-width="7" fill="none" stroke-linecap="round"/></g>
  <g class="m-open" style="display:none"><path d="M166 288 C170 330 230 330 234 288 C222 296 178 296 166 288Z" fill="#7A2E2E"/><path d="M182 312 C192 320 208 320 218 312 C212 306 188 306 182 312Z" fill="#FF8F8F"/></g>
  <g class="m-wow" style="display:none"><ellipse cx="200" cy="302" rx="17" ry="21" fill="#7A2E2E"/><ellipse cx="200" cy="312" rx="10" ry="7" fill="#FF8F8F"/></g>
  <g class="m-sleep" style="display:none"><path d="M186 298 C194 304 206 304 214 298" stroke="#7A2E2E" stroke-width="5" fill="none" stroke-linecap="round"/></g>
</svg>`;

  // Mia tucked in bed (head is placed separately so it can move)
  A.bed = () => `
<svg viewBox="0 0 900 620" width="900" height="620" overflow="visible">
  <rect x="40" y="40" width="820" height="230" rx="40" fill="${P.wood}"/>
  <rect x="70" y="70" width="760" height="200" rx="26" fill="${P.woodSh}" opacity=".35"/>
  <circle cx="110" cy="70" r="34" fill="${P.wood}"/><circle cx="790" cy="70" r="34" fill="${P.wood}"/>
  <ellipse cx="450" cy="300" rx="330" ry="100" fill="${P.pillow}"/>
  <ellipse cx="450" cy="330" rx="300" ry="60" fill="${P.pillowSh}" opacity=".7"/>
</svg>`;
  A.quilt = () => `
<svg viewBox="0 0 900 520" width="900" height="520" overflow="visible">
  <defs><pattern id="qstars" width="240" height="200" patternUnits="userSpaceOnUse">
    <path d="M30 20 l6 13 14 2 -10 10 3 14 -13 -7 -13 7 3 -14 -10 -10 14 -2z" fill="${P.quiltStar}" opacity=".9"/>
    <path d="M150 110 l5 11 12 2 -9 8 3 12 -11 -6 -11 6 3 -12 -9 -8 12 -2z" fill="${P.quiltStar}" opacity=".75" transform="rotate(14 150 120)"/>
    <path d="M200 30 l4 8 9 1 -7 6 2 9 -8 -5 -8 5 2 -9 -7 -6 9 -1z" fill="#FFF0C2" opacity=".7"/>
    <circle cx="90" cy="70" r="5" fill="#9DB3F2"/><circle cx="72" cy="168" r="4" fill="#9DB3F2"/><circle cx="210" cy="160" r="3" fill="#9DB3F2"/><circle cx="110" cy="130" r="3" fill="#C9D6FA"/></pattern></defs>
  <path d="M0 80 C120 30 300 10 450 14 C600 10 780 30 900 80 L900 520 L0 520Z" fill="${P.quilt}"/>
  <path d="M0 80 C120 30 300 10 450 14 C600 10 780 30 900 80 L900 520 L0 520Z" fill="url(#qstars)"/>
  <path d="M0 80 C120 30 300 10 450 14 C600 10 780 30 900 80 L900 130 C780 86 600 66 450 70 C300 66 120 86 0 130Z" fill="#F6EFE6"/>
  <path d="M0 130 C120 86 300 66 450 70 C600 66 780 86 900 130 L900 150 C780 110 600 92 450 96 C300 92 120 110 0 150Z" fill="${P.quiltSh}" opacity=".6"/>
  <g class="hands"><ellipse cx="370" cy="62" rx="34" ry="24" fill="${P.skin}"/><ellipse cx="530" cy="62" rx="34" ry="24" fill="${P.skin}"/>
  <path d="M352 54 l0 16 M370 50 l0 18 M388 54 l0 16 M512 54 l0 16 M530 50 l0 18 M548 54 l0 16" stroke="${P.skinSh}" stroke-width="4" stroke-linecap="round"/></g>
</svg>`;

  // ---------- Fox with lantern ----------
  // groups: .fox-tail (sway), .fox-head (tilt), .fox-ear-l/.fox-ear-r (flick), .fox-arm (lantern arm), .lantern-glow, .fox-eyes (blink)
  A.fox = (id = 'fox') => `
<svg class="${id}" viewBox="0 0 600 700" width="600" height="700" overflow="visible">
  <defs>
    <radialGradient id="${id}-lg" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#FFE9A8" stop-opacity=".95"/><stop offset=".35" stop-color="${P.glow}" stop-opacity=".55"/><stop offset="1" stop-color="${P.glow}" stop-opacity="0"/></radialGradient>
    <linearGradient id="${id}-body" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#F58A48"/><stop offset="1" stop-color="${P.foxSh}"/></linearGradient>
  </defs>
  <g class="fox-tail" style="transform-origin:300px 560px;transform-box:view-box">
    <path d="M300 560 C200 600 90 560 70 470 C60 420 90 380 120 400 C130 460 190 500 280 500Z" fill="url(#${id}-body)"/>
    <path d="M70 470 C60 420 90 380 120 400 C116 420 104 440 96 470 C88 480 76 482 70 470Z" fill="${P.foxW}"/>
  </g>
  <path d="M230 640 L226 690 L262 690 L264 640Z M336 640 L338 690 L374 690 L370 640Z" fill="${P.foxD}"/>
  <path d="M300 360 C380 360 400 460 392 560 C388 630 350 660 300 660 C250 660 212 630 208 560 C200 460 220 360 300 360Z" fill="url(#${id}-body)"/>
  <path d="M300 420 C340 420 350 500 346 580 C344 620 326 640 300 640 C274 640 256 620 254 580 C250 500 260 420 300 420Z" fill="${P.foxW}"/>
  <path d="M224 430 C200 470 196 520 214 560 L240 552 C230 520 234 480 248 450Z" fill="${P.foxSh}"/>
  <g class="fox-arm" style="transform-origin:372px 440px;transform-box:view-box">
    <path d="M372 430 C420 440 450 400 470 360 L490 372 C470 420 432 470 380 470Z" fill="url(#${id}-body)"/>
    <circle cx="482" cy="362" r="18" fill="${P.foxD}"/>
    <path d="M484 360 L520 200" stroke="${P.woodSh}" stroke-width="10" stroke-linecap="round"/>
    <g class="lantern" style="transform-origin:520px 200px;transform-box:view-box">
      <circle class="lantern-glow" cx="530" cy="290" r="190" fill="url(#${id}-lg)"/>
      <path d="M520 200 C528 220 532 232 532 244" stroke="${P.brassSh}" stroke-width="5" fill="none"/>
      <rect x="500" y="244" width="64" height="12" rx="6" fill="${P.brass}"/>
      <path d="M506 256 L558 256 L552 326 L512 326Z" fill="#FFE6A0" opacity=".95"/>
      <path class="flame" style="transform-origin:532px 306px;transform-box:view-box" d="M532 270 C546 290 544 306 532 312 C520 306 518 290 532 270Z" fill="#FF9E3D"/>
      <path d="M532 284 C538 294 538 302 532 306 C526 302 526 294 532 284Z" fill="#FFF6C8"/>
      <path d="M506 256 L512 326 M558 256 L552 326 M532 256 L532 266" stroke="${P.brassSh}" stroke-width="5"/>
      <rect x="504" y="324" width="56" height="12" rx="6" fill="${P.brass}"/>
    </g>
  </g>
  <path d="M228 440 C200 470 210 520 240 520 C250 500 252 470 250 450Z" fill="url(#${id}-body)"/>
  <g class="fox-head" style="transform-origin:300px 360px;transform-box:view-box">
    <g class="fox-ear-l" style="transform-origin:220px 200px;transform-box:view-box"><path d="M196 236 L190 110 L280 190Z" fill="${P.fox}"/><path d="M206 214 L204 140 L258 190Z" fill="${P.foxD}"/></g>
    <g class="fox-ear-r" style="transform-origin:380px 200px;transform-box:view-box"><path d="M404 236 L410 110 L320 190Z" fill="${P.fox}"/><path d="M394 214 L396 140 L342 190Z" fill="${P.foxD}"/></g>
    <path d="M300 170 C390 170 440 230 440 280 C440 330 380 380 300 380 C220 380 160 330 160 280 C160 230 210 170 300 170Z" fill="url(#${id}-body)"/>
    <path d="M160 282 C190 290 230 316 262 360 C230 372 186 350 170 320 C162 306 160 294 160 282Z M440 282 C410 290 370 316 338 360 C370 372 414 350 430 320 C438 306 440 294 440 282Z" fill="${P.foxW}"/>
    <path d="M262 330 C276 360 324 360 338 330 C330 372 270 372 262 330Z" fill="${P.foxW}"/>
    <ellipse cx="300" cy="334" rx="17" ry="12" fill="${P.foxD}"/><ellipse cx="295" cy="330" rx="5" ry="3" fill="#fff" opacity=".6"/>
    <g class="fox-eyes" style="transform-origin:300px 272px;transform-box:view-box">
      <ellipse cx="252" cy="274" rx="14" ry="18" fill="${P.foxD}"/><ellipse cx="348" cy="274" rx="14" ry="18" fill="${P.foxD}"/>
      <circle cx="257" cy="267" r="5" fill="#fff"/><circle cx="353" cy="267" r="5" fill="#fff"/>
    </g>
    <path class="fox-smile" d="M286 352 C292 360 308 360 314 352" stroke="${P.foxD}" stroke-width="5" fill="none" stroke-linecap="round"/>
    <ellipse cx="226" cy="306" rx="16" ry="9" fill="#FF8F7E" opacity=".45"/><ellipse cx="374" cy="306" rx="16" ry="9" fill="#FF8F7E" opacity=".45"/>
  </g>
</svg>`;

  // ---------- wall shadows ----------
  A.shadowMonster = () => `
<svg viewBox="0 0 600 900" width="600" height="900" overflow="visible">
  <g fill="#070A1C">
    <path class="mon-body" d="M300 120 C390 120 430 200 430 300 C430 380 470 520 470 900 L130 900 C130 520 170 380 170 300 C170 200 210 120 300 120Z"/>
    <g class="mon-arm-l" style="transform-origin:190px 360px;transform-box:view-box"><path d="M190 340 C120 360 60 300 30 220 L50 210 C80 270 120 300 160 300Z"/><path d="M30 220 l-30 -40 M38 214 l-14 -52 M48 210 l6 -50" stroke="#070A1C" stroke-width="14" stroke-linecap="round"/></g>
    <g class="mon-arm-r" style="transform-origin:410px 360px;transform-box:view-box"><path d="M410 340 C480 360 540 300 570 220 L550 210 C520 270 480 300 440 300Z"/><path d="M570 220 l30 -40 M562 214 l14 -52 M552 210 l-6 -50" stroke="#070A1C" stroke-width="14" stroke-linecap="round"/></g>
    <path d="M232 120 L210 40 L270 112Z M368 120 L390 40 L330 112Z"/>
  </g>
  <g class="mon-eyes" style="transform-origin:300px 230px;transform-box:view-box;opacity:0">
    <ellipse cx="258" cy="232" rx="26" ry="14" fill="#FFD84A" opacity=".25"/><ellipse cx="342" cy="232" rx="26" ry="14" fill="#FFD84A" opacity=".25"/>
    <path d="M238 226 Q258 244 278 226 Q258 236 238 226Z M322 226 Q342 244 362 226 Q342 236 322 226Z" fill="#FFE27A"/>
  </g>
</svg>`;
  A.shadowFox = () => `
<svg viewBox="0 0 600 600" width="600" height="600" overflow="visible">
  <g fill="#070A1C">
    <path d="M190 210 L170 60 L280 170Z M410 210 L430 60 L320 170Z"/>
    <path d="M300 150 C400 150 450 220 450 280 C450 360 380 420 300 420 C220 420 150 360 150 280 C150 220 200 150 300 150Z"/>
    <path d="M300 400 C380 400 400 480 400 600 L200 600 C200 480 220 400 300 400Z"/>
    <path d="M400 560 C480 560 560 500 560 420 C560 380 540 360 520 380 C520 450 470 500 400 500Z"/>
  </g>
</svg>`;

  // ---------- small friends ----------
  A.owl = () => `
<svg viewBox="0 0 200 220" width="200" height="220" overflow="visible">
  <path d="M100 30 C160 30 180 90 176 140 C172 190 140 210 100 210 C60 210 28 190 24 140 C20 90 40 30 100 30Z" fill="#8B6B9E"/>
  <path d="M100 100 C140 100 150 150 146 180 C140 200 120 206 100 206 C80 206 60 200 54 180 C50 150 60 100 100 100Z" fill="#CDB6D9"/>
  <path d="M40 50 L56 18 L76 46Z M160 50 L144 18 L124 46Z" fill="#8B6B9E"/>
  <circle cx="72" cy="86" r="30" fill="#FFF6E0"/><circle cx="128" cy="86" r="30" fill="#FFF6E0"/>
  <g class="owl-eyes" style="transform-origin:100px 86px;transform-box:view-box"><circle cx="74" cy="88" r="15" fill="#2A1F33"/><circle cx="126" cy="88" r="15" fill="#2A1F33"/><circle cx="79" cy="82" r="5" fill="#fff"/><circle cx="131" cy="82" r="5" fill="#fff"/></g>
  <path d="M92 108 L100 124 L108 108Z" fill="#F2B544"/>
</svg>`;
  A.moon = () => `
<svg viewBox="0 0 300 300" width="300" height="300" overflow="visible">
  <defs><radialGradient id="mglow" r="50%"><stop offset=".45" stop-color="#FFF1C2" stop-opacity=".55"/><stop offset="1" stop-color="#FFF1C2" stop-opacity="0"/></radialGradient></defs>
  <circle cx="150" cy="150" r="150" fill="url(#mglow)"/>
  <circle cx="150" cy="150" r="80" fill="#FFF1C2"/>
  <circle cx="122" cy="128" r="12" fill="#F2DC9C"/><circle cx="178" cy="176" r="16" fill="#F2DC9C"/><circle cx="170" cy="118" r="7" fill="#F2DC9C"/>
  <path class="moon-smile" d="M126 168 C140 182 160 182 174 168" stroke="#C9A85A" stroke-width="6" fill="none" stroke-linecap="round"/>
  <path d="M120 146 C126 140 134 140 140 146 M160 146 C166 140 174 140 180 146" stroke="#C9A85A" stroke-width="6" fill="none" stroke-linecap="round"/>
</svg>`;
  A.firefly = () => `<svg viewBox="0 0 60 60" width="60" height="60" overflow="visible"><circle cx="30" cy="30" r="28" fill="#FFE27A" opacity=".25"/><circle cx="30" cy="30" r="12" fill="#FFE27A" opacity=".55"/><circle cx="30" cy="30" r="6" fill="#FFFBE0"/></svg>`;
  A.mushroom = (c = '#7FD6C2') => `<svg viewBox="0 0 120 120" width="120" height="120" overflow="visible"><ellipse cx="60" cy="60" rx="60" ry="40" fill="${c}" opacity=".18"/><rect x="50" y="56" width="20" height="50" rx="10" fill="#F6EFE6"/><path d="M14 62 C14 30 40 14 60 14 C80 14 106 30 106 62Z" fill="${c}"/><circle cx="42" cy="40" r="7" fill="#fff" opacity=".8"/><circle cx="74" cy="32" r="5" fill="#fff" opacity=".8"/></svg>`;
  A.star = (c = '#FFD36B') => `<svg viewBox="0 0 40 40" width="40" height="40"><path d="M20 2 l5 12 13 1 -10 9 3 13 -11 -7 -11 7 3 -13 -10 -9 13 -1z" fill="${c}"/></svg>`;
  A.sparkle = (c = '#FFE7A3') => `<svg viewBox="0 0 40 40" width="40" height="40"><path d="M20 0 C22 14 26 18 40 20 C26 22 22 26 20 40 C18 26 14 22 0 20 C14 18 18 14 20 0Z" fill="${c}"/></svg>`;
  A.lampOff = () => `<svg viewBox="0 0 200 300" width="200" height="300"><path d="M50 20 L150 20 L180 120 L20 120Z" fill="#F0D9B5"/><rect x="92" y="120" width="16" height="130" fill="#B98C5E"/><ellipse cx="100" cy="262" rx="60" ry="16" fill="#B98C5E"/></svg>`;
  A.foxPlush = () => `<svg viewBox="0 0 200 200" width="200" height="200" overflow="visible">
  <path d="M60 70 L52 20 L96 56Z M140 70 L148 20 L104 56Z" fill="#EE7A3A"/><path d="M100 50 C150 50 168 90 168 116 C168 150 140 176 100 176 C60 176 32 150 32 116 C32 90 50 50 100 50Z" fill="#EE7A3A"/>
  <path d="M34 120 C60 124 80 140 94 166 C64 172 40 156 34 120Z M166 120 C140 124 120 140 106 166 C136 172 160 156 166 120Z" fill="#FFF3E4"/>
  <path d="M70 108 C76 114 84 114 90 108 M110 108 C116 114 124 114 130 108" stroke="#3B2A2E" stroke-width="5" fill="none" stroke-linecap="round"/><ellipse cx="100" cy="136" rx="9" ry="6" fill="#3B2A2E"/></svg>`;
})();
