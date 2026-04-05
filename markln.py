#!/usr/bin/python3
from time import sleep
from spellchecker import SpellChecker
import os, re
import argparse
import json
from typing import Optional, Set
from textual.strip import Strip
import pyperclip
from pathlib import Path
from textual.theme import Theme
from rich.style import Style
from textual import events
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.scroll_view import ScrollView
from textual.screen import ModalScreen
from textual.containers import Grid
from textual.suggester import Suggester
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import (
    Button,
    Footer,
    Header,
    ListView,
    ListItem,
    Input,
    Label,
    Markdown,
    MarkdownViewer,
    Static,
    TextArea,
    DirectoryTree,
)
from textual.geometry import Region
from enum import Enum
from textual.events import Key
from textual.reactive import reactive
from rich.text import Text

spell = SpellChecker()

PROGRAM_NAME = "MarkLn"
PROGRAM_VERSION = "1.3.1"
CONFIG_DIR = Path.home() / ".config/markln"
CONFIG_FILE = CONFIG_DIR / "config.json"
CUSTOM_THEME = None
AUTOCOMPLETE = True

HELP_MARKDOWN = """\
# Program Usage

## Keyboard Shortcuts

Press ALT+K for quick access to see all keyboard shortcuts

## Bookmarks

MarkLn, supports bookmarking lines. Toggle a bookmark with CTRL+B and navigate with ALT+Q or W keys. You can only navigate to bookmarks, goind forward or backward. You can't assign a number to a bookmark and call it by that.

## Header Navigation

Pressing the ALT+Up or Down keys, you can navigate through all markdown headers. It doesn't matter which level they are. As long the program will find a header upwards or backwards, will go to that position. This way, you can navigate through sections of your file, quickly.

## Find Text

Pressing CTRL+F, you can enter a string to search. If you toggle the Case Sensitive button, the search will be either case sensitive or not. Press CTRL+G to go to the next occurrance of the search term or press CTRL+Y to close the Search Bar.

## Options

You can enable/disable various usefull options, pressing the CTRL+\ keys. 

---

# Markdown Cheatsheet

## Text Formatting

- **Bold**: `**bold text**` or `__bold text__`
- *Italic*: `*italic text*` or `_italic text_`
- ***Bold Italic***: `***bold italic***`
- ~~Strikethrough~~: `~~strikethrough text~~`

## Headers

# Header 1
`# Header 1`

## Header 2
`## Header 2`

### Header 3
`### Header 3`

#### Header 4
`#### Header 4`

## Lists

### Unordered List
- Item 1
- Item 2
  - Nested item
  - Another nested item
  
### Ordered List
1. First item
2. Second item
   1. Nested item
   2. Another nested item

## Links & Images

- [Link](https://example.com): `[Link](https://example.com)`
- ![Image](https://example.com/image.jpg): `![Image](https://example.com/image.jpg)`

## Code

### Inline Code
Use `backticks` for inline code: `` `code` ``

### Code Blocks

\`\`\`python
def hello_world():
    print("Hello, World!")
\`\`\`

```python
def hello_world():
    print("Hello, World!")
```

### Blockquote
```
> This is a blockquote
> It can span multiple lines
>
> > And even be nested
```

> This is a blockquote
> It can span multiple lines
>
> > And even be nested

### Ruler

'---'

---

### Tables
```
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |


### Tasks

- [x] Completed task
- [ ] Incomplete task

### Tips

- Use blank lines to separate paragraphs
- Indent code blocks with 4 spaces or use triple backticks
- Table alignment uses colons: :--- left, :---: center, ---: right
- Escape special characters with backslash: \\*not italic*

"""


def load_config() -> dict:
    global CONFIG_FILE
    """Load user configuration from ~/.markln/config.json.

    Returns a dictionary with config values or sensible defaults.
    """
    default_config = {
        "theme": "textual-dark",
        "themefolder":"./themes/",
        "last_file": None,
        "window_mode": "split",  # split | editor | preview
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # merge defaults with loaded data
            return {**default_config, **data}
        except Exception as e:
            print(f"[WARN] Failed to read config: {e}")
            return default_config
    else:
        return default_config


def save_config(config: dict) -> None:
    """Save configuration to ~/.markln/config.json."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[WARN] Failed to save config: {e}")
        

class MarkdownTagsDialog(ModalScreen):
    """Dialog for selecting and inserting markdown tags"""
    
    MARKDOWN_TAGS = [
        ("Header 1", "# Header"),
        ("Header 2", "## Header"),
        ("Header 3", "### Header"),
        ("Bold", "**bold text**"),
        ("Italic", "*italic text*"),
        ("Bold Italic", "***bold italic***"),
        ("Strikethrough", "~~strikethrough text~~"),
        ("Inline Code", "`code`"),
        ("Code Block", "```\ncode block\n```"),
        ("Blockquote", "> blockquote"),
        ("Unordered List", "- list item"),
        ("Ordered List", "1. list item"),
        ("Link", "[text](url)"),
        ("Image", "![alt](image.jpg)"),
        ("Horizontal Rule", "---"),
        ("Table", "| Header | Header |\n|--------|--------|\n| Cell   | Cell   |"),
        ("Task List", "- [ ] task"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Select Markdown Tag (Enter to insert, Esc to cancel)", id="tags-title"),
            ListView(
                *[ListItem(Label(tag[0]), id=f"tag-{i}") for i, tag in enumerate(self.MARKDOWN_TAGS)],
                id="tags-list"
            ),
            Button("Cancel", variant="error", id="cancel"),
            id="tags-dialog"
        )

    def on_mount(self) -> None:
        self.query_one("#tags-list").focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle tag selection"""
        selected_index = int(event.item.id.split("-")[1])
        selected_tag = self.MARKDOWN_TAGS[selected_index][1]
        self.dismiss(selected_tag)

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
        
    def key_home(self) -> None:
        """Move selection to first item"""
        list_view = self.query_one("#tags-list")
        list_view.index = 0

    def key_end(self) -> None:
        """Move selection to last item"""
        list_view = self.query_one("#tags-list")
        list_view.index = len(self.MARKDOWN_TAGS) - 1

    def key_pageup(self) -> None:
        """Move selection up by page"""
        list_view = self.query_one("#tags-list")
        list_view.index = max(0, list_view.index - 5)

    def key_pagedown(self) -> None:
        """Move selection down by page"""
        list_view = self.query_one("#tags-list")
        list_view.index = min(len(self.MARKDOWN_TAGS) - 1, list_view.index + 5)
        
class OptionsDialog(ModalScreen):
    """Dialog for selecting various options"""
    
    MARKDOWN_TAGS = [
        ("Copy All text to clipboard", "copyall"),
        ("Copy Selection to clipboard", "copysel"),
        ("Paste from clipboard", "paste"),
        ("Toggle Auto Update Preview", "toggle_preview"),
        ("Update Preview", "update_preview"),
        ("Hide Table Of Contents", "treeview"),
        ("Toggle Autocomplete", "auto"),
        ("Clear Bookmarks", "clsbook"),
    ]

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Select an Option", id="options-title"),
            ListView(
                *[ListItem(Label(tag[0]), id=f"tag-{i}") for i, tag in enumerate(self.MARKDOWN_TAGS)],
                id="tags-list"
            ),
            Button("Cancel", variant="error", id="cancel"),
            id="tags-dialog"
        )

    def on_mount(self) -> None:
        self.query_one("#tags-list").focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle tag selection"""
        selected_index = int(event.item.id.split("-")[1])
        selected_tag = self.MARKDOWN_TAGS[selected_index][1]
        self.dismiss(selected_tag)

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)
        
    def key_home(self) -> None:
        """Move selection to first item"""
        list_view = self.query_one("#tags-list")
        list_view.index = 0

    def key_end(self) -> None:
        """Move selection to last item"""
        list_view = self.query_one("#tags-list")
        list_view.index = len(self.MARKDOWN_TAGS) - 1

    def key_pageup(self) -> None:
        """Move selection up by page"""
        list_view = self.query_one("#tags-list")
        list_view.index = max(0, list_view.index - 5)

    def key_pagedown(self) -> None:
        """Move selection down by page"""
        list_view = self.query_one("#tags-list")
        list_view.index = min(len(self.MARKDOWN_TAGS) - 1, list_view.index + 5)

class FileSuggester(Suggester):
    async def get_suggestion(self, value: str) -> str | None:
        path = next(Path().glob(f"{value}*"), None)
        return str(path) if path else None

class InfoDialog(ModalScreen):
    DEFAULT_CSS = """
    InfoDialog {
        align: center middle;
    }
    
    InfoDialog > #dialog-container {
        width: 80%;
        height: 70%;
        border: none;
        background: $surface;
    }
    
    InfoDialog #title-bar {
        height: 1;
        border: none;
        background: $accent 20%;
        padding: 0 1;
    }
    
    InfoDialog #title-label {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
    }
    
    InfoDialog #text-area {
        height: 1fr;
        margin: 1;
        border: solid $border;
    }
    
    InfoDialog #button-bar {
        height: 3;
        align: right middle;
        margin: 1;
    }
    
    InfoDialog Button {
        width: 12;
        margin: 0 1;
    }
    """
    
    def __init__(
        self, 
        content: str, 
        title: str = "Information", 
        read_only: bool = True,
        width: int = 80,
        height: int = 70
    ):
        
        super().__init__()
        self.content = content
        self.dialog_title = title
        self.read_only = read_only
        self.width = width
        self.height = height
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Update CSS with dynamic dimensions
        with Vertical(id="dialog-container"):
            with Horizontal(id="title-bar"):
                yield Label(self.dialog_title, id="title-label")
            
            yield TextArea(
                self.content, 
                id="text-area", 
                read_only=self.read_only
            )
            
            with Horizontal(id="button-bar"):
                yield Button("Close", id="close-button", variant="primary")
                yield Button("Copy", id="copy-button", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-button":
            self.dismiss()
        elif event.button.id == "copy-button":
            self._copy_to_clipboard()

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss()

class HelpScreen(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.title = "Markdown Help"

    def compose(self) -> ComposeResult:
        with Container(id="help-container"):
            yield MarkdownViewer(HELP_MARKDOWN, id="help-content", show_table_of_contents=True)
            with Container(id="help-buttons"):
                with Horizontal():
                    yield Button("Close", variant="primary", id="close")

    def on_mount(self) -> None:
        # Focus the markdown content so it can receive keyboard events
        self.query_one("#help-content").focus()

    @on(Button.Pressed, "#close")
    def close_pressed(self) -> None:
        self.dismiss()

    # Add keyboard bindings for the help screen
    def key_escape(self) -> None:
        """Close help when Escape is pressed"""
        self.dismiss()

    def key_down(self) -> None:
        """Scroll down"""
        help_content = self.query_one("#help-content")
        help_content.scroll_down()

    def key_up(self) -> None:
        """Scroll up"""
        help_content = self.query_one("#help-content")
        help_content.scroll_up()

    def key_pageup(self) -> None:
        """Scroll page up"""
        help_content = self.query_one("#help-content")
        help_content.scroll_page_up()

    def key_pagedown(self) -> None:
        """Scroll page down"""
        help_content = self.query_one("#help-content")
        help_content.scroll_page_down()
        
    def key_home(self) -> None:
        """Scroll page down"""
        help_content = self.query_one("#help-content")
        help_content.scroll_home()
        
    def key_end(self) -> None:
        """Scroll page down"""
        help_content = self.query_one("#help-content")
        help_content.scroll_end()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=f"{PROGRAM_NAME} v{PROGRAM_VERSION}")
    parser.add_argument("file", nargs="?", help="Markdown file to open")
    parser.add_argument(
        "--theme",
        default=None,
        help=(
            "Theme to use (built-in options include: textual-dark, textual-light, monokai, dracula, "
            "github-dark, github-light, nord, zenburn, and others)"
        ),
    )
    return parser.parse_args()

class QuitDialog(ModalScreen):
    def __init__(self) -> None:
        super().__init__()
        self.focusable_buttons = None
        self.current_button_index = 0

    def compose(self) -> ComposeResult:
        yield Grid(
            Static("You have unsaved changes. Save first?", id="question"),
            Button("Save", variant="primary", id="save"),
            Button("Don't Save", variant="error", id="dont_save"),
            Button("Cancel", id="cancel"),
            id="quit-dialog"
        )
        
    def on_mount(self) -> None:
        self.focusable_buttons = [
            self.query_one("#save"),
            self.query_one("#dont_save"),
            self.query_one("#cancel")
        ]
        self.current_button_index = 0
        self.focusable_buttons[0].focus()

    def key_left(self) -> None:
        """Move focus to previous button"""
        if self.focusable_buttons:
            self.current_button_index = (self.current_button_index - 1) % len(self.focusable_buttons)
            self.focusable_buttons[self.current_button_index].focus()

    def key_right(self) -> None:
        """Move focus to next button"""
        if self.focusable_buttons:
            self.current_button_index = (self.current_button_index + 1) % len(self.focusable_buttons)
            self.focusable_buttons[self.current_button_index].focus()

    @on(Button.Pressed, "#save")
    def save_pressed(self) -> None:
        self.dismiss("save")

    @on(Button.Pressed, "#dont_save")
    def dont_save_pressed(self) -> None:
        self.dismiss("dont_save")

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss("cancel")

class YesNoDialog(Screen):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container(id="yesno-dialog"):
            yield Static(self.message, id="message")
            with Horizontal(id="yesno-buttons"):
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", id="no")

    @on(Button.Pressed, "#yes")
    def yes_pressed(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def no_pressed(self) -> None:
        self.dismiss(False)

class SimpleDirectoryTree(DirectoryTree):
    """A simplified directory tree without parent navigation to avoid TreeNode issues"""
    
    def on_mount(self) -> None:
        """Focus the tree when mounted"""
        self.focus()
        
class CustomFooter(Footer):
    """Custom footer that includes cursor position"""
    
    def make_key_text(self) -> str:
        """Override to add cursor position"""
        base_text = super().make_key_text()
        # Get cursor position from app if available
        if hasattr(self.app, 'cursor_position'):
            line, col = self.app.cursor_position
            return f"{base_text} • Line: {line}, Col: {col}"
        return base_text

class SaveFileDialog(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.title = "Save As"

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            with Container(id="fixed_top", classes="savedialog-top"):
                yield Static("Directory:", classes="dialog-label")
                with Horizontal():
                    yield Button("^ Up", id="go_up", classes="nav-button")
                    yield Input(id="path_input", value=str(Path.cwd()), classes="dialog-input")
                yield Label("Filename:", classes="dialog-label")
                yield Input(id="filename", placeholder="Enter filename...", classes="dialog-input",suggester=FileSuggester(use_cache=False))
            with Container(id="tree_container"):
                yield SimpleDirectoryTree(path=Path.cwd(), id="tree")
            with Container(id="buttons_container", classes="dialog-bottom"):
                with Horizontal(id="button_row"):
                    yield Button("OK", variant="primary", id="ok")
                    yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#tree").focus()
    
    def key_backspace(self) -> None:
        """Go to parent directory when backspace is pressed in tree"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        if tree.has_focus:
            self.go_up_pressed()
            
    def key_escape(self) -> None:
        """Close dialog when Escape is pressed"""
        self.cancel_pressed()
        
    @on(Button.Pressed, "#go_up")
    def go_up_pressed(self) -> None:
        """Navigate to parent directory"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        current_path = Path(tree.path)
        parent_path = current_path.parent
        
        # Only navigate if we're not at the root
        if parent_path != current_path:
            tree.path = parent_path
            self.query_one("#path_input", Input).value = str(parent_path)
            tree.focus()

    @on(Input.Submitted, "#path_input")
    def change_path(self, event: Input.Submitted) -> None:
        new_path = event.input.value.strip()
        if new_path:
            try:
                p = Path(new_path).expanduser().absolute()
                if p.is_dir():
                    tree = self.query_one("#tree", SimpleDirectoryTree)
                    tree.path = p
                    event.input.value = str(p)
                    tree.focus()
                else:
                    self.notify(f"Directory not found: {new_path}", severity="error")
                    self.bell()
            except Exception as e:
                self.notify(f"Invalid path: {e}", severity="error")
                self.bell()

    @on(DirectoryTree.DirectorySelected, "#tree")
    def dir_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        tree = self.query_one("#tree", SimpleDirectoryTree)
        tree.path = event.path
        self.query_one("#path_input", Input).value = str(event.path)
        tree.focus()

    @on(DirectoryTree.FileSelected, "#tree")
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.query_one("#filename", Input).value = event.path.name
        self.query_one("#path_input", Input).value = str(event.path.parent)
        self.query_one("#filename").focus()

    @on(Button.Pressed, "#ok")
    def ok_pressed(self) -> None:
        path_val = self.query_one("#path_input", Input).value.strip()
        filename = self.query_one("#filename", Input).value.strip()
        if path_val and filename:
            # Auto-add .md extension if no extension provided
            if not Path(filename).suffix:
                filename += ".md"
            full_path = Path(path_val) / filename
            
            # Check if file exists
            if full_path.exists():
                # Push confirmation dialog
                self.app.push_screen(
                    YesNoDialog(f"File '{filename}' already exists. Overwrite?"),
                    callback=lambda overwrite: self._handle_overwrite(overwrite, full_path)
                )
            else:
                self.dismiss(str(full_path))
        else:
            self.notify("Please provide both path and filename", severity="error")
            self.bell()

    def _handle_overwrite(self, overwrite: bool, full_path: Path) -> None:
        """Handle the result of the overwrite confirmation"""
        if overwrite:
            self.dismiss(str(full_path))
        # else do nothing - stay in the save dialog

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)


class OpenFileDialog(Screen):
    def __init__(self) -> None:
        super().__init__()
        self.title = "Open File"

    def compose(self) -> ComposeResult:
        with Container(id="dialog-container"):
            with Container(id="fixed_top", classes="dialog-top"):
                yield Static("Select a file to open:", classes="dialog-label")
                with Horizontal():
                    yield Button("^ Up", id="go_up", classes="nav-button")
                    yield Input(id="path_input", value=str(Path.cwd()), classes="dialog-input")
            with Container(id="tree_container"):
                yield SimpleDirectoryTree(path=Path.cwd(), id="tree")
            with Container(id="buttons_container", classes="dialog-bottom"):
                with Horizontal(id="button_row"):
                    yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        self.query_one("#tree").focus()
        
    def key_backspace(self) -> None:
        """Go to parent directory when backspace is pressed in tree"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        if tree.has_focus:
            self.go_up_pressed()
    
    def key_escape(self) -> None:
        """Close dialog when Escape is pressed"""
        self.cancel_pressed()
        
    @on(Button.Pressed, "#go_up")
    def go_up_pressed(self) -> None:
        """Navigate to parent directory"""
        tree = self.query_one("#tree", SimpleDirectoryTree)
        current_path = Path(tree.path)
        parent_path = current_path.parent
        
        # Only navigate if we're not at the root
        if parent_path != current_path:
            tree.path = parent_path
            self.query_one("#path_input", Input).value = str(parent_path)
            tree.focus()

    @on(Input.Submitted, "#path_input")
    def change_path(self, event: Input.Submitted) -> None:
        new_path = event.input.value.strip()
        if new_path:
            try:
                p = Path(new_path).expanduser().absolute()
                if p.is_dir():
                    tree = self.query_one("#tree", SimpleDirectoryTree)
                    tree.path = p
                    event.input.value = str(p)
                    tree.focus()
                else:
                    self.notify(f"Directory not found: {new_path}", severity="error")
                    self.bell()
            except Exception as e:
                self.notify(f"Invalid path: {e}", severity="error")
                self.bell()

    @on(DirectoryTree.DirectorySelected, "#tree")
    def dir_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        tree = self.query_one("#tree", SimpleDirectoryTree)
        tree.path = event.path
        self.query_one("#path_input", Input).value = str(event.path)
        tree.focus()

    @on(DirectoryTree.FileSelected, "#tree")
    def file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(str(event.path))

    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)


class MODES(str, Enum):
    NORMAL = 'normal'
    VISUAL = 'visual'
    INSERT = 'insert'
    
class SuggestionPopup(ModalScreen):
    BINDINGS = [
        Binding("escape", "close"),
        Binding("home", "go_top"),
        Binding("end", "go_bottom"),
    ]

    CSS = """
    SuggestionPopup {
        align: center middle;
    }

    #box {
        width: 24;
        border: solid white;
        background: $panel;
        height: 10;
    }

    Input {
        height: 1;
        border: none;
    }

    ListView {
        max-height: 10;
    }
    """

    def __init__(self, word, suggestions, callback):
        super().__init__()
        self.all_suggestions = suggestions
        self.filtered = suggestions[:]
        self.callback = callback
        self.word = word

    def compose(self):
        self.input = Input(placeholder="Filter...")
        self.lv = ListView()

        yield Vertical(
            self.input,
            self.lv,
            id="box"
        )

    def on_mount(self):
        self.input.focus()
        self.update_list()

    # -------------------------
    # Filtering logic
    # -------------------------
    def on_input_changed(self, event: Input.Changed):
        query = event.value.lower()

        if not query:
            self.filtered = self.all_suggestions[:]
        else:
            self.filtered = [
                w for w in self.all_suggestions
                if query in w.lower()
            ]

        self.update_list()


    def update_list(self):
        self.lv.clear()
        for word in self.filtered:
            item = ListItem(Label(word))
            item.word = word  # attach the word
            self.lv.append(item)
        if self.filtered:
            self.lv.index = 0

    # -------------------------
    # Selection
    # -------------------------
    def on_list_view_selected(self, event: ListView.Selected):
        # Each ListItem now has a 'word' attribute attached
        selected_word = getattr(event.item, "word", None)
        if selected_word:
            self.callback(selected_word)
        self.dismiss()

    # -------------------------
    # Navigation
    # -------------------------
    def action_go_top(self):
        if self.lv.children:
            self.lv.index = 0
            self.lv.scroll_to_index(0)

    def action_go_bottom(self):
        if self.lv.children:
            last = len(self.lv.children) - 1
            self.lv.index = last
            self.lv.scroll_to_index(last)

    def action_close(self):
        self.dismiss()

class GotoLineDialog(ModalScreen):
    """Simple dialog to input line number"""
    
    DEFAULT_CSS = """
    GotoLineDialog {
        align: center middle;
    }
    
    #goto-dialog {
        grid-size: 1;
        grid-rows: 2 5 5;
        padding: 1;
        width: 40;
        height: 15;
        border: solid $accent;
        background: $surface;
        background-tint: $background;
    }
    
    #goto-title {
        height: 1;
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $text;
        border: none;
    }
    
    #line-input {
        width: 100%;
        margin-bottom: 1;
        border: solid $primary;
        height: 3;
    }
    
    #goto-dialog Horizontal {
        width: 100%;
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    
    #goto-dialog Button {
        width: 10;
        margin: 0 1;
        height: 3;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("Go to line:", id="goto-title"),
            Input(placeholder="Enter line number...", id="line-input"),
            Horizontal(
                Button("Go", variant="primary", id="go"),
#                Button("Cancel", id="cancel"),
            ),
            id="goto-dialog"
        )
    
    def on_mount(self) -> None:
        self.query_one("#line-input").focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._go_to_line(event.value)
    
    @on(Button.Pressed, "#go")
    def go_pressed(self) -> None:
        line_input = self.query_one("#line-input", Input)
        self._go_to_line(line_input.value)
    
    def _go_to_line(self, value: str) -> None:
        try:
            line_num = int(value.strip()) - 1  # Convert to 0-indexed
            if line_num >= 0:
                self.dismiss(line_num)
            else:
                self.bell()
        except ValueError:
            self.notify("Invalid Value!")
    
    @on(Button.Pressed, "#cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(None)
    
    def key_escape(self) -> None:
        self.dismiss(None)

class ExtendedTextArea(TextArea):
    """A subclass of TextArea with parenthesis-closing + full VIM keybindings."""

    opening_brackets = {'(': ')', '[': ']', '{': '}'}
    _opening_brackets = {'([{'}
    closing_brackets = set(')]}')
    

    mode: reactive[MODES] = reactive(MODES.INSERT)
    last_keys: reactive[str] = reactive('')          # ← for dd, gg, yy, etc.
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Regex to match markdown headers (1-6 # symbols followed by space)
        self.bookmarked_lines = set()
        self.header_pattern = re.compile(r'^#{1,6}\s+')
    
    def find_previous_header(self, current_line: int) -> Optional[int]:
        """Find the nearest header above the current line.
        
        Args:
            current_line: Current cursor line number (0-indexed)
            
        Returns:
            Line number of previous header, or None if not found
        """
        lines = self.text.splitlines()
        
        # Search upwards from current_line - 1 down to 0
        for line_num in range(current_line - 1, -1, -1):
            if line_num < len(lines) and self.header_pattern.match(lines[line_num]):
                return line_num
        
        return None
    
    def find_next_header(self, current_line: int) -> Optional[int]:
        """Find the nearest header below the current line.
        
        Args:
            current_line: Current cursor line number (0-indexed)
            
        Returns:
            Line number of next header, or None if not found
        """
        lines = self.text.splitlines()
        
        # Search downwards from current_line + 1 to end
        for line_num in range(current_line + 1, len(lines)):
            if self.header_pattern.match(lines[line_num]):
                return line_num
        
        return None
    
    def navigate_to_header(self, direction: str) -> bool:
        """Navigate to previous or next header."""
        current_line = self.cursor_location[0]
        
        if direction == "prev":
            target_line = self.find_previous_header(current_line)
        else:
            target_line = self.find_next_header(current_line)
        
        if target_line is not None:
            # Move cursor to the target line
            self.cursor_location = (target_line, 0)
            
            # Scroll to make the line visible using scroll_to_region with proper coordinates
            # Get the virtual coordinates of the target line
            #scroll_x = self.scroll_x
            #scroll_y = self.get_line_top(target_line)
            
            #self.scroll_to(x=scroll_x, y=scroll_y, animate=False)
            
            return True
        
        return False
    
    def _jump_to_line(self, line_number: int) -> None:
        """Jump to a specific line and scroll it into view."""
        # Move cursor to the start of the line
        self.cursor_location = (line_number, 0)
        
        # Scroll to make the line visible
        self.scroll_to_line(line_number)
        
        # Optional: Briefly highlight the line by selecting it
        from textual.widgets.text_area import Selection
        self.selection = Selection(start=(line_number, 0), end=(line_number + 1, 0))
        
        # Clear selection after a brief moment (optional)
        self.set_timer(0.5, lambda: setattr(self, 'selection', None))
    
    def toggle_bookmark(self, line_number: int):
        """Toggle bookmark on a specific line."""
        if line_number in self.bookmarked_lines:
            self.bookmarked_lines.remove(line_number)
        else:
            self.bookmarked_lines.add(line_number)
        #self.refresh()  # Trigger repaint to show/hide highlight
        self.refresh(layout=True)
    

    # def render_line(self, y: int) -> Strip:
        # """Render line with highlighting for bookmarked document lines."""
        # strip = super().render_line(y)
        
        # # Get the actual document line number at this visual position
        # # The y parameter is the visual line index, but we need the document line
        # document_line = self.get_line(y)
        
        # if document_line is not None and document_line in self.bookmarked_lines:
            # return strip.apply_style(Style(reverse=True))
        
        
        # return strip
    
    def _render_line_numbers(self) -> list[Text]:
        lines = self.text.splitlines()
        gutter = []
        print("GUTTER")
        for i, line in enumerate(lines):
            is_header = bool(self.header_pattern.match(line))
            is_bookmark = i in self.bookmarked_lines

            symbol = "  "
            style = "grey50"

            if is_header and is_bookmark:
                symbol = "◆★"
                style = "bold magenta"
            elif is_header:
                symbol = "◆ "
                style = "bold cyan"
            elif is_bookmark:
                symbol = "★ "
                style = "bold yellow"

            gutter.append(Text(f"{symbol}{i+1:>3} ", style=style))

        return gutter
        
    def _render_gutter(self) -> list[Text]:
        lines = self.text.splitlines()
        gutter = []

        for i in range(len(lines)):
            line = lines[i]

            is_header = bool(self.header_pattern.match(line))
            is_bookmark = i in self.bookmarked_lines

            symbol = "  "
            style = "grey50"

            if is_header and is_bookmark:
                symbol = "◆★"
                style = "bold magenta"
            elif is_header:
                symbol = "◆ "
                style = "bold cyan"
            elif is_bookmark:
                symbol = "★ "
                style = "bold yellow"

            gutter.append(
                Text(f"{symbol}{i+1:>3} ", style=style)
            )

        return gutter
        
    def get_gutter_text(self, line_number: int) -> Text:
#    def render_gutter_line(self, line_number: int) -> Text:
        lines = self.text.splitlines()
        line = lines[line_number] if line_number < len(lines) else ""

        is_header = bool(self.header_pattern.match(line))
        is_bookmark = line_number in self.bookmarked_lines

        # === SYMBOL LOGIC ===
        symbol = "  "  # default spacing

        if is_header and is_bookmark:
            symbol = "◆★"   # both
            style = "bold magenta"
        elif is_header:
            symbol = "◆ "   # header
            style = "bold cyan"
        elif is_bookmark:
            symbol = "★ "   # bookmark
            style = "bold yellow"
        else:
            style = "grey50"

        return Text(
            f"{symbol}{line_number + 1:>3} ",
            style=style
        )

    def watch_mode(self):
        self.border_title = f"{self.mode.value.upper()} {self.last_keys}"
        self.read_only = (self.mode == MODES.NORMAL)

    def watch_last_keys(self):
        """Nice visual feedback for multi-key commands (dd, gg, etc.)"""
        self.border_title = f"{self.mode.value.upper()} {self.last_keys}"

    def _on_key(self, event: events.Key) -> None:
        global AUTOCOMPLETE

        key = event.character

        if self.mode == MODES.NORMAL:
            # === INSERT MODE ENTRY ===
            if key in ('i', 'I', 'a', 'A', 's', 'S', 'o', 'O'):
                self._move_to_insert_mode(key)
                event.prevent_default()
                event.stop()
                return

            # === NAVIGATION (single keys) ===
            if key in ('h', 'j', 'k', 'l', 'w', 'b'):
                self._navigate_cursor(key)
                event.prevent_default()
                event.stop()
                return

            # === VIM COMMANDS ===
            if self._handle_vim_command(key):
                event.prevent_default()
                event.stop()
                return

            # Unknown normal-mode key → eat it (real vim behaviour)
            event.prevent_default()
            event.stop()
            return

        # ====================== INSERT MODE ======================
        elif self.mode == MODES.INSERT:
            if event.key == "escape":          # ← cleaner than tuple
                self.mode = MODES.NORMAL
                self.last_keys = ""
                event.prevent_default()
                event.stop()
                return

            # Markdown auto-complete helpers (your original logic)
            cursor_loc = self.cursor_location
            lines = self.text.split('\n')
            current_line = lines[cursor_loc[0]] if cursor_loc[0] < len(lines) else ""

            if key in self.opening_brackets:
                if not AUTOCOMPLETE: 
                    # If autocomplete is disabled, just insert the character normally
                    super()._on_key(event)
                    return
                self._auto_close_brackets_and_quotes(key)
                event.prevent_default()
                event.stop()
                return

            elif key == '*' and cursor_loc[1] > 0 and current_line[cursor_loc[1] - 1] == '*':
                self.insert("***")
                self.cursor_location = (cursor_loc[0], cursor_loc[1] + 1)
                event.prevent_default()
                event.stop()
                return
            elif key == '~' and cursor_loc[1] > 0 and current_line[cursor_loc[1] - 1] == '~':
                self.insert('~~~')
                self.cursor_location = (cursor_loc[0], cursor_loc[1] + 1)
                event.prevent_default()
                event.stop()
                return
            elif key == "`" and cursor_loc[1] > 0 and current_line[cursor_loc[1] - 2:cursor_loc[1]] == "``":
                self.insert("`\n\n```")
                self.cursor_location = (cursor_loc[0] + 1, 0)
                event.prevent_default()
                event.stop()
                return
            elif key in self.closing_brackets:
                if cursor_loc[1] < len(current_line) and current_line[cursor_loc[1]] == key:
                    # Skip over the existing closing bracket
                    self.move_cursor_relative(columns=+1)
                    event.prevent_default()
                    event.stop()
                    return
                else:
                    # No matching closing bracket exists, so just insert the character normally
                    super()._on_key(event)
                    return
                # if key == ']':
                    # if cursor_loc[1] > 1 and current_line[cursor_loc[1] - 2:cursor_loc[1]] == '![':
                        # self.move_cursor_relative(columns=+1)
                        # self.insert('()')
                        # self.move_cursor_relative(columns=-3)
                    # else:
                        # self.move_cursor_relative(columns=+1)
                # elif cursor_loc[1] < len(current_line) and current_line[cursor_loc[1]] == key:
                    # self.move_cursor_relative(columns=+1)

                # event.prevent_default()
                # event.stop()
                # return

            # ====================== THIS WAS MISSING ======================
            # All other keys (a, e, c, p, space, numbers, arrows, Backspace, Enter, etc.)
            # → let the original TextArea do normal typing/editing
            super()._on_key(event)

    # ====================== NEW: COMMAND HANDLER ======================
    def _handle_vim_command(self, key: str) -> bool:
        """Returns True if the key was consumed as a command."""
        if not key:          # ← protects against arrows, Backspace, etc.
            return False
        self.last_keys += key

        # ====================== SINGLE-KEY COMMANDS ======================
        if len(self.last_keys) == 1:
            match self.last_keys:
                case "x":
                    self.action_delete_right()
                case "X":
                    self.action_delete_left()
                case "u":
                    self.action_undo()
                case "0":
                    self.action_cursor_line_start()
                case "$":
                    self.action_cursor_line_end()
                case "p":
                    self._vim_paste(after=True)
                case "P":
                    self._vim_paste(after=False)
                case "G":
                    self.action_cursor_document_end()
                case "g":  # wait for second g
                    return True
                case _:
                    #self.last_keys = ""   # unknown single key
                    return False

            self.last_keys = ""
            return True

        # ====================== TWO-KEY COMMANDS ======================
        if len(self.last_keys) == 2:
            match self.last_keys:
                case "dd":
                    self._delete_line()
                case "yy":
                    self._yank_line()
                case "gg":
                    self.action_cursor_document_start()
                case "dw":
                    self._delete_word()
                case _:
                    self.last_keys = ""
                    return False

            self.last_keys = ""
            return True

        # More than 2 keys → reset (you can extend later)
        self.last_keys = ""
        return False

    # ====================== HELPER METHODS ======================
    def _move_to_insert_mode(self, char: str):
        match char:
            case "i": pass
            case "I": self.action_cursor_line_start()
            case "a": self.move_cursor_relative(columns=+1)
            case "A": self.action_cursor_line_end()
            case "s": self.action_delete_right() if self.text else None
            case "S": self._delete_line(); self.mode = MODES.INSERT; return
            case "o":
                self.action_cursor_line_end()
                self.insert("\n")
            case "O":
                self.action_cursor_line_start()
                self.insert("\n")
                self.move_cursor_relative(rows=-1)
        self.mode = MODES.INSERT
        self.last_keys = ""

    def _navigate_cursor(self, char: str):
        self.cursor_blink = False
        match char:
            case "h": self.move_cursor_relative(columns=-1)
            case "j": self.move_cursor_relative(rows=+1)
            case "k": self.move_cursor_relative(rows=-1)
            case "l": self.move_cursor_relative(columns=+1)
            case "w": self.action_cursor_word_right()
            case "b": self.action_cursor_word_left()
        self.cursor_blink = True

    def _delete_line(self):
        """dd - delete current line"""
        self.action_select_line()
        self.action_delete_line()

    def _yank_line(self):
        """yy - yank (copy) current line to system clipboard"""
        self.action_select_line()
        if self.selected_text:
            try:
                pyperclip.copy(self.selected_text)
            except Exception:
                pass
            self.action_copy()          # also keep internal clipboard
        self.clear_selection()

    def _vim_paste(self, after: bool = True):
        """p / P - paste from system clipboard"""
        try:
            text = pyperclip.paste()
            if text:
                if after:
                    self.move_cursor_relative(columns=1)   # after cursor
                self.insert(text)
        except Exception:
            pass

    def _delete_word(self):
        """dw - simple delete word (you can make it more powerful later)"""
        self.action_cursor_word_right()
        self.action_delete_left()   # delete the word we just jumped over

    def _auto_close_brackets_and_quotes(self, char: str):
        """Your original auto-close logic"""
        match char:
            case "(": self.insert("()")
            case "[": self.insert("[]")
            case "{": self.insert("{}")
            case "'": self.insert("''")
            case '"': self.insert('""')
            case '`': self.insert('``')
        self.move_cursor_relative(columns=-1)

class MDEditor(App[None]):
    global CUSTOM_THEME
    BINDINGS = [
        Binding("ctrl+b", "toggle_bookmark", "", priority=True),
        Binding("alt+i", "show_info", "", priority=True),
        Binding("alt+k", "show_keys", "", priority=True),
        Binding("alt+up", "previous_header", "", tooltip="Navigate to previous header"),
        Binding("alt+down", "next_header", "", tooltip="Navigate to next header"),
        ("ctrl+q", "quit", ""),
        ("ctrl+o", "load_file", ""),
        ("ctrl+s", "save_file", ""),
        ("ctrl+n", "new_file", ""),
        ("ctrl+shift+s", "save_as", ""),
        ("ctrl+t", "toggle_editor", ""),
        ("ctrl+j", "sync_preview", ""),
        ("home", "scroll_home", ""),
        ("end", "scroll_end", ""),
        ("ctrl+home", "edit_scroll_home", ""),
        ("ctrl+end", "edit_scroll_end", ""),
        ("alt+g", "markdown_tags", ""),
        ("ctrl+r", "toggle_wrap", ""),
        ("ctrl+backslash", "options", ""),
        Binding("ctrl+l", "goto_line", "", priority=True), 
        Binding("alt+w", "next_bookmark", "", priority=True),
        Binding("alt+q", "prev_bookmark", "", priority=True),
        Binding("alt+h", "help", "", priority=True),
        Binding("alt+e", "select_editor", "", priority=True),
        Binding("alt+p", "select_preview", "", priority=True),
        Binding("alt+s", "select_split", "", priority=True),
        Binding("alt+c", "spell_check", "", priority=True),
        Binding("ctrl+y", "resetfind", "", priority=True),
        Binding("ctrl+f", "focus_search", "Search", priority=True),
        Binding("ctrl+g", "find_next", "Next", priority=True),
        Binding("ctrl+shift+g", "find_prev", "Prev", priority=True),
    ]
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .footer {
        height: 1;
        padding: 0 1;
        background: $surface;
        color: $text;
        /* text-style: bold; */
    }
    
    .footer.hidden {
        display: none;
    }
    
    #tags-dialog {
        grid-size: 1;
        grid-gutter: 1 1;
        grid-rows: auto 1fr auto;
        padding: 0 1;
        width: 40;
        height: 20;
        border: thick $background 80%;
        background: $surface;
    }

    #tags-title {
        height: auto;
        width: 100%;
        content-align: center middle;
        padding: 1;
        text-style: bold;
    }

    #tags-list {
        width: 100%;
        height: 1fr;
        border: solid $accent;
    }

    #tags-dialog Button {
        width: 100%;
        height: 3;
    }
    
    .hidden {
        display: none;
    }
    
    Notify {
        align: right top;
    }
    
    #dialog-container {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    
    .dialog-top {
        height: 6;
        padding: 1;
        /* border: solid $accent; */
        background: $panel;
    }
    
    .savedialog-top {
        height: 10;
        padding: 1;
        /* border: solid $accent; */
        background: $panel;
    }
    
    .dialog-bottom {
        height: auto;
        padding:1;
        /* border: solid $accent; */
        background: $panel;
    }
    
    .dialog-label {
        margin-bottom: 0;
        color: $text;
    }
    
    .dialog-input {
        width: 100%;
        margin-bottom: 0;
    }
    
    #tree_container {
        width: 100%;
        height: 1fr;
        /* border: solid $accent; */
    }
    
    #tree {
        width: 100%;
        height: 100%;
    }
    
    
    #buttons_container {
        height: auto;
    }
    
    #button_row {
        width: 100%;
        align: center middle;
        height: auto;
    }
    
    #button_row > Button {
        margin: 0 1;
    }
    
    /* Main app layout */
    #ui {
        width: 100%;
        height: 1fr;
        layout: horizontal;
    }
    
    #editor {
        width: 1fr;
        height: 100%;
        /* border: solid $accent; */
    }
    
    MarkdownH1 {
        background: #A0A0A030;
        padding: 1;
        margin: 1 1;
    }
    
    MarkdownH2 {
        background: #A0A0A030;
        padding: 0 1;
        text-align: center;
        text-style: bold;
        margin: 1 1;
    }
    
    MarkdownH3 {
        text-style: bold;
        margin: 2 1;
    }
    
    MarkdownH4 {
        text-style: underline;
        margin: 2 1;
    }
    
    #ui.editor-only #editor {
        width: 100% !important;
    }
    #ui.preview-only #preview {
        width: 100% !important;
    }
    
    #preview {
        width: 1fr;
        height: 100%;
        /* border: solid $accent; */
        padding: 1;
        overflow: auto;
    }
    
    /* Ensure proper focus styling */
    DirectoryTree:focus {
       /* border: solid $accent; */
    }
    
     #yesno-dialog {
        width: auto;
        height: auto;
        padding: 2;
        /* border: double $accent; */
        background: $panel;
        align: center middle;
    }
    
    #message {
        text-align: center;
        margin-bottom: 2;
    }
    
    #yesno-buttons {
        align: center middle;
    }
    
    #yesno-buttons > Button {
        margin: 0 1;
    }
        #quit-dialog {
        width: auto;
        height: auto;
        padding: 2;
        /* border: double $accent; */
        background: $panel;
        align: center middle;
    }
    
    #quit-dialog {
        width: auto;
        height: auto;
        padding: 2;
        border: double $accent;
        background: $panel;
        align: center middle;
        max-width: 50;
        max-height: 10;
    }
    #quit-dialog #message {
        text-align: center;
        margin-bottom: 2;
    }
    #quit-buttons {
        align: center middle;
    }
    #quit-buttons > Button {
        margin: 0 1;
    }

    #help-container {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    
    #help-content {
        width: 100%;
        height: 1fr;
        padding: 1 2;
        overflow-y: auto;
        /* border: solid $accent; */
    }
    
    #help-content:focus {
        /* border: double $accent; */
    }
    
    #help-buttons {
        height: auto;
        padding: 1;
        /* border: solid $accent; */
        background: $panel;
    }
    
    #help-buttons > Horizontal {
        width: 100%;
        align: right middle;
        height: auto;
    }
    .nav-button {
        width: auto;
        min-width: 5;
        margin-right: 1;
    }
    
    QuitDialog {
        align: center middle;
    }
    
    MarkdownTagsDialog {
        align: center middle;
    }
    
    OptionsDialog {
        align: center middle;
    }
    
    #quit-dialog {
        grid-size: 3;  /* 3 columns for three horizontal buttons */
        grid-gutter: 1 1;
        grid-rows: 1fr auto;  /* Row 1 for question, Row 2 auto for buttons */
        padding: 0 1;
        width: auto;
        height: 15;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 3;  /* Span all three columns */
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    #quit-dialog Button {
        width: 1fr;  /* Equal width across columns */
        height: 3;
    }

    Button {
        width: 100%;
    }
    
    #path_input {
        border: blank;
    }
    
    #filename  {
        border: blank;
    }
    
    #case_toggle {
      width: 8;
      align: right middle;
    }
    
    #search_bar {
        height: 3;
        border: none;
        background: $panel;
    }

    #search_input {
        width: 1fr;
        height: 3;
    }
    
    #search_bar.hidden {
        display: none;
    }
    
    """

    current_file: Optional[str] = None
    current_mode: Optional[str] = 'split'
    current_view_state: int = 0  # 0: split, 1: editor-only, 2: preview-only
    _preview_update_scheduled = False
    _original_content: str = ""  # Track original content to detect changes
    _has_unsaved_changes: bool = False  # Track if there are unsaved changes
    
    search_term: str = ""
    search_index: int = 0
    last_match: Optional[int] = None
    case_sensitive: bool = False

    def __init__(self, initial_file: Optional[str] = None, theme: str = "dark") -> None:
        super().__init__()
        self.initial_file = initial_file
        self._requested_theme = theme  # Store requested theme, don't set self.theme directly
        self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: Untitled"
        self.current_file: Optional[str] = None
        self.current_mode: Optional[str] = 'split'
        self._preview_update_scheduled = False
        self._original_content: str = ""
        self.do_auto_preview = True
        self._has_unsaved_changes: bool = False
        # self.footer_text = "Ctrl+O: Open • Ctrl+S: Save • Ctrl+Shift+S: Save As • Ctrl+T: Toggle • F2: Sync • F3: Tags • Ctrl+L: Help • Ctrl+Q: Quit"
        self.footer_text = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="ui"):
            #yield ExtendedTextArea.code_editor(language="python")
            yield ExtendedTextArea(id="editor", tab_behavior="indent", language="markdown")
            #yield TextArea.code_editor(id="editor", tab_behavior="indent", language="markdown")
            yield Markdown(id="preview")
        # Hidden fullscreen viewer overlay
        yield MarkdownViewer(id="preview_viewer", show_table_of_contents=True, classes="hidden")
        #yield CustomFooter()
        
        with Horizontal(id="search_bar", classes="hidden"):
            yield Input(placeholder="Search...", id="search_input")
            yield Button("case", id="case_toggle")
        
        yield Static(id="footer", classes="footer")  # Use Static instead of Footer

    def on_mount(self) -> None:
        # Set theme first
        theme_value = getattr(self, "_requested_theme", config.get("theme", "textual-dark"))
        editor = self.query_one("#editor", TextArea)
        editor.cursor_blink = True
        editor.match_cursor_bracket = True  # This highlights matching brackets
        self.opening_brackets = {
        '(': ')',
        '[': ']',
        '{': '}',
        '"': '"',
        "'": "'",
        '`': '`',
        '**': '**',
        '*': '*',
        }
        self.auto_complete_chars = set('([{"\'`*')
        self.closing_brackets = set(')]}"\'`*')

        editor = self.query_one("#editor", TextArea)
        editor.indent_type = "spaces"
        editor.indent_width = 2
        editor.cursor_blink = True
        editor.match_cursor_bracket = True
        editor.compact = True
        editor.show_line_numbers = True

        editor.focus()
        self._original_content = editor.text

        # Load initial file if provided
        if self.initial_file:
            self.load_file(self.initial_file)
        self.update_cursor_position()
        self.action_toggle_editor()

    def _get_text(self):
        return self.query_one("#editor", TextArea).text

    def _get_cursor_index(self):
        editor = self.query_one("#editor", TextArea)
        lines = editor.text.split("\n")
        row, col = editor.cursor_location
        return sum(len(lines[i]) + 1 for i in range(row)) + col

    def _index_to_location(self, index: int):
        text = self._get_text()
        before = text[:index]

        row = before.count("\n")
        col = len(before.split("\n")[-1])

        return (row, col)
        
    def _set_cursor_index(self, index: int):
        editor = self.query_one("#editor", TextArea)
        text = editor.text

        before = text[:index]
        row = before.count("\n")
        col = len(before.split("\n")[-1])

        editor.cursor_location = (row, col)

        # 👇 highlight match
        if self.search_term:
            length = len(self.search_term)
            editor.selection = (
                (row, col),
                self._index_to_location(index + length)
            )

        editor.scroll_to(y=row, animate=False)

    def get_active_theme(self) -> str:
        """Return the current active theme name or .tcss path."""
        return getattr(self, "_custom_theme_path", self.theme)

    def action_find_next(self):
        term = self.search_term
        if not term:
            return

        text = self._get_text()
        start = self._get_cursor_index() + 1

        if not self.case_sensitive:
            text = text.lower()
            term = term.lower()

        pos = text.find(term, start)

        if pos == -1:
            pos = text.find(term, 0)

        if pos != -1:
            self._set_cursor_index(pos)
            self.last_match = pos

        # 🔥 return focus to editor
        self.query_one("#editor").focus()

    def action_focus_search(self):
        bar = self.query_one("#search_bar")
        bar.remove_class("hidden")
        
        footer = self.query_one("#footer")
        footer.add_class("hidden")

        input_box = self.query_one("#search_input", Input)
        input_box.value = self.search_term
        input_box.focus()
        input_box.select_all()

    def action_find_prev(self):
        term = self.search_term
        if not term:
            return

        text = self._get_text()
        start = self._get_cursor_index() - 1

        if not self.case_sensitive:
            text = text.lower()
            term = term.lower()

        pos = text.rfind(term, 0, start)

        if pos == -1:
            pos = text.rfind(term)

        if pos != -1:
            self._set_cursor_index(pos)
            self.last_match = pos

        # 🔥 return focus
        self.query_one("#editor").focus()
        
    @on(Input.Changed, "#search_input")
    def update_search(self, event: Input.Changed):
        self.search_term = event.value
        self.last_match = None
    
    @on(Button.Pressed, "#case_toggle")
    def toggle_case(self):
        self.case_sensitive = not self.case_sensitive
        btn = self.query_one("#case_toggle", Button)
        btn.label = "Case Sens." if self.case_sensitive else "Case Ins."

    @on(TextArea.Changed)
    def on_text_changed(self, event: TextArea.Changed) -> None:
        """Update cursor position when text changes (includes cursor moves during editing)"""
        self.update_cursor_position()
    
    def update_cursor_position(self) -> None:
        """Update cursor position in footer"""
        editor = self.query_one("#editor", TextArea)
        line, column = editor.cursor_location
        line += 1
        column += 1
        
        footer = self.query_one("#footer", Static)
        footer.update(f"{line:>3}:{column:<3}|ESC[d]:VIMode[/]|ALT+K[d]:Keys[/]|CTRL+G[d]:Tags[/]|ALT+H[d]:Help[/]|CTRL+\\:[d]Options[/]|^Q[d]:Quit[/]")
            
    def load_file(self, filename: str) -> None:
        """Load a file programmatically"""
        try:
            file_path = Path(filename).expanduser().absolute()
            if file_path.exists() and file_path.is_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                editor = self.query_one("#editor", TextArea)
                editor.load_text(text)
                self.current_file = str(file_path)
                self._original_content = text
                self._has_unsaved_changes = False
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {file_path.name}"
                self.notify(f"Loaded {file_path.name}")
            else:
                # Set up for a new file without creating it yet
                editor = self.query_one("#editor", TextArea)
                editor.load_text("")
                self.current_file = str(file_path)
                self._original_content = ""
                self._has_unsaved_changes = False  # It's empty, so no changes yet
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {file_path.name} (new)"
                self.notify(f"New file: {file_path.name} (will be created on save)")
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")

    @on(TextArea.Changed, "#editor")
    def update_preview(self) -> None:
        """Update preview with debouncing and track changes"""
        if self.current_view_state == 1: return
        if self.do_auto_preview == False: return
        if not self._preview_update_scheduled:
            self._preview_update_scheduled = True
            self.set_timer(1, self._do_update_preview)
        
        # Check for unsaved changes
        current_text = self.query_one("#editor", TextArea).text
        self._has_unsaved_changes = (current_text != self._original_content)
        
        # Update title to show unsaved changes
        if self._has_unsaved_changes:
            base_title = f"{PROGRAM_NAME} v{PROGRAM_VERSION}"
            if self.current_file:
                base_title += f" :: {os.path.basename(self.current_file)}"
            self.title = f"{base_title} *"
        else:
            if self.current_file:
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {os.path.basename(self.current_file)}"
            else:
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: Untitled"

    def _do_update_preview(self) -> None:
        """Efficiently update Markdown preview (only when using the lightweight Markdown widget)."""
        self._preview_update_scheduled = False
        text = self.query_one("#editor", TextArea).text

        preview = self.query_one("#preview")
        if isinstance(preview, Markdown):
            #preview.update(text)
            self.call_after_refresh(preview.update, text)

    def action_load_file(self) -> None:
        if any(isinstance(screen, OpenFileDialog) for screen in self.screen_stack):
            return  # Help screen already open
        if self._has_unsaved_changes:
            self.push_screen(QuitDialog(), callback=self._handle_openunsaved_decision)
        else:
            self.push_screen(OpenFileDialog(), callback=self.load_file_callback)
    
    def _handle_openunsaved_decision(self, decision: str) -> None:
        if decision == "save":
            if self.current_file:
                self._save_to_file(self.current_file)
                self._original_content = self.query_one("#editor", TextArea).text
                self._has_unsaved_changes = False
            else:
                # If no current file, show save as dialog first
                self.push_screen(SaveFileDialog(), callback=self._just_save)
            self.push_screen(OpenFileDialog(), callback=self.load_file_callback)
        elif decision == "dont_save":
            self.push_screen(OpenFileDialog(), callback=self.load_file_callback)
    
    def _handle_new_decision(self, decision: str) -> None:
        if decision == "save":
            if self.current_file:
                self._save_to_file(self.current_file)
                self._original_content = self.query_one("#editor", TextArea).text
                self._has_unsaved_changes = False
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: Untitled"
            else:
                # If no current file, show save as dialog first
                self.reset_file()
                self.push_screen(SaveFileDialog(), callback=self._just_save)
                self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: Untitled"
            self.reset_file()
            
        elif decision == "dont_save":
            self.reset_file()

    def load_file_callback(self, filename: Optional[str]) -> None:
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            editor = self.query_one("#editor", TextArea)
            editor.load_text(text)
            self.current_file = filename
            self._original_content = text  # Update original content
            self._has_unsaved_changes = False
            self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {os.path.basename(filename)}"
            self.notify(f"Loaded {filename}")
            self.update_cursor_position() 
        except FileNotFoundError:
            self.notify("File not found", severity="error")
        except PermissionError:
            self.notify("Permission denied to read file", severity="error")
        except UnicodeDecodeError:
            self.notify("File encoding error - try UTF-8 encoded file", severity="error")
        except Exception as e:
            self.notify(f"Error loading file: {e}", severity="error")
    
    def action_markdown_tags(self) -> None:
        """Show markdown tags dialog"""
        if self.current_view_state == 2: return
        self.push_screen(MarkdownTagsDialog(), callback=self._insert_markdown_tag)
    
    def action_options(self) -> None:
        """Show options dialog"""
        self.push_screen(OptionsDialog(), callback=self._execute_option)
        
    def action_toggle_wrap(self) -> None:
        editor = self.query_one("#editor", TextArea)
        editor.soft_wrap = not editor.soft_wrap

    def _insert_markdown_tag(self, tag: Optional[str]) -> None:
        """Insert the selected markdown tag at cursor position"""
        if tag:
            editor = self.query_one("#editor", TextArea)
            editor.insert(tag)
            editor.focus()
            
    def _execute_option(self, tag: Optional[str]) -> None:
        global AUTOCOMPLETE
        if tag == "copyall":
            editor = self.query_one("#editor", TextArea)
            if editor.text:
                pyperclip.copy(editor.text)
                self.notify("Document copied to system clipboard")
            else:
                self.notify("No text to copy...")
        elif tag == 'auto':
            AUTOCOMPLETE = not AUTOCOMPLETE
        elif tag == 'clsbook':
            text_area = self.query_one(ExtendedTextArea)
            text_area.bookmarked_lines.clear()
            self.notify("Bookmarks Cleared!")
        elif tag == "update_preview":
            prestate = self.do_auto_preview
            self.do_auto_preview = True
            self.update_preview()
            self.do_auto_preview = prestate
        elif tag == "toggle_preview":
            self.do_auto_preview = not self.do_auto_preview
            if self.do_auto_preview:
                self.update_preview()
        elif tag == "paste":
            self.key_ctrl_v()
        elif tag == "copysel":
            editor = self.query_one("#editor", TextArea)
            selected_text = editor.selected_text
            if selected_text:
                try:
                    pyperclip.copy(selected_text)
                    self.notify("Copied to system clipboard")
                except Exception as e:
                    self.notify(f"Failed to copy to clipboard: {e}", severity="error")
            else:
                self.notify("No text to copy...")
        
        elif tag == "treeview":
            pv = self.query_one("#preview_viewer", MarkdownViewer)
            pv.show_table_of_contents = (not pv.show_table_of_contents)
    
    def action_scroll_home(self) -> None:
        """Scroll to the top"""
        editor = self.query_one("#editor", TextArea)
        if editor.has_focus:
            pass
        elif self.query_one("#editor").styles.display == "none":
            # Preview is focused and editor is hidden
            preview_container = self.query_one("#preview_viewer", MarkdownViewer)
            preview_container.scroll_home()

    def action_scroll_end(self) -> None:
        """Scroll to the bottom"""
        editor = self.query_one("#editor", TextArea)
        if editor.has_focus:
            pass
        elif self.query_one("#editor").styles.display == "none":
            # Preview is focused and editor is hidden
            preview_container = self.query_one("#preview_viewer", MarkdownViewer)
            preview_container.scroll_end()
    
    def action_edit_scroll_home(self) -> None:
        """Scroll to the top"""
        editor = self.query_one("#editor", TextArea)
        if editor.has_focus:
            editor.scroll_home()
            editor.cursor_location = (0, 0)
            
    def action_sync_preview(self) -> None:
        """Sync preview scroll position to approximate editor cursor location."""
        
        try:
            preview = self.query_one("#preview", Markdown)  # Direct reference
        except:
            return

        editor = self.query_one("#editor", TextArea)
        preview = self.query_one("#preview", Markdown)  # Direct reference
        
        return_focus = False
        if editor.has_focus: return_focus = True
        
        # Force immediate preview update
        self._do_update_preview()
        
        def _perform_sync():
            cursor_line, _ = editor.cursor_location
            total_lines = max(1, len(editor.text.split('\n')))
            fraction = cursor_line / total_lines
            
            # Markdown/ScrollView metrics
            virtual_height = preview.virtual_size.height
            visible_height = preview.size.height
            max_scroll_y = max(0, virtual_height - visible_height)
            
            target_y = fraction * max_scroll_y
            
            # Instant scroll
            preview.scroll_to(y=target_y, animate=False)
            
            # Return focus to editor
            if return_focus: editor.focus()
            #self.notify(f"Synced preview to ~line {cursor_line + 1}")
        
        self.call_after_refresh(_perform_sync)
    
    def action_goto_line(self) -> None:
        """Show dialog to go to a specific line number"""
        def goto_callback(line_num):
            if line_num is not None:
                editor = self.query_one("#editor", TextArea)
                lines = editor.text.split("\n")
                if 0 <= line_num < len(lines):
                    # Move cursor to line
                    editor.cursor_location = (line_num, 0)
                    # Scroll to make it visible
                    editor.scroll_to(y=line_num)
                    #editor.scroll_to_line(line_num)
                    # Briefly highlight the line
                    #from textual.widgets.text_area import Selection
                    #editor.selection = Selection(
                    #    start=(line_num, 0), 
                    #    end=(line_num + 1, 0)
                    #)
                    # Clear selection after a moment
                    #self.set_timer(0.5, lambda: setattr(editor, 'selection', None))
                    #self.notify(f"Jumped to line {line_num + 1}")
                else:
                    self.notify(f"Line {line_num + 1} out of range (1-{len(lines)})", severity="error")
        
        self.push_screen(GotoLineDialog(), callback=goto_callback)
        
    def action_show_info(self):
        """Show an information dialog."""
        editor = self.query_one("#editor", TextArea)
        lines = editor.text.split("\n")
        
        info_text = f"Total Lines: {len(lines)}"
        info_text += f"Words: {len(editor.text.split(' '))}"
        
        dialog = InfoDialog(
            info_text, 
            title="Document Information",
            read_only=True,
            width=75,
            height=65
        )
        self.push_screen(dialog)
      
    def action_show_keys(self):
        keys = """
BookMarks
---------
CTRL+B : Toggle Bookmark
ALT +Q : Previous Bookmark
ALT +W : Next Bookmark

Headers
-------
ALT+Up : Previous Header
ALT+Dn : Next Header

Search
------
CTRL+F : Start Search / ReFocus 
CTRL+Y : Close Search Bar
CTRL+G : Find Next
CTRL+L : Goto Line

Document
-------
ALT+I  : Show Document Info
CTRL+O : Open File
CTRL+N : New Document
CTRL+S : Save File
CTRL+R : Wrap Document Toggle
CTRL+SHIFT+S : Save File As

View
----
CTRL+J : Sync Preview with Editor
ALT+E  : Switch to Editor
ALT+P  : Switch to Preview
ALT+S  : Swithc to Split View

Various
-------
ALT+C  : Check word for misspeling
ALT+K  : Show Key Shortcuts
CTRL+G : Insert MD TAG
CTRL+\ : Options
CTRL+L : Help
        """       
        
        dialog = InfoDialog(
            keys, 
            title="Keys",
            read_only=True,
            width=75,
            height=65
        )
        self.push_screen(dialog)
    
    def action_edit_scroll_end(self) -> None:
        """Scroll to the bottom"""
        editor = self.query_one("#editor", TextArea)
        if editor.has_focus:
            lines = editor.text.split("\n")
            last_line = len(lines) - 1
            last_column = len(lines[-1]) if lines else 0
            editor.cursor_location = (last_line, last_column)
            editor.scroll_end()

    def get_current_word(self):
        editor = self.query_one("#editor", TextArea)

        row, col = editor.cursor_location
        lines = editor.text.splitlines()

        if row >= len(lines):
            return "", 0, 0

        line = lines[row]

        left = col
        right = col

        # Expand left
        while left > 0 and line[left - 1].isalnum():
            left -= 1

        # Expand right
        while right < len(line) and line[right].isalnum():
            right += 1

        word = line[left:right]

        return word, row, left, right

    def replace_word(self, new_word, row, start_col, end_col):
        editor = self.query_one("#editor", TextArea)
        lines = editor.text.splitlines()

        line = lines[row]
        lines[row] = line[:start_col] + new_word + line[end_col:]

        editor.text = "\n".join(lines)
        editor.cursor_location = (row, start_col + len(new_word))

    # -------------------------
    # Action triggered by Alt+C
    # -------------------------
    def action_spell_check(self):
        word, row, start, end = self.get_current_word()

        if not word:
            return

        # Check spelling
        if word.lower() in spell:
            self.notify(f"'{word}' is correct. No suggestions")
            return

        suggestions = list(spell.candidates(word))

        if not suggestions:
            self.notify("No suggestions found!")
            return

        # Show popup
        self.push_screen(
            SuggestionPopup(word,
                suggestions,
                lambda w: self.replace_word(w, row, start, end)
            )
        )
    
    def action_select_editor(self) -> None:
        self.current_view_state = 1
        self.current_mode = "editor"
        self.action_toggleselect_editor()
    
    def action_select_preview(self) -> None:
        self.current_view_state = 2
        self.current_mode = "preview"
        self.action_toggleselect_editor()
    
    def action_select_split(self) -> None:
        self.current_view_state = 0
        self.current_mode = "split"
        self.action_toggleselect_editor()
        
    def action_toggle_editor(self) -> None:
        self.current_view_state = (self.current_view_state + 1) % 3
        if self.current_view_state == 1:
            self.current_mode = "editor"
        elif self.current_view_state == 2:
            self.current_mode = "preview"
        elif self.current_view_state == 0:
            self.current_mode = "split"
        self.action_toggleselect_editor()
        
    def action_toggleselect_editor(self) -> None:
        """Cycle: split -> editor-only -> preview-only (overlay MarkdownViewer) -> split."""

        editor = self.query_one("#editor")
        preview = self.query_one("#preview")      # lightweight Markdown
        text = editor.text

        # footer is used as an anchor so we mount the viewer in the same area
        footer = self.query_one("#footer")

        def ensure_viewer_with_text(text_to_set: str, on_mounted: Optional[callable] = None) -> None:
            """Ensure an overlay MarkdownViewer exists with `text_to_set` as content.
            If the existing viewer supports an in-place update we use it, otherwise we recreate the widget safely.
            `on_mounted` is called after the new widget is mounted (or immediately if updated in-place)."""
            try:
                viewer = self.query_one("#preview_viewer")
            except Exception:
                viewer = None

            if viewer is not None:
                # Try in-place updates if widget provides them
                if hasattr(viewer, "update"):
                    try:
                        viewer.update(text_to_set)
                        if on_mounted:
                            on_mounted()
                        return
                    except Exception:
                        pass
                if hasattr(viewer, "set_document"):
                    try:
                        viewer.set_document(text_to_set)
                        if on_mounted:
                            on_mounted()
                        return
                    except Exception:
                        pass

                # Can't update in-place: remove & recreate
                viewer.remove()

            # Mount new viewer after refresh to avoid DuplicateIds / race conditions
            def _mount_new():
                new = MarkdownViewer(text_to_set, id="preview_viewer", show_table_of_contents=True)
                # mount before footer so ordering stays consistent with compose()
                self.mount(new, before=footer)
                # keep it hidden by default — caller may show it
                new.styles.display = "none"
                if on_mounted:
                    on_mounted()

            self.call_after_refresh(_mount_new)

        def show_viewer():
            try:
                v = self.query_one("#preview_viewer")
                v.remove_class("hidden")
                v.styles.display = "block"
                v.styles.width = "100%"
                v.styles.height = "100%"
                v.focus()
            except Exception:
                pass

        def hide_viewer():
            try:
                v = self.query_one("#preview_viewer")
                v.add_class("hidden")
                v.styles.display = "none"
            except Exception:
                pass

        # reset default visible state for split
        editor.styles.display = "block"
        preview.styles.display = "block"
        editor.styles.width = "1fr"
        preview.styles.width = "1fr"

        if self.current_view_state == 1:
            # Editor-only
            preview.styles.display = "none"
            editor.styles.width = "100%"
            hide_viewer()
            editor.focus()

        elif self.current_view_state == 2:
            # Fullscreen: hide editor+light preview, ensure overlay viewer has the text then show it
            editor.styles.display = "none"
            preview.styles.display = "none"
            ensure_viewer_with_text(text, on_mounted=show_viewer)

        else:
            # Split view
            hide_viewer()
            editor.focus()

        self.refresh(layout=True)
    
    def action_quit(self) -> None:
        """Quit the application with confirmation for unsaved changes"""
        if self._has_unsaved_changes:
            self.push_screen(QuitDialog(), callback=self._handle_quit_decision)
        else:
            self.exit()
            
    def action_help(self) -> None:  # Add this method
        """Show help screen"""
        if any(isinstance(screen, HelpScreen) for screen in self.screen_stack):
            return  # Help screen already open
        self.push_screen(HelpScreen())
    
    def _handle_quit_decision(self, decision: str) -> None:
        """Handle the user's decision from the quit dialog"""
        if decision == "save":
            if self.current_file:
                self._save_to_file(self.current_file)
                self._original_content = self.query_one("#editor", TextArea).text
                self._has_unsaved_changes = False
                self.exit()
            else:
                # If no current file, show save as dialog first
                self.push_screen(SaveFileDialog(), callback=self._save_and_quit)
        elif decision == "dont_save":
            self.exit()
        # else "cancel" - do nothing
    
    def _save_and_quit(self, filename: Optional[str]) -> None:
        """Save to a new file and then quit"""
        if filename:
            self._save_to_file(filename)
            self.current_file = filename
            self._original_content = self.query_one("#editor", TextArea).text
            self._has_unsaved_changes = False
            self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {os.path.basename(filename)}"
            self.exit()
            
    def _just_save(self, filename: Optional[str]) -> None:
        """Save to a new file and then quit"""
        if filename:
            self._save_to_file(filename)
            self.current_file = filename
            self._original_content = self.query_one("#editor", TextArea).text
            self._has_unsaved_changes = False
            self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {os.path.basename(filename)}"
    
    def action_save_file(self) -> None:
        if any(isinstance(screen, SaveFileDialog) for screen in self.screen_stack):
            return  # Help screen already open
        if self.current_file:
            self._save_to_file(self.current_file)
            editor = self.query_one("#editor", TextArea)
            self._original_content = editor.text
            self._has_unsaved_changes = False
            base_title = f"{PROGRAM_NAME} v{PROGRAM_VERSION}"
            if self.current_file:
                base_title += f" :: {os.path.basename(self.current_file)}"
            self.title = f"{base_title}"
        else:
            self.push_screen(SaveFileDialog(), callback=self.save_file_callback)
            
    def action_new_file(self) -> None:
        if self._has_unsaved_changes:
            self.push_screen(QuitDialog(), callback=self._handle_new_decision)
        else:
            self.reset_file()
    
    def reset_file(self):
        editor = self.query_one("#editor", TextArea)
        editor.text = ""
        self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: Untitled"
        self.current_file = None
        self._has_unsaved_changes = False

    def action_save_as(self) -> None:
        self.push_screen(SaveFileDialog(), callback=self.save_file_callback)

    def save_file_callback(self, filename: Optional[str]) -> None:
        if not filename:
            return
        self._save_to_file(filename)
        self.current_file = filename
        self._original_content = self.query_one("#editor", TextArea).text  # Update original content
        self._has_unsaved_changes = False
        self.title = f"{PROGRAM_NAME} v{PROGRAM_VERSION} :: {os.path.basename(filename)}"

    def _save_to_file(self, filename: str) -> None:
        try:
            # Ensure directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.query_one("#editor", TextArea).text)
            self.notify(f"Saved {filename}")
        except PermissionError:
            self.notify("Permission denied to save file", severity="error")
        except OSError as e:
            self.notify(f"File system error: {e}", severity="error")
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")
    
    @on(Input.Submitted, "#search_input")
    def submit_search(self, event: Input.Submitted):
        self.search_term = event.value

        # 🔥 start search from current cursor (or reset if you prefer)
        self.last_match = None

        # go to first match
        self.action_find_next()
    
    def action_resetfind(self):
        bar = self.query_one("#search_bar")

        if not bar.has_class("hidden"):
            bar.add_class("hidden")
            self.query_one("#editor").focus()
            
            editor = self.query_one("#editor", TextArea)
            cursor = editor.cursor_location
            editor.selection = (cursor, cursor)
            editor.focus()

        footer = self.query_one("#footer")
        if  footer.has_class("hidden"):
            footer.remove_class("hidden")
            
    
    def key_ctrl_c(self) -> None:
        """Handle Ctrl+C to copy to system clipboard"""
        editor = self.query_one("#editor", TextArea)
        selected_text = editor.selected_text
        if selected_text:
            try:
                pyperclip.copy(selected_text)
                self.notify("Copied to system clipboard")
            except Exception as e:
                self.notify(f"Failed to copy to clipboard: {e}", severity="error")
        # Still let TextArea handle its internal copy
        editor.copy()

    def action_toggle_bookmark(self):
        """Toggle bookmark at current cursor line."""
        text_area = self.query_one(ExtendedTextArea)
        current_line = text_area.cursor_location[0]  # Get current line number
        text_area.toggle_bookmark(current_line)
        
        status = "added to" if current_line in text_area.bookmarked_lines else "removed from"
        self.notify(f"Bookmark {status} line {current_line + 1}")
    
    def action_next_bookmark(self):
        """Jump to next bookmark."""
        text_area = self.query_one(ExtendedTextArea)
        if not text_area.bookmarked_lines:
            self.notify("No bookmarks")
            return
        
        current_line = text_area.cursor_location[0]
        
        # Find next bookmark after current line
        next_bookmarks = [l for l in sorted(text_area.bookmarked_lines) if l > current_line]
        
        if next_bookmarks:
            target_line = next_bookmarks[0]
        else:
            # Wrap around to first bookmark
            target_line = sorted(text_area.bookmarked_lines)[0]
        
        # Move cursor to bookmark line and highlight it
        text_area.cursor_location = (target_line, 0)
        # text_area.select_line(target_line)
    
    def action_prev_bookmark(self):
        """Jump to prev bookmark."""
        text_area = self.query_one(ExtendedTextArea)
        if not text_area.bookmarked_lines:
            self.notify("No bookmarks")
            return
        
        current_line = text_area.cursor_location[0]
        
        # Find next bookmark after current line
        next_bookmarks = [l for l in sorted(text_area.bookmarked_lines) if l < current_line]
        
        if next_bookmarks:
            target_line = next_bookmarks[-1]
        else:
            # Wrap around to first bookmark
            target_line = sorted(text_area.bookmarked_lines)[-1]
        
        # Move cursor to bookmark line and highlight it
        text_area.cursor_location = (target_line, 0)
        # text_area.select_line(target_line)

    def action_previous_header(self) -> None:
        """Navigate to previous header."""
        text_area = self.query_one(ExtendedTextArea)
        text_area.navigate_to_header("prev")
        #if not text_area.navigate_to_header("prev"):
        #    self.notify("No header above", severity="warning")
    
    def action_next_header(self) -> None:
        """Navigate to next header."""
        text_area = self.query_one(ExtendedTextArea)
        text_area.navigate_to_header("next")
        #if not text_area.navigate_to_header("next"):
            #self.notify("No header below", severity="warning")
            
    def key_ctrl_x(self) -> None:
        """Handle Ctrl+X to cut to system clipboard"""
        editor = self.query_one("#editor", TextArea)
        selected_text = editor.selected_text
        if selected_text:
            try:
                pyperclip.copy(selected_text)
                self.notify("Cut to system clipboard")
            except Exception as e:
                self.notify(f"Failed to cut to clipboard: {e}", severity="error")
        # Still let TextArea handle its internal cut
        editor.cut()

    def key_ctrl_v(self) -> None:
        """Handle Ctrl+V to paste from system clipboard"""
        try:
            clipboard_text = pyperclip.paste()
            if clipboard_text:
                editor = self.query_one("#editor", TextArea)
                editor.insert(clipboard_text)
                self.notify("Pasted from system clipboard")
            else:
                self.notify("Nothing to paste...")
        except Exception as e:
            self.notify(f"Failed to paste from clipboard: {e}", severity="error")
    
    def key_down(self) -> None:
        """Scroll down when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_down()
    
    def key_n(self) -> None:
        """Scroll down when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_down()

    def key_up(self) -> None:
        """Scroll up when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_up()

    def key_pageup(self) -> None:
        """Scroll page up when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_page_up()

    def key_pagedown(self) -> None:
        """Scroll page down when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_page_down()

    def key_home(self) -> None:
        """Scroll to top when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_home()

    def key_end(self) -> None:
        """Scroll to bottom when preview is focused"""
        if self.query_one("#editor").styles.display == "none":
            pr = self.query_one("#preview_viewer", MarkdownViewer)
            pr.scroll_end()


def load_theme_from_file(path: str | Path) -> Theme:
    """Load a Textual theme from a JSON file."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Pass JSON fields directly as keyword arguments to Theme()
    return Theme(**data)


if __name__ == "__main__":
    args = parse_arguments()
    config = load_config()
    # Command-line theme overrides config
    theme = args.theme

    app = MDEditor(initial_file=args.file)
    if not theme:
        tmp = config.get("theme", "textual-dark")
        if os.path.isfile(config.get("themefolder")+tmp):
            themefile = load_theme_from_file(config.get("themefolder")+tmp)
            app.register_theme(themefile)
            app.theme = themefile.name
        else:
            app.theme = tmp

    if config['window_mode'] == "split":
        app.current_view_state = 2
    elif config['window_mode'] == "editor":
        app.current_view_state = 3
    else:
        app.current_view_state = 1

    app.run()

    # Save current theme and last file when exiting
    config["theme"] = app.get_active_theme()
    config["last_file"] = app.current_file
    config["window_mode"] = app.current_mode
    save_config(config)
