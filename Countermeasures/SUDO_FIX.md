# Countermeasure Sudo Configuration

## The Password Prompt Issue

If you're experiencing issues where you can't input your sudo password before the terminal resets, this is because:

1. **Countermeasures require `sudo` for iptables** - Blocking IPs/ports needs root privileges
2. **Password prompts timeout** - Subprocess calls timeout after 5 seconds waiting for password
3. **Captured output prevents input** - The code uses `capture_output=True`, blocking terminal interaction

## Solution

You have two options:

### Option 1: Configure Passwordless Sudo (Recommended)

Run the setup script to allow iptables commands without password: 

```bash
cd /home/kali/Documents/Code/SECIDS-CNN
sudo bash Countermeasures/setup_passwordless_sudo.sh
```

**What this does:**
- Creates `/etc/sudoers.d/secids-countermeasures`
- Allows your user to run iptables without password
- Only affects specific iptables commands (safe and minimal)
- Can be easily removed later

**After setup:**
```bash
# Now works without password prompts!
python3 Countermeasures/passive_ui.py
python3 Countermeasures/active_ui.py
```

### Option 2: Run with Sudo

Always run countermeasure UIs with sudo:

```bash
sudo python3 Countermeasures/passive_ui.py
sudo python3 Countermeasures/active_ui.py
```

**Caveat:** You'll need to enter password each time you run.

## Testing Without Sudo

If you just want to test without blocking capability:

```bash
# Run normally (will warn about missing sudo)
python3 Countermeasures/passive_ui.py

# When prompted, choose 'y' to continue without blocking
# Threats will be detected and logged, but not blocked
```

## How the Fix Works

### Before Fix
```
[Terminal] → Run countermeasure
[Code] → subprocess.run(['sudo', 'iptables', ...], capture_output=True)
[sudo] → Password: ___
[Terminal] → ⚠️  Can't type! subprocess captured stdin/stdout
[After 5 seconds] → Timeout! Command fails
```

### After Fix
```
[Code] → Check sudo access first with 'sudo -n iptables -L'
[If available] → Proceed with blocking
[If not available] → Show clear warning, skip blocking, continue monitoring
```

### With Passwordless Sudo
```
[Terminal] → Run countermeasure
[Code] → subprocess.run(['sudo', 'iptables', ...])
[sudo] → Passwordless configuration found, executing...
[iptables] → IP blocked successfully ✓
```

## Verification

Check if passwordless sudo is working:

```bash
# Should show iptables rules without password prompt
sudo iptables -L

# Should work without password
sudo iptables -A INPUT -s 192.168.1.100 -j DROP
sudo iptables -D INPUT -s 192.168.1.100 -j DROP
```

## Troubleshooting

### "sudo: a password is required"
```bash
# Configure passwordless sudo
sudo bash Countermeasures/setup_passwordless_sudo.sh
```

### "Permission denied" even with sudo
```bash
# Check if iptables is installed
which iptables

# Install if missing (Kali usually has it)
sudo apt-get install iptables
```

### "Timeout blocking IP" in logs
```bash
# This means sudo asked for password and timed out
# Solution: Configure passwordless sudo (Option 1 above)
```

### Want to remove passwordless sudo later?
```bash
sudo rm /etc/sudoers.d/secids-countermeasures
```

## Updated Behavior

The countermeasure system now:

1. **Checks sudo availability on startup** - No more surprise timeouts
2. **Warns you immediately** - Clear message if sudo isn't available
3. **Allows monitoring without blocking** - Still useful for threat detection
4. **Provides helpful instructions** - Shows exactly how to fix the issue
5. **Handles timeouts gracefully** - Better error messages

## Additional Notes

- **Development/Testing:** Passwordless sudo recommended for convenience
- **Production:** Consider running as a dedicated service with proper privileges
- **Security:** Passwordless sudo config only allows specific iptables commands
- **Logs:** Check `Countermeasures/logs/` for detailed error messages

## Quick Reference

| Scenario | Command | Requires Password? |
|----------|---------|-------------------|
| **With passwordless sudo** | `python3 Countermeasures/passive_ui.py` | No |
| **Without configuration** | `sudo python3 Countermeasures/passive_ui.py` | Yes (once per run) |
| **Monitor-only mode** | `python3 Countermeasures/passive_ui.py` then 'y' | No (but can't block) |

---

**Setup Script:** [setup_passwordless_sudo.sh](setup_passwordless_sudo.sh)  
**System Updated:** 2026-02-23  
**Issue:** Password prompt timeout fixed ✓
