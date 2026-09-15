#!/usr/bin/env python3
"""Bubble Card — DIAGONAL SEGMENTED PILL generator (module version = VERSION below).

ONE source (SHARED below) is emitted three ways so they cannot drift:
  bubble-pill-mod.yaml  (A) a card with inline `styles:`   (B) the `segmented_pill` module
  prototype.html        a standalone replica of Bubble's sub-buttons-card DOM that runs SHARED
                        verbatim against a fake `hass`, for headless-Chromium renders.
Edit HERE, never the YAML/HTML by hand.  Run:  python3 gen_yaml.py
"""
import json, textwrap, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = '1.0.0'   # THE version string — threads into the YAML header, the module `version:` metadata and the
                    # prototype title via __VERSION__ (published Bubble Card mods start at 1.0.0; the v2.0.x
                    # numbers in NOTES-v2.md were internal working labels). verify/test_v2.cjs asserts it.
MODULE_ID = sys.argv[1] if len(sys.argv) > 1 else 'segmented_pill'   # python3 gen_yaml.py segmented_pill_v2 → install under that id
# The module code reads its knobs from this.config[MODULE_ID] and the editor's visible_if reads card[MODULE_ID]:
# a module installed under a different id than its code expects silently sees NO config (blank labels, no modes).
EDITOR_SECTIONS = 6       # the visual editor exposes knobs for this many sections; the CODE has no cap

# =============================================================================================
#  SHARED — the body of the `${(() => { ... })()}` template. `cfg` is defined by the form.
#  `this` = the Bubble card, `hass` is live. Bubble applies the template with
#  Function("hass","entity","state",…,"card",…) — see NOTES.md "Templating".
# =============================================================================================
SHARED = r'''
/* ---------- knobs: every per-section knob is `<name>_<i>` (1-based), read by index ---------- */
const hex  = (v) => (v && String(v).trim()) ? '#' + String(v).replace('#','').trim() : null;
const num  = (v, d) => { const n = parseFloat(v); return isNaN(n) ? d : n; };
const knob = (name, i) => cfg[name + '_' + i];
const angle = Math.min(135, Math.max(45, num(cfg.angle, 105)));   /* 105 = "╱", 75 = "╲" */
const tint  = num(cfg.tint, 16);                                   /* default fill strength, % */
const scale = num(cfg.scale, 1);                                   /* optional density knob, 1 = auto */
const side  = (v) => String(v || '').toLowerCase() === 'right' ? 'right' : 'left';
const iconSide = side(cfg.icon_side);                              /* global default: icon left | right of the text */

/* ======================================================================
   ENTITY COLOR — approximates the color HA paints this entity's icon.
   A partial port of the HA frontend's stateActive() + stateColorCss() +
   the light rgb_color contrast tweak (hsv: s<.4 → s=.4, s<.1 → v=225).
   NOT exact parity: known divergences from HA (weather, camera
   "recording", lawn_mower states, group color derivation, "unknown")
   are listed under "Color fidelity" in the README.
   ====================================================================== */
const UNAVAIL = 'var(--state-unavailable-color, var(--disabled-text-color, #6f6f6f))';
const NEUTRAL = 'var(--pill-neutral-color, var(--state-icon-color, var(--secondary-text-color)))';
/* domains HA colors by state; everything else (numeric sensors…) stays neutral */
const COLORED = ['alarm_control_panel','alert','automation','binary_sensor','calendar','camera',
  'climate','cover','device_tracker','fan','group','humidifier','input_boolean','lawn_mower','light',
  'lock','media_player','person','plant','remote','schedule','script','siren','sun','switch','timer',
  'update','vacuum','valve','water_heater'];
const isActive = (dom, st) => {                         /* HA stateActive() */
  if (['button','event','input_button','scene'].includes(dom)) return st !== 'unavailable';
  if (st === 'unavailable' || st === 'unknown') return false;
  if (st === 'off' && dom !== 'alert') return false;
  switch (dom) {
    case 'alarm_control_panel': return st !== 'disarmed';
    case 'alert':               return st !== 'idle';
    case 'cover': case 'valve': return st !== 'closed';
    case 'device_tracker': case 'person': return st !== 'not_home';
    case 'lawn_mower':          return ['mowing','error'].includes(st);
    case 'lock':                return st !== 'locked';
    case 'media_player':        return st !== 'standby';
    case 'vacuum':              return !['idle','docked','paused'].includes(st);
    case 'plant':               return st === 'problem';
    case 'group':               return ['on','home','open','locked','problem'].includes(st);
    case 'timer':               return st === 'active';
    case 'camera':              return st === 'streaming';
  }
  return true;
};
const rgb2hsv = ([r,g,b]) => { const mx = Math.max(r,g,b), mn = Math.min(r,g,b), d = mx - mn;
  let h = 0; if (d) { h = mx === r ? ((g-b)/d) % 6 : mx === g ? (b-r)/d + 2 : (r-g)/d + 4; h = (h*60 + 360) % 360; }
  return [h, mx ? d/mx : 0, mx]; };
const hsv2rgb = ([h,s,v]) => { const f = (n) => { const k = (n + h/60) % 6; return v - v*s*Math.max(0, Math.min(k, 4-k, 1)); };
  return [f(5), f(3), f(1)]; };
const lightRgb = (a) => {                                /* rgb_color, else hs_color → rgb */
  const rgb = a.rgb_color || (a.hs_color ? hsv2rgb([a.hs_color[0], a.hs_color[1]/100, 255]) : null);
  if (!rgb) return null;
  const hsv = rgb2hsv(rgb);                              /* HA: lift pale colors to a readable tone */
  if (hsv[1] < .4) { if (hsv[1] < .1) hsv[2] = 225; else hsv[1] = .4; }
  return 'rgb(' + hsv2rgb(hsv).map(Math.round).join(',') + ')';
};
const entColor = (id) => {
  const so = id && hass.states[id];
  if (!so) return UNAVAIL;
  const st = String(so.state).toLowerCase(), a = so.attributes || {}, dom = id.split('.')[0];
  if (st === 'unavailable' || st === 'unknown') return UNAVAIL;
  if (dom === 'sensor' && a.device_class === 'battery') {           /* HA: battery by level */
    const b = parseFloat(st), lvl = b >= 70 ? 'high' : b >= 30 ? 'medium' : 'low';
    return `var(--state-sensor-battery-${lvl}-color, var(--state-active-color))`;
  }
  if (!COLORED.includes(dom)) return NEUTRAL;
  const on = isActive(dom, st);
  if (dom === 'light' && on) { const c = lightRgb(a); if (c) return `var(--bubble-light-color, ${c})`; }
  const key = st.replace(/[^a-z0-9]+/g, '_'), act = on ? 'active' : 'inactive';
  const chain = a.device_class ? [`--state-${dom}-${a.device_class}-${key}-color`] : [];
  chain.push(`--state-${dom}-${key}-color`, `--state-${dom}-${act}-color`, `--state-${act}-color`);
  return chain.reduceRight((acc, v) => `var(${v}, ${acc})`, on ? 'var(--primary-color)' : NEUTRAL);
};

/* ---------- DYNAMIC NUMBER of an entity (for mode 'value' and tint_mode 'value') ---------- */
const numOf = (id) => {
  const so = id && hass.states[id]; if (!so) return NaN;
  const st = String(so.state), a = so.attributes || {}, dom = id.split('.')[0];
  const n = parseFloat(st); if (!isNaN(n)) return n;                 /* numeric state */
  const off = st === 'off' || st === 'closed';
  switch (dom) {                                                     /* numeric attribute */
    case 'light':        return off ? 0 : (a.brightness ?? 255) / 255 * 100;
    case 'fan':          return off ? 0 : (a.percentage ?? 100);
    case 'cover':        return a.current_position ?? (off ? 0 : 100);
    case 'valve':        return a.current_position ?? (off ? 0 : 100);
    case 'climate':      return a.current_temperature ?? NaN;
    case 'humidifier':   return a.current_humidity ?? a.humidity ?? NaN;
    case 'media_player': return a.volume_level != null ? a.volume_level * 100 : NaN;
  }
  return NaN;
};

/* ---------- section color: explicit hex → mode 'active' / 'value' (opt-in) → entity color ----------
   mode 'active': entity ACTIVE (HA stateActive: on / detected / open / home / playing …) → active_color_i
   (blank = HA's own active color); INACTIVE or unavailable → the same neutral/inactive chain the
   default uses for an off entity. A motion sensor with active_color_i = blue → blue when detected,
   grey when clear. (color_i is the always-on fixed color and still wins over every mode.)
   mode 'value': numOf() against low_i / high_i thresholds → low/mid/high colors; the in-range
   default cycles through the theme palette by section index. */
const MID = ['var(--accent-color, #ff9800)', 'var(--primary-color, #03a9f4)', 'var(--success-color, #4caf50)',
             'var(--info-color, #4dd0e1)', 'var(--warning-color, #ff9800)', 'var(--error-color, #db4437)'];
const isOn = (id) => {
  const so = id && hass.states[id]; if (!so) return false;
  const st = String(so.state).toLowerCase();
  return st !== 'unavailable' && st !== 'unknown' && isActive(id.split('.')[0], st);
};
const sectionColor = (i, id) => {
  const fixed = hex(knob('color', i)); if (fixed) return fixed;
  if (knob('mode', i) === 'active') return (isOn(id) && hex(knob('active_color', i))) || entColor(id);
  if (knob('mode', i) === 'value') {
    const v = numOf(id), lo = parseFloat(knob('low', i)), hi = parseFloat(knob('high', i));
    if (isNaN(v)) return UNAVAIL;
    if (!isNaN(lo) && v <= lo) return hex(knob('low_color', i))  || 'var(--info-color, #4dd0e1)';
    if (!isNaN(hi) && v >= hi) return hex(knob('high_color', i)) || 'var(--error-color, #db4437)';
    return hex(knob('mid_color', i)) || MID[(i - 1) % MID.length];
  }
  return entColor(id);
};

/* ---------- section tint (fill strength, %): same fixed / value pattern as the colors ----------
   tint_i          fixed % for this section (blank = the pill's `tint`)
   tint_mode_i     'value' → the section's dynamic number (brightness %, fan %, position, a sensor
                   reading …) is mapped from tint_value_min_i..tint_value_max_i (default 0..100)
                   onto tint_min_i..tint_max_i (default 5..tint_i or 60). Off / 0 → tint_min_i.   */
const sectionTint = (i, id) => {
  const fixed = num(knob('tint', i), NaN);
  if (knob('tint_mode', i) === 'value') {
    const v  = numOf(id), lo = num(knob('tint_value_min', i), 0), hi = num(knob('tint_value_max', i), 100);
    const t0 = num(knob('tint_min', i), 5), t1 = num(knob('tint_max', i), isNaN(fixed) ? 60 : fixed);
    if (isNaN(v)) return t0;
    const f = hi === lo ? 1 : Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
    return Math.round((t0 + (t1 - t0) * f) * 10) / 10;
  }
  return isNaN(fixed) ? tint : fixed;
};

/* ---------- labels: top_i / bottom_i — a plain string, or a JS template with ${ } ----------
   Evaluated here with the same scope Bubble gives its templates: hass, entity (this section's
   entity id), state, stateObj, attributes, card (the card config), and `this` = the card. A
   template that throws renders as an empty label rather than breaking the pill.               */
const tpl = (s, id) => {
  if (s == null || s === '') return '';
  s = String(s);
  if (!s.includes('${')) return s;
  try {
    const so = hass.states[id];
    const out = new Function('hass', 'entity', 'state', 'stateObj', 'attributes', 'card',
      'return `' + s.replace(/`/g, '\\`') + '`;')
      .call(this, hass, id, so?.state, so, so?.attributes || {}, this.config);
    return out == null ? '' : String(out);
  } catch (e) { return ''; }
};
const cssStr = (s) => '"' + s.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\a ') + '"';

/* ---------- sections = the card's sub-buttons, in order; N = the count, no cap ----------
   card_type "sub-buttons" renders sub_button.bottom (its editor writes that shape and drops
   `main`); a hand-written array or a {main:[…]} object is accepted too. A sub-button without
   `entity` inherits the card's entity, as Bubble itself does. Adding a section = adding a
   sub-button; every index below reads N.                                                     */
const sb   = this.config?.sub_button;
const list = Array.isArray(sb) ? sb : (sb?.bottom?.length ? sb.bottom : (sb?.main || []));
const btns = list.filter(Boolean);
const ids  = btns.map(b => b.entity ?? this.config?.entity);
const N    = Math.max(1, ids.length);
/* name on its own row: Bubble writes "Name · State" as ONE string into the name container, so a stacked
   name/state cannot be split there. name_slot / name_slot_i ('top' | 'bottom') puts the sub-button's
   \`name\` (else the entity's friendly name) into that label row instead — keep show_name off. An explicit
   top_i / bottom_i still wins over it. */
const nameOf = (b, id) => String(b?.name ?? hass.states[id]?.attributes?.friendly_name ?? '');
const nameSlot = (i) => { const v = String(knob('name_slot', i) || cfg.name_slot || '').toLowerCase(); return v === 'top' || v === 'bottom' ? v : ''; };
const secs = ids.map((id, k) => {
  const i = k + 1, ns = nameSlot(i);
  return { i, id,
    color: sectionColor(i, id), tint: sectionTint(i, id),
    text:  hex(knob('text_color', i))  || 'var(--pill-text-color)',
    label: hex(knob('label_color', i)) || 'var(--pill-label-color)',
    side:  knob('icon_side', i) ? side(knob('icon_side', i)) : iconSide,   /* icon_side_i overrides icon_side */
    top:    tpl(knob('top', i), id)    || (ns === 'top'    ? nameOf(btns[k], id) : ''),
    bottom: tpl(knob('bottom', i), id) || (ns === 'bottom' ? nameOf(btns[k], id) : '') };
});

/* ---------- geometry: three stacked angled hard-stop gradients on the pill's ::before canvas ----------
   1. divider hairlines   2. section fills (padding-box)   3. section rims (border-box, showing
   through the transparent border). Stop k (k = 1..N-1) is placed where the k/N cell boundary
   crosses the pill's mid-height WHATEVER the pill's width: 50% of the gradient line is the pill
   center and one pill width along that line is 100cqw × sin(angle) (the pill is the query
   container). Plain k/N would drift by up to half the pill height on a narrow 6-section pill.
   The default divider color is the NEXT section's color (the section the divider leads into).  */
const sin = Math.sin(angle * Math.PI / 180);
const at  = (k, d) => `calc(50% + ${((k / N - .5) * sin).toFixed(4)} * 100cqw ${d < 0 ? '-' : '+'} ${Math.abs(d)}px)`;
const dw  = num(cfg.divider_width, 2) / 2, feather = .5;
const fills = (pre) => N === 1 ? `var(--_${pre}1) 0%, var(--_${pre}1) 100%`
  : Array.from({ length: N - 1 }, (_, k) =>
      `var(--_${pre}${k + 1}) ${at(k + 1, -feather)}, var(--_${pre}${k + 2}) ${at(k + 1, feather)}`).join(', ');
const dividers = (N === 1 || dw <= 0) ? 'transparent 0%, transparent 100%'
  : Array.from({ length: N - 1 }, (_, k) =>
      `transparent ${at(k + 1, -dw)}, var(--_d${k + 1}) ${at(k + 1, -dw)}, var(--_d${k + 1}) ${at(k + 1, dw)}, transparent ${at(k + 1, dw)}`).join(', ');

/* ---------- whole-pill knobs → CSS custom properties (all overridable per card in `styles:`) ---------- */
const borderColor  = hex(cfg.border_color);
const dividerColor = hex(cfg.divider_color);
const pillVars = [
  `--pill-angle: ${angle}deg`,
  `--pill-sections: ${N}`,
  `--pill-scale: ${scale}`,
  `--pill-cell: calc(100cqw / ${N})`,
  `--pill-height: ${cfg.height ? num(cfg.height, 56) + 'px' : 'var(--row-height, 56px)'}`,
  `--pill-radius: ${cfg.radius != null && cfg.radius !== '' ? num(cfg.radius, 28) + 'px' : 'calc(var(--pill-height) / 2)'}`,
  `--pill-border-width: ${num(cfg.border_width, 1)}px`,
  `--pill-rim: ${num(cfg.rim, 55)}%`,
  `--pill-tint: ${tint}%`,
  `--pill-divider-strength: ${cfg.divider_strength != null && cfg.divider_strength !== '' ? num(cfg.divider_strength, 30) + '%' : 'var(--pill-tint)'}`,
  `--pill-base: var(--card-background-color, var(--ha-card-background, #1c1c1c))`,
  `--pill-text-color: ${hex(cfg.text_color) || 'var(--primary-text-color)'}`,
  `--pill-label-color: ${hex(cfg.label_color) || 'var(--secondary-text-color)'}`,
  `--pill-font-size: ${cfg.font_size ? `calc(${num(cfg.font_size, 15)}px * var(--pill-scale))` : 'calc(clamp(10px, var(--pill-cell) * .14, 15px) * var(--pill-scale))'}`,
  `--pill-font-weight: ${num(cfg.font_weight, 600)}`,
  `--pill-icon-size: ${cfg.icon_size ? `calc(${num(cfg.icon_size, 21)}px * var(--pill-scale))` : 'calc(clamp(15px, var(--pill-cell) * .19, 22px) * var(--pill-scale))'}`,
  `--pill-label-size: ${cfg.label_size ? `calc(${num(cfg.label_size, 10)}px * var(--pill-scale))` : 'calc(clamp(8px, var(--pill-cell) * .09, 10.5px) * var(--pill-scale))'}`,
  `--pill-label-weight: ${num(cfg.label_weight, 500)}`,
  `--pill-label-transform: ${cfg.label_transform === 'uppercase' ? 'uppercase' : 'none'}`,
  `--pill-icon-gap: 4px`,
  `--pill-pad: 4px`,
  `--pill-label-inset: 3px`,
];
secs.forEach(({ i, color, tint: t, text, label }) => pillVars.push(
  `--pill-color-${i}: ${color}`,
  `--pill-tint-${i}: ${t}%`,
  `--pill-text-color-${i}: ${text}`,
  `--pill-label-color-${i}: ${label}`,
  `--_f${i}: var(--pill-fill-${i}, color-mix(in srgb, var(--pill-color-${i}) var(--pill-tint-${i}), var(--pill-base)))`,
  `--_r${i}: var(--pill-rim-${i}, ${borderColor || `color-mix(in srgb, var(--pill-color-${i}) var(--pill-rim), transparent)`})`));
for (let k = 1; k < N; k++) pillVars.push(
  `--_d${k}: var(--pill-divider-${k}, ${dividerColor || `color-mix(in srgb, var(--pill-color-${k + 1}) var(--pill-divider-strength), transparent)`})`);

/* per-section rules: color/text/label vars, icon side (the grid's area order — the label overlays and
   the canvas are untouched), and the two label slots (content: none = no slot) */
const perSection = secs.map(({ i, top, bottom, side: sd }) => `
.bubble-sub-button-bottom-container .bubble-sub-button-${i} { --_c: var(--pill-color-${i}); --_t: var(--pill-text-color-${i}); --_l: var(--pill-label-color-${i});${sd === 'right' ? ' grid-template-columns: 1fr minmax(0, auto) auto 1fr; grid-template-areas: ". text icon .";' : ''} }
.bubble-sub-button-bottom-container .bubble-sub-button-${i}::before { content: ${top ? cssStr(top) : 'none'}; }
.bubble-sub-button-bottom-container .bubble-sub-button-${i}::after  { content: ${bottom ? cssStr(bottom) : 'none'}; }`).join('');

return `
/* ===== DOM (Bubble 3.3, from a live card): the sub-buttons-card container .bubble-sub-buttons-container is
   the block that gives the card its height, and .bubble-sub-button-bottom-container (→ lane → group →
   .bubble-sub-button-N) holds the buttons. Bubble appends that row to content.firstChild.firstChild, so it
   is INSIDE the container when the container holds a <style> and its SIBLING when the container is empty —
   both happen with the same bundle. Nothing below assumes either: the pill vars are set on BOTH elements,
   button rules are scoped to the bottom container, and each paints its own pseudo-element canvas. ===== */
.bubble-sub-buttons-container.bubble-container,
.bubble-sub-buttons-container.bubble-container ~ .bubble-sub-button-bottom-container,
.bubble-sub-buttons-container.bubble-container .bubble-sub-button-bottom-container {
  ${pillVars.join(';\n  ')};
}
/* ===== the pill: its height is FIXED by --pill-height — never by --row-size. Bubble's editor auto-sizes
   \`rows\` from what it MEASURES (the bottom container), so a pill whose height followed \`rows\` would feed
   its own measurement: rows → taller pill → taller measurement → more rows, without end. ===== */
.bubble-sub-buttons-container.bubble-container {
  container-type: inline-size;
  position: relative;
  height: var(--pill-height) !important;
  min-height: 0 !important;
  background: none !important;
  border: none !important;
  border-radius: var(--pill-radius) !important;
  box-shadow: var(--pill-shadow, var(--bubble-sub-buttons-box-shadow, var(--bubble-box-shadow, none))) !important;
  overflow: clip;
}
/* ===== the canvas: the pill container's own ::before, under the buttons (the buttons sit in the bottom
   container, which paints above it whether it is a child or a sibling). A pseudo-element resolves cqw
   against its originating element, so the stop math above sees the pill width. ===== */
.bubble-sub-buttons-container.bubble-container::before {
  content: ""; position: absolute; inset: 0; z-index: 0; pointer-events: none; opacity: 1 !important;
  box-sizing: border-box;
  border: var(--pill-border-width) solid transparent;
  border-radius: var(--pill-radius);
  background:
    linear-gradient(var(--pill-angle), ${dividers}) padding-box,
    linear-gradient(var(--pill-angle), ${fills('f')}) padding-box,
    linear-gradient(var(--pill-angle), ${fills('r')}) border-box;
}
/* ===== Bubble's bottom sub-button row = the element its editor MEASURES to auto-size \`rows\`
   (rows = 1 + ceil(height - 40) / 64, i.e. it assumes 8px above and below the row). Keep it exactly
   16px shorter than the pill and independent of rows: the editor then lands on the rows that fit the
   pill in one step and stops. The buttons overflow it by 8px each way to fill the pill. ===== */
.bubble-sub-button-bottom-container {
  position: absolute !important; inset: 8px 0 !important; z-index: 1;
  width: auto !important; height: auto !important; min-height: 0 !important; max-height: none !important;
  margin: 0 !important; padding: 0 !important; gap: 0 !important;
  overflow: visible !important; background: none !important; border: none !important;
  container-type: inline-size;
  clip-path: inset(-8px 0 round var(--pill-radius));   /* the pill's rounded outline, even as a sibling of the pill */
  flex-direction: row !important; flex-wrap: nowrap !important;
  justify-content: stretch !important; align-items: stretch !important;
}
/* Bubble wraps bottom sub-buttons in an alignment lane and a group: make both a full-width, gap-less row */
.bubble-sub-button-bottom-container .bubble-sub-button-alignment-lane,
.bubble-sub-button-bottom-container .bubble-sub-button-group {
  display: flex !important; flex: 1 1 0% !important; flex-direction: row !important; flex-wrap: nowrap !important;
  width: 100% !important; max-width: none !important; min-width: 0 !important; height: 100% !important;
  gap: 0 !important; margin: 0 !important; padding: 0 !important; overflow: visible !important;
  justify-content: stretch !important; align-items: stretch !important;
}
/* ===== one section = one sub-button: an equal flex cell, a ONE-row grid for the data plus two overlays =====
     top label    (::before, from top_i)   — absolute, pinned to the cell's top edge
     icon | name · state · attribute       (Bubble's own elements, the grid's only row, centered in the
                                            FULL cell height; icon_side flips the row)
     bottom label (::after, from bottom_i) — absolute, pinned to the cell's bottom edge
   The labels are out of flow, so adding or removing one never moves the icon + state: the data sits at the
   same height in every section, labelled or not (v2.0.5 — before this the labels were grid rows and a
   bottom label lifted the data, a top label pushed it down).                                            */
.bubble-sub-button-bottom-container .bubble-sub-button {
  position: relative;
  flex: 1 1 0% !important; width: auto !important; min-width: 0 !important; max-width: none !important;
  height: calc(100% + 16px) !important; margin: -8px 0 !important; padding: 0 var(--pill-pad) !important;
  background: none !important; border-radius: 0 !important; box-shadow: none !important;
  transition: none !important; overflow: hidden;
  display: grid !important;
  /* 1fr spacers either side keep icon + text centered together */
  grid-template-columns: 1fr auto minmax(0, auto) 1fr;
  grid-template-rows: auto;
  grid-template-areas: ". icon text .";
  align-content: center; justify-content: stretch; align-items: center; justify-items: center;
  column-gap: var(--pill-icon-gap);
  font-size: var(--pill-font-size); font-weight: var(--pill-font-weight); line-height: 1.2;
  color: var(--_t);
}
.bubble-sub-button-bottom-container .bubble-sub-button:not(:has(.bubble-sub-button-icon)),
.bubble-sub-button-bottom-container .bubble-sub-button:has(.bubble-sub-button-name-container:empty) { column-gap: 0; }
.bubble-sub-button-bottom-container .bubble-sub-button > .bubble-feedback-container,
.bubble-sub-button-bottom-container .bubble-sub-button > ha-ripple { position: absolute; inset: 0; border-radius: 0; }
.bubble-sub-button-bottom-container .bubble-sub-button-icon {
  grid-area: icon; --mdc-icon-size: var(--pill-icon-size); color: var(--_c) !important; margin: 0 !important;
}
.bubble-sub-button-bottom-container .bubble-sub-button-name-container {
  grid-area: text; display: block !important; min-width: 0; max-width: 100%; margin: 0 !important;
  overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important;
  -webkit-line-clamp: unset !important; text-align: center;
}
/* The labels are absolute overlays on the cell (its containing block: the sub-button is position: relative)
   with NO grid placement, so they sit outside the track sizing entirely — their nowrap text can never widen
   the cell or push the icon and state apart (the v2.0.3 width fix, now structural; \`contain: inline-size\`
   stays as a belt-and-braces guard). Width = the cell minus its padding (left/right insets = --pill-pad),
   then the text ellipsizes inside its own section. Bubble's own \`.needs-outline::after\` (absolute, inset 0,
   an outline shadow) is overridden by the explicit insets and box-shadow below.                          */
.bubble-sub-button-bottom-container .bubble-sub-button::before,
.bubble-sub-button-bottom-container .bubble-sub-button::after {
  position: absolute; left: var(--pill-pad); right: var(--pill-pad); box-shadow: none; z-index: auto;
  pointer-events: none; grid-area: auto;
  /* justify-self: stretch — the grid's justify-items: center would otherwise apply to this positioned box too
     (both inline insets are set) and shrink it to its text; stretch fills left..right, then ellipsizes */
  display: block; contain: inline-size; justify-self: stretch; width: auto; min-width: 0; max-width: none; margin: 0;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  font-size: var(--pill-label-size); font-weight: var(--pill-label-weight); line-height: 1.15;
  letter-spacing: .03em; text-transform: var(--pill-label-transform); color: var(--_l); text-align: center;
}
.bubble-sub-button-bottom-container .bubble-sub-button::before { top: var(--pill-label-inset); bottom: auto; }
.bubble-sub-button-bottom-container .bubble-sub-button::after  { bottom: var(--pill-label-inset); top: auto; }
${perSection}
`;
'''.strip('\n')

CARD_CFG = r'''
/* ---------- knobs (same keys as the module editor) ----------
   Per-section knobs are `<name>_<i>`, i = the sub-button's 1-based position. Everything
   blank/absent = the entity's HA color (approximated) at the pill's default tint, no labels.
   Section count is NOT a knob: it follows the number of sub-buttons under `bottom:`.   */
const cfg = {
  /* --- whole pill --- */
  angle: 105,            /* 105 = "╱", 75 = "╲" (45–135 accepted)                */
  tint: 16,              /* default fill strength %                              */
  text_color: '',        /* hex, blank = theme --primary-text-color              */
  label_color: '',       /* hex, blank = theme --secondary-text-color            */
  label_transform: '',   /* '' | 'uppercase'                                     */
  scale: 1,              /* optional density knob: <1 tighter, >1 roomier        */
  icon_side: 'left',     /* 'left' | 'right' of the name/state; icon_side_i overrides per section */
  name_slot: '',         /* '' | 'top' | 'bottom': put each section's name on its own label row (name_slot_i overrides) */
  font_size: '', icon_size: '', label_size: '',   /* px; blank = scale with the cell width */
  font_weight: 600, label_weight: 500,
  height: '',            /* px; blank = Bubble's row height (56). Do not use rows: for this */
  radius: '',            /* px; blank = full pill                                */
  border_width: 1,       /* px rim line; 0 = none                                */
  border_color: '',      /* hex; blank = each section's own color at `rim` %     */
  rim: 55,               /* rim strength %                                       */
  divider_width: 2,      /* px; 0 = none                                         */
  divider_color: '',     /* hex; blank = the next section's color                */
  divider_strength: '',  /* %; blank = follows `tint`                            */
  /* --- section 1 --- */
  color_1: '',           /* fixed hex — wins over everything                     */
  mode_1: 'auto',        /* 'auto' inherit | 'active' | 'value'                  */
  active_color_1: '',    /* mode 'active': color while ON                        */
  low_1: '', high_1: '', low_color_1: '', mid_color_1: '', high_color_1: '',   /* mode 'value' */
  tint_1: '',            /* fixed % for this section                             */
  tint_mode_1: 'value',  /* 'value' = tint follows the dynamic number (brightness %) */
  tint_value_min_1: 0, tint_value_max_1: 100, tint_min_1: 5, tint_max_1: 60,
  text_color_1: '', label_color_1: '', icon_side_1: '', name_slot_1: '',
  top_1: 'Island',       /* labels: plain text or a ${ } JS template             */
  bottom_1: '${(attributes.brightness ?? 0) / 255 > .5 ? "bright" : "dim"}',
  /* --- section 2 --- */
  mode_2: 'value', low_2: 60, high_2: 78, low_color_2: '4dd0e1', high_color_2: 'db4437',
  top_2: 'Kitchen', bottom_2: '${state} ${attributes.unit_of_measurement ?? ""}',
  /* --- section 3 --- */
  mode_3: 'active', active_color_3: '2196f3',
  top_3: 'Motion', bottom_3: '${state === "on" ? "detected" : "clear"}',
  /* --- section 4 --- */
  color_4: 'ff9800', tint_4: 30,
  top_4: 'Heater',
};
'''.strip('\n')

def indent(s, n): return textwrap.indent(s, ' ' * n)

HEADER = r'''# =============================================================================
#  Segmented Pill (diagonal) — a Bubble Card mod   v__VERSION__
#  Bubble Card v3.3.0 + Bubble Card Tools.
#
#  One rounded pill split into diagonal sections, one per sub-button of a
#  "Sub-buttons only" card. Add a sub-button, get a section — any N.
#
#  Two forms below, same template (generated by gen_yaml.py):
#    A) a CARD with inline `styles:`  — paste into a card's YAML editor
#    B) the `__MODULE_ID__` MODULE   — Bubble Card ▸ Modules ▸ YAML, then
#       `modules: [__MODULE_ID__]` on a sub-buttons card
#
#  Per section (i = sub-button position): color_i / mode_i (blank = approximates
#  the entity's HA color; 'active' + active_color_i; 'value' + low_i / high_i
#  thresholds), tint_i / tint_mode_i, top_i / bottom_i labels (text or ${ } JS),
#  icon_side_i, name_slot_i, text_color_i, label_color_i.
#  Whole pill: angle, tint, icon_side, name_slot, text/label colors and sizes,
#  height, radius, border, rim, dividers. Every knob is in the module editor;
#  per-card overrides via the --pill-* CSS custom properties in `styles:`.
#
#  `${ }` templates are Bubble Card JS, not Jinja. Needs color-mix() and
#  container-query units (Chromium 111+ / Safari 16.2+ / Firefox 113+).
# =============================================================================


# -----------------------------------------------------------------------------
#  A) CARD — inline styles.  Example: FOUR sections — a color light (tint
#     follows brightness) ╱ kitchen temperature (thresholds) ╱ motion (blue
#     when detected) ╱ a heater switch (fixed orange) — with top + bottom
#     labels. Drop or add a sub-button under `bottom:` and the same card
#     renders 3 or 5 sections. Edit `cfg` for knobs.
# -----------------------------------------------------------------------------
type: custom:bubble-card
card_type: sub-buttons                 # "Sub-buttons only": every section is a sub-button
sub_button:
  bottom:                              # this card type renders `bottom` (its editor writes it)
    - entity: light.island_lights      # section 1
      icon: mdi:lightbulb
      show_icon: true
      show_state: false
      show_attribute: true             # show the DYNAMIC NUMBER: HA formats brightness as 0–100 %
      attribute: brightness
      show_background: false
      scrolling_effect: false
      tap_action:
        action: toggle
      hold_action:
        action: more-info
    - entity: sensor.kitchen_thermometer_temperature   # section 2
      icon: mdi:thermometer
      show_icon: true
      show_state: true
      show_background: false
      scrolling_effect: false
      tap_action:
        action: more-info
    - entity: binary_sensor.kitchen_motion             # section 3
      icon: mdi:motion-sensor
      show_icon: true
      show_state: false
      show_background: false
      scrolling_effect: false
      tap_action:
        action: more-info
    - entity: switch.heater                            # section 4
      icon: mdi:radiator
      show_icon: true
      show_state: true
      show_background: false
      scrolling_effect: false
      tap_action:
        action: toggle
styles: |
  ${(() => {
'''

MODULE_HEAD = r'''

---
# -----------------------------------------------------------------------------
#  B) MODULE — Bubble Card ▸ Modules ▸ YAML. Then, on a sub-buttons card:
#         modules: [__MODULE_ID__]
#         __MODULE_ID__:
#           tint: 20
#           top_1: Island              # labels: plain text …
#           bottom_1: '${(attributes.brightness ?? 0) / 255 > .5 ? "bright" : "dim"}'   # … or ${ } JS
#           tint_mode_1: value         # section 1 fill follows brightness
#           mode_2: value              # section 2 colored by thresholds
#           low_2: 62
#           high_2: 78
#           mode_3: active             # blue while motion is on, grey when clear
#           active_color_3: 2196f3
#           color_4: ff9800            # fixed
#     Four sub-buttons under `sub_button: bottom:` = four sections.
# -----------------------------------------------------------------------------
__MODULE_ID__:
  name: Segmented Pill (diagonal)
  version: '__VERSION__'
  creator: Anigeek
  supported:
    - sub-buttons
  description: |-
    <p>Turns a "Sub-buttons only" card into one rounded pill split into diagonal sections, one per sub-button. Add a sub-button, get a section — any number.</p>
    <ul>
      <li>Each section approximates its entity's HA state color by default (close to HA, not exact parity). Per section you can pin a hex, color by value with low/high thresholds, or use a custom color only while active.</li>
      <li>Fill strength (tint) is fixed or follows the entity's number, e.g. brightness.</li>
      <li>Top and bottom labels per section, plain text or <code>${ }</code> JS templates. Icons sit left or right of the text.</li>
      <li>Borders, rim, dividers, radius, height and type sizes are configurable; type scales to the space by default.</li>
    </ul>
    <p>Sub-buttons want <code>show_background: false</code> and <code>scrolling_effect: false</code>.</p>
  code: |-
    ${(() => {
      const cfg = this.config?.__MODULE_ID__ || {};
'''

def count_expr(n):
    """visible_if: the card has at least n sub-buttons (array, {bottom}, or {main} shape)."""
    return (f'((s) => Array.isArray(s) ? s.length : ((s?.bottom?.length) || (s?.main?.length) || 0))'
            f'(card?.sub_button) >= {n}')

def editor_section(n):
    has = count_expr(n)
    mode = f"card?.{MODULE_ID}?.mode_{n}"
    tmode = f"card?.{MODULE_ID}?.tint_mode_{n}"
    def field(name, label, sel, extra_vis=None, prefix=None):
        vis = has if extra_vis is None else f"{has} && {extra_vis}"
        out = f"    - name: {name}_{n}\n      label: {label}\n"
        if prefix: out += f"      prefix: '{prefix}'\n"
        out += f'      visible_if: "{vis}"\n      selector:\n{indent(sel, 8)}\n'
        return out
    TEXT = 'text: {}'
    NUM  = 'number:\n  mode: box\n  step: any'
    PCT  = 'number:\n  min: 0\n  max: 100\n  mode: box'
    return (f'    # ---- section {n} ----\n'
        + field('color', f"Section {n} color (hex, blank = follow the entity's HA color, approximated)", TEXT, prefix='#')
        + field('mode', f"Section {n} color source (when color is blank)",
                'select:\n  mode: dropdown\n  options:\n'
                "    - value: auto\n      label: Follow the entity's HA color, approximated (default)\n"
                "    - value: active\n      label: Custom color when ACTIVE, neutral when off\n"
                "    - value: value\n      label: By value — thresholds below")
        + field('active_color', f"Section {n} active color (hex, blank = HA's active color)", TEXT, f"{mode} === 'active'", prefix='#')
        + field('low',  f"Section {n} low threshold (≤ → low color)", NUM, f"{mode} === 'value'")
        + field('high', f"Section {n} high threshold (≥ → high color)", NUM, f"{mode} === 'value'")
        + field('low_color',  f"Section {n} low color (hex, blank = theme info)", TEXT, f"{mode} === 'value'", prefix='#')
        + field('mid_color',  f"Section {n} in-range color (hex, blank = theme palette by index)", TEXT, f"{mode} === 'value'", prefix='#')
        + field('high_color', f"Section {n} high color (hex, blank = theme error)", TEXT, f"{mode} === 'value'", prefix='#')
        + field('tint_mode', f"Section {n} tint (fill strength) source",
                'select:\n  mode: dropdown\n  options:\n'
                "    - value: fixed\n      label: Fixed (the pill's tint, or the % below)\n"
                "    - value: value\n      label: By value — follows brightness / % / position / reading")
        + field('tint', f"Section {n} tint % (blank = the pill's tint; in By-value mode = the top of the range)", PCT)
        + field('tint_value_min', f"Section {n} value at minimum tint (default 0)", NUM, f"{tmode} === 'value'")
        + field('tint_value_max', f"Section {n} value at maximum tint (default 100)", NUM, f"{tmode} === 'value'")
        + field('tint_min', f"Section {n} minimum tint % (default 5)", PCT, f"{tmode} === 'value'")
        + field('tint_max', f"Section {n} maximum tint % (default = tint above, else 60)", PCT, f"{tmode} === 'value'")
        + field('top',    f"Section {n} top label (text or ${{ }} JS template)", TEXT)
        + field('bottom', f"Section {n} bottom label (text or ${{ }} JS template)", TEXT)
        + field('icon_side', f"Section {n} icon side (blank = the pill's icon side)",
                'select:\n  mode: dropdown\n  options:\n'
                "    - value: ''\n      label: Pill default\n"
                "    - value: left\n      label: Left of the text\n"
                "    - value: right\n      label: Right of the text")
        + field('name_slot', f"Section {n} name row (blank = the pill's name row setting)",
                'select:\n  mode: dropdown\n  options:\n'
                "    - value: ''\n      label: Pill default\n"
                "    - value: none\n      label: No name row\n"
                "    - value: top\n      label: Name on the top row\n"
                "    - value: bottom\n      label: Name on the bottom row")
        + field('text_color',  f"Section {n} text color (hex, blank = pill text color)", TEXT, prefix='#')
        + field('label_color', f"Section {n} label color (hex, blank = pill label color)", TEXT, prefix='#'))

def expandable(name, title, icon, fields, visible_if=None):
    """One collapsible editor group (HA ha-form `type: expandable`, rendered by Bubble's module tab).
    `flatten: true` keeps the stored keys FLAT (the code reads cfg.angle / cfg.color_1, never a nested
    object); `expanded: false` = collapsed by default. `fields` is a 4-space-indented field list."""
    out = (f'    - type: expandable\n      name: {name}\n      title: {title}\n      icon: {icon}\n'
           f'      flatten: true\n      expanded: false\n')
    if visible_if: out += f'      visible_if: "{visible_if}"\n'
    return out + '      schema:\n' + indent(fields, 4)

# ---- whole pill: the two essentials stay top-level; everything else sits in collapsible groups ----
EDITOR_TOP = '''    - name: angle
      label: Divider direction
      selector:
        select:
          mode: dropdown
          options:
            - value: 105
              label: ╱  (105°)
            - value: 75
              label: ╲  (75°)
    - name: tint
      label: Default fill tint strength (%)
      selector:
        number:
          min: 0
          max: 100
          mode: box
'''

PILL_LAYOUT = '''    - name: icon_side
      label: Icon side (default for every section)
      selector:
        select:
          mode: dropdown
          options:
            - value: left
              label: Left of the text (default)
            - value: right
              label: Right of the text
    - name: name_slot
      label: Name row (each section's name on its own row; keep show_name off)
      selector:
        select:
          mode: dropdown
          options:
            - value: none
              label: None (default)
            - value: top
              label: Top row
            - value: bottom
              label: Bottom row
    - name: text_color
      label: Text color, all sections (hex, blank = theme text color)
      prefix: '#'
      selector:
        text: {}
    - name: label_color
      label: Label color, all sections (hex, blank = theme secondary text)
      prefix: '#'
      selector:
        text: {}
    - name: label_transform
      label: Label case
      selector:
        select:
          mode: dropdown
          options:
            - value: none
              label: As written
            - value: uppercase
              label: UPPERCASE
    - name: scale
      label: Size scale (1 = auto; <1 tighter, >1 roomier — optional)
      selector:
        number:
          min: 0.5
          max: 2
          step: 0.05
          mode: box
    - name: font_size
      label: State/name font size px (blank = scales with the section width)
      selector:
        number:
          mode: box
    - name: icon_size
      label: Icon size px (blank = scales with the section width)
      selector:
        number:
          mode: box
    - name: label_size
      label: Label font size px (blank = scales with the section width)
      selector:
        number:
          mode: box
    - name: font_weight
      label: State/name font weight (default 600)
      selector:
        number:
          min: 100
          max: 900
          step: 100
          mode: box
    - name: label_weight
      label: Label font weight (default 500)
      selector:
        number:
          min: 100
          max: 900
          step: 100
          mode: box
    - name: height
      label: Pill height px (blank = Bubble's row height; the editor sizes `rows` to fit)
      selector:
        number:
          mode: box
    - name: radius
      label: Corner radius px (blank = full pill)
      selector:
        number:
          mode: box
'''

PILL_BORDERS = '''    - name: border_width
      label: Border (rim) width px (default 1, 0 = none)
      selector:
        number:
          min: 0
          max: 8
          mode: box
    - name: border_color
      label: Border color (hex, blank = each section's own color)
      prefix: '#'
      selector:
        text: {}
    - name: rim
      label: Border (rim) strength % (default 55)
      selector:
        number:
          min: 0
          max: 100
          mode: box
    - name: divider_width
      label: Divider width px (default 2, 0 = none)
      selector:
        number:
          min: 0
          max: 8
          mode: box
    - name: divider_color
      label: Divider color (hex, blank = the next section's color)
      prefix: '#'
      selector:
        text: {}
    - name: divider_strength
      label: Divider strength % (blank = follows tint)
      selector:
        number:
          min: 0
          max: 100
          mode: box
'''

EDITOR_END = '''  author: Anigeek
'''

def editor():
    """The module editor: angle + tint top-level, then collapsible groups — two for the whole pill and one
    per section (v2.0.4). A flat wall of 141 fields made Bubble's visual editor crawl; ha-form only lays out
    an expandable's children once it is opened. The section groups carry the sub-button-count `visible_if`
    (as every field inside them already did) — see NOTES-v2.md v2.0.4 for what Bubble 3.3 does with it."""
    out = EDITOR_TOP
    out += expandable('pill_layout', 'Pill — layout & type', 'mdi:pill', PILL_LAYOUT)
    out += expandable('pill_borders', 'Pill — borders & dividers', 'mdi:border-outside', PILL_BORDERS)
    for n in range(1, EDITOR_SECTIONS + 1):
        out += expandable(f'section_{n}', f'Section {n}', f'mdi:numeric-{n}-box-outline',
                          editor_section(n), count_expr(n))
    return out + EDITOR_END

# =============================================================================================
#  PROTOTYPE — replica of Bubble's sub-buttons-card DOM + the base CSS the module overrides,
#  running SHARED verbatim. Each demo pill is scoped with CSS nesting (`#id { <module css> }`).
# =============================================================================================
PROTO_TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bubble segmented pill — prototype v__VERSION__ (sub-buttons card, generic N)</title>
<style>
  html, body { margin: 0; background: #2a2d33; font-family: Roboto, "Segoe UI", system-ui, sans-serif; }
  body { padding: 22px 26px; }
  .themes { display: flex; gap: 22px; align-items: flex-start; }
  /* Stand-ins for HA's theme variables — the pill only ever reads THESE. --state-* = HA's shipped defaults. */
  .theme { padding: 22px 24px 8px; border-radius: 12px; width: 740px;
           background: var(--primary-background-color); color: var(--primary-text-color);
    --amber-color: #ffc107; --cyan-color: #00bcd4; --purple-color: #926bc7; --light-blue-color: #03a9f4;
    --state-active-color: var(--amber-color);
    --state-light-active-color: var(--amber-color);
    --state-switch-active-color: var(--amber-color);
    --state-fan-active-color: var(--cyan-color);
    --state-cover-active-color: var(--purple-color);
    --state-media_player-active-color: var(--light-blue-color);
    --state-inactive-color: var(--state-icon-color);
    --state-unavailable-color: var(--disabled-text-color);
    --row-height: 56px; --row-size: 1; --row-gap: 8px;
  }
  .theme-dark {
    --primary-background-color: #111111; --card-background-color: #1c1c1c;
    --secondary-background-color: #202020;
    --primary-text-color: #e1e1e1; --secondary-text-color: #9b9b9b;
    --disabled-text-color: #6f6f6f; --state-icon-color: #9b9b9b;
    --primary-color: #03a9f4; --accent-color: #ff9800;
    --success-color: #4caf50; --warning-color: #ff9800; --error-color: #db4437; --info-color: #4dd0e1;
  }
  .theme-light {
    --primary-background-color: #fafafa; --card-background-color: #ffffff;
    --secondary-background-color: #e5e5e5;
    --primary-text-color: #212121; --secondary-text-color: #727272;
    --disabled-text-color: #bdbdbd; --state-icon-color: #44739e;
    --primary-color: #03a9f4; --accent-color: #ff9800;
    --success-color: #4caf50; --warning-color: #ff9800; --error-color: #db4437; --info-color: #4dd0e1;
  }
  h1 { font-size: 12px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase;
       color: var(--secondary-text-color); margin: 0 0 18px; }
  .row { display: flex; align-items: flex-start; gap: 14px; margin: 0 0 18px; }
  .row .label { width: 118px; flex: none; font-size: 11px; line-height: 1.4; color: var(--secondary-text-color); padding-top: 4px; }
  .row .label b { display: block; color: var(--primary-text-color); font-weight: 500; font-size: 12px; }
  .row .demo { display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
  .cap { font-size: 10px; line-height: 1.35; color: var(--secondary-text-color); margin-top: -4px; }

  /* ===== Bubble Card's OWN base CSS for a sub-buttons card (from the served v3.3 bundle) — the
     rules the module has to beat. Kept verbatim so the overrides are tested against reality. ===== */
  ha-card { display: block; position: relative; background: none; border-radius: 16px; box-shadow: none; }
  .bubble-sub-button.background-on { background-color: var(--bubble-sub-button-light-background-color, #4caf50); }
  .bubble-sub-button.background-off { background-color: var(--bubble-sub-button-background-color, rgba(255,255,255,.1)); }
  .bubble-sub-button-name-container[style*="-webkit-box"] { line-height: 1.1; }
  ha-card .card-content { padding: 0; }
  .bubble-container { position: relative; width: 100%; height: 50px;
    background-color: var(--bubble-sub-buttons-main-background-color, var(--bubble-main-background-color, var(--background-color-2, var(--secondary-background-color))));
    border-radius: var(--bubble-sub-buttons-border-radius, var(--bubble-border-radius, calc(var(--row-height,56px)/2)));
    box-shadow: var(--bubble-sub-buttons-box-shadow, var(--bubble-box-shadow, none));
    overflow: hidden; overflow: clip; touch-action: auto; border: var(--bubble-sub-buttons-border, var(--bubble-border, none)); box-sizing: border-box; }
  .large .bubble-container { height: calc( var(--row-height,56px) * var(--row-size,1) + var(--row-gap,8px) * ( var(--row-size,1) - 1 )); }
  .bubble-container.with-bottom-buttons { align-items: flex-start; }
  .bubble-sub-button-container { position: relative; display: flex; justify-content: var(--bubble-sub-button-justify-content, end); inset-inline-end: 8px; align-content: center; gap: 8px; align-items: center; }
  .bubble-sub-button-container.fixed-top { align-self: flex-start; margin-top: 10px; }
  .bubble-sub-button-bottom-container { position: absolute; display: flex; justify-content: var(--bubble-sub-button-justify-content, end); bottom: 0; width: calc(100% - 16px); margin: 0 8px 8px 8px; gap: 8px; pointer-events: none; flex-wrap: nowrap; }
  .bubble-sub-button-bottom-container.alignment-lanes-active { justify-content: flex-start; }
  .bubble-sub-button-bottom-container > * { pointer-events: auto; }
  .bubble-sub-button-bottom-container .bubble-sub-button-group { pointer-events: none; flex: 0 0 auto; min-width: 0; }
  .bubble-sub-button-bottom-container .bubble-sub-button-group > * { pointer-events: auto; }
  .bubble-sub-button-bottom-container .bubble-sub-button-group.alignment-fill { flex: 1 1 0%; }
  .bubble-sub-button-alignment-lane { display: flex; flex-wrap: nowrap; gap: 8px; align-items: center; }
  .bubble-sub-button-alignment-lane.lane-fill { flex: 1 1 100%; width: 100%; min-width: 0; justify-content: flex-start; }
  .bubble-sub-button-alignment-lane.lane-expand { flex: 1 1 0%; min-width: 0; }
  .bubble-sub-button-group { display: flex; position: relative; gap: 8px; align-items: center; width: 100%; }
  .bubble-sub-button-group.display-inline { flex-direction: row; justify-content: var(--bubble-sub-button-group-justify-content, end); }
  .bubble-sub-button-group.group-layout-inline > .bubble-sub-button { width: auto; }
  .bubble-sub-button { display: flex; flex-wrap: nowrap; flex-direction: row-reverse; align-items: center; justify-content: center; position: relative; inset-inline-end: 0; box-sizing: border-box; width: max-content; min-width: 36px; height: var(--bubble-sub-button-height, 36px); vertical-align: middle; font-size: 12px; border-radius: var(--bubble-sub-button-border-radius, var(--bubble-border-radius, 18px)); padding: 0 8px; white-space: nowrap; transition: all 0.5s ease-in-out; color: var(--primary-text-color); }
  .bubble-sub-button.fill-width { flex: 1 1 0%; }
  .bubble-sub-button-name-container { display: flex; overflow: auto; }
  .bubble-sub-button-icon { flex-shrink: 0; }
  .bubble-sub-button-icon.icon-with-state { margin-inline-end: 4px; }
  .show-icon { display: flex; --mdc-icon-size: 16px; }
  .bubble-sub-button.needs-outline::after { content: ""; position: absolute; inset: 0; z-index: 2; pointer-events: none; border-radius: inherit; box-shadow: var(--bubble-sub-button-outline, inset 0 0 0 1px rgba(var(--rgb-primary-text-color, 0, 0, 0), 0.2)); }
  .bubble-feedback-container { position: absolute; inset: 0; pointer-events: none; }
  /* stand-in for <ha-icon>: an SVG the size of --mdc-icon-size, painted in currentColor */
  svg.bubble-sub-button-icon { width: var(--mdc-icon-size, 24px); height: var(--mdc-icon-size, 24px); fill: currentColor; display: block; }
</style>
</head>
<body>

<!-- SVG glyphs = Material Design Icons paths (what mdi:* renders in HA) -->
<svg width="0" height="0" style="position:absolute">
  <symbol id="i-thermo" viewBox="0 0 24 24"><path d="M15 13V5A3 3 0 0 0 9 5V13A5 5 0 1 0 15 13M12 4A1 1 0 0 1 13 5V8H11V5A1 1 0 0 1 12 4Z"/></symbol>
  <symbol id="i-humid" viewBox="0 0 24 24"><path d="M12,3.25C12,3.25 6,10 6,14C6,17.32 8.69,20 12,20A6,6 0 0,0 18,14C18,10 12,3.25 12,3.25M14.47,9.97L15.53,11.03L9.53,17.03L8.47,15.97M9.75,10A1.25,1.25 0 0,1 11,11.25A1.25,1.25 0 0,1 9.75,12.5A1.25,1.25 0 0,1 8.5,11.25A1.25,1.25 0 0,1 9.75,10M14.25,14.5A1.25,1.25 0 0,1 15.5,15.75A1.25,1.25 0 0,1 14.25,17A1.25,1.25 0 0,1 13,15.75A1.25,1.25 0 0,1 14.25,14.5Z"/></symbol>
  <symbol id="i-gauge" viewBox="0 0 24 24"><path d="M12,16A3,3 0 0,1 9,13C9,11.88 9.61,10.9 10.5,10.39L20.21,4.77L14.68,14.35C14.18,15.33 13.17,16 12,16M12,3C13.81,3 15.5,3.5 16.97,4.32L14.87,5.53C14,5.19 13,5 12,5A8,8 0 0,0 4,13C4,15.21 4.89,17.21 6.34,18.65H6.35C6.74,19.04 6.74,19.67 6.35,20.06C5.96,20.45 5.32,20.45 4.93,20.07V20.07C3.12,18.26 2,15.76 2,13A10,10 0 0,1 12,3M22,13C22,15.76 20.88,18.26 19.07,20.07V20.07C18.68,20.45 18.05,20.45 17.66,20.06C17.27,19.67 17.27,19.04 17.66,18.65V18.65C19.11,17.2 20,15.21 20,13C20,12 19.81,11 19.46,10.1L20.67,8C21.5,9.5 22,11.18 22,13Z"/></symbol>
  <symbol id="i-bulb" viewBox="0 0 24 24"><path d="M12,2A7,7 0 0,0 5,9C5,11.38 6.19,13.47 8,14.74V17A1,1 0 0,0 9,18H15A1,1 0 0,0 16,17V14.74C17.81,13.47 19,11.38 19,9A7,7 0 0,0 12,2M9,21A1,1 0 0,0 10,22H14A1,1 0 0,0 15,21V20H9V21Z"/></symbol>
  <symbol id="i-fan" viewBox="0 0 24 24"><path d="M12,11A1,1 0 0,0 11,12A1,1 0 0,0 12,13A1,1 0 0,0 13,12A1,1 0 0,0 12,11M12.5,2C17,2 17.11,5.57 14.75,6.75C13.76,7.24 13.32,8.29 13.13,9.22C13.61,9.42 14.03,9.73 14.35,10.13C18.05,8.13 22.03,8.92 22.03,12.5C22.03,17 18.46,17.1 17.28,14.73C16.78,13.74 15.72,13.3 14.79,13.11C14.59,13.59 14.28,14 13.88,14.34C15.87,18.03 15.08,22 11.5,22C7,22 6.91,18.42 9.27,17.24C10.25,16.75 10.69,15.71 10.89,14.79C10.4,14.59 9.97,14.27 9.65,13.87C5.96,15.85 2,15.07 2,11.5C2,7 5.56,6.89 6.74,9.26C7.24,10.25 8.29,10.68 9.22,10.87C9.41,10.39 9.73,9.97 10.14,9.65C8.15,5.96 8.94,2 12.5,2Z"/></symbol>
  <symbol id="i-lamp" viewBox="0 0 24 24"><path d="M8,2H16L20,14H4L8,2M11,15H13V20H18V22H6V20H11V15Z"/></symbol>
  <symbol id="i-motion" viewBox="0 0 24 24"><path d="M12,4A4,4 0 0,1 16,8A4,4 0 0,1 12,12A4,4 0 0,1 8,8A4,4 0 0,1 12,4M12,14C16.42,14 20,15.79 20,18V20H4V18C4,15.79 7.58,14 12,14Z"/></symbol>
  <symbol id="i-door" viewBox="0 0 24 24"><path d="M8,3C6.89,3 6,3.89 6,5V21H18V5C18,3.89 17.11,3 16,3H8M8,5H16V19H8V5M13,11V13H15V11H13Z"/></symbol>
  <symbol id="i-garage" viewBox="0 0 24 24"><path d="M22,9V20H20V11H4V20H2V9L12,5L22,9M19,12H5V14H19V12M19,18H5V20H19V18M19,15H5V17H19V15Z"/></symbol>
  <symbol id="i-radiator" viewBox="0 0 24 24"><path d="M3.5,3H5.5V5H3.5V3M7.5,3H9.5V5H7.5V3M11.5,3H13.5V5H11.5V3M15.5,3H17.5V5H15.5V3M19.5,3H21.5V5H19.5V3M3,7H21V17H3V7M5,9V15H7V9H5M9,9V15H11V9H9M13,9V15H15V9H13M17,9V15H19V9H17M4,19H20V21H4V19Z"/></symbol>
  <symbol id="i-battery" viewBox="0 0 24 24"><path d="M16,20H8V6H16M16.67,4H15V2H9V4H7.33A1.33,1.33 0 0,0 6,5.33V20.67C6,21.4 6.6,22 7.33,22H16.67A1.33,1.33 0 0,0 18,20.67V5.33C18,4.6 17.4,4 16.67,4Z"/></symbol>
  <symbol id="i-power" viewBox="0 0 24 24"><path d="M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M13,3H11V13H13"/></symbol>
</svg>

<div class="themes">
  <div class="theme theme-dark"><h1>HA default dark theme</h1></div>
  <div class="theme theme-light"><h1>HA default light theme</h1></div>
</div>

<script>
// Fake hass — shapes copied from live HA entities (read-only).
const hass = {
  states: {
    'light.island_lights':      { entity_id:'light.island_lights', state: 'on',  attributes: { rgb_color: [170, 85, 255], hs_color: [270, 66.667], brightness: 128, color_mode: 'rgb', friendly_name: 'Island' } },
    'light.living_room_front':  { entity_id:'light.living_room_front', state: 'on',  attributes: { rgb_color: [255, 255, 251], hs_color: [54.768, 1.6], brightness: 255, color_mode: 'color_temp', friendly_name: 'Front' } },
    'light.dim':                { entity_id:'light.dim', state: 'on',  attributes: { rgb_color: [170, 85, 255], brightness: 26, friendly_name: 'Dim' } },
    'light.office_lamp':        { entity_id:'light.office_lamp', state: 'off', attributes: { friendly_name: 'Lamp' } },
    'fan.living_room_fan':      { entity_id:'fan.living_room_fan', state: 'on',  attributes: { percentage: 66, friendly_name: 'Fan' } },
    'fan.basement_fan':         { entity_id:'fan.basement_fan', state: 'off', attributes: { friendly_name: 'Fan' } },
    'binary_sensor.motion_on':   { entity_id:'binary_sensor.motion_on', state: 'on',  attributes: { device_class: 'motion', friendly_name: 'Motion' } },
    'binary_sensor.motion_off':  { entity_id:'binary_sensor.motion_off', state: 'off', attributes: { device_class: 'motion', friendly_name: 'Motion' } },
    'binary_sensor.door_open':   { entity_id:'binary_sensor.door_open', state: 'on',  attributes: { device_class: 'door', friendly_name: 'Door' } },
    'binary_sensor.door_closed': { entity_id:'binary_sensor.door_closed', state: 'off', attributes: { device_class: 'door', friendly_name: 'Door' } },
    'cover.garage':             { entity_id:'cover.garage', state: 'open', attributes: { current_position: 40, friendly_name: 'Garage' } },
    'switch.heater':            { entity_id:'switch.heater', state: 'on', attributes: { friendly_name: 'Heater' } },
    'sensor.kitchen_thermometer_temperature': { entity_id:'sensor.kitchen_thermometer_temperature', state: '61.016', attributes: { unit_of_measurement: '°F', device_class: 'temperature', friendly_name: 'Kitchen' } },
    'sensor.kitchen_thermometer_humidity':    { entity_id:'sensor.kitchen_thermometer_humidity', state: '53.02',  attributes: { unit_of_measurement: '%',  device_class: 'humidity', friendly_name: 'Kitchen' } },
    'sensor.pressure':          { entity_id:'sensor.pressure', state: '1012', attributes: { unit_of_measurement: 'hPa', device_class: 'pressure', friendly_name: 'Pressure' } },
    'sensor.battery':           { entity_id:'sensor.battery', state: '42', attributes: { unit_of_measurement: '%', device_class: 'battery', friendly_name: 'Battery' } },
    'sensor.power':             { entity_id:'sensor.power', state: '318', attributes: { unit_of_measurement: 'W', device_class: 'power', friendly_name: 'Power' } },
    'sensor.unavail':           { entity_id:'sensor.unavail', state: 'unavailable', attributes: { friendly_name: 'Gone' } },
  },
  formatEntityState: (so) => ({ on: 'On', off: 'Off', open: 'Open', closed: 'Closed' })[so.state] ?? so.state,
};

// ======= VERBATIM module body (gen_yaml.py SHARED) — `this` = the card, exactly as Bubble applies it =======
const CFG_LINE = __CFG_LINE__;
const SHARED = __SHARED__;
const pillCss = new Function('hass', CFG_LINE + '\n' + SHARED);
// ======= end verbatim =======

const ICON = { light: 'i-bulb', fan: 'i-fan', binary_sensor: 'i-motion', cover: 'i-garage', switch: 'i-radiator', sensor: 'i-thermo' };
const iconFor = (b) => b.icon ? b.icon : (ICON[(b.entity || '').split('.')[0]] || 'i-gauge');
// what Bubble's own name container shows: name · state · attribute, joined by " · "
const midText = (b) => {
  const so = hass.states[b.entity]; if (!so) return b.show_state === false ? '' : 'Unavailable';
  const parts = [];
  if (b.show_name) parts.push(b.name ?? so.attributes.friendly_name);
  if (b.show_state) parts.push(hass.formatEntityState(so));
  if (b.show_attribute && b.attribute) {
    const v = so.attributes[b.attribute];
    parts.push(b.attribute === 'brightness' ? Math.round(v / 255 * 100) + ' %' : String(v));
  }
  return parts.join(' · ');
};
let uid = 0;
// Replica of the real DOM: ha-card > .card-content.large > .bubble-sub-buttons-container.bubble-container.with-bottom-buttons
//   > .bubble-sub-button-container.fixed-top (empty main row) + .bubble-sub-button-bottom-container > lane > group > .bubble-sub-button-k
function pill(config, width) {
  const id = 'p' + (++uid);
  const subs = config.sub_button.bottom;
  const btn = (b, k) => `<div class="bubble-sub-button bubble-sub-button-${k + 1} fill-width ${k % 2 ? 'background-off' : 'background-on'} bubble-action bubble-action-enabled" style="--bubble-sub-button-light-background-color: rgb(66, 214, 72);">
      <div class="bubble-feedback-container"><div class="bubble-feedback-element feedback-element"></div></div>
      <div class="bubble-sub-button-name-container" style="white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: ellipsis; overflow: hidden;">${midText(b)}</div>
      ${b.show_icon === false ? '' : `<svg class="bubble-sub-button-icon show-icon icon-with-state"><use href="#${iconFor(b)}"/></svg>`}
    </div>`;
  // Ground truth (captured from a live card, 2026-09-06): the container is EMPTY and the bottom row is its
  // SIBLING. Bubble attaches the row to content.firstChild.firstChild, so the same bundle also yields the
  // nested shape when the container holds a <style>; the module's selectors must work for both.
  const html = `<ha-card id="${id}" style="width:${width}px"><div class="card-content large" style="padding: 0px;">
    <div class="bubble-sub-buttons-container bubble-container with-bottom-buttons" style="--row-size: 1;"></div>
    <div class="bubble-sub-button-bottom-container alignment-lanes-active groups-layout-inline">
      <div class="bubble-sub-button-alignment-lane lane-fill lane-expand" data-lane="fill" style="order: 3;">
        <div class="bubble-sub-button-group position-bottom display-inline group-layout-inline alignment-fill" data-group-id="g_bottom_auto" data-lane-needs-fill="true">
          ${subs.map(btn).join('')}
        </div></div></div></div></ha-card>`;
  const css = pillCss.call({ config }, hass);
  return { html, css: `#${id} {\n${css}\n}` };   // native CSS nesting scopes the module's selectors to this pill
}
function row(title, note, pills, caps) {
  const wrap = document.createElement('div'); wrap.className = 'row';
  const demo = pills.map((p, i) => p.html + (caps && caps[i] ? `<div class="cap">${caps[i]}</div>` : '')).join('');
  wrap.innerHTML = `<div class="label"><b>${title}</b>${note}</div><div class="demo">${demo}</div>`;
  const style = document.createElement('style'); style.textContent = pills.map(p => p.css).join('\n');
  wrap.prepend(style);
  return wrap;
}
const SB = (entity, extra = {}) => ({ entity, show_icon: true, show_state: true, show_background: false, scrolling_effect: false, ...extra });
const rows = () => [
  row('1 · Two, inherited', 'light ╱ fan, the bedroom look:<br>angle 75, tint 20, yellow text',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan')] },
             segmented_pill: { angle: 75, tint: 20, text_color: 'F1F519' } }, 194),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.basement_fan')] },
             segmented_pill: { angle: 75, tint: 20, text_color: 'F1F519' } }, 194) ],
    ['fan on', 'fan off → inactive grey; divider = section 2 color']),
  row('2 · Three, mode: active', 'motion trio (hallway card): cyan while detected, neutral when clear; no labels',
    [ pill({ sub_button: { bottom: [SB('binary_sensor.motion_on', { show_state: false }), SB('binary_sensor.motion_off', { show_state: false }), SB('binary_sensor.door_open', { show_state: false })] },
             segmented_pill: { tint: 40, angle: 75, mode_1: 'active', active_color_1: '00BCD5', mode_2: 'active', active_color_2: '00BCD5', mode_3: 'active', active_color_3: '00BCD5' } }, 300) ]),
  row('3 · Four — the example', 'card A config: tint by brightness ╱ thresholds ╱ active ╱ fixed; top + templated bottom labels',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('sensor.kitchen_thermometer_temperature'), SB('binary_sensor.motion_on', { show_state: false }), SB('switch.heater')] },
             segmented_pill: __CARD_CFG__ }, 396),
      pill({ sub_button: { bottom: [SB('light.dim', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('sensor.kitchen_thermometer_temperature'), SB('binary_sensor.motion_off', { show_state: false }), SB('switch.heater')] },
             segmented_pill: Object.assign({}, __CARD_CFG__, { low_2: 55, high_2: 60 }) }, 396) ],
    ['light 50 % (128/255 = 50.2 %) → tint 33 %, label "bright" (> 50 %); temp in range; motion detected', 'light 10 % → tint 10 %; temp ≥ high → red; motion clear → grey']),
  row('4 · Five, uppercase labels', 'value thresholds + inherited, label_transform: uppercase, scale 1',
    [ pill({ sub_button: { bottom: [SB('sensor.kitchen_thermometer_temperature'), SB('sensor.kitchen_thermometer_humidity'), SB('sensor.pressure'), SB('sensor.battery'), SB('cover.garage', { show_state: false, show_attribute: true, attribute: 'current_position' })] },
             segmented_pill: { label_transform: 'uppercase', mode_1: 'value', low_1: 60, high_1: 78, mode_2: 'value', low_2: 30, high_2: 60, low_color_2: 'ff9800', high_color_2: 'ff9800',
               top_1: 'Temp', top_2: 'Humidity', top_3: 'Pressure', top_4: 'Battery', top_5: 'Garage',
               bottom_1: '${state > 70 ? "warm" : "cool"}', bottom_5: '${state}' } }, 520) ]),
  row('5 · Six', 'six sections; type scales down with the cell width — at 396 (phone/section) vs 700 (roomy)',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan', { show_state: false, show_attribute: true, attribute: 'percentage' }), SB('sensor.kitchen_thermometer_temperature'), SB('sensor.kitchen_thermometer_humidity'), SB('binary_sensor.door_open'), SB('sensor.power')] },
             segmented_pill: { tint: 22, top_1: 'Island', top_2: 'Fan', top_3: 'Temp', top_4: 'Humidity', top_5: 'Door', top_6: 'Power', mode_3: 'value', low_3: 60, high_3: 78, mode_6: 'value', high_6: 300 } }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan', { show_state: false, show_attribute: true, attribute: 'percentage' }), SB('sensor.kitchen_thermometer_temperature'), SB('sensor.kitchen_thermometer_humidity'), SB('binary_sensor.door_open'), SB('sensor.power')] },
             segmented_pill: { tint: 22, top_1: 'Island', top_2: 'Fan', top_3: 'Temp', top_4: 'Humidity', top_5: 'Door', top_6: 'Power', mode_3: 'value', low_3: 60, high_3: 78, mode_6: 'value', high_6: 300, bottom_6: '${state} W' } }, 592) ]),
  row('6 · Borders', 'border_width 2 · border_color fixed · divider 3px white · radius 12 · rim 80',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan'), SB('light.living_room_front', { show_state: false, show_attribute: true, attribute: 'brightness' })] },
             segmented_pill: { border_width: 2, border_color: '8899aa', divider_width: 3, divider_color: 'ffffff', divider_strength: 35, radius: 12, rim: 80, tint: 28 } }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan'), SB('light.living_room_front', { show_state: false, show_attribute: true, attribute: 'brightness' })] },
             segmented_pill: { border_width: 0, divider_width: 0, tint: 28 } }, 396) ],
    ['', 'border_width 0 · divider_width 0 → fills only']),
  row('7 · Tint by value', 'three lights at 10 / 50 / 100 % — fill strength follows brightness (tint_mode: value, 5–60 %)',
    [ pill({ sub_button: { bottom: [SB('light.dim', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('light.living_room_front', { show_state: false, show_attribute: true, attribute: 'brightness' })] },
             segmented_pill: { tint_mode_1: 'value', tint_mode_2: 'value', tint_mode_3: 'value', color_1: 'aa55ff', color_2: 'aa55ff', color_3: 'aa55ff', bottom_1: 'dim', bottom_2: 'half', bottom_3: 'full' } }, 396) ]),
  row('9 · icon_side', 'global icon_side: right (labels stay put) · per-section: icon_side_2: left overrides the global right',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('sensor.kitchen_thermometer_temperature'), SB('binary_sensor.motion_on', { show_state: false }), SB('switch.heater')] },
             segmented_pill: Object.assign({}, __CARD_CFG__, { icon_side: 'right' }) }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan'), SB('sensor.kitchen_thermometer_temperature')] },
             segmented_pill: { tint: 22, icon_side: 'right', icon_side_2: 'left' } }, 396) ],
    ['icon_side: right — the sketch\'s icon-right-of-value', 'icon_side: right + icon_side_2: left (mixed)']),
  row('10 · Long labels (fix A)', 'a label longer than its section ellipsizes INSIDE the section; icon + state stay together; N = 2 / 4 / 6',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan')] },
             segmented_pill: { top_1: 'looooooooooooooooooooooooooooooooooooooooooooooooong', bottom_2: 'this bottom label is also far too long for its section' } }, 300),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('sensor.kitchen_thermometer_temperature'), SB('binary_sensor.motion_on', { show_state: false }), SB('switch.heater')] },
             segmented_pill: Object.assign({}, __CARD_CFG__, { top_1: 'Island pendant lights over the counter', bottom_3: 'motion detected in the kitchen a moment ago' }) }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan', { show_state: false, show_attribute: true, attribute: 'percentage' }), SB('sensor.kitchen_thermometer_temperature'), SB('sensor.kitchen_thermometer_humidity'), SB('binary_sensor.door_open'), SB('sensor.power')] },
             segmented_pill: { tint: 22, top_1: 'Island pendant', top_2: 'Living room ceiling fan', top_3: 'Temperature', top_4: 'Relative humidity', top_5: 'Front door', top_6: 'Whole-house power draw', bottom_6: '${state} W' } }, 396) ]),
  row('11 · Name + state stacked (fix B)', 'name_slot: top — the name on its own row, state in the middle (keep show_name off) · name_slot: bottom · for comparison: Bubble\'s own show_name (one line, "Fan · On")',
    [ pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan'), SB('binary_sensor.door_open')] },
             segmented_pill: { tint: 20, name_slot: 'top' } }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan', { name: 'Ceiling fan' }), SB('binary_sensor.door_open')] },
             segmented_pill: { tint: 20, name_slot: 'bottom', name_slot_3: 'top', top_1: 'Kitchen' } }, 396),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_name: true, show_state: false, show_attribute: true, attribute: 'brightness' }), SB('fan.living_room_fan', { show_name: true }), SB('binary_sensor.door_open', { show_name: true })] },
             segmented_pill: { tint: 20 } }, 396) ],
    ['name_slot: top', 'name_slot: bottom · section 2 uses its sub-button name "Ceiling fan" · name_slot_3: top · top_1 explicit wins', 'show_name: true (Bubble joins "Name · State" on one line — unchanged)']),
  row('12 · Anchored labels (v2.0.5)', 'the same fan in four sections — no label · top only · bottom only · both: the icon + state sit at the SAME height in all four; labels float at the edges and never move the data',
    [ pill({ sub_button: { bottom: [SB('fan.living_room_fan'), SB('fan.living_room_fan'), SB('fan.living_room_fan'), SB('fan.living_room_fan')] },
             segmented_pill: { tint: 22, top_2: 'top label', bottom_3: 'bottom label', top_4: 'top label', bottom_4: 'bottom label' } }, 396),
      pill({ sub_button: { bottom: [SB('fan.living_room_fan'), SB('fan.living_room_fan'), SB('fan.living_room_fan'), SB('fan.living_room_fan')] },
             segmented_pill: { tint: 22, scale: 1.4, height: 88, icon_side: 'right', top_2: 'top label', bottom_3: 'bottom label', top_4: 'top label', bottom_4: 'bottom label' } }, 396) ],
    ['none · top · bottom · both — 56px pill', 'the same at height 88 · scale 1.4 · icon_side right']),
  row('8 · Edge cases', 'one section · icon-only · unavailable entity · scale 1.4 with rows: 2 height',
    [ pill({ sub_button: { bottom: [SB('fan.living_room_fan')] }, segmented_pill: { top_1: 'Just one' } }, 194),
      pill({ sub_button: { bottom: [SB('light.island_lights', { show_state: false }), SB('fan.living_room_fan', { show_state: false }), SB('sensor.unavail', { show_state: false }), SB('light.office_lamp', { show_state: false })] }, segmented_pill: { tint: 30 } }, 240),
      pill({ sub_button: { bottom: [SB('sensor.kitchen_thermometer_temperature'), SB('sensor.kitchen_thermometer_humidity')] },
             segmented_pill: { scale: 1.4, height: 88, top_1: 'Temperature', top_2: 'Humidity', bottom_1: 'kitchen', bottom_2: 'kitchen', mode_1: 'value', low_1: 60, high_1: 78, mode_2: 'value', low_2: 30, high_2: 60, low_color_2: 'ff9800', high_color_2: 'ff9800' } }, 396) ]),
];
document.querySelectorAll('.theme').forEach(t => rows().forEach(r => t.appendChild(r)));
</script>
</body>
</html>
'''

def build():
    out = HEADER + indent(CARD_CFG, 4) + '\n\n' + indent(SHARED, 4) + '\n  })()}\n'
    out += MODULE_HEAD + indent(SHARED, 6) + '\n    })()}\n  editor:\n'
    out += editor()
    out = out.replace('__MODULE_ID__', MODULE_ID).replace('__VERSION__', VERSION)
    open(os.path.join(HERE, 'bubble-pill-mod.yaml'), 'w').write(out)
    print('bubble-pill-mod.yaml', len(out), 'module id', MODULE_ID, 'version', VERSION)

    # the prototype gets the module-form cfg line and SHARED as JSON string literals (verbatim)
    cfg_obj = CARD_CFG[CARD_CFG.index('const cfg = ') + len('const cfg = '):].rstrip().rstrip(';')
    proto = (PROTO_TEMPLATE
             .replace('__CFG_LINE__', json.dumps('const cfg = this.config?.' + MODULE_ID + ' || {};'))
             .replace('__SHARED__', json.dumps(SHARED))
             .replace('__CARD_CFG__', '(' + cfg_obj + ')')
             .replace('__VERSION__', VERSION))
    open(os.path.join(HERE, 'prototype.html'), 'w').write(proto)
    print('prototype.html', len(proto))

if __name__ == '__main__':
    build()
