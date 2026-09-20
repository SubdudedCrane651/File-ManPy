import os
import shutil
import curses

TAB = getattr(curses, "KEY_TAB", 9)

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

def draw_panel(stdscr, path, items, index, active, startx, width):
    h, w = stdscr.getmaxyx()
    title = f"{path}"
    stdscr.addstr(0, startx + 1, title[:width - 2])

    for i, name in enumerate(items[:h - 3]):
        y = i + 1
        attr = curses.A_NORMAL
        if active and i == index:
            attr = curses.A_REVERSE
        display = name
        if is_dir(path, name):
            display += "/"
        stdscr.addstr(y, startx + 1, display[:width - 2], attr)

def status_line(stdscr, msg="F5 Copy  F6 Move  F8 Delete  Tab Switch  Enter Open  q Quit"):
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h - 1, 1, msg[:w - 2])

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)

    left_path = os.getcwd()
    right_path = os.getcwd()
    left_items = list_dir(left_path)
    right_items = list_dir(right_path)
    left_idx = 0
    right_idx = 0
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
            active_panel == "left",
            0,
            half
        )
        draw_panel(
            stdscr,
            right_path,
            right_items,
            right_idx,
            active_panel == "right",
            half,
            w - half
        )

        status_line(stdscr, message or "F5 Copy  F6 Move  F8 Delete  Tab Switch  Enter Open  q Quit")
        stdscr.refresh()

        key = stdscr.getch()
        message = ""

        if key == ord('q'):
            break

        # Switch panel
        elif key == TAB:

            active_panel = "right" if active_panel == "left" else "left"

        # Arrow navigation
        elif key in (curses.KEY_UP, curses.KEY_DOWN):
            if active_panel == "left":
                if key == curses.KEY_UP and left_idx > 0:
                    left_idx -= 1
                elif key == curses.KEY_DOWN and left_idx < len(left_items) - 1:
                    left_idx += 1
            else:
                if key == curses.KEY_UP and right_idx > 0:
                    right_idx -= 1
                elif key == curses.KEY_DOWN and right_idx < len(right_items) - 1:
                    right_idx += 1

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

        # F5: copy
        elif key == curses.KEY_F5:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                err = copy_item(left_path, name, right_path)
                if err:
                    message = f"Copy error: {err}"
                right_items = list_dir(right_path)
            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                err = copy_item(right_path, name, left_path)
                if err:
                    message = f"Copy error: {err}"
                left_items = list_dir(left_path)

        # F6: move
        elif key == curses.KEY_F6:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                err = move_item(left_path, name, right_path)
                if err:
                    message = f"Move error: {err}"
                left_items = list_dir(left_path)
                right_items = list_dir(right_path)
                left_idx = min(left_idx, max(0, len(left_items) - 1))
            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                err = move_item(right_path, name, left_path)
                if err:
                    message = f"Move error: {err}"
                right_items = list_dir(right_path)
                left_items = list_dir(left_path)
                right_idx = min(right_idx, max(0, len(right_items) - 1))

        # F8: delete
        elif key == curses.KEY_F8:
            if active_panel == "left" and left_items:
                name = left_items[left_idx]
                err = delete_item(left_path, name)
                if err:
                    message = f"Delete error: {err}"
                left_items = list_dir(left_path)
                left_idx = min(left_idx, max(0, len(left_items) - 1))
            elif active_panel == "right" and right_items:
                name = right_items[right_idx]
                err = delete_item(right_path, name)
                if err:
                    message = f"Delete error: {err}"
                right_items = list_dir(right_path)
                right_idx = min(right_idx, max(0, len(right_items) - 1))

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
