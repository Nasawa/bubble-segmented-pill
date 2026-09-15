# Bubble Card internals worth knowing

Notes for anyone building on Segmented Pill or writing their own Bubble Card module. Each of these bit
during this module's build, and each is easy to regress.

- **Sibling-DOM structure.** On a *real* Bubble sub-buttons card the buttons do **not** nest under
  `.bubble-sub-buttons-container` — that container renders **empty**, and the buttons live in
  `.bubble-sub-button-bottom-container`, its **sibling** (Bubble attaches the row to
  `content.firstChild.firstChild`). Every button rule is rooted at `.bubble-sub-button-bottom-container`,
  with the `--pill-*` vars mirrored onto it and its own `container-type`. Descendant selectors rooted at
  `.bubble-sub-buttons-container` silently match nothing on the live card.
- **`card_type: sub-buttons` renders only `sub_button.bottom`.** An array, or `sub_button.main`, renders
  nothing. Sections *are* the bottom sub-buttons. (The Bubble 3.3 editor may store `sub_button` as
  `{main:[...], bottom:[...]}` rather than an array — the resolver handles both.)
- **The editor auto-rows loop.** Bubble's card editor runs `_computeAndApplyRows` — a `ResizeObserver`
  that sets `rows = 1 + ceil((h-40)/64)` and fires config-changed. If the pill's height follows
  `--row-size` and its bottom container is stretched to the pill, each pass grows it until the tab dies.
  The fix keeps the pill height off `--row-size` and pins the bottom container to `inset: 8px 0`
  (= pill − 16, what the formula assumes), buttons overflowing ±8px, gradients on the pill's `::before`.
- **Absolute-overlay labels.** Top/bottom labels are `position: absolute` overlays *out* of the grid
  flow, so adding/removing a label does not shift the icon/state. The width `contain: inline-size` is
  structural so labels never size the tracks.
- **`visible_if` only works inside object selectors.** Bubble module-editor fields render through HA
  `ha-form`, which does **not** honor `visible_if`. The editor groups fields into `type: expandable`
  accordions instead (which must carry `flatten: true`, or ha-form nests the values and the runtime never
  sees them).
- **Name and state are one text node.** Bubble concats them (`[name, state, …].join(" · ")`), so they are
  not separately targetable — hence the optional `name_slot` label row.
- **Templating is `${ }` JavaScript, not Jinja.** A `${}` label can't do live relative time (the module
  only re-renders on a hass state change) — use Bubble's native `show_last_changed: true` or an additive
  relative-time module.
