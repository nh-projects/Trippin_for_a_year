# Mobile-responsive collapsible sidebar for world-map.html

## Changes to `world-map.template.html`

### 1. CSS — Add toggle button base style (hidden on desktop)

After line 35 (`.legend-dot` rule), before the media query:
```css
.sidebar-toggle { display: none; }
```

### 2. CSS — Replace the existing media query on line 36

**Old:**
```css
@media (max-width: 700px) { body { flex-direction: column-reverse; } .sidebar { width: 100%; max-height: 200px; flex-direction: row; flex-wrap: wrap; gap: 10px; padding: 14px; overflow-y: auto; } .sidebar h2, .sidebar .sub, .result-count, .legend { display: none; } .filter-group { flex: 1; min-width: 120px; } }
```

**New:**
```css
@media (max-width: 700px) {
  body { height: 100dvh; }
  .content-wrap { position: relative; }
  .sidebar-toggle { display: flex; align-items: center; justify-content: center; position: fixed; top: 10px; right: 10px; z-index: 1002; width: 40px; height: 40px; border: none; border-radius: 8px; background: #1a1a2e; color: #eee; font-size: 22px; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.3); }
  .sidebar { position: absolute; top: 0; right: 0; height: 100%; z-index: 1001; transform: translateX(100%); transition: transform .2s ease; box-shadow: -4px 0 12px rgba(0,0,0,.4); }
  .sidebar.open { transform: translateX(0); }
  .sidebar h2, .sidebar .sub, .result-count, .legend { display: none; }
  .filter-group { flex: 1; min-width: 120px; }
}
```

### 3. HTML — Add toggle button element

After the closing `</div>` of `.sidebar` (line 88), before `<script>` (line 90):
```html
<button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle filters">☰</button>
```

### 4. JS — Add toggle event handler

After the `resetBtn` click handler (after line 186), before `initMap()` (line 188):
```js
document.getElementById('sidebarToggle').addEventListener('click', function() {
  document.querySelector('.sidebar').classList.toggle('open');
});
```

## After editing the template

Regenerate `world-map.html`:
```bash
python3 generate_map.py
```
