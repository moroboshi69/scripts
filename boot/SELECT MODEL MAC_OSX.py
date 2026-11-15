#!/usr/bin/env python3
# ==============================================================================
# Title:        R36S DTB Firmware Selector
# Author:       moroboshi69
# Description:  Interactive terminal utility using a split-pane curses layout
#               to select and apply DTB firmware configurations on macOS.
# ==============================================================================

curses_import_error = None
try:
  import curses
  import os
  import sys
  import glob
  import shutil
  import re
except Exception as e:
  curses_import_error = e

# Directory and file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = (
    os.path.dirname(SCRIPT_DIR)
    if os.path.basename(SCRIPT_DIR) == "dtb"
    else SCRIPT_DIR
)
BACKUP_DIR = os.path.join(ROOT_DIR, "select_device backup")


def locate_ini():
  """Locates the r36_devices.ini configuration file in standard directories."""
  for candidate in [
      os.path.join(ROOT_DIR, "r36_devices.ini"),
      os.path.join(ROOT_DIR, "dtb", "r36_devices.ini"),
  ]:
    if os.path.isfile(candidate):
      return candidate
  return None


def parse_devices(ini_path):
  """Parses device sections and hardware variants from the INI file."""
  device_variants = {}
  all_devices = []
  current_section = ""

  with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#") or line.startswith(";"):
        continue

      section_match = re.match(r"^\[(.*)\]$", line)
      if section_match:
        current_section = section_match.group(1).strip()
        all_devices.append(current_section)
        device_variants[current_section] = "unknown"
      elif current_section:
        variant_match = re.match(r"^variant\s*=\s*(.*)$", line, re.IGNORECASE)
        if variant_match:
          device_variants[current_section] = variant_match.group(1).strip()

  return all_devices, device_variants


def get_current_selection_name():
  """Retrieves the name of the currently installed device from the root directory."""
  root_markers = glob.glob(os.path.join(ROOT_DIR, "DTBs installed - *"))
  if root_markers:
    return os.path.basename(root_markers[0]).replace(
        "DTBs installed - ", ""
    )

  return "None"


def get_backup_file_list():
  """Retrieves a list of filenames stored in the backup directory."""
  if not os.path.isdir(BACKUP_DIR):
    return ["No backup folder found."]
  files = [os.path.basename(f) for f in glob.glob(os.path.join(BACKUP_DIR, "*"))]
  return sorted(files) if files else ["Backup folder is empty."]


def backup_existing_files():
  """Backs up existing DTB, BMP, and marker files prior to file updates."""
  existing_dtbs = glob.glob(os.path.join(ROOT_DIR, "*.dtb"))
  existing_bmps = glob.glob(os.path.join(ROOT_DIR, "*.bmp"))
  existing_markers = glob.glob(os.path.join(ROOT_DIR, "DTBs installed - *"))
  files_to_backup = existing_dtbs + existing_bmps + existing_markers

  backed_up_list = []
  if files_to_backup:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for old_file in glob.glob(os.path.join(BACKUP_DIR, "*")):
      try:
        os.remove(old_file)
      except Exception:
        pass

    for f in files_to_backup:
      shutil.copy2(f, BACKUP_DIR)
      backed_up_list.append(os.path.basename(f))

  return backed_up_list


def restore_backup():
  """Restores previously backed up configuration files into the root directory."""
  backup_files = glob.glob(os.path.join(BACKUP_DIR, "*"))
  if not backup_files:
    return False, "No backup files found."

  restored_files = []
  for f in backup_files:
    shutil.copy2(f, ROOT_DIR)
    restored_files.append(os.path.basename(f))

  file_str = ", ".join(restored_files)
  return True, f"Restored previous backup ({len(restored_files)} files): {file_str}"


def apply_device_selection(chosen, chosen_variant):
  """Applies the selected device configuration, updating DTBs and boot images."""
  source_folder = os.path.join(ROOT_DIR, "dtb", chosen_variant, chosen)
  if not os.path.isdir(source_folder):
    return False, f"Source folder not found: {source_folder}"

  backed_up = backup_existing_files()

  # Remove existing DTB files
  removed_dtbs = []
  for f in glob.glob(os.path.join(ROOT_DIR, "*.dtb")):
    removed_dtbs.append(os.path.basename(f))
    try:
      os.remove(f)
    except Exception:
      pass

  # Resolve boot image resolution source folder based on model naming
  if "ProMax" in chosen or "R45H" in chosen or "R46H" in chosen:
    boot_source = os.path.join(ROOT_DIR, "dtb", "images", "1024")
  elif "R36S-Plus" in chosen:
    boot_source = os.path.join(ROOT_DIR, "dtb", "images", "720")
  elif "R50H" in chosen:
    boot_source = os.path.join(ROOT_DIR, "dtb", "images", "1280")
  else:
    boot_source = os.path.join(ROOT_DIR, "dtb", "images", "640")

  copied_boots = []
  if os.path.isdir(boot_source):
    for f in os.listdir(boot_source):
      src_path = os.path.join(boot_source, f)
      if os.path.isfile(src_path):
        shutil.copy2(src_path, ROOT_DIR)
        copied_boots.append(f)

  # Copy device-specific files from source folder
  copied_device_files = []
  log_buffer = f"Selected : {chosen}\nVariant  : {chosen_variant}\n"
  for f in os.listdir(source_folder):
    src_path = os.path.join(source_folder, f)
    if os.path.isfile(src_path):
      shutil.copy2(src_path, ROOT_DIR)
      copied_device_files.append(f)
      log_buffer += f"Copied: {f}\n"

  # Create installation marker file
  for m in glob.glob(os.path.join(ROOT_DIR, "DTBs installed - *")):
    try:
      os.remove(m)
    except Exception:
      pass

  marker_file = os.path.join(ROOT_DIR, f"DTBs installed - {chosen}")
  with open(marker_file, "w", encoding="utf-8") as mf:
    mf.write(log_buffer)

  summary = (
      f"Applied {chosen} ({chosen_variant}) | Backed up ({len(backed_up)}):"
      f" {', '.join(backed_up[:3])}{'...' if len(backed_up)>3 else ''} | Copied"
      f" {len(copied_device_files)} DTBs, {len(copied_boots)} boot images"
  )
  return True, summary


def show_confirmation_popup(stdscr, chosen, chosen_variant):
  """Displays a pop-up window confirming the proposed changes and files."""
  h, w = stdscr.getmaxyx()
  pop_h = 17
  pop_w = min(74, w - 4)
  pop_y = max(0, (h - pop_h) // 2)
  pop_x = max(0, (w - pop_w) // 2)

  win = curses.newwin(pop_h, pop_w, pop_y, pop_x)
  win.keypad(True)
  win.box()

  source_folder = os.path.join(ROOT_DIR, "dtb", chosen_variant, chosen)
  source_files = (
      [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
      if os.path.isdir(source_folder)
      else []
  )

  win.addstr(1, 2, " CONFIRM DEVICE CONFIGURATION ", curses.color_pair(1) | curses.A_BOLD)
  win.addstr(3, 3, f"Target Device : {chosen}")
  win.addstr(4, 3, f"Variant Group : {chosen_variant}")
  win.addstr(5, 3, f"Files to be copied ({len(source_files)} device files):")

  row_idx = 6
  for f in source_files[:5]:
    if row_idx < pop_h - 4:
      win.addstr(row_idx, 5, f"• {f[:pop_w-10]}")
      row_idx += 1
  if len(source_files) > 5:
    if row_idx < pop_h - 4:
      win.addstr(row_idx, 5, f"... and {len(source_files) - 5} more file(s)")
      row_idx += 1

  win.addstr(pop_h - 5, 3, "Proceed with updating DTB and boot files?", curses.color_pair(6) | curses.A_BOLD)
  win.addstr(pop_h - 3, pop_w // 2 - 18, "[Y / Enter] Yes / [N] No / [Q] Quit", curses.color_pair(2) | curses.A_BOLD)

  win.refresh()

  while True:
    key = win.getch()
    if key in [ord("y"), ord("Y"), 10, 13]:
      return "yes"
    elif key in [ord("n"), ord("N"), 27]:
      return "no"
    elif key in [ord("q"), ord("Q")]:
      return "quit"


def show_revert_popup(stdscr):
  """Displays a confirmation pop-up window for restoring the backup."""
  h, w = stdscr.getmaxyx()
  pop_h = 17
  pop_w = min(74, w - 4)
  pop_y = max(0, (h - pop_h) // 2)
  pop_x = max(0, (w - pop_w) // 2)

  win = curses.newwin(pop_h, pop_w, pop_y, pop_x)
  win.keypad(True)
  win.box()

  backup_files = glob.glob(os.path.join(BACKUP_DIR, "*"))
  backup_filenames = [os.path.basename(f) for f in backup_files]

  win.addstr(1, 2, " CONFIRM BACKUP REVERSION ", curses.color_pair(6) | curses.A_BOLD)
  win.addstr(3, 3, f"Backup Folder : select_device backup")
  win.addstr(4, 3, f"Files to be restored ({len(backup_filenames)} files):")

  row_idx = 5
  for f in backup_filenames[:5]:
    if row_idx < pop_h - 5:
      win.addstr(row_idx, 5, f"• {f[:pop_w-10]}")
      row_idx += 1
  if len(backup_filenames) > 5:
    if row_idx < pop_h - 5:
      win.addstr(row_idx, 5, f"... and {len(backup_filenames) - 5} more file(s)")
      row_idx += 1

  win.addstr(pop_h - 5, 3, "Warning: This will overwrite current root files.", curses.color_pair(3))
  win.addstr(pop_h - 4, 3, "Proceed with backup reversion?", curses.color_pair(6) | curses.A_BOLD)
  win.addstr(pop_h - 2, pop_w // 2 - 18, "[Y / Enter] Yes / [N] No / [Q] Quit", curses.color_pair(2) | curses.A_BOLD)

  win.refresh()

  while True:
    key = win.getch()
    if key in [ord("y"), ord("Y"), 10, 13]:
      return "yes"
    elif key in [ord("n"), ord("N"), 27]:
      return "no"
    elif key in [ord("q"), ord("Q")]:
      return "quit"


def main(stdscr):
  """Main curses loop managing the split layout and dedicated status pane."""
  curses.curs_set(0)
  stdscr.keypad(True)
  curses.start_color()

  # Initialize color pairs
  curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Active highlight
  curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
  curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLACK)

  ini_path = locate_ini()
  if not ini_path:
    stdscr.clear()
    stdscr.addstr(2, 2, "ERROR: r36_devices.ini not found!", curses.color_pair(3))
    stdscr.addstr(4, 2, "Press any key to exit.")
    stdscr.getch()
    return

  all_devices, device_variants = parse_devices(ini_path)
  if not all_devices:
    stdscr.clear()
    stdscr.addstr(2, 2, "ERROR: No devices found in INI!", curses.color_pair(3))
    stdscr.addstr(4, 2, "Press any key to exit.")
    stdscr.getch()
    return

  # Group devices by variant
  variants_map = {}
  for dev in all_devices:
    v = device_variants[dev]
    if v not in variants_map:
      variants_map[v] = []
    variants_map[v].append(dev)

  variant_order = ["r36s", "clone", "soysauce"]
  sorted_variants = [v for v in variant_order if v in variants_map]
  for v in variants_map:
    if v not in sorted_variants:
      sorted_variants.append(v)

  # Construct left pane categories
  categories = []
  for v in sorted_variants:
    label = f"{v.upper()} (Unsupported)" if v in ["clone", "soysauce"] else v.upper()
    categories.append({"name": label, "variant_key": v, "type": "variant"})
  categories.append({"name": "REVERT BACKUP", "variant_key": None, "type": "action"})

  active_pane = 0  # 0 = Left Pane, 1 = Right Pane
  left_row = 0
  right_row = 0
  left_scroll = 0
  right_scroll = 0
  status_msg = "Ready. Use Arrows/Enter to navigate, Tab to switch panes, Q to Quit."

  while True:
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    if h < 16 or w < 60:
      stdscr.addstr(0, 0, "Terminal window too small (min 60x16 required).")
      stdscr.refresh()
      key = stdscr.getch()
      if key in [ord("q"), ord("Q")]:
        break
      continue

    # Header display matching TATE mode layout style
    title = " R36S DTB Firmware Selector "
    stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.color_pair(1) | curses.A_BOLD)
    subtitle = "Author: moroboshi69"
    stdscr.addstr(2, max(0, (w - len(subtitle)) // 2), subtitle, curses.A_DIM)

    current_installed = get_current_selection_name()
    stdscr.addstr(4, 2, f"Active Root: {ROOT_DIR}", curses.A_DIM)
    stdscr.addstr(5, 2, f"Current Selection: {current_installed}", curses.color_pair(2) | curses.A_BOLD)

    # Layout dimensions
    pane_top = 7
    footer_height = 4
    pane_height = h - pane_top - footer_height - 1
    left_width = 28
    right_width = w - left_width - 5

    # Draw vertical divider strictly bounded above the footer pane
    left_attr = curses.color_pair(1) if active_pane == 0 else curses.A_DIM
    for y in range(pane_top, pane_top + pane_height):
      if 0 <= y < h and 0 <= left_width + 3 < w:
        stdscr.addch(y, left_width + 3, curses.ACS_VLINE, left_attr)

    stdscr.addstr(pane_top - 1, 3, " Categories ", curses.color_pair(1) | curses.A_BOLD)
    
    # Dynamic header for Right Pane based on selected category type
    current_cat = categories[left_row]
    right_header = " Backup Files to Revert " if current_cat["type"] == "action" else " Devices "
    stdscr.addstr(pane_top - 1, left_width + 6, right_header, curses.color_pair(1) | curses.A_BOLD)

    # Render Left Pane Items
    if left_row < 0:
      left_row = 0
    elif left_row >= len(categories):
      left_row = len(categories) - 1

    if left_row < left_scroll:
      left_scroll = left_row
    elif left_row >= left_scroll + pane_height:
      left_scroll = left_row - pane_height + 1

    for idx in range(pane_height):
      cat_idx = left_scroll + idx
      if cat_idx >= len(categories):
        break

      y = pane_top + idx
      cat = categories[cat_idx]
      display_text = f" {cat['name'][:left_width-2]:<{left_width-2}} "

      try:
        if cat_idx == left_row:
          if active_pane == 0:
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
          else:
            stdscr.attron(curses.A_REVERSE)
          stdscr.addstr(y, 2, display_text)
          stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
          stdscr.attroff(curses.A_REVERSE)
        else:
          stdscr.addstr(y, 2, display_text)
      except Exception:
        pass

    # Determine right pane items based on left category selection
    if current_cat["type"] == "variant":
      current_items = variants_map.get(current_cat["variant_key"], [])
    else:
      current_items = get_backup_file_list()

    # Render Right Pane Items
    if right_row < 0:
      right_row = 0
    elif right_row >= len(current_items):
      right_row = len(current_items) - 1

    if right_row < right_scroll:
      right_scroll = right_row
    elif right_row >= right_scroll + pane_height:
      right_scroll = right_row - pane_height + 1

    for idx in range(pane_height):
      item_idx = right_scroll + idx
      if item_idx >= len(current_items):
        break

      y = pane_top + idx
      x = left_width + 5
      item_text = current_items[item_idx]

      if current_cat["type"] == "variant":
        is_installed = (item_text == current_installed)
        prefix = "* " if is_installed else "  "
        raw_display = f"{prefix}{item_text}"
      else:
        raw_display = f"• {item_text}"

      display_text = f" {raw_display[:right_width-2]:<{right_width-2}} "

      try:
        if current_cat["type"] == "action":
          if item_idx == right_row and active_pane == 1:
            stdscr.attron(curses.color_pair(4) | curses.color_pair(6) | curses.A_BOLD)
            stdscr.addstr(y, x, display_text)
            stdscr.attroff(curses.color_pair(4) | curses.color_pair(6) | curses.A_BOLD)
          else:
            stdscr.addstr(y, x, display_text, curses.color_pair(6) | curses.A_BOLD)
        elif item_idx == right_row and active_pane == 1:
          if current_cat["type"] == "variant" and item_text == current_installed:
            stdscr.attron(curses.color_pair(4) | curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(y, x, display_text)
            stdscr.attroff(curses.color_pair(4) | curses.color_pair(2) | curses.A_BOLD)
          else:
            stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            stdscr.addstr(y, x, display_text)
            stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        else:
          if current_cat["type"] == "variant" and item_text == current_installed:
            stdscr.addstr(y, x, display_text, curses.color_pair(2) | curses.A_BOLD)
          else:
            stdscr.addstr(y, x, display_text)
      except Exception:
        pass

    # Draw separator line above the status footer pane
    sep_y = pane_top + pane_height
    try:
      stdscr.addstr(sep_y, 0, "-" * w, curses.color_pair(1))
    except Exception:
      pass

    # Render Dedicated Status Footer Pane
    status_y = sep_y + 1
    try:
      stdscr.addstr(status_y, 2, "STATUS / ACTION LOG:", curses.color_pair(1) | curses.A_BOLD)
      stdscr.addstr(status_y + 1, 2, status_msg[: w - 4], curses.color_pair(5))
      stdscr.addstr(status_y + 2, 2, "[Tab / Enter] Switch Panes  [Arrows] Navigate  [Q] Quit", curses.A_DIM)
    except Exception:
      pass

    stdscr.refresh()

    key = stdscr.getch()

    if key in [ord("q"), ord("Q")]:
      break
    elif key in [9, curses.KEY_LEFT, curses.KEY_RIGHT]:
      active_pane = 1 - active_pane
      right_row = 0
      right_scroll = 0
    elif key in [curses.KEY_UP, ord("k"), ord("K")]:
      if active_pane == 0:
        left_row = max(0, left_row - 1)
        right_row = 0
        right_scroll = 0
      else:
        right_row = max(0, right_row - 1)
    elif key in [curses.KEY_DOWN, ord("j"), ord("J")]:
      if active_pane == 0:
        left_row = min(len(categories) - 1, left_row + 1)
        right_row = 0
        right_scroll = 0
      else:
        right_row = min(len(current_items) - 1, right_row + 1)
    elif key in [10, 13]:
      if active_pane == 0:
        # Switch focus to the right pane when Enter is pressed on categories
        active_pane = 1
        right_row = 0
        right_scroll = 0
      else:
        if current_cat["type"] == "action":
          result = show_revert_popup(stdscr)
          if result == "yes":
            success, msg = restore_backup()
            status_msg = msg
          elif result == "quit":
            break
          else:
            status_msg = "Cancelled backup reversion."
        else:
          if current_items and current_cat["type"] == "variant":
            chosen = current_items[right_row]
            chosen_variant = current_cat["variant_key"]

            result = show_confirmation_popup(stdscr, chosen, chosen_variant)
            if result == "yes":
              success, msg = apply_device_selection(chosen, chosen_variant)
              status_msg = msg
            elif result == "quit":
              break
            else:
              status_msg = f"Cancelled update for {chosen}."


if __name__ == "__main__":
  if curses_import_error:
    print(f"Error initializing curses: {curses_import_error}")
    sys.exit(1)
  try:
    curses.wrapper(main)
  except Exception as err:
    print(f"An error occurred: {err}")
