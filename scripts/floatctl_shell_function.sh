#!/bin/bash
# FloatCtl function for development - reflects changes immediately
# Add this to your ~/.zshrc or ~/.bashrc

# Option 1: Simple approach using PYTHONPATH
floatctl() {
    PYTHONPATH="/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py/src:$PYTHONPATH" \
    UV_PROJECT_ROOT="/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py" \
    uv run --project "/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py" \
    python -m floatctl "$@"
}

# Option 2: If Option 1 doesn't work, use this approach
# floatctl() {
#     local floatctl_py="/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py/src/floatctl/__main__.py"
#     UV_PROJECT_ROOT="/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py" \
#     uv run --project "/Users/evan/projects/float-workspace/offical-exports/data-2025-06-28-07-14-08/floatctl-py" \
#     python "$floatctl_py" "$@"
# }