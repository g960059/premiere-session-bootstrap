#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
extension_id="com.g960059.premiere-bootstrap-probe"
source_dir="$repo_root/uxp/premiere-bootstrap-probe"
target_root="$HOME/Library/Application Support/Adobe/UXP/extensions"
target_dir="$target_root/$extension_id"

mkdir -p "$target_root"
rm -rf "$target_dir"
ln -s "$source_dir" "$target_dir"

echo "Installed UXP probe:"
echo "  $target_dir -> $source_dir"
echo
echo "If Premiere does not show it, enable Developer Mode and load this folder"
echo "with Adobe UXP Developer Tool:"
echo "  $source_dir"
