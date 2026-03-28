# MarkLn v1.3.1

A terminal-based markdown editor built with Textual (Python TUI framework)

### DESCRIPTION
A feature-rich markdown editor that runs in the terminal with real-time preview. Edit markdown files with instant rendering in a split-pane interface. Perfect for quick editing without leaving the command line.

### FEATURES

- Dual-pane interface: Edit markdown with live preview
- Toggle between views (Synced, Editor, Preview)
- Table of contents, dynamically created
- Tags selector to insert easily markdown tags
- Quick Navigation between headers
- Supports Bookmark Navigation
- File management: Open, save, and save-as functionality
- Keyboard-driven: Fully operable with keyboard shortcuts
- Full mouse support also
- Theme support
- Autocomplete feature for brackets and markdown syntax
- VIM keybindings support INSERT/NORMAL modes ^
- Comprehensive help: Built-in markdown syntax reference
- Editor supports common key shortcuts for copy/paste/undo - ctrl-c, ctrl-x, ctrl-w
- Support for terminal shortcuts like ctrl-w and others
- Resize on the fly
- Syntax Highlighting

^ VIM support is not 100% implemented

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

- Ctrl+T: Toggle editor/preview
- Ctrl+Q: Quit
- Ctrl+Home: Go to document start
- Ctrl+End: Go to document end
- ESC: Goes to VIM Mode (i to return to normal mode)
- CTRL+B : Toggle Bookmark
- ALT +Q : Previous Bookmark
- ALT +W : Next Bookmark
- ALT+Up : Previous Header
- ALT+Dn : Next Header
- CTRL+F : Start Search / ReFocus 
- CTRL+Y : Close Search Bar
- CTRL+G : Find Next
- CTRL+L : Goto Line
- ALT+I  : Show Document Info
- CTRL+O : Open File
- CTRL+N : New Document
- CTRL+S : Save File
- CTRL+R : Wrap Document Toggle
- CTRL+SHIFT+S : Save File As
- CTRL+J : Sync Preview with Editor
- ALT+E  : Switch to Editor
- ALT+P  : Switch to Preview
- ALT+S  : Swithc to Split View
- ALT+K  : Show Key Shortcuts
- CTRL+G : Insert MD TAG
- CTRL+\ : Options
- CTRL+L : Help

### SUPPORTED MARKDOWN

- Headers (#, ##, ###)
- Bold and italic text
- Lists (ordered and unordered)
- Code blocks and inline code
- Links and images
- Blockquotes
- Tables
- Horizontal rules

### AUTOCOMPLETE FEATURE

The program can now autocomplete brackets like: []. (), {} 
It can also complete the bold ** and strike-through ~~ markdown syntax, as well detect an Image link ![] and add the parenthesis.

### QUICK NAVIGATION

From version 1.3.1 you can use Header and Bookmark navigation to move quickly in a file. With bookmarks, you can add a bookmark to any line and use ALT+Q/E keys to go forth or backward, between bookmarks. Using the ALT+UP/DOWN keys, you can navigate between headers, of any level.

### CONVERTING TO HTML

There is also a quick and simple utility for basic conversion of a markdown document to HTML. It uses a Python library, that has been installed, when you installed `MarkLn` so there is no need for extra packages/libs. There are tons of MD converters out there, from which you can chose from. This one included, only for convinience.

### VIM KEYBINDINGS SUPPORT

| Action                  | Key(s)                  | Description                          |
|-------------------------|-------------------------|--------------------------------------|
| Enter Insert mode       | `i` `I` `a` `A` `s` `S` `o` `O` | Standard Vim entry points            |
| Back to Normal mode     | `Esc` or `Ctrl+C`       | From Insert mode                     |

**Navigation**
- `h` / `j` / `k` / `l` — left / down / up / right  
- `w` / `b` — word forward / word backward  
- Arrow keys (`←` `↓` `↑` `→`) — also work (Textual native movement)  
- `0` — start of line  
- `$` — end of line  
- `gg` — top of document  
- `G` — bottom of document  

**Editing**
- `x` — delete character under cursor  
- `X` — delete character before cursor  
- `dd` — delete current line  
- `yy` — yank (copy) current line to system clipboard  
- `p` — paste after cursor  
- `P` — paste before cursor  
- `dw` — delete word (forward)  
- `u` — undo last change  

**Special**
- `S` — delete line and enter Insert mode (like `cc` in Vim)

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

### CHANGELOG

**1.1**

- When text is changed and try to quit or create a new file, now a Save dialog appears.
- Minor bugs and code optimization.

**1.2**
- Added feature to show/hide TOC
- Added Options dialog, with functions
- Colorized the statusbar
- When in full editor mode, the markdown preview doesn't update, so makes typing quicker and responsive
- Added the option to stop continues rendering of Markdown on the preview, to make typing more responsive. You can Update the preview, from the options menu
- The app. now has a config file to save default values, like theme, last file, window mode
- You can specify in which mode you want the app to open at start, with the "window_mode" value of the config file. The values it accepts are: split, preview, editor
- Added support for installing external themes. Specify the folder of the themes and the name of the theme file to load a new one.
- When exiting the program, the current theme will be saved and applied next time you run it again
- Three new themes provided: Arctic, Turbo Pascal, MSDOS

**1.3**
- VIM Keybindings support
- Autocomplete feature added

**1.3.1**
- Added Bookmarks Navigation
- Added Header Navigation
- Added Find/Search functionality
