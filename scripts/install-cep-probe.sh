#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
extension_id="com.g960059.premiere-bootstrap-probe"
source_dir="$repo_root/cep/$extension_id"
target_root="$HOME/Library/Application Support/Adobe/CEP/extensions"
target_dir="$target_root/$extension_id"

mkdir -p "$target_root"
rm -rf "$target_dir"
ln -s "$source_dir" "$target_dir"

# Enable unsigned CEP extension loading for common CEP generations used by
# recent Adobe apps. Missing domains are harmless.
for version in 9 10 11 12 13; do
  defaults write "com.adobe.CSXS.$version" PlayerDebugMode 1
done

echo "Installed CEP probe:"
echo "  $target_dir -> $source_dir"
echo
echo "Restart Premiere Pro, then open:"
echo "  Window > Extensions > Premiere Bootstrap Probe"

