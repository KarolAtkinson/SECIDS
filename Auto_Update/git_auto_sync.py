#!/usr/bin/env python3
"""
Git Auto-Sync Script
Automatically synchronizes local repository with GitHub
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
import json
import argparse
import os
import re
import urllib.request
import urllib.error
from typing import Optional


class GitAutoSync:
    """Handles automatic Git synchronization with remote repository"""
    
    def __init__(self, repo_path=None, dry_run=False):
        """
        Initialize Git auto-sync
        
        Args:
            repo_path: Path to git repository (default: project root)
            dry_run: If True, show what would be done without executing
        """
        if repo_path is None:
            # Get project root (2 levels up from this script)
            self.repo_path = Path(__file__).parent.parent
        else:
            self.repo_path = Path(repo_path)
        
        self.dry_run = dry_run
        self.log_file = Path(__file__).parent / 'logs' / 'git_sync.log'
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def run_command(self, cmd: list, capture_output: bool = True) -> tuple:
        """
        Run a shell command
        
        Args:
            cmd: Command as list of strings
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            Tuple of (success, stdout, stderr)
        """
        if self.dry_run:
            self.log(f"DRY RUN: Would execute: {' '.join(cmd)}", "DRY-RUN")
            return (True, "", "")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return (result.returncode == 0, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            self.log(f"Command timed out: {' '.join(cmd)}", "ERROR")
            return (False, "", "Command timed out")
        except Exception as e:
            self.log(f"Command failed: {e}", "ERROR")
            return (False, "", str(e))
    
    def check_git_status(self) -> dict:
        """
        Check current Git status
        
        Returns:
            Dictionary with status information
        """
        status = {
            'has_changes': False,
            'untracked_files': 0,
            'modified_files': 0,
            'deleted_files': 0,
            'branch': 'unknown',
            'ahead': 0,
            'behind': 0
        }
        
        # Get current branch
        success, stdout, stderr = self.run_command(['git', 'branch', '--show-current'])
        if success:
            status['branch'] = stdout.strip()
        
        # Check for changes
        success, stdout, stderr = self.run_command(['git', 'status', '--porcelain'])
        if success:
            lines = [line for line in stdout.split('\n') if line.strip()]
            status['has_changes'] = len(lines) > 0
            
            for line in lines:
                if line.startswith('??'):
                    status['untracked_files'] += 1
                elif line.startswith(' M') or line.startswith('M '):
                    status['modified_files'] += 1
                elif line.startswith(' D') or line.startswith('D '):
                    status['deleted_files'] += 1
        
        # Check commits ahead/behind
        success, stdout, stderr = self.run_command(
            ['git', 'rev-list', '--left-right', '--count', 'HEAD...@{u}']
        )
        if success and stdout.strip():
            parts = stdout.strip().split()
            if len(parts) == 2:
                status['ahead'] = int(parts[0])
                status['behind'] = int(parts[1])
        
        return status

    def get_origin_remote(self) -> str:
        """Return origin remote URL or empty string."""
        success, stdout, _ = self.run_command(['git', 'remote', 'get-url', 'origin'])
        if not success:
            return ""
        return stdout.strip()

    def parse_github_slug(self, remote_url: str) -> Optional[str]:
        """Extract owner/repo slug from GitHub HTTPS/SSH remote."""
        if not remote_url:
            return None

        match = re.search(r'github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
        if not match:
            return None

        owner = match.group(1).strip()
        repo = match.group(2).strip()
        if not owner or not repo:
            return None
        return f"{owner}/{repo}"

    def check_remote_privacy(self) -> dict:
        """
        Check remote repository visibility using GitHub API.

        Returns:
            dict with keys: ok, remote, slug, reachable, private, visibility, message
        """
        remote = self.get_origin_remote()
        slug = self.parse_github_slug(remote)

        result = {
            'ok': False,
            'remote': remote,
            'slug': slug,
            'reachable': False,
            'private': None,
            'visibility': 'unknown',
            'message': ''
        }

        if not remote:
            result['message'] = 'Origin remote not found'
            return result

        if not slug:
            result['message'] = 'Origin is not a GitHub repository URL'
            return result

        api_url = f"https://api.github.com/repos/{slug}"
        req = urllib.request.Request(api_url, headers={'Accept': 'application/vnd.github+json'})

        token = os.getenv('GITHUB_TOKEN', '').strip() or os.getenv('GH_TOKEN', '').strip()
        if token:
            req.add_header('Authorization', f'Bearer {token}')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode('utf-8'))
                private = bool(payload.get('private', False))
                visibility = str(payload.get('visibility', 'private' if private else 'public'))
                result.update(
                    {
                        'ok': True,
                        'reachable': True,
                        'private': private,
                        'visibility': visibility,
                        'message': f"Remote visibility: {visibility}",
                    }
                )
                return result
        except urllib.error.HTTPError as exc:
            result['message'] = f'GitHub API HTTP error: {exc.code}'
            return result
        except urllib.error.URLError as exc:
            result['message'] = f'GitHub API not reachable: {exc.reason}'
            return result
        except Exception as exc:
            result['message'] = f'Failed to check remote privacy: {exc}'
            return result
    
    def pull_changes(self) -> bool:
        """
        Pull changes from remote repository
        
        Returns:
            True if successful
        """
        self.log("Fetching changes from remote...")
        success, stdout, stderr = self.run_command(['git', 'fetch', 'origin'])
        
        if not success:
            self.log(f"Fetch failed: {stderr}", "ERROR")
            return False
        
        self.log("Pulling changes...")
        success, stdout, stderr = self.run_command(['git', 'pull', '--rebase', 'origin'])
        
        if success:
            self.log("Successfully pulled changes from remote", "SUCCESS")
            if stdout.strip():
                self.log(f"Pull output: {stdout.strip()}")
        else:
            self.log(f"Pull failed: {stderr}", "ERROR")
        
        return success
    
    def push_changes(self, commit_message: Optional[str] = None) -> bool:
        """
        Stage, commit, and push changes to remote repository
        
        Args:
            commit_message: Custom commit message (auto-generated if None)
        
        Returns:
            True if successful
        """
        status = self.check_git_status()
        
        if not status['has_changes']:
            self.log("No local changes to commit", "INFO")
            return True
        
        # Stage all changes
        self.log(f"Staging {status['modified_files']} modified, "
                f"{status['untracked_files']} untracked files...")
        success, stdout, stderr = self.run_command(['git', 'add', '-A'])
        
        if not success:
            self.log(f"Failed to stage changes: {stderr}", "ERROR")
            return False
        
        # Generate commit message if not provided
        if commit_message is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Auto-sync: {timestamp}"
            
            details = []
            if status['modified_files'] > 0:
                details.append(f"{status['modified_files']} modified")
            if status['untracked_files'] > 0:
                details.append(f"{status['untracked_files']} new")
            if status['deleted_files'] > 0:
                details.append(f"{status['deleted_files']} deleted")
            
            if details:
                commit_message += f" ({', '.join(details)})"
        
        # Commit changes
        self.log(f"Committing with message: {commit_message}")
        success, stdout, stderr = self.run_command(['git', 'commit', '-m', commit_message])
        
        if not success and 'nothing to commit' not in stderr:
            self.log(f"Commit failed: {stderr}", "ERROR")
            return False
        
        # Push to remote
        self.log("Pushing to remote repository...")
        success, stdout, stderr = self.run_command(['git', 'push', 'origin', status['branch']])
        
        if success:
            self.log("Successfully pushed changes to GitHub", "SUCCESS")
        else:
            self.log(f"Push failed: {stderr}", "ERROR")
        
        return success
    
    def sync(self, pull_first: bool = True, push: bool = True) -> dict:
        """
        Perform full synchronization
        
        Args:
            pull_first: Pull changes before pushing
            push: Push local changes after pull
        
        Returns:
            Dictionary with sync results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'pull_success': False,
            'push_success': False,
            'status': {}
        }
        
        self.log("=" * 60)
        self.log("Starting Git auto-sync...")
        
        # Get initial status
        results['status'] = self.check_git_status()
        self.log(f"Current branch: {results['status']['branch']}")
        self.log(f"Local changes: {results['status']['has_changes']}")
        self.log(f"Commits ahead: {results['status']['ahead']}, behind: {results['status']['behind']}")

        require_private = os.getenv('SECIDS_REQUIRE_PRIVATE_REPO', '1').strip().lower() not in {'0', 'false', 'no'}
        privacy = self.check_remote_privacy()
        results['privacy'] = privacy
        if privacy.get('ok'):
            self.log(privacy.get('message', 'Remote visibility check complete'))
        else:
            self.log(f"Remote visibility check warning: {privacy.get('message', 'unknown')}", "WARNING")

        if require_private:
            if not privacy.get('ok'):
                self.log('Aborting sync: could not verify remote privacy while SECIDS_REQUIRE_PRIVATE_REPO=1', 'ERROR')
                return results
            if not bool(privacy.get('private')):
                self.log('Aborting sync: remote repository is public while SECIDS_REQUIRE_PRIVATE_REPO=1', 'ERROR')
                return results
        
        # Pull changes first
        if pull_first:
            results['pull_success'] = self.pull_changes()
        else:
            results['pull_success'] = True  # Skip pull
        
        # Push local changes
        if push and results['pull_success']:
            results['push_success'] = self.push_changes()
        else:
            results['push_success'] = False
        
        self.log("Git sync completed")
        self.log("=" * 60)
        
        return results


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description="Automatically synchronize Git repository with GitHub"
    )
    parser.add_argument(
        '--repo', 
        type=str, 
        default=None,
        help="Path to Git repository (default: project root)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be done without executing"
    )
    parser.add_argument(
        '--pull-only',
        action='store_true',
        help="Only pull changes, don't push"
    )
    parser.add_argument(
        '--push-only',
        action='store_true',
        help="Only push changes, don't pull first"
    )
    parser.add_argument(
        '--message',
        type=str,
        default=None,
        help="Custom commit message"
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help="Show current Git status only"
    )
    parser.add_argument(
        '--check-privacy',
        action='store_true',
        help="Check GitHub remote visibility and exit"
    )
    
    args = parser.parse_args()
    
    # Create sync instance
    sync = GitAutoSync(repo_path=args.repo, dry_run=args.dry_run)
    
    # Handle status-only request
    if args.status:
        status = sync.check_git_status()
        privacy = sync.check_remote_privacy()
        print("\n" + "=" * 60)
        print("Git Repository Status")
        print("=" * 60)
        print(f"Branch: {status['branch']}")
        print(f"Modified files: {status['modified_files']}")
        print(f"Untracked files: {status['untracked_files']}")
        print(f"Deleted files: {status['deleted_files']}")
        print(f"Commits ahead of remote: {status['ahead']}")
        print(f"Commits behind remote: {status['behind']}")
        print(f"Has local changes: {status['has_changes']}")
        print(f"Remote visibility: {privacy.get('visibility', 'unknown')}")
        print(f"Remote private: {privacy.get('private')}")
        if privacy.get('message'):
            print(f"Privacy check: {privacy.get('message')}")
        print("=" * 60 + "\n")
        return 0

    if args.check_privacy:
        privacy = sync.check_remote_privacy()
        print(json.dumps(privacy, indent=2))
        return 0 if privacy.get('ok') and bool(privacy.get('private')) else 1
    
    # Determine sync mode
    pull_first = not args.push_only
    push = not args.pull_only
    
    # Perform sync
    results = sync.sync(pull_first=pull_first, push=push)
    
    # Exit with appropriate code
    if results['pull_success'] and (results['push_success'] or not push):
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
