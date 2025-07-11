# Local ComfyUI Development Setup

This setup allows you to run a base version of the worker-comfyui image locally to test workflows and identify missing nodes.

## Quick Start

1. **Run the setup script:**
   ```bash
   ./scripts/setup-local.sh
   ```

2. **Access ComfyUI:**
   - Open your browser and go to `http://localhost:8188`
   - You'll see the ComfyUI interface

3. **Test your workflow:**
   - Import your workflow JSON file
   - ComfyUI will show which nodes are missing (they'll appear as red/error nodes)
   - Note down the missing node names

## Manual Setup

If you prefer to run commands manually:

```bash
# Create directories
mkdir -p local-data/output local-data/input local-data/models

# Build and start the container
docker-compose -f docker-compose.local.yml up --build
```

## What This Gives You

- **Base ComfyUI installation** with standard nodes
- **GPU support** (if you have NVIDIA GPU)
- **Persistent storage** for outputs and inputs
- **Web interface** at `http://localhost:8188`
- **Ability to test workflows** and see missing nodes

## Finding Missing Nodes

When you import a workflow, missing nodes will:
- Appear as red/error nodes in the interface
- Show error messages when you try to execute the workflow
- Be listed in the console output

Common missing nodes you might need:
- `ComfyUI-Manager` (for installing other nodes)
- `ComfyUI-AnimateDiff-Evolved`
- `ComfyUI-IPAdapter-Plus`
- `ComfyUI-Essentials`
- Custom nodes from the Comfy Registry

## Next Steps

Once you identify the missing nodes, you can:

1. **Create a custom Dockerfile** (as described in `docs/customization.md`)
2. **Install the missing nodes** using `comfy-node-install`
3. **Build your custom image** for deployment

## Stopping the Container

```bash
docker-compose -f docker-compose.local.yml down
```

## Troubleshooting

- **No GPU support**: Remove the `deploy.resources.reservations.devices` section from `docker-compose.local.yml`
- **Port already in use**: Change the port mapping in `docker-compose.local.yml` (e.g., `"8189:8188"`)
- **Permission issues**: Make sure Docker has access to your GPU (install nvidia-docker if needed) 