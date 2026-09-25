# FileDrop

> Lightweight LAN file receiver — send files from **any device** on your network to your PC via browser. No apps, no accounts, no cables.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![Flask](https://img.shields.io/badge/Flask-2.x-black?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

---

## How It Works

1. Run `filedrop.py` on your PC
2. It prints a local IP address and port
3. Open that URL on **any device** on the same network (phone, tablet, another laptop)
4. Drag & drop or browse files — they land instantly in a folder on your PC

Works over **Wi-Fi**, **LAN cable**, or any local network connection.

---

## Features

- Drag-and-drop or click-to-browse upload
- Multiple files at once with individual progress bars
- Works from any browser — no app install on the sending device
- Cross-platform: **Windows**, **Linux** (Kali, Ubuntu, etc.), **macOS**
- Auto-detects all network interfaces (Wi-Fi, LAN, VPN, Docker)
- Custom save directory and port via CLI flags
- Minimal dependencies — just Python + Flask

---

## Requirements

- Python 3.7 or higher
- Flask

```bash
pip install flask
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/VoidCatalyst/filedrop.git
cd filedrop

# Install dependency
pip install flask
```

---

## Usage

### Basic (saves to `~/Desktop/FileDrop`)

```bash
python filedrop.py
```

### Custom save directory

```bash
python filedrop.py -d /path/to/folder
```

### Custom port (default: 8080)

```bash
python filedrop.py -p 9090
```

### All options

```bash
python filedrop.py -d /path/to/folder -p 9090
```

---

## Output Example

```
  FileDrop
  ----------------------------------------------------
  saving to : /home/kali/Desktop/FileDrop
  bind      : 0.0.0.0:8080
  open from another device:
      http://192.168.0.112:8080/
      http://127.0.0.1:8080/   (this machine)
  ----------------------------------------------------
  Ctrl-C to stop
```

Open the printed URL on any device on the same network and start uploading.

---

## Use Cases

| Scenario | How |
|---|---|
| Phone → PC over Wi-Fi | Run on PC, open IP in phone browser |
| Laptop A → Laptop B via LAN cable | Set static IPs, run on receiver, open in sender browser |
| Any device → Kali Linux (pentesting lab) | Run on Kali, receive files from any device |
| Office file sharing (no USB) | Run on PC, share IP with colleagues |

---

## LAN Cable (Direct Connection) Setup

1. Connect two devices with an Ethernet cable
2. On the **receiving** device: run `filedrop.py`, note the LAN IP shown
3. On the **sending** device: set a static IP in the same subnet
4. Open the receiver's IP in any browser and upload

---

## CLI Reference

| Flag | Default | Description |
|---|---|---|
| `-d`, `--dir` | `~/Desktop/FileDrop` | Directory to save uploaded files |
| `-p`, `--port` | `8080` | Port to listen on |
| `-H`, `--host` | `0.0.0.0` | Host to bind (0.0.0.0 = all interfaces) |

---

## License

MIT — free to use, modify and distribute.
