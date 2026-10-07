# EmulationStation Gamelist Sorter

An interactive terminal UI script for managing, filtering, and reordering systems in EmulationStation (`es_systems.cfg`). 

If you've got a handheld running ArkOS, dArkOS, or a custom Linux setup with a massive list of emulators and ports, this script splits your monolithic configuration into individual files in `es_systems.d/`, lets you sort them visually, and automatically rebuilds the main config.

## Features

* **Individual XML Bootstrapping:** Automatically splits `/etc/emulationstation/es_systems.cfg` into modular XMLs inside `~/.emulationstation/es_systems.d/`.
* **Smart ROM Filtering:** Automatically hides systems that don't have valid ROM directories or contain zero games.
* **Flexible Sorting:** Sort instantly by system ID, full platform name, manufacturer hierarchy, or revert to original order.
* **Automatic Restart:** Rewrites `es_systems.cfg`, and triggers a `systemd` restart of EmulationStation.

## Controls

| Action | Keyboard | Handheld Controller |
| :--- | :--- | :--- |
| **Navigate Up / Down** | Up / Down Arrow or `W` / `S` | D-Pad Up / Down (or Left Analog Stick) |
| **Move System Up / Down**| `A` / `B` | Button A / Button B |
| **Page Up / Down** | Page Up / Page Down | L / R Shoulder Buttons |
| **Open Sort Menu** | `X` | Button X |
| **Save & Restart ES** | `S` or Enter | START |
| **Quit (No Save)** | `Q` or Esc | SELECT |

## Requirements

* Python 3.x with `curses` support.
* A Linux environment running EmulationStation (tested on handhelds like the R36S and similar Rockchip devices).
* Read/write access to `~/.emulationstation/`.
* `sudo` privileges if you need the script to restart the `emulationstation` systemd service.
