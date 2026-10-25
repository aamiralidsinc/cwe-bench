#!/bin/bash
exec "$HOME/.local/bin/claude" -p "Reply with exactly the single word: PONG" --model "$MODEL" --output-format json
