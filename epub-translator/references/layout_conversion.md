# EPUB Layout Conversion Guide

This guide covers writing direction and text layout conversion for EPUB translation.

**Key Principle**: Layout should match the **TARGET language** conventions, not the source.

---

## Writing Direction Overview

### Default Layout Convention

**All languages default to horizontal LTR** unless user explicitly requests otherwise.

| Language | Default Direction | Default Writing Mode | Vertical Available |
|----------|-------------------|---------------------|-------------------|
| Korean (ko) | LTR | horizontal-tb | No |
| English (en) | LTR | horizontal-tb | No |
| Japanese (ja) | LTR | horizontal-tb | Yes (on request) |
| Chinese (zh) | LTR | horizontal-tb | Yes (on request) |
| Arabic (ar) | RTL | horizontal-tb | No |
| Hebrew (he) | RTL | horizontal-tb | No |
| Persian (fa) | RTL | horizontal-tb | No |
| Urdu (ur) | RTL | horizontal-tb | No |

**Note**: Japanese and Chinese use horizontal-tb by default. Vertical writing (vertical-rl) is only applied when user explicitly requests it with `--vertical` option.

### Conversion Matrix (Default Behavior)

| Source → Target | Page Direction | Writing Mode | Text Direction |
|-----------------|----------------|--------------|----------------|
| ja (vertical) → ko | rtl → ltr | vertical-rl → horizontal-tb | - |
| ja (vertical) → en | rtl → ltr | vertical-rl → horizontal-tb | - |
| ja (vertical) → ja | rtl → ltr | vertical-rl → horizontal-tb | - |
| en → ja | ltr (keep) | horizontal-tb (keep) | - |
| en → zh | ltr (keep) | horizontal-tb (keep) | - |
| en → ar | ltr → rtl | - | ltr → rtl |
| en → he | ltr → rtl | - | ltr → rtl |
| ar → ko | rtl → ltr | - | rtl → ltr |
| ar → ja | rtl → ltr | - | rtl → ltr |
| zh-TW (vertical) → ko | rtl → ltr | vertical-rl → horizontal-tb | - |

**Note**: Even when translating TO Japanese/Chinese, output is horizontal by default.

---

## Files to Modify

### 1. content.opf (Package Document)

#### Page Progression Direction

```xml
<!-- Japanese vertical (BEFORE) -->
<spine page-progression-direction="rtl">

<!-- Korean/English (AFTER) -->
<spine page-progression-direction="ltr">
```

**Conversion Rules:**
- To Korean/English/Chinese(simplified): `ltr`
- To Arabic/Hebrew/Persian: `rtl`
- To Japanese (if keeping vertical): `rtl`

#### Writing Mode Metadata

```xml
<!-- Japanese vertical (BEFORE) -->
<meta property="rendition:layout">pre-paginated</meta>
<meta property="rendition:orientation">auto</meta>
<meta property="rendition:spread">landscape</meta>
<meta name="primary-writing-mode" content="vertical-rl"/>

<!-- Korean/English (AFTER) -->
<meta property="rendition:layout">reflowable</meta>
<meta name="primary-writing-mode" content="horizontal-tb"/>
```

### 2. stylesheet.css (and other CSS files)

#### Writing Mode

```css
/* Japanese vertical (BEFORE) */
body {
    writing-mode: vertical-rl;
    -webkit-writing-mode: vertical-rl;
    -epub-writing-mode: vertical-rl;
}

/* Korean/English horizontal (AFTER) */
body {
    writing-mode: horizontal-tb;
    -webkit-writing-mode: horizontal-tb;
    -epub-writing-mode: horizontal-tb;
}
```

#### Text Direction (for RTL languages)

```css
/* LTR language (BEFORE) */
body {
    direction: ltr;
    text-align: left;
}

/* RTL language like Arabic (AFTER) */
body {
    direction: rtl;
    text-align: right;
}
```

#### Complete CSS Conversion Patterns

| Property | Vertical-RL → Horizontal-TB | LTR → RTL |
|----------|----------------------------|-----------|
| `writing-mode` | `vertical-rl` → `horizontal-tb` | (no change) |
| `direction` | (no change) | `ltr` → `rtl` |
| `text-align: left` | (no change) | → `text-align: right` |
| `text-align: right` | (no change) | → `text-align: left` |
| `float: left` | (no change) | → `float: right` |
| `float: right` | (no change) | → `float: left` |
| `margin-left` | (no change) | → `margin-right` |
| `margin-right` | (no change) | → `margin-left` |
| `padding-left` | (no change) | → `padding-right` |
| `padding-right` | (no change) | → `padding-left` |
| `text-combine-upright` | Remove | (no change) |
| `-webkit-text-combine` | Remove | (no change) |

### 3. XHTML Files

#### Language Attribute

```xml
<!-- BEFORE -->
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja">

<!-- AFTER (Korean) -->
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ko">
```

#### Inline Styles

Check and convert inline styles in elements:

```xml
<!-- Japanese vertical inline (BEFORE) -->
<p style="writing-mode: vertical-rl;">Text</p>

<!-- Korean horizontal (AFTER) -->
<p style="writing-mode: horizontal-tb;">Text</p>
```

#### Direction Attribute

```xml
<!-- LTR (BEFORE) -->
<p dir="ltr">Text</p>

<!-- RTL target (AFTER) -->
<p dir="rtl">Text</p>
```

### 4. nav.xhtml / toc.ncx

Update direction if present:

```xml
<!-- For RTL targets -->
<nav epub:type="toc" dir="rtl">
```

---

## Conversion Scripts

### Vertical to Horizontal (Japanese → Korean/English)

```bash
# content.opf
sed -i 's/page-progression-direction="rtl"/page-progression-direction="ltr"/g' content.opf
sed -i 's/primary-writing-mode" content="vertical-rl"/primary-writing-mode" content="horizontal-tb"/g' content.opf

# CSS files
find . -name "*.css" -exec sed -i \
    -e 's/writing-mode:\s*vertical-rl/writing-mode: horizontal-tb/g' \
    -e 's/-webkit-writing-mode:\s*vertical-rl/-webkit-writing-mode: horizontal-tb/g' \
    -e 's/-epub-writing-mode:\s*vertical-rl/-epub-writing-mode: horizontal-tb/g' \
    -e 's/text-combine-upright:[^;]*;//g' \
    -e 's/-webkit-text-combine:[^;]*;//g' \
    {} \;

# XHTML inline styles
find . -name "*.xhtml" -exec sed -i \
    -e 's/writing-mode:\s*vertical-rl/writing-mode: horizontal-tb/g' \
    -e 's/xml:lang="ja"/xml:lang="ko"/g' \
    {} \;
```

### LTR to RTL (English → Arabic/Hebrew)

```bash
# content.opf
sed -i 's/page-progression-direction="ltr"/page-progression-direction="rtl"/g' content.opf

# CSS files - swap left/right
find . -name "*.css" -exec sed -i \
    -e 's/direction:\s*ltr/direction: rtl/g' \
    -e 's/text-align:\s*left/text-align: __RIGHT__/g' \
    -e 's/text-align:\s*right/text-align: left/g' \
    -e 's/text-align:\s*__RIGHT__/text-align: right/g' \
    -e 's/float:\s*left/float: __RIGHT__/g' \
    -e 's/float:\s*right/float: left/g' \
    -e 's/float:\s*__RIGHT__/float: right/g' \
    {} \;

# XHTML
find . -name "*.xhtml" -exec sed -i \
    -e 's/dir="ltr"/dir="rtl"/g' \
    -e 's/xml:lang="en"/xml:lang="ar"/g' \
    {} \;
```

### RTL to LTR (Arabic → Korean/English)

```bash
# content.opf
sed -i 's/page-progression-direction="rtl"/page-progression-direction="ltr"/g' content.opf

# CSS files - swap right/left
find . -name "*.css" -exec sed -i \
    -e 's/direction:\s*rtl/direction: ltr/g' \
    -e 's/text-align:\s*right/text-align: __LEFT__/g' \
    -e 's/text-align:\s*left/text-align: right/g' \
    -e 's/text-align:\s*__LEFT__/text-align: left/g' \
    {} \;

# XHTML
find . -name "*.xhtml" -exec sed -i \
    -e 's/dir="rtl"/dir="ltr"/g' \
    {} \;
```

---

## Target Language Decision Table

Use this table to determine layout settings based on target language.

**Default: All languages use horizontal LTR** (except RTL languages like Arabic/Hebrew).

| Target Language | page-progression-direction | writing-mode | direction | Notes |
|-----------------|---------------------------|--------------|-----------|-------|
| Korean (ko) | ltr | horizontal-tb | ltr | |
| English (en) | ltr | horizontal-tb | ltr | |
| Japanese (ja) | ltr | horizontal-tb | ltr | **Default** |
| Japanese (ja) --vertical | rtl | vertical-rl | ltr | Only with `--vertical` flag |
| Chinese (zh) | ltr | horizontal-tb | ltr | **Default** |
| Chinese (zh) --vertical | rtl | vertical-rl | ltr | Only with `--vertical` flag |
| Arabic (ar) | rtl | horizontal-tb | rtl | |
| Hebrew (he) | rtl | horizontal-tb | rtl | |
| Persian (fa) | rtl | horizontal-tb | rtl | |

---

## Special Considerations

### Japanese Vertical Features to Remove

When converting from Japanese vertical to horizontal:

1. **Text Combine (縦中横)**: Numbers/letters rotated in vertical text
   ```css
   /* Remove these */
   text-combine-upright: all;
   -webkit-text-combine: horizontal;
   ```

2. **Ruby positioning**: May need adjustment for horizontal
   ```css
   /* Vertical ruby */
   ruby-position: under;
   /* Horizontal ruby - typically over */
   ruby-position: over;
   ```

3. **Emphasis dots**: Position changes
   ```css
   /* Vertical */
   text-emphasis-position: left;
   /* Horizontal */
   text-emphasis-position: over right;
   ```

### RTL Language Special Features

When converting to RTL languages:

1. **Bidirectional text**: Preserve LTR portions (numbers, English words)
   ```html
   <span dir="ltr">ABC123</span>
   ```

2. **List markers**: Consider RTL-appropriate markers

3. **Punctuation**: Some punctuation may need mirroring

### Image Considerations

- Images with text may need separate handling
- Diagrams with directional flow may need noting
- Cover images typically don't need mirroring

---

## Validation Checklist

After layout conversion, verify:

- [ ] `content.opf` page-progression-direction matches target
- [ ] All CSS files have correct writing-mode
- [ ] All CSS files have correct direction
- [ ] XHTML files have correct xml:lang attribute
- [ ] No leftover vertical-rl in horizontal target
- [ ] No leftover direction:rtl in LTR target (and vice versa)
- [ ] Text flows correctly in target direction
- [ ] Ruby/emphasis marks positioned correctly
- [ ] Numbers and embedded LTR text display correctly in RTL

---

## Integration with Translation Workflow

Layout conversion should be applied:

1. **In orchestrator Phase 3** (Finalization), after content translation
2. **Before packaging** the final EPUB
3. **Based on target language**, not source language

The orchestrator should:
1. Detect source layout (vertical/RTL/LTR)
2. Determine target layout from target language
3. Apply appropriate conversion scripts
4. Verify conversion success
