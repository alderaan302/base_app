# Text Widget Markdown Guide

This guide explains all the markdown features available when using **Markup editor** type in Text widgets.

## Headers

Use `#` symbols to create headers. More symbols = smaller header.

```
# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6
```

# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6

---

## Text Formatting

### Bold Text
Wrap text in double asterisks or double underscores:
- `**bold text**` → **bold text**
- `__bold text__` → __bold text__

### Italic Text
Wrap text in single asterisks or single underscores:
- `*italic text*` → *italic text*
- `_italic text_` → _italic text_

### Bold and Italic
Combine them:
- `***bold and italic***` → ***bold and italic***
- `___bold and italic___` → ___bold and italic___

### Strikethrough
Use double tildes:
- `~~strikethrough~~` → ~~strikethrough~~

---

## Links

### Basic Links
```
[Link Text](https://example.com)
```
[Visit GitHub](https://github.com)

### Links with Titles
```
[Link Text](https://example.com "Tooltip text")
```
[Google](https://google.com "Go to Google")

### Automatic Links
```
<https://example.com>
```
<https://example.com>

---

## Lists

### Unordered Lists
Use `-`, `*`, or `+`:
```
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3
```
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

### Ordered Lists
Use numbers followed by periods:
```
1. First item
2. Second item
3. Third item
   1. Nested item 3.1
   2. Nested item 3.2
```
1. First item
2. Second item
3. Third item
   1. Nested item 3.1
   2. Nested item 3.2

---

## Code

### Inline Code
Wrap in single backticks:
```
Use `code` for inline code
```
Use `code` for inline code

### Code Blocks
Use triple backticks:
````
```
function example() {
  console.log("Hello World");
}
```
````

```
function example() {
  console.log("Hello World");
}
```

### Code Blocks with Syntax Highlighting
Specify the language after the opening backticks:
````
```python
def hello():
    print("Hello, World!")
```
````

```python
def hello():
    print("Hello, World!")
```

---

## Blockquotes

Use `>` to create blockquotes:
```
> This is a blockquote.
> It can span multiple lines.
>
> > Nested blockquotes are also possible.
```

> This is a blockquote.
> It can span multiple lines.
>
> > Nested blockquotes are also possible.

---

## Horizontal Rules

Create horizontal lines with three or more hyphens, asterisks, or underscores:
```
---
***
___
```

---

## Tables

Create tables using pipes `|` and hyphens `-`:
```
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
| Row 3    | Data     | Data     |
```

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
| Row 3    | Data     | Data     |

### Table Alignment
Use colons to align columns:
```
| Left Align | Center Align | Right Align |
|:-----------|:------------:|------------:|
| Left       | Center       | Right       |
| Text       | Text         | Text        |
```

| Left Align | Center Align | Right Align |
|:-----------|:------------:|------------:|
| Left       | Center       | Right       |
| Text       | Text         | Text        |

---

## Images

```
![Alt Text](image-url.png)
![Alt Text](image-url.png "Image Title")
```

**Note:** Images work best with full URLs or relative paths to accessible resources.

---

## Task Lists

Create checkboxes with `- [ ]` and `- [x]`:
```
- [x] Completed task
- [ ] Incomplete task
- [ ] Another task
```

- [x] Completed task
- [ ] Incomplete task
- [ ] Another task

---

## Line Breaks

### Single Line Break
End a line with two spaces and press Enter:
```
Line 1··
Line 2
```

### Paragraph Break
Leave an empty line between paragraphs:
```
Paragraph 1

Paragraph 2
```

---

## Escaping Characters

Use backslash `\` to escape markdown characters:
```
\*Not italic\*
\[Not a link\]
```

\*Not italic\*
\[Not a link\]

---

## HTML in Markdown

You can use HTML tags directly in markdown:
```html
<div style="color: red;">This is red text</div>
<strong>Bold HTML</strong>
<em>Italic HTML</em>
```

<div style="color: red;">This is red text</div>
<strong>Bold HTML</strong>
<em>Italic HTML</em>

---

## Tips for Using Markup Editor in Text Widgets

1. **Preview your content**: Add the widget, then refresh to see how it renders
2. **Keep it simple**: Complex nested structures may not display perfectly in smaller widgets
3. **Use links**: Great for creating navigation or reference documentation
4. **Resize widgets**: Make widgets larger to accommodate more content
5. **Edit anytime**: Click the settings icon on any widget to update content
6. **Mix and match**: Use different markdown features to create rich, informative widgets

---

## Common Use Cases

### Documentation Widget
Create quick reference guides for your reports:
```
## Quick Reference

### API Endpoints
- `GET /api/data` - Fetch data
- `POST /api/data` - Create data
- `DELETE /api/data/:id` - Remove data

### Status Codes
| Code | Meaning |
|------|---------|
| 200  | Success |
| 404  | Not Found |
| 500  | Server Error |
```

### Status Dashboard
Display current status or important notices:
```
# System Status

✅ **All Systems Operational**

Last updated: 2026-05-24

---

### Recent Updates
- Database backup completed
- Security patches applied
- Performance optimization deployed
```

### Instructions Widget
Step-by-step guides:
```
## How to Use This Report

1. Select an integration from the dropdown
2. Choose metrics to visualize
3. Adjust time range if needed
4. Click "Generate" to create charts

> **Tip:** Bookmark this report for quick access!
```

---

## Additional Resources

- [Markdown Guide](https://www.markdownguide.org/) - Comprehensive markdown documentation
- [CommonMark Spec](https://commonmark.org/) - Markdown specification
- [GitHub Flavored Markdown](https://github.github.com/gfm/) - Extended markdown syntax

---

**Version:** 1.0  
**Last Updated:** May 2026
