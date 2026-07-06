set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VALIDATOR="$SCRIPT_DIR/../skills/zul-writer/scripts/validate-zul.py"
SAMPLE_ZUL="$SCRIPT_DIR/valid/valid-sample.zul"
exec python3 "$VALIDATOR" "$SAMPLE_ZUL"
