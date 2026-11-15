#!/usr/bin/env python3
# ==============================================================================
# Title:        FinalBurn Neo Vertical (TATE) Manager
# Author:       moroboshi69
# Description:  Interactive curses UI with flicker-free event-driven rendering
#               and full hardware controller support.
# ==============================================================================

import curses
import os
import glob
import struct

REMAP_DIR = "/home/ark/.config/retroarch/config/remaps/FinalBurn Neo"
OPT_DIR = "/home/ark/.config/retroarch/config/FinalBurn Neo"
OPT_FILE = os.path.join(OPT_DIR, "arcade.opt")

GAMES = [
    "1941", "1942", "1943", "1943kai", "1943mii", "1945kiii", "19xx", "99lstwar", "acitya", "acrobatm",
    "ad2083", "aerofgt", "afighter", "agallet", "airass", "airattck", "airduel", "ajax", "alcon", "alibaba",
    "alpine", "amazon", "amidar", "angelkds", "anteater", "arabian", "arbalest", "arcadian", "argus", "arkanoid",
    "arkatour", "arknoid2", "armedf", "armorcar", "armwrest", "ashura", "aso", "assault", "asuka", "atlantis",
    "avengers", "azurian", "bagman", "baluba", "bankp", "baryon", "batrider", "batsugun", "battlane", "battlnts",
    "battroad", "bbakraid", "bcruzm12", "bermudat", "bgaregga", "bigbang", "bigbucks", "bigprowr", "bigrun", "bioatack",
    "birdiy", "birdtry", "bjtwinpa", "bladestl", "blastoff", "blkhole", "block", "blockcar", "blswhstl", "bluehawk",
    "blueprntj", "bnj", "boggy84", "bombbee", "bombjack", "bongo", "boomrang", "botanic", "bowlrama", "brkthru",
    "btime", "buccanrs", "buggychl", "bwings", "cadanglr", "cairblad", "calibr50", "calipso", "capbowl", "carjmbre",
    "carnival", "castfant", "catacomb", "cavelon", "cburnrub", "centiped", "cexplore", "cfboy0a1", "cfghtice", "cflyball",
    "cgraplop", "chanbara", "checkman", "cheekyms", "chinagat", "chinhero", "chkun", "chopper", "chqflag", "chwy",
    "circusc", "citybomb", "ckong", "ckongpt2", "clapapa", "cmanhat", "cmissnx", "cnightst", "colony7", "combh",
    "commando", "commsega", "complexx", "congo", "contra", "coozumou", "cosmogng", "cppicf", "cprobowl", "cprogolf",
    "cpsoccer", "cptennis", "crbaloon", "crshrace", "crush", "crzrally", "cscrtry", "csdtenis", "cskater", "csuperas",
    "cterrani", "ctisland", "ctornado", "curvebal", "cutieq", "cybattlr", "cyclshtg", "cyvern", "daikaiju", "daioh",
    "dambustr", "dangar", "dangseed", "darkmist", "darwin", "dblewing", "ddonpach", "ddp2", "ddp3",
    "desertbr", "desertwr", "devilfsh", "devstors", "digdug", "digdug2", "dimahoo", "dingo", "dirtfoxj", "disco",
    "divebomb", "dkong", "dkong3", "dkongjr", "docastle", "dockman", "dogfight", "dogyuun", "dommy", "donpachi",
    "dorodon", "downtown", "dragnblz", "drakton", "dremshpr", "driftout", "drivfrcp", "drmicro", "drtoppel", "dsaber",
    "dspirit", "dyger", "earthjkr", "eeekk", "efdt", "eggor", "eightfrc", "elecyoyo", "enduror", "espgal",
    "esprade", "evinston", "exedexes", "exerion", "explbrkr", "extrmatn", "eyes", "f1gp", "f1gp2", "f1gpstar",
    "fantasyu", "fastlane", "fbneo", "feversos", "fghtatck", "fhawk", "fightrol", "finalizr", "firebatl", "fireshrk",
    "firetrap", "fixeight", "flipjack", "flkatck", "flyboy", "flytiger", "fnkyfish", "fourtrax", "freekick", "freeze",
    "frogger", "frontlin", "fshark", "fspiderb", "fstarfrc", "funkybee", "futspy", "gaiapols", "galaga", "galaga88",
    "galaxian", "galaxygn", "galivan", "galmedes", "gametngk", "gaplus", "gardia", "gbusters", "geebee", "gemini",
    "gground", "ghox", "gigas", "gnbarich", "gondo", "gorodki", "gprider", "grasspin", "grdnstrm", "grindstm",
    "grobda", "gseeker", "gstream", "gtclassc", "gulfstrm", "gulfwar2", "gunbird", "gunbird2", "gundhara", "gunfront",
    "gunlock", "gunnail", "gunsmoke", "guwange", "guzzler", "gwar", "gyrodine", "gyruss", "hal21", "halleysc",
    "hamaway", "hangon", "hangonjr", "harem", "hbarrel", "hcrash", "heiankyo", "hoccer", "homo", "hopprobo",
    "horekid", "horshoes", "hotchase", "hotdogst", "hotshock", "hstennis", "huncholy", "hustler", "hwrace", "hydra",
    "igmo", "ikari", "imago", "imgfight", "intrepid", "invaders", "ixion", "jack", "jackal", "jackrabt",
    "jcross", "jin", "jjack", "joinem", "jollyjgr", "journey", "joyfulr", "jrpacman", "jumpbug", "jumpcoas",
    "jumpkun", "jumpshot", "jungler", "junofrst", "kageki", "kaitei", "kamikcab", "kangaroo", "ket", "kicker",
    "kickman", "kikikai", "kingball", "kingdmgp", "krzybowl", "kyros", "ladybug", "ladymstr", "lasso", "lastday",
    "lastduel", "lastmisn", "leds2011", "legion", "lethalth", "levers", "lgtnfght", "liberate", "lizwiz", "lnc",
    "locomotn", "loht", "losttomb", "loverboy", "lsasquad", "lwings", "m660", "machomou", "macross", "macrossp",
    "madshark", "maniach", "manybloc", "mappy", "mariner", "mars", "marvins", "masterw", "matmania", "mazinger",
    "megadon", "megaforc", "megazone", "megrescu", "mercs", "merlinmm", "metafox", "metlfrzr", "metlhawk", "midres",
    "mightguy", "mikie", "milliped", "mimonkey", "minefld", "mirax", "misncrft", "mjleague", "mmonkey", "mofflott",
    "moguchan", "monymony", "moonal2", "mooncrst", "moonqsr", "moonwar", "mouser", "mplanets", "mrdo", "mrflea",
    "mrjong", "mrkougar", "mrtnt", "mrviking", "mschamp", "msisaac", "mspacman", "mtwins", "musicbal", "mystston",
    "navarone", "nebulray", "neobattl", "neogeo", "netwars", "newsin7", "newtemplate", "nibbler", "ninjemak", "nitrobal",
    "nmouse", "nob", "nost", "nsub", "olibochu", "omega", "omegaf", "orbitron", "outzone", "ozmawars",
    "ozon1", "packbang", "pacman", "pacmania", "pacnpal", "pacplus", "paddlema", "pandoras", "passsht", "pbaction",
    "pballoon", "pengo", "percuss", "perfrman", "phelios", "phoenix", "phozon", "pickin", "pisces", "pitnrun",
    "playball", "pleiads", "plusalph", "pollux", "pooyan", "popflame", "popper", "porky", "poundfor", "pprobe",
    "progolf", "progress", "psurge", "puckman", "punchout", "qbert", "qbertqub", "qix", "quantum", "quester",
    "r2dx_v33", "rackemup", "radarscp", "raflesia", "raiden", "raiden2", "raiden2dx", "raidendx", "rallybik", "raphero",
    "razmataz", "rdft", "rdft2", "reaktor", "redclash", "redhawk", "redrobin", "redufo", "regulus",
    "repulse", "retofinv", "revngr84", "rfjet", "ridleofp", "ringking", "roadf", "robocop2", "rockduck", "rocnrope",
    "rompers", "roundup", "route16", "rshark", "rumba", "ryujina", "s1945", "s1945ii", "s1945iii", "safarir",
    "samurai", "samuraia", "sandscrp", "sarge", "sasuke", "satansat", "sbagman", "sbasketb", "sbomber", "scobra",
    "scontra", "scorpion", "scotrsht", "scramble", "scregg", "seawolft", "seicross", "sengekis", "senjyo", "shollow",
    "shtrider", "shufshot", "sidearms", "silkroad", "silvmil", "sinistar", "skullfng", "skyadvnt", "skyalert", "skyarmy",
    "skybase", "skyfox", "skylancr", "skysmash", "skysoldr", "slither", "slspirit", "solarfox", "sonicbom", "sos",
    "spacecr", "spacedx", "spacefb", "spcinv95", "spcpostn", "speakres", "speedbal", "spnchout", "springer", "spyhunt",
    "sqbert", "sqix", "sraider", "srdarwin", "srdmissn", "srumbler", "ssi", "ssmissin", "ssozumo", "sspirits",
    "sstingry", "sstriker", "starfigh", "starjack", "stg", "stinger", "stmblade", "stratgys", "streakng", "stuntair",
    "sub", "superbon", "superpac", "superx", "suprglob", "suprmous", "suprridr", "suzuka8h", "swapAB", "swat",
    "szaxxon", "tacscan", "tactcian", "tail2nos", "tankbust", "tazmania", "tcobra2", "tdragon", "tempest", "template",
    "terracre", "tharrier", "thedeep", "theend", "thehand", "thepit", "thief", "thunderl", "tigerh", "timefgtr",
    "timelimt", "timeplt", "timescan", "tnextspc", "tnk3", "todruaga", "tokio", "tokisens", "toobin", "tp84",
    "tricktrp", "triplep", "tripool", "trisport", "tron", "truxton", "truxton2", "tsamurai", "turbofrc", "turtles",
    "tutankhm", "twinbee", "twincobr", "twineag2", "twineagl", "twinhawk", "ultrax", "unclepoo", "uniwars", "upndown",
    "usclssic", "valkyrie", "vandyke", "vandykeb", "vangrd2", "vanguard", "vanvan", "vaportra", "varth", "vasara",
    "vasara2", "vastar", "victoryc", "victroad", "vimana", "viprp1", "vmetal", "volfied", "vsgongf", "vulgus",
    "wanted", "warpwarp", "waterski", "wingforc", "wiping", "wivernwg", "wiz", "wmatch", "wndrplnt", "woodpeck",
    "worldwar", "wrestwar", "wrofaero", "wwestern", "wyvernf0", "xevious", "xxmissio", "yamagchi", "yamato", "youjyudn",
    "zaviga", "zaxxon", "zerohour", "zingzip", "zoar", "zodiack", "zzyzzyxx",
]


class HandheldInput:

  def __init__(self):
    self.fd = None
    self.held_action = None
    self.hold_counter = 0
    self.find_controller_device()

  def find_controller_device(self):
    for event_path in sorted(glob.glob("/dev/input/event*")):
      try:
        name_path = (
            f"/sys/class/input/{os.path.basename(event_path)}/device/name"
        )
        if os.path.exists(name_path):
          with open(name_path, "r") as nf:
            name = nf.read().strip().lower()
          if any(
              k in name
              for k in ["joypad", "gamepad", "joystick", "keys", "controller"]
          ):
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
        _, _, ev_type, code, value = struct.unpack("llHhi", data)

        action = None
        if ev_type == 1:  # Key event
          if code in [103, 544]:
            action = "NAV_UP"
          elif code in [108, 545]:
            action = "NAV_DOWN"
          elif code == 310:
            action = "PAGE_UP"
          elif code == 311:
            action = "PAGE_DOWN"
          elif code == 305:
            action = "MOVE_UP"  # Button A
          elif code == 304:
            action = "MOVE_DOWN"  # Button B
          elif code == 307:
            action = "SORT_MENU"
          elif code == 705:
            action = "START"
          elif code == 704:
            action = "SELECT"
        elif ev_type == 3:  # Axis event
          if code in [1, 17]:
            if value < -10000:
              action = "NAV_UP"
            elif value > 10000:
              action = "NAV_DOWN"

        if action:
          if value in (1, 2):
            current_event_action = action
            self.held_action = action
            self.hold_counter = 0
          elif value == 0:
            if self.held_action == action:
              self.held_action = None
              self.hold_counter = 0
    except (BlockingIOError, InterruptedError):
      pass
    except Exception:
      pass

    if current_event_action:
      return current_event_action

    if self.held_action in (
        "NAV_UP",
        "NAV_DOWN",
        "MOVE_UP",
        "MOVE_DOWN",
        "PAGE_UP",
        "PAGE_DOWN",
    ):
      self.hold_counter += 1
      if self.hold_counter > 12:
        if (self.hold_counter - 12) % 4 == 0:
          return self.held_action

    return None


def check_tate_status():
  opt_active = False
  if os.path.exists(OPT_FILE):
    with open(OPT_FILE, "r") as f:
      content = f.read()
      if 'fbneo-vertical-mode = "TATE alternate"' in content:
        opt_active = True

  rmp_exists = any(
      os.path.exists(os.path.join(REMAP_DIR, f"{game}.rmp")) for game in GAMES
  )
  return opt_active and rmp_exists


def enable_tate():
  os.makedirs(REMAP_DIR, exist_ok=True)
  os.makedirs(OPT_DIR, exist_ok=True)

  lines = []
  if os.path.exists(OPT_FILE):
    with open(OPT_FILE, "r") as f:
      lines = f.readlines()

  found = False
  new_lines = []
  for line in lines:
    if line.startswith("fbneo-vertical-mode"):
      new_lines.append('fbneo-vertical-mode = "TATE alternate"\n')
      found = True
    else:
      new_lines.append(line)
  if not found:
    new_lines.append('fbneo-vertical-mode = "TATE alternate"\n')

  with open(OPT_FILE, "w") as f:
    f.writelines(new_lines)

  base_remap_content = """input_libretro_device_p1 = "1"
input_player1_analog_dpad_mode = "1"
input_player1_btn_a = "0"
input_player1_btn_b = "-1"
input_player1_btn_x = "8"
input_player1_stk_r_x+ = "5"
input_player1_stk_r_x- = "4"
input_player1_stk_r_y+ = "6"
input_player1_stk_r_y- = "7"
input_remap_port_p1 = "0"
input_turbo_allow_dpad = "false"
input_turbo_bind = "15"
input_turbo_button = "15"
input_turbo_duty_cycle = "0"
input_turbo_enable = "true"
input_turbo_mode = "1"
input_turbo_period = "6"
"""

  created = 0
  skipped = 0
  for game in GAMES:
    dest = os.path.join(REMAP_DIR, f"{game}.rmp")
    if os.path.exists(dest):
      skipped += 1
    else:
      with open(dest, "w") as f:
        f.write(base_remap_content)
      created += 1

  return f"Enabled! Created {created} remaps, skipped {skipped} existing."


def disable_tate():
  if os.path.exists(OPT_FILE):
    with open(OPT_FILE, "r") as f:
      lines = f.readlines()
    new_lines = [
        line for line in lines if not line.startswith("fbneo-vertical-mode")
    ]
    with open(OPT_FILE, "w") as f:
      f.writelines(new_lines)

  deleted = 0
  for game in GAMES:
    dest = os.path.join(REMAP_DIR, f"{game}.rmp")
    if os.path.exists(dest):
      os.remove(dest)
      deleted += 1

  return f"Disabled! Removed {deleted} remaps and TATE option."


def run_menu(stdscr):
  curses.curs_set(0)
  stdscr.keypad(True)
  curses.start_color()
  curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
  curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
  curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)

  hw_input = HandheldInput()
  current_row = 0
  status_message = (
      "Use D-Pad/Arrows to navigate, A / Enter to select, Q / Select to quit."
  )

  menu_items = [
      "Enable TATE Mode (Create remaps & apply option)",
      "Disable TATE Mode (Delete remaps & clear option)",
      "Exit",
  ]

  # Set input timeout to 100ms so we block efficiently without hammering CPU/display
  stdscr.timeout(100)
  redraw_needed = True

  while True:
    if redraw_needed:
      stdscr.clear()
      h, w = stdscr.getmaxyx()

      is_active = check_tate_status()

      # Title
      title = " FinalBurn Neo Vertical (TATE) Manager "
      stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.A_BOLD)
      subtitle = "Author: moroboshi69"
      stdscr.addstr(2, max(0, (w - len(subtitle)) // 2), subtitle, curses.A_DIM)

      # Status display
      stdscr.addstr(4, 4, "STATUS: ", curses.A_BOLD)
      if is_active:
        stdscr.addstr("ENABLED", curses.color_pair(1) | curses.A_BOLD)
      else:
        stdscr.addstr("DISABLED", curses.color_pair(2) | curses.A_BOLD)

      start_y = 7
      for idx, item in enumerate(menu_items):
        x = 6
        y = start_y + idx
        if idx == current_row:
          stdscr.attron(curses.color_pair(3))
          stdscr.addstr(y, x, f" > {item} ")
          stdscr.attroff(curses.color_pair(3))
        else:
          stdscr.addstr(y, x, f"   {item} ")

      if status_message:
        stdscr.addstr(h - 2, 4, status_message[: w - 5], curses.A_ITALIC)

      stdscr.refresh()
      redraw_needed = False

    # Wait for input (blocks up to 100ms)
    key = stdscr.getch()
    hw_action = hw_input.poll_action()

    if key == curses.ERR and not hw_action:
      continue

    nav = None
    if key in [curses.KEY_UP, ord("w"), ord("W")]:
      nav = "NAV_UP"
    elif key in [curses.KEY_DOWN, ord("s"), ord("S")]:
      nav = "NAV_DOWN"
    elif key in [10, 13, ord("a"), ord("A")]:
      nav = "CONFIRM"
    elif key in [27, ord("q"), ord("Q")]:
      nav = "CANCEL"
    else:
      if hw_action == "NAV_UP":
        nav = "NAV_UP"
      elif hw_action == "NAV_DOWN":
        nav = "NAV_DOWN"
      elif hw_action in ["MOVE_UP", "START"]:
        nav = "CONFIRM"
      elif hw_action in ["MOVE_DOWN", "SELECT"]:
        nav = "CANCEL"

    if nav == "NAV_UP":
      current_row = (current_row - 1) % len(menu_items)
      redraw_needed = True
    elif nav == "NAV_DOWN":
      current_row = (current_row + 1) % len(menu_items)
      redraw_needed = True
    elif nav == "CONFIRM":
      if current_row == 0:
        status_message = enable_tate()
      elif current_row == 1:
        status_message = disable_tate()
      elif current_row == 2:
        break
      redraw_needed = True
    elif nav == "CANCEL":
      break


def main():
  try:
    curses.wrapper(run_menu)
  except Exception:
    pass


if __name__ == "__main__":
  main()
