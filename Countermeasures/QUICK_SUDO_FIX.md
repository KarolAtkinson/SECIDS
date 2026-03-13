# Sudo Password Fix - Quick Setup Guide

## The Problem You're Experiencing

❌ **"Can't input password before terminal resets"**

When running countermeasures, you see a password prompt but can't type anything before it times out.

## Quick Fix (30 seconds)

Run this ONE command:

```bash
sudo bash Countermeasures/setup_passwordless_sudo.sh
```

Enter your password **once**, and you're done!

## Now Test It

```bash
# Should work without asking for password
python3 Countermeasures/passive_ui.py
```

## What Just Happened?

The script configured your system to allow iptables commands without a password prompt. This is:
- ✅ Safe (only specific iptables commands)
- ✅ Convenient (no more password timeout issues)
- ✅ Reversible (run in the script to see removal command)

## Alternative: Run with Sudo Each Time

If you don't want to configure passwordless sudo:

```bash
sudo python3 Countermeasures/passive_ui.py
```

You'll enter password **once per session** instead of for every iptables command.

## More Information

- **Detailed explanation:** `Countermeasures/SUDO_FIX.md`
- **Full summary:** `SUDO_PASSWORD_FIX_SUMMARY.md`
- **Manual section:** `Master-Manual.md` Section 23.12

---

**TL;DR:** Run `sudo bash Countermeasures/setup_passwordless_sudo.sh` and the password timeout problem is fixed forever!
