#!/bin/zsh
set -e
package_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$package_dir"
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$package_dir"
if command -v label-studio >/dev/null 2>&1; then
  exec label-studio start --port 8080
fi
if [[ -x "$HOME/.local/bin/label-studio" ]]; then
  exec "$HOME/.local/bin/label-studio" start --port 8080
fi
echo "Label Studio was not found in this Terminal environment."
echo "Activate the environment where it is installed, then run this file again."
read -r "?Press Return to close."
