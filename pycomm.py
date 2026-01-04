import urwid
import os
from datetime import datetime

# --- Color Palette ---
PALETTE = [
    ('selected', 'black', 'light gray'),
    ('normal', 'default', 'default'),
    ('header', 'white', 'dark blue'),
    ('menu', 'black', 'light cyan'),
    ('menu_selected', 'white', 'dark blue'),
    ('disabled', 'dark gray', 'default'),
    ('path', 'light cyan', 'default'),
]

# --- Menu Definitions ---
MENU_ITEMS = [
    ('File', [
        ('Open (Ctrl+O)', 'open'),
        ('Save', 'save'),
        ('---', None),
        ('Exit (Ctrl+Q)', 'exit'),
    ]),
    ('Edit', [
        ('Copy', 'copy'),
        ('Paste', 'paste'),
    ]),
]

def get_file_metadata(filename):
    if not os.path.exists(filename):
        return "File not found."
    stat = os.stat(filename)
    return "\n".join([
        f"Name: {filename}",
        f"Size: {stat.st_size:,} bytes",
        f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
    ])

class MenuBar(urwid.WidgetWrap):
    def __init__(self):
        self.menu_items = MENU_ITEMS
        self.menu_widgets = self.build_menus()
        super().__init__(urwid.Columns(self.menu_widgets))

    def build_menus(self):
        widgets = []
        for name, items in self.menu_items:
            btn = urwid.Button(name)
            urwid.connect_signal(btn, 'click', self.on_menu_click, user_args=[name, items])
            widgets.append(('pack', urwid.AttrMap(btn, 'menu', 'menu_selected')))
        return widgets

    def on_menu_click(self, name, items, button):
        self.show_submenu(name, items)

    def show_submenu(self, title, items):
        body = [urwid.Text(('menu_selected', title)), urwid.Divider('-')]
        for label, action in items:
            if label == '---':
                body.append(urwid.Divider('-'))
                continue
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', self.on_submenu_click, user_args=[action])
            body.append(urwid.AttrMap(btn, 'menu', 'menu_selected'))
        
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        overlay = urwid.Overlay(
            top_w=urwid.LineBox(listbox),
            bottom_w=urwid.SolidFill(),
            align='left',
            width=('relative', 50),
            valign='top',
            height=('relative', 50),
        )
        urwid.MainLoop(overlay, palette=PALETTE).run()

    def on_submenu_click(self, action, button):
        if action == 'exit':
            raise urwid.ExitMainLoop()

class FileLister:
    def __init__(self):
        self.files = [f for f in os.listdir('.') if os.path.isfile(f)]
        self.selected_index = 0 if self.files else -1

        # Menu Bar (top line)
        self.menu_bar = MenuBar()
        
        # Current directory (second line)
        self.path_text = urwid.Text(
            ("path", f"Directory: {os.getcwd()}"), 
            align='left'
        )
        
        # Header with menu and path
        header = urwid.Pile([
            ('pack', self.menu_bar),  # Menu on first line
            ('pack', self.path_text)  # Path on second line
        ])

        # File List Panel
        self.file_widgets = [
            urwid.AttrMap(urwid.Text(f" {f}"), 'normal', 'selected')
            for f in self.files
        ]
        self.file_list = urwid.SimpleListWalker(self.file_widgets)
        self.listbox = urwid.ListBox(self.file_list)
        self.listbox.ignore_focus = True
        self.file_panel = urwid.LineBox(
            urwid.Padding(self.listbox, left=1, right=1),
            title="Files",
            title_attr='header'
        )

        # Metadata Panel
        self.metadata_text = urwid.Text("Select a file to view details.")
        self.metadata_panel = urwid.LineBox(
            urwid.Padding(self.metadata_text, left=1, right=1),
            title="File Details",
            title_attr='header'
        )

        # Main Layout
        self.columns = urwid.Columns([
            ('weight', 2, self.file_panel),
            ('weight', 3, self.metadata_panel),
        ])
        
        self.body = urwid.Frame(
            body=self.columns,
            header=header,
            footer=urwid.Text(("header", "↑/↓: Navigate | F10: Menu | Ctrl+Q: Exit"))
        )

    def _update_selection(self):
        if self.selected_index >= 0:
            for i, widget in enumerate(self.file_widgets):
                widget.set_attr_map({None: 'selected' if i == self.selected_index else 'normal'})
            self.metadata_text.set_text(get_file_metadata(self.files[self.selected_index]))
            self.listbox.set_focus(self.selected_index)

    def handle_input(self, key):
        if key.lower() == 'q' or key == 'ctrl q':
            raise urwid.ExitMainLoop()
        elif key == 'f10':
            self.menu_bar.show_submenu("Menu", [])
        elif key == 'up' and self.selected_index > 0:
            self.selected_index -= 1
            self._update_selection()
        elif key == 'down' and self.selected_index < len(self.files) - 1:
            self.selected_index += 1
            self._update_selection()
        else:
            return

    def run(self):
        self._update_selection()
        loop = urwid.MainLoop(
            self.body,
            palette=PALETTE,
            unhandled_input=self.handle_input,
            handle_mouse=False
        )
        loop.run()

if __name__ == "__main__":
    FileLister().run()