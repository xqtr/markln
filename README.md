# MarkLn v1.1

A terminal-based markdown editor built with Textual (Python TUI framework)

### DESCRIPTION
A feature-rich markdown editor that runs in the terminal with real-time preview. Edit markdown files with instant rendering in a split-pane interface. Perfect for quick editing without leaving the command line.

### FEATURES

- Dual-pane interface: Edit markdown with live preview
- Toggle between views (Synced, Editor, Preview)
- Table of contents, dynamically created
- Tags selector to insert easily markdown tags (F3)
- File management: Open, save, and save-as functionality
- Keyboard-driven: Fully operable with keyboard shortcuts
- Full mouse support also
- Theme support
- Comprehensive help: Built-in markdown syntax reference
- Editor supports common key shortcuts for copy/paste/undo - ctrl-c, ctrl-x, ctrl-w
- Support for terminal shortcuts like ctrl-w and others
- Resize on the fly
- Syntax Highlighting

### INSTALLATION

#### Prerequisites:

- Python 3.8 or higher
- pip package manager

**Steps:**

Clone the repository:

`git clone <repository-url>`
`cd markln`

**Install requirements:**

`pip install -r requirements.txt`

**Run the editor:**

`python markln.py`

### USAGE

Keyboard shortcuts:

- Tab: Switch between controls
- Ctrl+O: Open file
- Ctrl+S: Save file
- Ctrl+Shift+S: Save as
- Ctrl+T: Toggle editor/preview
- Ctrl+L: Show help
- Ctrl+N: New file
- Ctrl+R: Toggle Wrap
- Ctrl+J: Sync Editor with Preview
- Ctrl+G : Dialog box to insert Markdown Tags
- Ctrl+Q: Quit
- Ctrl+Home: Go to document start
- Ctrl+End: Go to document end

### SUPPORTED MARKDOWN

- Headers (#, ##, ###)
- Bold and italic text
- Lists (ordered and unordered)
- Code blocks and inline code
- Links and images
- Blockquotes
- Tables
- Horizontal rules

### DEPENDENCIES

- Python standard library
- Textual - TUI framework
- PyperClip


### SHOWCASE

![dual panel](https://cp737.net/files/markln/markln-main.png)

![open dialog](https://cp737.net/files/markln/markln-open.png)

![live preview](https://cp737.net/files/markln/markln-preview.png)

![tags list](https://cp737.net/files/markln/markln-tags.png)

### LICENSE
GPL-3.0-or-later

### SUPPORT
For issues and questions, please check the issues page or create a new issue with detailed description.

This editor is designed for developers who prefer working in the terminal and need a quick, efficient way to edit markdown files with instant visual feedback.

