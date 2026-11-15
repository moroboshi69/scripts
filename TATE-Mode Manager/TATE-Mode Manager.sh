#!/usr/bin/env bash
# ==============================================================================
# Title:        FinalBurn Neo Vertical (TATE) Manager Wrapper
# Author:       moroboshi69
# Description:  Launches the TATE-Mode Python curses utility from EmulationStation.
# ==============================================================================

# Ensure proper terminal rendering on ArkOS / EmulationStation
export TERM=linux
printf "\033c" > /dev/tty1

# Run the Python curses script attached to tty1
python3 "/roms/tools/TATE-Mode Manager.py" < /dev/tty1 > /dev/tty1 2>&1

# Clear screen on exit before returning to EmulationStation
printf "\033c" > /dev/tty1
