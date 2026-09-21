import os
import shutil
import curses

TAB = getattr(curses, "KEY_TAB", 9)

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

def draw_panel(stdscr, path, items, index, scroll, active, startx, width):
    h, w = stdscr.getmaxyx()
    visible_rows = h - 3

    stdscr.addstr(0, startx + 1, path[:width - 2])

    # Slice the visible window
    window = items[scroll : scroll + visible_rows]

    for i, name in enumerate(window):
        y = i + 1
        attr = curses.A_REVERSE if active and (scroll + i) == index else curses.A_NORMAL
        display = name + ("/" if os.path.isdir(os.path.join(path, name)) else "")
        # Determine color
        full = os.path.join(path, name)
        if os.path.isdir(full):
            color = curses.color_pair(1)
        elif os.access(full, os.X_OK):
            color = curses.color_pair(2)
        else:
            color = curses.color_pair(3)

        stdscr.addstr(y, startx + 1, display[:width - 2], attr | color)


def status_line(stdscr, msg="F2 CMD  F4 Edit  F5 Copy  F6 Move  F8 Delete  Tab Switch  Enter Open  q Quit"):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 1, 1, msg[:w - 2])

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # Directory = blue
    curses.init_pair(1, curses.COLOR_BLUE, -1)

    # Executable = green
    curses.init_pair(2, curses.COLOR_GREEN, -1)

    # Normal file = default
    curses.init_pair(3, -1, -1)

    stdscr.keypad(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

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

        status_line(stdscr, message or "F2 CMD  F4 Edit  F5 Copy  F6 Move  F8 Delete  Tab Switch  Enter Open  q Quit")
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
                    
        elif key == curses.KEY_F2:
            cmd = command_line(stdscr)
            os.system(cmd)
            message = f"Ran: {cmd}"                    
                    
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

if __name__ == "__main__":
    curses.wrapper(main)
