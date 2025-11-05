#!/bin/bash
# Fix CosyVoice2 model paths in configuration

MODEL_DIR="/root/.cache/modelscope/hub/iic/CosyVoice2-0.5B"
YAML_FILE="$MODEL_DIR/cosyvoice2.yaml"

echo "Fixing CosyVoice2 model paths..."
echo "Model directory: $MODEL_DIR"
echo "YAML file: $YAML_FILE"

# Backup the original file
cp "$YAML_FILE" "$YAML_FILE.backup"
echo "✓ Created backup: $YAML_FILE.backup"

# Replace empty pretrain_path with the model directory
# The LLM model files (llm.pt, etc.) are in the same directory
sed -i "s|pretrain_path: ''|pretrain_path: '$MODEL_DIR'|g" "$YAML_FILE"
sed -i 's|pretrain_path: ""|pretrain_path: "'$MODEL_DIR'"|g' "$YAML_FILE"

# Also try replacing if the path is set to '!ref <root>'
sed -i "s|pretrain_path: !ref <root>|pretrain_path: '$MODEL_DIR'|g" "$YAML_FILE"

# Replace any relative paths with absolute paths
sed -i "s|llm: !ref <root>/llm.pt|llm: $MODEL_DIR/llm.pt|g" "$YAML_FILE"
sed -i "s|flow: !ref <root>/flow.pt|flow: $MODEL_DIR/flow.pt|g" "$YAML_FILE"
sed -i "s|hift: !ref <root>/hift.pt|hift: $MODEL_DIR/hift.pt|g" "$YAML_FILE"

echo "✓ Updated paths in YAML file"
echo ""
echo "Showing differences:"
diff "$YAML_FILE.backup" "$YAML_FILE" || true

echo ""
echo "✓ Done! Restart the TTS service now."

