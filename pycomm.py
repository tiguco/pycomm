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
    ('menu_bg', 'white', 'dark blue'),
    ('menu_divider', 'light gray', 'dark blue'),
    ('dialog_bg', 'white', 'dark blue'),
    ('dialog_button', 'black', 'light cyan'),
    ('dialog_button_focus', 'white', 'dark blue'),
    ('date', 'light green', 'default'),
    ('size', 'yellow', 'default'),
    ('dir_name', 'light magenta', 'default'),
    ('dir_label', 'light cyan', 'default'),
    ('error', 'white', 'dark red'),
]

# --- Menu Definitions ---
MENU_ITEMS = [
    ('File', [
        ('Open (Ctrl+O)', 'open'),
        ('Save', 'save'),
        ('---', None),
        ('Go Up (Backspace)', 'go_up'),
        ('Close', 'close_menu'),
        ('Exit (Ctrl+Q)', 'exit'),
    ]),
    ('Edit', [
        ('Copy', 'copy'),
        ('Paste', 'paste'),
    ]),
]

def get_file_metadata(path):
    """Get metadata for a file or directory."""
    if not os.path.exists(path):
        return "Path not found."
    
    try:
        stat = os.stat(path)
        
        if os.path.isfile(path):
            return "\n".join([
                f"Name: {os.path.basename(path)}",
                f"Type: File",
                f"Size: {stat.st_size:,} bytes",
                f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            ])
        elif os.path.isdir(path):
            # Try to count items in directory
            try:
                items = os.listdir(path)
                dir_count = sum(1 for item in items if os.path.isdir(os.path.join(path, item)))
                file_count = sum(1 for item in items if os.path.isfile(os.path.join(path, item)))
                item_text = f"{len(items)} items ({dir_count} dirs, {file_count} files)"
            except:
                item_text = "Access denied"
                
            return "\n".join([
                f"Name: {os.path.basename(path)}",
                f"Type: Directory",
                f"Contains: {item_text}",
                f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            ])
        else:
            return f"Name: {os.path.basename(path)}\nType: Unknown"
    except Exception as e:
        return f"Error: {str(e)}"

def get_file_size_formatted(size_in_bytes):
    """Convert file size to human readable format."""
    if size_in_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def get_item_info(item_path, is_dir=False):
    """Get item information for display in the list."""
    if not os.path.exists(item_path):
        return os.path.basename(item_path), "N/A", "N/A", is_dir
    
    try:
        stat = os.stat(item_path)
        
        # Item name (with / suffix for directories)
        name = os.path.basename(item_path)
        if is_dir:
            name = f"{name}/"
        
        # Modification date and time
        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
        
        # Size or directory label
        if is_dir:
            try:
                # Count items in directory
                items = os.listdir(item_path)
                dir_count = sum(1 for item in items if os.path.isdir(os.path.join(item_path, item)))
                file_count = sum(1 for item in items if os.path.isfile(os.path.join(item_path, item)))
                size_label = f"({dir_count}D {file_count}F)"
            except:
                size_label = "(dir)"
        else:
            size_label = get_file_size_formatted(stat.st_size)
        
        return name, mod_time, size_label, is_dir
    except Exception:
        return os.path.basename(item_path), "N/A", "N/A", is_dir

class MenuBar(urwid.WidgetWrap):
    def __init__(self, main_loop, file_lister):
        self.menu_items = MENU_ITEMS
        self.menu_widgets = self.build_menus()
        self.main_loop = main_loop
        self.file_lister = file_lister
        self.active_menu = None
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
        # Close any existing menu first
        if self.active_menu:
            self.close_menu()
        
        body = [urwid.AttrMap(urwid.Text(f" {title}"), 'menu_bg'), urwid.AttrMap(urwid.Divider('-'), 'menu_divider')]
        for label, action in items:
            if label == '---':
                body.append(urwid.AttrMap(urwid.Divider('-'), 'menu_divider'))
                continue
            btn = urwid.Button(label)
            urwid.connect_signal(btn, 'click', self.on_submenu_click, user_args=[action])
            body.append(urwid.AttrMap(btn, 'menu', 'menu_selected'))
        
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker(body))
        frame = urwid.Frame(
            urwid.AttrMap(listbox, 'menu_bg'),
            footer=urwid.AttrMap(urwid.Text(" [ESC] Close "), 'menu')
        )
        
        # Create overlay that covers the entire screen
        self.active_menu = urwid.Overlay(
            top_w=urwid.LineBox(frame, title=""),
            bottom_w=self.main_loop.widget,  # Current widget as background
            align='left',
            width=('relative', 30),
            valign='top',
            height=('relative', 50),
            min_width=20,
            min_height=8
        )
        
        # Replace the main widget with the overlay
        self.main_loop.widget = self.active_menu

    def close_menu(self):
        """Close the active menu overlay."""
        if self.active_menu:
            # Restore the original widget (the bottom_w of the overlay)
            self.main_loop.widget = self.active_menu.bottom_w
            self.active_menu = None

    def show_confirmation_dialog(self, title, message, on_yes, on_no=None):
        """Show a confirmation dialog with Yes/No buttons."""
        # Close any existing menu first
        if self.active_menu:
            self.close_menu()
        
        # Create dialog content
        text = urwid.Text(('dialog_bg', message), align='center')
        
        # Create Yes button
        yes_button = urwid.Button("Yes")
        urwid.connect_signal(yes_button, 'click', on_yes)
        
        # Create No button
        no_button = urwid.Button("No")
        def on_no_click(button):
            if on_no:
                on_no()
            self.close_menu()
        urwid.connect_signal(no_button, 'click', on_no_click)
        
        # Create button row
        button_row = urwid.Columns([
            ('weight', 1, urwid.AttrMap(yes_button, 'dialog_button', 'dialog_button_focus')),
            ('weight', 1, urwid.AttrMap(no_button, 'dialog_button', 'dialog_button_focus')),
        ])
        
        # Create dialog layout
        pile = urwid.Pile([
            ('pack', urwid.AttrMap(urwid.Text(f" {title} "), 'dialog_bg')),
            ('pack', urwid.AttrMap(urwid.Divider('-'), 'menu_divider')),
            ('pack', urwid.Padding(text, left=1, right=1)),
            urwid.Divider(),
            ('pack', urwid.Padding(button_row, left=4, right=4)),
        ])
        
        # Create dialog box
        dialog = urwid.LineBox(
            urwid.AttrMap(pile, 'dialog_bg'),
            title=title
        )
        
        # Create overlay
        self.active_menu = urwid.Overlay(
            top_w=dialog,
            bottom_w=self.main_loop.widget,
            align='center',
            width=('relative', 50),
            valign='middle',
            height=('relative', 30),
            min_width=40,
            min_height=10
        )
        
        # Replace the main widget with the overlay
        self.main_loop.widget = self.active_menu

    def on_submenu_click(self, action, button):
        if action == 'exit':
            self.show_exit_confirmation()
        elif action == 'close_menu':
            self.close_menu()
        elif action == 'go_up':
            self.file_lister.go_up_directory()
        elif action == 'open':
            # Example action - you can implement actual functionality here
            print(f"Menu action: {action}")
        else:
            self.close_menu()
            # Add other menu actions here

    def show_exit_confirmation(self):
        """Show confirmation dialog for exiting."""
        def confirm_exit(button):
            raise urwid.ExitMainLoop()
        
        self.show_confirmation_dialog(
            title="Exit Confirmation",
            message="Are you sure you want to exit?",
            on_yes=confirm_exit,
            on_no=self.close_menu
        )

    def show_error_dialog(self, title, message):
        """Show an error dialog."""
        self.show_confirmation_dialog(
            title=title,
            message=message,
            on_yes=self.close_menu,
            on_no=self.close_menu
        )

class FileLister:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.menu_bar = None
        self.loop = None
        
        # Build the initial UI
        self.build_ui()
        
    def build_ui(self):
        """Build or rebuild the entire UI."""
        # Create the directory listing
        self.refresh_directory_listing()
        
        # Create the main layout
        self.columns = urwid.Columns([
            ('weight', 3.6, self.item_panel),
            ('weight', 2, self.metadata_panel),
        ])
        
        # Build the header
        header = None
        if self.menu_bar:
            self.path_text = urwid.Text(
                ("path", f"Directory: {self.current_dir}"), 
                align='left'
            )
            header = urwid.Pile([
                ('pack', self.menu_bar),
                ('pack', self.path_text)
            ])
        
        # Create the main frame
        self.body = urwid.Frame(
            body=self.columns,
            header=header,
            footer=urwid.Text(("header", "↑/↓: Navigate | Enter: Open | Backspace: Go Up | F10: Menu | ESC: Close Menu | Ctrl+Q: Exit"))
        )

    def refresh_directory_listing(self):
        """Refresh the directory listing based on current directory."""
        try:
            # Get all items in current directory
            all_items = os.listdir(self.current_dir)
            
            # Separate directories and files
            self.directories = []
            self.files = []
            
            for item in all_items:
                item_path = os.path.join(self.current_dir, item)
                if os.path.isdir(item_path):
                    self.directories.append(item)
                elif os.path.isfile(item_path):
                    self.files.append(item)
            
            # Sort alphabetically (case-insensitive)
            self.directories.sort(key=str.lower)
            self.files.sort(key=str.lower)
            
            # Combine: directories first, then files
            self.all_items = self.directories + self.files
            self.selected_index = 1 if (self.all_items or self.current_dir != os.path.expanduser("~")) else 0
            
            # Create item list with three columns
            self.item_widgets = []
            self.item_info = []
            
            # Add ".." (parent directory) entry at the top if not at home directory
            if self.current_dir != os.path.expanduser("~"):
                parent_name = ".."
                parent_widget = urwid.Text(('dir_name', f" {parent_name}/"))
                parent_date = urwid.Text(('date', " "), align='right')
                parent_size = urwid.Text(('dir_label', " (parent)"), align='right')
                
                parent_row = urwid.Columns([
                    ('weight', 5, parent_widget),
                    ('weight', 3, parent_date),
                    ('weight', 2, parent_size),
                ])
                
                self.item_widgets.append(urwid.AttrMap(parent_row, 'normal', 'selected'))
                self.item_info.append((parent_name, "", "(parent)", True))
            
            # Add directories
            for d in self.directories:
                item_path = os.path.join(self.current_dir, d)
                name, mod_time, size_label, is_dir = get_item_info(item_path, is_dir=True)
                self.item_info.append((name, mod_time, size_label, is_dir))
                
                # Create three columns for each directory
                name_widget = urwid.Text(('dir_name', f" {d}/"))
                date_widget = urwid.Text(('date', f" {mod_time}"), align='right')
                size_widget = urwid.Text(('dir_label', f" {size_label}"), align='right')
                
                # Combine into a single row with three columns
                item_row = urwid.Columns([
                    ('weight', 5, name_widget),
                    ('weight', 3, date_widget),
                    ('weight', 2, size_widget),
                ])
                
                self.item_widgets.append(urwid.AttrMap(item_row, 'normal', 'selected'))
            
            # Add files
            for f in self.files:
                item_path = os.path.join(self.current_dir, f)
                name, mod_time, size_label, is_dir = get_item_info(item_path, is_dir=False)
                self.item_info.append((name, mod_time, size_label, is_dir))
                
                # Create three columns for each file
                name_widget = urwid.Text(f" {f}")
                date_widget = urwid.Text(('date', f" {mod_time}"), align='right')
                size_widget = urwid.Text(('size', f" {size_label}"), align='right')
                
                # Combine into a single row with three columns
                item_row = urwid.Columns([
                    ('weight', 5, name_widget),
                    ('weight', 3, date_widget),
                    ('weight', 2, size_widget),
                ])
                
                self.item_widgets.append(urwid.AttrMap(item_row, 'normal', 'selected'))
                
        except Exception as e:
            # Error accessing directory
            self.all_items = []
            self.selected_index = -1
            self.item_widgets = []
            self.item_info = []
            
            error_text = urwid.Text(f"Error accessing directory: {str(e)}", align='center')
            self.item_widgets.append(urwid.AttrMap(error_text, 'error'))
        
        # Create list widgets
        self.item_list = urwid.SimpleListWalker(self.item_widgets)
        self.listbox = urwid.ListBox(self.item_list)
        self.listbox.ignore_focus = True
        self.item_panel = urwid.LineBox(
            urwid.Padding(self.listbox, left=1, right=1),
            title="Files and Directories",
            title_attr='header'
        )

        # Metadata Panel
        self.metadata_text = urwid.Text("Select an item to view details.")
        self.metadata_panel = urwid.LineBox(
            urwid.Padding(self.metadata_text, left=1, right=1),
            title="Item Details",
            title_attr='header'
        )

    def _update_selection(self):
        if 0 <= self.selected_index < len(self.item_widgets):
            for i, widget in enumerate(self.item_widgets):
                widget.set_attr_map({None: 'selected' if i == self.selected_index else 'normal'})
            
            # Update metadata panel
            if self.current_dir != os.path.expanduser("~") and self.selected_index == 0:
                # ".." parent directory
                parent_dir = os.path.dirname(self.current_dir) or self.current_dir
                self.metadata_text.set_text(f"Name: ..\nType: Parent Directory\nPath: {parent_dir}")
            else:
                # Adjust for ".." if present
                item_index = self.selected_index
                if self.current_dir != os.path.expanduser("~"):
                    item_index -= 1
                
                if 0 <= item_index < len(self.all_items):
                    selected_item = self.all_items[item_index]
                    item_path = os.path.join(self.current_dir, selected_item)
                    self.metadata_text.set_text(get_file_metadata(item_path))
                else:
                    self.metadata_text.set_text("No item selected")
            
            if self.listbox:
                self.listbox.set_focus(self.selected_index)

    def go_up_directory(self):
        """Navigate to parent directory."""
        parent_dir = os.path.dirname(self.current_dir)
        if parent_dir and self.current_dir != os.path.expanduser("~"):
            self.change_directory(parent_dir)
        else:
            if self.menu_bar:
                self.menu_bar.show_error_dialog("Info", "Already at root directory")

    def change_directory(self, new_dir):
        """Change to a new directory and update the display."""
        try:
            # Update current directory
            self.current_dir = os.path.abspath(new_dir)
            
            # Rebuild the UI with new directory contents
            self.build_ui()
            
            # Update the main loop widget
            if self.loop:
                self.loop.widget = self.body
            
            # Update selection
            self._update_selection()
                
        except Exception as e:
            if self.menu_bar:
                self.menu_bar.show_error_dialog("Error", f"Cannot change directory: {str(e)}")

    def open_selected_item(self):
        """Open the selected item (enter directory or file)."""
        if self.selected_index < 0 or self.selected_index >= len(self.item_widgets):
            return
            
        # Check if we're selecting ".."
        if self.current_dir != os.path.expanduser("~") and self.selected_index == 0:
            self.go_up_directory()
        else:
            # Adjust for ".." if present
            item_index = self.selected_index
            if self.current_dir != os.path.expanduser("~"):
                item_index -= 1
            
            if 0 <= item_index < len(self.directories):
                # It's a directory - navigate into it
                dir_name = self.directories[item_index]
                new_dir = os.path.join(self.current_dir, dir_name)
                self.change_directory(new_dir)
            elif item_index < len(self.all_items):
                # It's a file
                file_index = item_index - len(self.directories)
                if 0 <= file_index < len(self.files):
                    file_name = self.files[file_index]
                    if self.menu_bar:
                        self.menu_bar.show_error_dialog("Info", f"Selected file: {file_name}\n(File opening not implemented)")

    def handle_input(self, key):
        if key.lower() == 'q' or key == 'ctrl q':
            if self.menu_bar:
                self.menu_bar.show_exit_confirmation()
        elif key == 'f10':
            if self.menu_bar:
                self.menu_bar.show_submenu("File", self.menu_bar.menu_items[0][1])
        elif key == 'esc':
            if self.menu_bar and self.menu_bar.active_menu:
                self.menu_bar.close_menu()
            else:
                return
        elif key == 'up' and self.selected_index > 0:
            self.selected_index -= 1
            self._update_selection()
        elif key == 'down' and self.selected_index < len(self.item_widgets) - 1:
            self.selected_index += 1
            self._update_selection()
        elif key == 'enter':
            self.open_selected_item()
        elif key == 'backspace':
            self.go_up_directory()
        else:
            return

    def run(self):
        # Create MainLoop first with temporary body
        self.loop = urwid.MainLoop(
            urwid.SolidFill(),  # Temporary widget
            palette=PALETTE,
            unhandled_input=self.handle_input,
            handle_mouse=False
        )
        
        # Now create MenuBar with reference to the loop and file_lister
        self.menu_bar = MenuBar(self.loop, self)
        
        # Build the complete UI with menu bar
        self.build_ui()
        
        # Set the main loop widget to our body
        self.loop.widget = self.body
        
        # Set initial selection
        self._update_selection()
        
        # Run the main loop
        self.loop.run()

if __name__ == "__main__":
    FileLister().run()
