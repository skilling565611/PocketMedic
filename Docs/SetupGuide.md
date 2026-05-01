# Setup Guide

## Requirements

- Python 3.9 or later
- Windows 10/11 (primary target) — macOS and Linux are supported for most features

### Optional dependencies

| Package  | Used for                             |
|----------|--------------------------------------|
| `psutil` | Detailed CPU and RAM information     |

Install optional packages:

```bash
pip install psutil
```

---

## Installation

1. **Clone the repository** (or copy the folder to a USB drive for portable use):

```bash
git clone https://github.com/skilling565611/PocketMedic.git
cd PocketMedic
```

2. **(Optional)** Create a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. **Install optional dependencies**:

```bash
pip install psutil
```

---

## Running PocketMedic

### Terminal UI (recommended for portable / headless use)

```bash
python PocketMedic.py
```

### Graphical Dashboard

```python
from Core.Logger import Logger
from GUI.Dashboard import Dashboard

logger = Logger()
Dashboard(logger=logger).run()
```

---

## Configuration

Global settings are stored in `Config/Global.Settings.json`.

Device-specific behaviour is controlled by profiles in `Config/`:

| File                          | Description                     |
|-------------------------------|---------------------------------|
| `Global.Settings.json`        | App-wide defaults               |
| `ArcticPrime.Profile.json`    | ArcticPrime hardware profile    |
| `ControlPrime.Profile.json`   | ControlPrime hardware profile   |

Edit these files with any text editor.

---

## Adding Portable Tools

Copy portable executables into `PortableTools/`.  PocketMedic will
discover and list them in the UI automatically (feature coming in v0.9).

---

## Adding Scripts

Place `.py`, `.bat`, or `.sh` scripts into `Scripts/`.  They can be
launched from the TerminalUI (feature coming in a future release).

---

## Log Files

Logs are written to `Logs/YYYY-MM-DD.log`.  Each run appends to the
file for the current date.
