import os
import shutil
import curses
import time
import subprocess
import os
import sys


TAB = getattr(curses, "KEY_TAB", 9)

def sort_popup(stdscr):
    options = [
        "Name (A → Z)",
        "Name (Z → A)",
        "Size (small → large)",
        "Size (large → small)",
        "Date (old → new)",
        "Date (new → old)"
    ]

    h, w = stdscr.getmaxyx()
    win_h = len(options) + 4
    win_w = 30
    win_y = (h - win_h) // 2
    win_x = (w - win_w) // 2

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.keypad(True)          # ⭐ REQUIRED ⭐
    win.box()
    win.addstr(1, 2, "Sort by:")

    idx = 0

    while True:
        for i, opt in enumerate(options):
            attr = curses.A_REVERSE if i == idx else curses.A_NORMAL
            win.addstr(3 + i, 2, opt.ljust(win_w - 4), attr)

        win.refresh()
        key = win.getch()

        if key == curses.KEY_UP:
            idx = (idx - 1) % len(options)
        elif key == curses.KEY_DOWN:
            idx = (idx + 1) % len(options)
        elif key in (10, 13):  # Enter
            return idx
        elif key == 27:        # ESC
            return None

def sort_items(path, items, mode):
    # Remove ".." temporarily
    real_items = items[1:]

    def full(item):
        return os.path.join(path, item)

    if mode == 0:  # Name A→Z
        real_items.sort()
    elif mode == 1:  # Name Z→A
        real_items.sort(reverse=True)
    elif mode == 2:  # Size small→large
        real_items.sort(key=lambda x: os.path.getsize(full(x)))
    elif mode == 3:  # Size large→small
        real_items.sort(key=lambda x: os.path.getsize(full(x)), reverse=True)
    elif mode == 4:  # Date old→new
        real_items.sort(key=lambda x: os.path.getmtime(full(x)))
    elif mode == 5:  # Date new→old
        real_items.sort(key=lambda x: os.path.getmtime(full(x)), reverse=True)

    return [".."] + real_items

def input_box(stdscr, prompt):
    curses.echo()
    h, w = stdscr.getmaxyx()

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(h - 3, 1, prompt.ljust(w - 2))
    stdscr.attroff(curses.color_pair(1))

    stdscr.move(h - 2, 1)
    stdscr.clrtoeol()

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(h - 2, 1, "> ")
    stdscr.attroff(curses.color_pair(1))

    stdscr.refresh()

    path = stdscr.getstr(h - 2, 3, w - 4).decode("utf-8")
    curses.noecho()
    return path.strip()

def safe_date(mtime):
    try:
        if mtime > 0:
            return time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    except:
        pass
    return "---------- --:--"

def run_file(path, name):
    full = os.path.join(path, name)

    # Executable
    if name.lower().endswith(".exe"):
        subprocess.Popen([full], shell=True)

    # Batch file
    elif name.lower().endswith(".bat") or name.lower().endswith(".cmd"):
        subprocess.Popen(["cmd.exe", "/c", full], shell=True)

    # PowerShell script
    elif name.lower().endswith(".ps1"):
        subprocess.Popen([
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", full
        ], shell=True)

    # Python script (optional)
    elif name.lower().endswith(".py"):
        subprocess.Popen([sys.executable, full], shell=True)

    # Everything else: open with default Windows app
    else:
        os.startfile(full)

def draw_title_bar(stdscr, path, items, index):
    if not items:
        return

    name = items[index]
    full = os.path.join(path, name)

    # Get stats
    try:
        stat = os.stat(full)
        size = stat.st_size
        mtime = stat.st_mtime
    except:
        size = 0
        mtime = 0

    # Format size
    if size < 1024:
        size_str = f"{size} B"
    elif size < 1024 * 1024:
        size_str = f"{size // 1024} KB"
    else:
        size_str = f"{size // (1024 * 1024)} MB"

    # Format date
    #date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime))
    date_str = safe_date(mtime)


    # Build line
    line = f"{name}   {size_str}   {date_str}"

    h, w = stdscr.getmaxyx()

    # Draw title bar one line above the command bar
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(h - 2, 1, line[:w - 2])
    stdscr.attroff(curses.color_pair(1))


def draw_panel_frame(win):
    win.border('|', '|', '=', '=', '+', '+', '+', '+')

def init_colors():
    curses.start_color()
    curses.use_default_colors()

    # Background color pair
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)

    # Selected item
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)

    # Normal item
    curses.init_pair(3, curses.COLOR_WHITE, -1)

def command_line(stdscr):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 2, 1, "Command: ")
    stdscr.clrtoeol()
    stdscr.refresh()

    curses.echo()
    cmd = stdscr.getstr(h - 2, 10, 200).decode("utf-8")
    curses.noecho()

    return cmd

def confirm_dialog(stdscr, message):
    h, w = stdscr.getmaxyx()
    win_h = 5
    win_w = len(message) + 10
    win_y = (h - win_h) // 2
    win_x = (w - win_w) // 2

    win = curses.newwin(win_h, win_w, win_y, win_x)
    win.box()
    win.addstr(1, 2, message)
    win.addstr(3, 2, "[Y]es   [N]o")
    win.refresh()

    while True:
        key = win.getch()
        if key in (ord('y'), ord('Y')):
            return True
        if key in (ord('n'), ord('N')):
            return False
        
def edit_file(path, name):
    full = os.path.join(path, name)
    if os.path.isdir(full):
        return "Cannot edit a directory."

    # Windows
    if os.name == "nt":
        os.system(f'notepad "{full}"')
    else:
        # Linux / macOS
        os.system(f'nano "{full}"')
 
def list_dir(path):
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        items = ["<permission denied>"]

    # Insert parent directory entry
    return [".."] + items

def is_dir(path, name):
    full = os.path.join(path, name)
    return os.path.isdir(full)

def copy_item(src_dir, name, dst_dir):
    src = os.path.join(src_dir, name)
    dst = os.path.join(dst_dir, name)
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        return str(e)
    return None

def move_item(src_dir, name, dst_dir):
    src = os.path.join(src_dir, name)
    dst = os.path.join(dst_dir, name)
    try:
        shutil.move(src, dst)
    except Exception as e:
        return str(e)
    return None

def delete_item(dir_path, name):
    target = os.path.join(dir_path, name)
    try:
        if os.path.isdir(target):
            shutil.rmtree(target)
        else:
            os.remove(target)
    except Exception as e:
        return str(e)
    return None

def file_icon(full):
    name = os.path.basename(full).lower()

    # Parent directory
    if name == "..":
        return "■"

    # Directory
    if os.path.isdir(full):
        return "■"

    # Executable
    if name.endswith(".exe"):
        return "⚙️"

    # Python file
    if name.endswith(".py"):
        return "π"

    # Text file
    if name.endswith(".txt"):
        return "✎"

    # Archives
    if name.endswith((".zip", ".rar", ".7z")):
        return "⛁"

    # Images
    if name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
        return "▣"

    # Default file
    return "□"


def draw_panel(stdscr, path, items, index, scroll, active, startx, width):
    h, w = stdscr.getmaxyx()
    visible_rows = h - 3

    # Fill panel background
    for y in range(h - 1):
        stdscr.addstr(y, startx, " " * width, curses.color_pair(1))

    # Draw panel frame
    stdscr.vline(1, startx, curses.ACS_VLINE, h - 2)
    stdscr.vline(1, startx + width - 1, curses.ACS_VLINE, h - 2)
    stdscr.hline(0, startx, curses.ACS_HLINE, width)
    stdscr.hline(h - 1, startx, curses.ACS_HLINE, width)

    # Panel title (path)
    stdscr.addstr(0, startx + 1, path[:width - 2], curses.color_pair(1))

    # Slice visible window
    window = items[scroll : scroll + visible_rows]

    for i, name in enumerate(window):
        y = i + 1
        attr = curses.A_REVERSE if active and (scroll + i) == index else curses.A_NORMAL

        full = os.path.join(path, name)

        # ICON
        icon = file_icon(full)

        # Determine color
        if os.path.isdir(full):
            color = curses.color_pair(1)
        elif os.access(full, os.X_OK):
            color = curses.color_pair(2)
        else:
            color = curses.color_pair(3)

        # --- NEW: size + date ---
        try:
            st = os.stat(full)
            size = st.st_size
            mtime = st.st_mtime
        except:
            size = 0
            mtime = 0

        # Format size
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size // 1024} KB"
        else:
            size_str = f"{size // (1024 * 1024)} MB"

        # Format date
        date_str = safe_date(mtime)

        # Build final line WITH ICON
        # icon = 4 chars, so name gets 26 instead of 30
        line = f"{icon} {name:<28} {size_str:>10}  {date_str}"

        stdscr.addstr(y, startx + 1, line[:width - 2], attr | color)


def status_line(stdscr, msg="F2 CMD  F4 Edit  F5 Copy  F6 Move  F7 Input dir  F8 Delete  S Sort  Tab Switch  Enter Open  q Quit"):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 1, 1, msg[:w - 2])
    

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # PANEL OBJECTS MUST BE CREATED HERE
    left_panel = Panel(os.getcwd())
    right_panel = Panel(os.getcwd())

    active_left = True   # <-- REQUIRED

    # Directory = blue
    curses.init_pair(1, curses.COLOR_BLUE, -1)

    # Executable = green
    curses.init_pair(2, curses.COLOR_GREEN, -1)

    # Normal file = default
    curses.init_pair(3, -1, -1)

    stdscr.keypad(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    
    stdscr.bkgd(' ', curses.color_pair(1))
    stdscr.clear()

    left_path = os.getcwd()
    right_path = os.getcwd()
    left_items = list_dir(left_path)
    right_items = list_dir(right_path)
    left_idx = 0
    right_idx = 0
    left_scroll = 0
    right_scroll = 0
    active_panel = "left"
    message = ""

    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        half = w // 2

        draw_panel(
            stdscr,
            left_path,
            left_items,
            left_idx,
            left_scroll,
            active_panel == "left",
            0,
            half
        )

        draw_panel(
            stdscr,
            right_path,
            right_items,
            right_idx,
            right_scroll,
            active_panel == "right",
            half,
            w - half
        )
        
        init_colors()
        
        draw_title_bar(
            stdscr,
            left_path if active_panel == "left" else right_path,
            left_items if active_panel == "left" else right_items,
            left_idx if active_panel == "left" else right_idx
        )

        status_line(stdscr, message or "F2 CMD  F4 Edit  F5 Copy  F6 Move  F7 Input dir  F8 Delete  s Sort  Tab Switch  Enter Open  q Quit")
        stdscr.refresh()

        key = stdscr.getch()
        message = ""

        if key == ord('q'):
            break
        
        # Switch panel
        elif key == TAB:

            active_panel = "right" if active_panel == "left" else "left"

        # Arrow navigation
        elif key == curses.KEY_UP:
            if active_panel == "left":
                if left_idx > 0:
                    left_idx -= 1
                    if left_idx < left_scroll:
                        left_scroll -= 1
            else:
                if right_idx > 0:
                    right_idx -= 1
                    if right_idx < right_scroll:
                        right_scroll -= 1

        elif key == curses.KEY_DOWN:
            if active_panel == "left":
                if left_idx < len(left_items) - 1:
                    left_idx += 1
                    h, w = stdscr.getmaxyx()
                    visible = h - 3
                    if left_idx >= left_scroll + visible:
                        left_scroll += 1
            else:
                if right_idx < len(right_items) - 1:
                    right_idx += 1
                    h, w = stdscr.getmaxyx()
                    visible = h - 3
                    if right_idx >= right_scroll + visible:
                        right_scroll += 1
                        
        elif key == curses.KEY_PPAGE:  # PgUp
                h, w = stdscr.getmaxyx()
                visible = h - 3
                if active_panel == "left":
                    left_idx = max(0, left_idx - visible)
                    left_scroll = max(0, left_scroll - visible)
                else:
                    right_idx = max(0, right_idx - visible)
                    right_scroll = max(0, right_scroll - visible)

        elif key == curses.KEY_NPAGE:  # PgDn
                h, w = stdscr.getmaxyx()
                visible = h - 3
                if active_panel == "left":
                    left_idx = min(len(left_items) - 1, left_idx + visible)
                    left_scroll = min(len(left_items) - visible, left_scroll + visible)
                else:
                    right_idx = min(len(right_items) - 1, right_idx + visible)
                    right_scroll = min(len(right_items) - visible, right_scroll + visible)
                    
        elif key == curses.KEY_HOME:
            if active_panel == "left":
                left_idx = 0
                left_scroll = 0
            else:
                right_idx = 0
                right_scroll = 0

        elif key == curses.KEY_END:
            if active_panel == "left":
                left_idx = len(left_items) - 1
                h, w = stdscr.getmaxyx()
                visible = h - 3
                left_scroll = max(0, len(left_items) - visible)
            else:
                right_idx = len(right_items) - 1
                h, w = stdscr.getmaxyx()
                visible = h - 3
                right_scroll = max(0, len(right_items) - visible)
                        
        # Enter: open directory
        elif key in (curses.KEY_ENTER, 10, 13):
            if active_panel == "left" and left_items:
                name = left_items[left_idx]

                if name == "..":
                    # Go up one directory
                    parent = os.path.dirname(left_path)
                    left_path = parent if parent else left_path
                    left_items = list_dir(left_path)
                    left_idx = 0

                elif is_dir(left_path, name):
                    left_path = os.path.join(left_path, name)
                    left_items = list_dir(left_path)
                    left_idx = 0
                    left_scroll = 0     # ← REQUIRED
                    
                else:
                    run_file(left_path, name)

            elif active_panel == "right" and right_items:
                name = right_items[right_idx]

                if name == "..":
                    parent = os.path.dirname(right_path)
                    right_path = parent if parent else right_path
                    right_items = list_dir(right_path)
                    right_idx = 0

                elif is_dir(right_path, name):
                    right_path = os.path.join(right_path, name)
                    right_items = list_dir(right_path)
                    right_idx = 0
                    right_scroll = 0    # ← REQUIRED
                
                else:
                    run_file(right_path, name)
                    
        elif key == curses.KEY_F2:
            path = left_path if active_panel == "left" else right_path

            curses.endwin()

            if os.name == "nt":
                cmd = f'start "" cmd.exe /K "cd /d {path}"'
                subprocess.call(cmd, shell=True)
            else:
                subprocess.call(['x-terminal-emulator', '-e', f'cd "{path}" && bash'], shell=True)

            stdscr.clear()
            stdscr.refresh()


        elif key == curses.KEY_F4:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                message = edit_file(left_path, name)
            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                message = edit_file(right_path, name)

        # F5: copy
        elif key == curses.KEY_F5:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                if confirm_dialog(stdscr, f"Copy '{name}' to right panel?"):
                    err = copy_item(left_path, name, right_path)
                    if err:
                        message = f"Copy error: {err}"
                right_items = list_dir(right_path)
                right_scroll = 0

            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                if confirm_dialog(stdscr, f"Copy '{name}' to left panel?"):
                    err = copy_item(right_path, name, left_path)
                    if err:
                        message = f"Copy error: {err}"
                left_items = list_dir(left_path)
                left_scroll = 0

        # F6: move
        elif key == curses.KEY_F6:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                if confirm_dialog(stdscr, f"Move '{name}' to right panel?"):
                    err = move_item(left_path, name, right_path)
                    if err:
                        message = f"Move error: {err}"
                left_items = list_dir(left_path)
                right_items = list_dir(right_path)
                left_scroll = right_scroll = 0

            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                if confirm_dialog(stdscr, f"Move '{name}' to left panel?"):
                    err = move_item(right_path, name, left_path)
                    if err:
                        message = f"Move error: {err}"
                right_items = list_dir(right_path)
                left_items = list_dir(left_path)
                left_scroll = right_scroll = 0
                
        elif key == curses.KEY_F7:
            new_path = input_box(stdscr, "Enter directory path:")

            if os.path.isdir(new_path):
                if active_panel == "left":
                    left_path = new_path
                    left_items = list_dir(left_path)
                    left_idx = 0
                    left_scroll = 0
                else:
                    right_path = new_path
                    right_items = list_dir(right_path)
                    right_idx = 0
                    right_scroll = 0
            else:
                message = f"Invalid directory: {new_path}"
                
        elif key == ord('s'):
            mode = sort_popup(stdscr)
            if mode is not None:
                if active_panel == "left":
                    left_items = sort_items(left_path, left_items, mode)
                    left_idx = 0
                    left_scroll = 0
                else:
                    right_items = sort_items(right_path, right_items, mode)
                    right_idx = 0
                    right_scroll = 0
                message = f"Sorted using mode {mode}"
                
                      

        # F8: delete
        elif key == curses.KEY_F8:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                if confirm_dialog(stdscr, f"Delete '{name}'?"):
                    err = delete_item(left_path, name)
                    if err:
                        message = f"Delete error: {err}"
                left_items = list_dir(left_path)
                left_idx = min(left_idx, max(0, len(left_items) - 1))
                left_scroll = 0

            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                if confirm_dialog(stdscr, f"Delete '{name}'?"):
                    err = delete_item(right_path, name)
                    if err:
                        message = f"Delete error: {err}"
                right_items = list_dir(right_path)
                right_idx = min(right_idx, max(0, len(right_items) - 1))
                right_scroll = 0

        # Mouse: simple click selection
        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, _ = curses.getmouse()
                if 1 <= my < h - 1:
                    if mx < half:
                        active_panel = "left"
                        if my - 1 < len(left_items):
                            left_idx = my - 1
                    else:
                        active_panel = "right"
                        if my - 1 < len(right_items):
                            right_idx = my - 1
            except curses.error:
                pass
            
class Panel:
    def __init__(self, path):
        self.path = path
        self.items = []
        self.index = 0
        self.scroll = 0
            
if __name__ == "__main__":
    curses.wrapper(main)
