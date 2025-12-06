# MarkLn v1.2

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

# Installation Ubuntu/Debian

This guide will walk you through installing the 'markln' application on Ubuntu or Debian-based systems using the provided '.deb' package.

**Step 1: Download the .deb package**

1.  Open your web browser and go to the MarkLn GitHub Releases page:
    `https://github.com/lowtiertrash/markln_deb/releases` (Replace 'lowtiertrash/markln_deb' with your actual repository path if different).
2.  Locate the latest release (e.g., 'v0.1.0').
3.  Under the "Assets" section of the release, download the `markln_0.1.0_all.deb` file.

 Alternatively, you can download it directly from your terminal. Replace 'YOUR_GITHUB_USERNAME' and 'YOUR_REPO_NAME' and 'VERSION' with the correct values.

```bash
# Example using wget (replace with actual download URL from GitHub Releases)
wget https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/releases/download/VERSION/markln_0.1.0_all.deb
```
*Example for v0.1.0 assuming lowtiertrash/markln_deb:*
```bash
wget https://github.com/lowtiertrash/markln_deb/releases/download/v0.1.0/markln_0.1.0_all.deb
```

**Step 2: Install the .deb package**

1.  Open your terminal.
2.  Navigate to the directory where you downloaded the '.deb' package (e.g., `cd ~/Downloads`).
3.  Install the package using `dpkg`:
 ```bash
 sudo dpkg -i markln_0.1.0_all.deb
 ```
You might encounter dependency errors during this step. This is normal if you don't have all required libraries installed. We will fix this in the next step.


**Step 3: Resolve Dependencies (if any)**

If `dpkg` reported dependency errors, you can automatically install the missing packages using `apt`:

```bash
sudo apt install -f
```

This command will attempt to correct a system where dependencies are unmet. It will usually install any missing packages required by 'markln'.

**Step 4: Run MarkLn**

Once the installation is complete and dependencies are resolved, you can launch the MarkLn application directly from your terminal:

```bash
markln
```
If you encounter any issues, please refer to the troubleshooting section or report an issue on the GitHub repository.



# PIP INSTALLATION 
 Prerequisites:
 Python 3.8 or higher
 pip package manager
 Steps:

 ## Clone the repository:
```
 git clone <repository-url> cd markln
```
 Install requirements:
```
 pip install -r requirements.txt
```
 Run the editor:

 ```
python markln.py
 ```


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
- Ctrl+G: Dialog box to insert Markdown Tags
- Ctrl+Q: Quit
- Ctrl+\: Options Menu
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
