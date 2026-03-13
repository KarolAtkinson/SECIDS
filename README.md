# SecIDS-CNN First-Time Guide

This is the first page for new users. Follow these steps and the project will be ready in VS Code.

Repository:
- https://github.com/KarolAtkinson/SECIDS

## 1. Download And Open

1. Download or clone the repository.
2. Open the project folder in VS Code.
3. Open a terminal in the project root.

## 2. One-Command Setup (Recommended)

This setup creates the virtual environment, installs Python dependencies, writes VS Code extension recommendations, and asks for your permission before installing extensions.

Linux/Kali/macOS:
```bash
./Launchers/bootstrap.sh
```

Windows PowerShell:
```powershell
.\Launchers\bootstrap.ps1
```

Cross-platform direct:
```bash
python Launchers/bootstrap_vscode.py
```

## 3. Start WebUI

Linux/Kali/macOS:
```bash
source .venv_test/bin/activate
python3 WebUI/production_server.py
```

Windows PowerShell:
```powershell
.\.venv_test\Scripts\Activate.ps1
python WebUI\production_server.py
```

Open:
- http://127.0.0.1:8080/login

## 4. Login

1. Go to `/login`.
2. Enter your username and password.
3. Click `Login`.
4. Change password if prompted on first sign-in.

## Default Credentials (First-Time Setup)

When no user database exists yet, the system creates these temporary accounts.
**You will be required to change all passwords on first login.**

| Username   | Password      | Role     | Can Do                                  |
|------------|---------------|----------|-----------------------------------------|
| `admin`    | `admin123`    | admin    | Everything — manage users, all settings |
| `operator` | `operator123` | operator | Run scans, countermeasures, simulations |
| `viewer`   | `viewer123`   | viewer   | Read-only dashboards and results        |
| `guest`    | `guest123`    | guest    | Limited view access                     |

> **Important:** Change all passwords immediately after first login.
> The admin account can add, remove, and reset passwords for all other users under **Settings → Users**.

## Multi-User Access

Multiple users can be logged in simultaneously. Each session is fully isolated.
The admin can manage users at `/portal` → Settings → Users:
- Add new users with any role
- Reset or disable accounts
- Upgrade/downgrade user roles at any time

## 5. Notes For Non-Kali Systems

- Simulation and most WebUI workflows run on Windows/Linux/macOS.
- Some live capture or system-level countermeasure features may require Linux/Kali tools and elevated permissions.

## 6. If VS Code Extensions Are Not Auto-Installed

The bootstrap script asks first. If you skipped, run it again, or install from recommendations in:
- `.vscode/extensions.json`
