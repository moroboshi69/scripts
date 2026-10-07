#!/usr/bin/env python3
"""EmulationStation Gamelist Sorter
Author: moroboshi69
Date: 2026-10-07

An interactive terminal UI to reorder, filter, and manage system entries 
in EmulationStation's `es_systems.cfg`.

Features:
    - Automatically bootstraps individual system XML files into `/home/ark/.emulationstation/es_systems.d/`.
    - Filters out inactive systems or systems with empty ROM directories.
    - Interactive Sort Menu (by ID, Full Name, Manufacturer, or Reset).
"""

import os
import glob
import re
import curses
import time
import struct
import traceback

ES_DIR = os.path.expanduser("~/.emulationstation")
D_DIR = os.path.join(ES_DIR, "es_systems.d")
OUTPUT_FILE = os.path.join(ES_DIR, "es_systems.cfg")
MASTER_CONFIG = "/etc/emulationstation/es_systems.cfg"

SYSTEM_CACHE = {}

class HandheldInput:
    def __init__(self):
        self.fd = None
        self.held_action = None
        self.hold_counter = 0
        self.find_controller_device()

    def find_controller_device(self):
        for event_path in sorted(glob.glob("/dev/input/event*")):
            try:
                name_path = f"/sys/class/input/{os.path.basename(event_path)}/device/name"
                if os.path.exists(name_path):
                    with open(name_path, "r") as nf:
                        name = nf.read().strip().lower()
                    if any(k in name for k in ["joypad", "gamepad", "joystick", "keys", "controller"]):
                        self.fd = os.open(event_path, os.O_RDONLY | os.O_NONBLOCK)
                        break
            except Exception:
                continue
        
        if self.fd is None and os.path.exists("/dev/input/event0"):
            try:
                self.fd = os.open("/dev/input/event0", os.O_RDONLY | os.O_NONBLOCK)
            except Exception:
                pass

    def poll_action(self):
        if not self.fd:
            return None
             
        current_event_action = None
        
        try:
            while True:
                data = os.read(self.fd, 24)
                if len(data) < 24:
                    break
                _, _, ev_type, code, value = struct.unpack('llHhi', data)
               
                action = None
                if ev_type == 1:  # Key event
                    if code in [103, 544]: action = "NAV_UP"
                    elif code in [108, 545]: action = "NAV_DOWN"
                    elif code == 310:        action = "PAGE_UP"    # L Button
                    elif code == 311:        action = "PAGE_DOWN"  # R Button
                    elif code == 305:        action = "MOVE_UP"    # Button A
                    elif code == 304:        action = "MOVE_DOWN"  # Button B
                    elif code == 307:        action = "SORT_MENU"  # Button X
                    elif code == 705:        action = "START"      # START
                    elif code == 704:        action = "SELECT"     # SELECT
                elif ev_type == 3:  # Axis event
                    if code in [1, 17]:
                        if value < -10000: action = "NAV_UP"
                        elif value > 10000: action = "NAV_DOWN"
                       
                if action:
                    if value in (1, 2):  # Press or repeat
                        current_event_action = action
                        self.held_action = action
                        self.hold_counter = 0
                    elif value == 0:  # Release
                        if self.held_action == action:
                            self.held_action = None
                            self.hold_counter = 0
        except (BlockingIOError, InterruptedError):
            pass
        except Exception:
            pass
             
        if current_event_action:
            return current_event_action
             
        if self.held_action in ("NAV_UP", "NAV_DOWN", "MOVE_UP", "MOVE_DOWN", "PAGE_UP", "PAGE_DOWN"):
            self.hold_counter += 1
            if self.hold_counter > 12:
                if (self.hold_counter - 12) % 4 == 0:
                    return self.held_action
        
        return None

def bootstrap_systems():
    os.makedirs(D_DIR, exist_ok=True)
    if not os.listdir(D_DIR):
        if not os.path.exists(MASTER_CONFIG):
            raise FileNotFoundError(f"Master config not found at {MASTER_CONFIG}")
        with open(MASTER_CONFIG, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
         
        blocks = re.findall(r'(<system>.*?</system>)', content, re.DOTALL | re.IGNORECASE)
        for block in blocks:
            name_match = re.search(r'<name>\s*(.*?)\s*</name>', block, re.IGNORECASE)
            if name_match:
                sys_name = name_match.group(1)
                out_path = os.path.join(D_DIR, f"{sys_name}.xml")
                with open(out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(block)
    return True

def clean_prefixes():
    for f in glob.glob(os.path.join(D_DIR, "[0-9][0-9]_*.xml")):
        base = os.path.basename(f)
        clean_name = re.sub(r'^[0-9]{2}_', '', base)
        os.rename(f, os.path.join(D_DIR, clean_name))

def system_has_games(content):
    path_match = re.search(r'<path>\s*(.*?)\s*</path>', content, re.IGNORECASE)
    ext_match = re.search(r'<extension>\s*(.*?)\s*</extension>', content, re.IGNORECASE)
    
    if not path_match:
        return True
         
    rom_path = path_match.group(1).strip()
    rom_path = os.path.expanduser(rom_path)
    
    if not os.path.isabs(rom_path):
        clean_rom_path = rom_path.lstrip('./')
        for base in ['/roms', os.path.expanduser('~/roms'), os.path.expanduser('~/.emulationstation'), '/home/ark/roms', '/storage/roms']:
            test_path = os.path.join(base, clean_rom_path)
            if os.path.exists(test_path):
                rom_path = test_path
                break
    
    if not os.path.exists(rom_path) or not os.path.isdir(rom_path):
        return False
         
    ext_str = ext_match.group(1) if ext_match else ""
    extensions = tuple(ext.strip().lower() for ext in ext_str.split()) if ext_str else ()
    
    try:
        with os.scandir(rom_path) as it:
            for entry in it:
                if entry.name.startswith('.'):
                    continue
                if entry.is_file():
                    if not extensions or entry.name.lower().endswith(extensions):
                        return True
                elif entry.is_dir():
                    try:
                        with os.scandir(entry.path) as sub_it:
                            for sub_entry in sub_it:
                                if not sub_entry.name.startswith('.') and (not extensions or sub_entry.name.lower().endswith(extensions)):
                                    return True
                    except Exception:
                        pass
    except Exception:
        return False
         
    return False

def get_system_info(sys_name):
    if sys_name in SYSTEM_CACHE:
        return SYSTEM_CACHE[sys_name]

    xml_path = os.path.join(D_DIR, f"{sys_name}.xml")
    if not os.path.exists(xml_path):
        res = (None, None, True)
        SYSTEM_CACHE[sys_name] = res
        return res

    with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    if re.search(r'<hidden>\s*(true|1)\s*</hidden>', content, re.IGNORECASE) or not system_has_games(content):
        res = (None, None, True)
        SYSTEM_CACHE[sys_name] = res
        return res
         
    fn_match = re.search(r'<fullname>\s*(.*?)\s*</fullname>', content, re.IGNORECASE)
    fullname = fn_match.group(1) if fn_match else sys_name
    
    res = (sys_name, fullname, False)
    SYSTEM_CACHE[sys_name] = res
    return res

def get_active_systems():
    active = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8", errors="ignore") as f:
            out_content = f.read()
        names = re.findall(r'<name>\s*(.*?)\s*</name>', out_content, re.IGNORECASE)
        for name in names:
            s_name, _, _ = get_system_info(name)
            if s_name and s_name not in active:
                active.append(s_name)
             
    for f in sorted(os.listdir(D_DIR)):
        if f.endswith(".xml") and not f.startswith("."):
            sys_name = f[:-4]
            s_name, _, _ = get_system_info(sys_name)
            if s_name and s_name not in active:
                active.append(s_name)
    return active

def get_category_color(sys_name):
    s = sys_name.lower().strip()
    
    # Sets to prevent substring overlapping bugs
    nintendo = {'nes', 'snes', 'n64', 'n64dd', 'gb', 'gbc', 'gba', 'nds', '3ds', 'gc', 'gamecube', 'virtualboy', 'pokemini', 'switch', 'wii', 'wiiu', 'fds'}
    sega = {'sega32x', 'segacd', 'sega-cd', 'mastersystem', 'megadrive', 'genesis', 'saturn', 'dc', 'dreamcast', 'gamegear', 'sg1000', 'sc3000'}
    arcade_neogeo = {'arcade', 'mame', 'fba', 'fbneo', 'neogeo', 'cps1', 'cps2', 'cps3', 'atomiswave', 'naomi', 'pgm', 'cave', 'daphne', 'ineogeo'}
    ngp_portable = {'ngp', 'ngpc', 'neogeopocket', 'neogeopocketcolor', 'swan', 'wonderswan', 'wonderswancolor', 'gamewatch'}
    sony = {'psx', 'ps1', 'ps2', 'psp', 'psvita', 'sonypsp'}
    nec = {'pce', 'pcengine', 'tg16', 'turbografx', 'supergrafx', 'pcecd', 'pcenginecd'}
    atari = {'atari2600', 'atari5200', 'atari7800', 'atarilynx', 'atarijaguar', 'atari8bit', 'atariest', 'st'}
    computers = {'amstrad', 'c64', 'commodore', 'amiga', 'zxspectrum', 'msx', 'msx2', 'x1', 'x68000', 'pc', 'dos', 'scummvm', 'oric', 'electron', 'bbc', 'trs80', 'apple2'}
    fantasy = {'pico-8', 'pico8', 'TIC-80', 'lexaloffle'}

    if s in nintendo:
        return 5  # Nintendo (Magenta)
    elif s in sega:
        return 6  # Sega (Cyan)
    elif s in arcade_neogeo:
        return 7  # Arcade / MAME (Yellow)
    elif s in ngp_portable:
        return 8  # Handhelds / NGP / WonderSwan (Green)
    elif s in sony:
        return 9  # Sony (Red)
    elif s in nec:
        return 10 # NEC (Blue)
    elif s in atari:
        return 11 # Atari (White)
    elif s in computers or s in fantasy:
        return 8  # Computers & Fantasy Consoles (Green)
    
    # Fallback substring checks for compound or custom names
    if any(k in s for k in ['nes', 'snes', 'n64', 'gameboy', 'pokemon', 'switch', 'wii']):
        return 5
    elif any(k in s for k in ['sega', 'megadrive', 'genesis', 'saturn', 'dreamcast', 'gear']):
        return 6
    elif any(k in s for k in ['mame', 'arcade', 'neogeo', 'cps', 'fbneo', 'fba']):
        return 7
    elif any(k in s for k in ['ngp', 'wonderswan', 'pocket']):
        return 8
    elif any(k in s for k in ['playstation', 'psx', 'psp', 'sony']):
        return 9
    elif any(k in s for k in ['pce', 'turbografx', 'supergrafx']):
        return 10
    elif any(k in s for k in ['atari', 'lynx', 'jaguar']):
        return 11
    else:
        return 8  # Default Green for computers/ports

def get_manufacturer_rank(sys_name):
    s = sys_name.lower().strip()
    if s in {'nes', 'snes', 'n64', 'gb', 'gbc', 'gba', 'nds', '3ds', 'gc', 'gamecube', 'virtualboy', 'switch', 'wii'}:
        return 1
    elif s in {'sega32x', 'segacd', 'mastersystem', 'megadrive', 'genesis', 'saturn', 'dc', 'dreamcast', 'gamegear'}:
        return 2
    elif s in {'arcade', 'mame', 'fba', 'fbneo', 'neogeo', 'cps1', 'cps2', 'cps3', 'atomiswave', 'naomi'}:
        return 3
    elif s in {'psx', 'ps1', 'ps2', 'psp', 'psvita'}:
        return 4
    elif s in {'pce', 'pcengine', 'tg16', 'turbografx', 'supergrafx'}:
        return 5
    elif s in {'ngp', 'ngpc', 'neogeopocket', 'swan', 'wonderswan'}:
        return 6
    elif s in {'atari2600', 'atari5200', 'atari7800', 'atarilynx', 'atarijaguar'}:
        return 7
    else:
        return 8

def run_sort_menu(stdscr, fullnames, hw_input):
    options = [
        ("Alphabetical (System ID)", "sort_short"),
        ("Alphabetical (Full Name)", "sort_full"),
        ("By Manufacturer", "sort_mfg"),
        ("Reset to Initial Order", "reset")
    ]
     
    current_sel = 0
    h, w = stdscr.getmaxyx()
    box_w = 42
    box_h = len(options) + 4
    box_y = (h - box_h) // 2
    box_x = (w - box_w) // 2
     
    c_cyan = curses.color_pair(3) if curses.has_colors() else 0
    c_yellow = curses.color_pair(4) if curses.has_colors() else 0
     
    stdscr.nodelay(True)
    while True:
        for y in range(box_h):
            stdscr.addstr(box_y + y, box_x, " " * box_w, curses.color_pair(3) if curses.has_colors() else 0)
         
        stdscr.addch(box_y, box_x, curses.ACS_ULCORNER, c_cyan)
        stdscr.addch(box_y, box_x + box_w - 1, curses.ACS_URCORNER, c_cyan)
        stdscr.addch(box_y + box_h - 1, box_x, curses.ACS_LLCORNER, c_cyan)
        stdscr.addch(box_y + box_h - 1, box_x + box_w - 1, curses.LRCORNER if hasattr(curses, 'LRCORNER') else curses.ACS_LRCORNER, c_cyan)
         
        for x in range(box_x + 1, box_x + box_w - 1):
            stdscr.addch(box_y, x, curses.ACS_HLINE, c_cyan)
            stdscr.addch(box_y + box_h - 1, x, curses.ACS_HLINE, c_cyan)
        for y in range(box_y + 1, box_y + box_h - 1):
            stdscr.addch(y, box_x, curses.ACS_VLINE, c_cyan)
            stdscr.addch(y, box_x + box_w - 1, curses.ACS_VLINE, c_cyan)
             
        stdscr.addstr(box_y, box_x + 3, " Select Sort Method ", curses.A_BOLD | c_cyan)
         
        for idx, (label, action_key) in enumerate(options):
            row = box_y + 2 + idx
            display_label = f" {label} ".ljust(box_w - 4)
            attr = curses.A_REVERSE if idx == current_sel else 0
            if curses.has_colors() and idx != current_sel:
                attr |= c_yellow
            stdscr.addstr(row, box_x + 2, display_label, attr)
             
        stdscr.refresh()
         
        key = stdscr.getch()
        hw_action = hw_input.poll_action()

        nav = None
        if key in [curses.KEY_UP, ord('w'), ord('W')]: nav = "NAV_UP"
        elif key in [curses.KEY_DOWN, ord('s'), ord('S')]: nav = "NAV_DOWN"
        elif key in [10, 13, ord('a'), ord('A')]: nav = "CONFIRM"
        elif key in [27, ord('q'), ord('Q'), ord('b'), ord('B')]: nav = "CANCEL"
        else:
            if hw_action == "NAV_UP": nav = "NAV_UP"
            elif hw_action == "NAV_DOWN": nav = "NAV_DOWN"
            elif hw_action == "MOVE_UP": nav = "CONFIRM"
            elif hw_action == "MOVE_DOWN": nav = "CANCEL"

        if nav == "NAV_UP":
            current_sel = (current_sel - 1) % len(options)
        elif nav == "NAV_DOWN":
            current_sel = (current_sel + 1) % len(options)
        elif nav == "CONFIRM":
            return options[current_sel][1]
        elif nav == "CANCEL":
            return None

        time.sleep(0.03)

def run_menu(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
     
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        max_colors = getattr(curses, 'COLORS', 8)
         
        green_bg = 22 if max_colors >= 256 else curses.COLOR_BLACK
        red_bg = 52 if max_colors >= 256 else curses.COLOR_BLACK

        try:
            curses.init_pair(3, curses.COLOR_CYAN, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            curses.init_pair(5, curses.COLOR_MAGENTA, -1)
            curses.init_pair(6, curses.COLOR_CYAN, -1)
            curses.init_pair(7, curses.COLOR_YELLOW, -1)
            curses.init_pair(8, curses.COLOR_GREEN, -1)
            curses.init_pair(9, curses.COLOR_RED, -1)
            curses.init_pair(10, curses.COLOR_BLUE, -1)
            curses.init_pair(11, curses.COLOR_WHITE, -1)
             
            for base in range(5, 12):
                fg_color = curses.pair_content(base)[0]
                curses.init_pair(base + 10, fg_color, green_bg)

            for base in range(5, 12):
                fg_color = curses.pair_content(base)[0]
                curses.init_pair(base + 20, fg_color, red_bg)
        except Exception:
            pass

    hw_input = HandheldInput()
     
    bootstrap_systems()
    clean_prefixes()
     
    systems = get_active_systems()
    if not systems:
        stdscr.nodelay(False)
        stdscr.addstr(0, 0, "Error: No active systems found with games! Press any key to exit.")
        stdscr.refresh()
        stdscr.getch()
        return

    stdscr.nodelay(True)
    initial_systems = list(systems)

    fullnames = {sys: get_system_info(sys)[1] for sys in systems}

    current_idx = 0
    scroll_offset = 0

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
         
        if h < 14 or w < 60:
            stdscr.addstr(0, 0, "Terminal window too small! Please resize.")
            stdscr.refresh()
            time.sleep(0.1)
            continue

        modified_count = sum(1 for idx, sys in enumerate(systems) if idx != initial_systems.index(sys))
         
        c_cyan = curses.color_pair(3) if curses.has_colors() else 0
        c_yellow = curses.color_pair(4) if curses.has_colors() else 0
         
        stdscr.addstr(0, 2, " EmulationStation System Sorter ", curses.A_BOLD | c_cyan)
        if modified_count > 0:
            stdscr.addstr(0, 34, f" [ {modified_count} modified ] ", curses.A_BOLD | c_yellow)

        box_top = 2
        box_left = 2
        box_height = h - 7
        box_width = min(w - 4, 62)
        box_bottom = box_top + box_height - 1
        box_right = box_left + box_width - 1

        stdscr.addch(box_top, box_left, curses.ACS_ULCORNER, c_cyan)
        stdscr.addch(box_top, box_right, curses.ACS_URCORNER, c_cyan)
        stdscr.addch(box_bottom, box_left, curses.ACS_LLCORNER, c_cyan)
        stdscr.addch(box_bottom, box_right, curses.LRCORNER if hasattr(curses, 'LRCORNER') else curses.ACS_LRCORNER, c_cyan)
         
        for x in range(box_left + 1, box_right):
            stdscr.addch(box_top, x, curses.ACS_HLINE, c_cyan)
            stdscr.addch(box_bottom, x, curses.ACS_HLINE, c_cyan)
        for y in range(box_top + 1, box_bottom):
            stdscr.addch(y, box_left, curses.ACS_VLINE, c_cyan)
            stdscr.addch(y, box_right, curses.ACS_VLINE, c_cyan)

        stdscr.addstr(box_top, 4, " Active Systems Library ", curses.A_BOLD | c_cyan)

        viewport_top = box_top + 1
        viewport_bottom = box_bottom - 1
        max_display = viewport_bottom - viewport_top + 1
        total = len(systems)

        if current_idx < scroll_offset:
            scroll_offset = current_idx
        elif current_idx >= scroll_offset + max_display:
            scroll_offset = current_idx - max_display + 1

        for i in range(max_display):
            sys_idx = scroll_offset + i
            row = viewport_top + i
            if sys_idx >= total:
                stdscr.addstr(row, box_left + 1, " " * (box_width - 2))
                continue
                 
            sys_item = systems[sys_idx]
            fn = fullnames.get(sys_item, sys_item)
             
            orig_idx = initial_systems.index(sys_item)
            if sys_idx < orig_idx:
                arrow = "↑"
            elif sys_idx > orig_idx:
                arrow = "↓"
            else:
                arrow = " "

            max_text_len = box_width - 8
            raw_str = f"{sys_idx + 1:02d}. [{sys_item}] - {fn} {arrow}"
            if len(raw_str) > max_text_len:
                raw_str = raw_str[:max_text_len-3] + "..."
            display_str = raw_str.ljust(max_text_len)

            cat_base = get_category_color(sys_item)
             
            if curses.has_colors():
                if sys_idx < orig_idx:
                    attr = curses.color_pair(cat_base + 10)
                elif sys_idx > orig_idx:
                    attr = curses.color_pair(cat_base + 20)
                else:
                    attr = curses.color_pair(cat_base)
            else:
                attr = 0
             
            if sys_idx == current_idx:
                attr |= curses.A_REVERSE
                stdscr.addstr(row, box_left + 1, f" > {display_str} ", attr)
            else:
                stdscr.addstr(row, box_left + 1, f"   {display_str} ", attr)

        if total > max_display:
            thumb_height = max(1, int(max_display * (max_display / total)))
            thumb_pos = int(scroll_offset / (total - max_display) * (max_display - thumb_height)) if total > max_display else 0
            for i in range(max_display):
                sb_row = viewport_top + i
                sb_char = "█" if thumb_pos <= i < thumb_pos + thumb_height else "│"
                stdscr.addstr(sb_row, box_right, sb_char, c_yellow)

        footer_top = box_bottom + 1
        stdscr.addch(footer_top, box_left, curses.ACS_LTEE, c_cyan)
        stdscr.addch(footer_top, box_right, curses.ACS_RTEE, c_cyan)
        for x in range(box_left + 1, box_right):
            stdscr.addch(footer_top, x, curses.ACS_HLINE, c_cyan)
             
        stdscr.addstr(footer_top, box_left + 2, " Controls & Options ", curses.A_BOLD | c_cyan)
        stdscr.addstr(footer_top + 1, box_left + 1, " D-Pad: Nav | L/R: PgUp/PgDn | A/B: Move Up/Down ".center(box_width - 2))
        stdscr.addstr(footer_top + 2, box_left + 1, " X: Sort Menu ".center(box_width - 2), c_yellow)
        stdscr.addstr(footer_top + 3, box_left + 1, " START: Save & Restart | SELECT: Quit Without Saving ".center(box_width - 2), c_yellow)

        stdscr.refresh()
         
        stdscr.nodelay(True)
        key = stdscr.getch()
        hw_action = hw_input.poll_action()

        if key == curses.KEY_UP: nav = "NAV_UP"
        elif key == curses.KEY_DOWN: nav = "NAV_DOWN"
        elif key in [ord('a'), ord('A')]: nav = "MOVE_UP"
        elif key in [ord('b'), ord('B')]: nav = "MOVE_DOWN"
        elif key in [ord('x'), ord('X')]: nav = "SORT_MENU"
        elif key in [ord('s'), ord('S'), 10, 13]: nav = "START"
        elif key in [ord('q'), ord('Q'), 27]: nav = "SELECT"
        else: nav = hw_action

        if nav == "NAV_UP":
            if current_idx > 0:
                current_idx -= 1
        elif nav == "NAV_DOWN":
            if current_idx < len(systems) - 1:
                current_idx += 1
        elif nav == "PAGE_UP":
            current_idx = max(0, current_idx - 10)
        elif nav == "PAGE_DOWN":
            current_idx = min(len(systems) - 1, current_idx + 10)
        elif nav == "MOVE_UP":
            if current_idx > 0:
                systems[current_idx], systems[current_idx - 1] = systems[current_idx - 1], systems[current_idx]
                current_idx -= 1
        elif nav == "MOVE_DOWN":
            if current_idx < len(systems) - 1:
                systems[current_idx], systems[current_idx + 1] = systems[current_idx + 1], systems[current_idx]
                current_idx += 1
        elif nav == "SORT_MENU":
            sort_choice = run_sort_menu(stdscr, fullnames, hw_input)
            stdscr.nodelay(True)
            if sort_choice == "sort_short":
                systems.sort()
                current_idx = 0
            elif sort_choice == "sort_full":
                systems.sort(key=lambda s: fullnames.get(s, s).lower())
                current_idx = 0
            elif sort_choice == "sort_mfg":
                systems.sort(key=lambda s: (get_manufacturer_rank(s), fullnames.get(s, s).lower()))
                current_idx = 0
            elif sort_choice == "reset":
                systems = list(initial_systems)
                current_idx = 0
        elif nav == "SELECT":
            return
        elif nav == "START":
            os.chdir(D_DIR)
            for idx, sys in enumerate(systems, 1):
                prefix = f"{idx:02d}"
                if os.path.exists(f"{sys}.xml"):
                    os.rename(f"{sys}.xml", f"{prefix}_{sys}.xml")
             
            with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
                out.write("<systemList>\n")
                for f in sorted(glob.glob(os.path.join(D_DIR, "[0-9][0-9]_*.xml"))):
                    with open(f, "r", encoding="utf-8", errors="ignore") as sf:
                        out.write(sf.read())
                out.write("</systemList>\n")
             
            stdscr.erase()
            stdscr.addstr(3, 2, "Changes saved! Restarting EmulationStation...", c_yellow)
            stdscr.refresh()
            time.sleep(1)
             
            os.system("sudo systemctl restart emulationstation")
            return
         
        time.sleep(0.03)

def main():
    try:
        curses.wrapper(run_menu)
    except Exception as e:
        with open('/tmp/es_sort_error.log', 'w') as err_file:
            traceback.print_exc(file=err_file)
        print("\n\n=== SCRIPT CRASHED ===")
        traceback.print_exc()
        time.sleep(5)

if __name__ == "__main__":
    main()
