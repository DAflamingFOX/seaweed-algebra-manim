#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"

# Full Wind-Down
uv run manim -qm --disable_caching --format=gif -o full_wind_down examples.py FullWindDown

# Rotation Contraction
uv run manim -qm --disable_caching --format=gif -o rotation_contraction-reference examples.py RotationContractionReference
uv run manim -qm --disable_caching --format=gif -o rotation_contraction-secondary examples.py RotationContractionSecondary

# Pure Contraction
uv run manim -qm --disable_caching --format=gif -o pure_contraction-reference examples.py PureContractionReference
uv run manim -qm --disable_caching --format=gif -o pure_contraction-secondary examples.py PureContractionSecondary

# Component Deletion
uv run manim -qm --disable_caching --format=gif -o component_deletion-reference examples.py ComponentDeletionReference
uv run manim -qm --disable_caching --format=gif -o component_deletion-secondary examples.py ComponentDeletionSecondary

# Flip
uv run manim -qm --disable_caching --format=gif -o flip-reference examples.py FlipReference
uv run manim -qm --disable_caching --format=gif -o flip-secondary examples.py FlipSecondary

# Block Elimination
uv run manim -qm --disable_caching --format=gif -o block_elimination-reference examples.py BlockEliminationReference
uv run manim -qm --disable_caching --format=gif -o block_elimination-secondary examples.py BlockEliminationSecondary
