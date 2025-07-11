
import runpod
from runpod.serverless.utils import rp_upload
import json
import time
import os
import requests
import base64
from io import BytesIO

# Configurations
COMFY_API_URL = "http://127.0.0.1:8188"
COMFY_API_MAX_WAIT = 30  # Increased to ensure wait until ComfyUI is ready
COMFY_POLLING_MAX_WAIT = 30  # Max seconds to wait for job completion
COMFY_API_RETRY_DELAY = 0.1  # Initial backoff delay
REFRESH_WORKER = os.environ.get("REFRESH_WORKER", "false").lower() == "true"

def validate_input(job_input):
    """Validates input for required parameters."""
    if job_input is None:
        return None, "Please provide input"
    
    if isinstance(job_input, str):
        try:
            job_input = json.loads(job_input)
        except json.JSONDecodeError:
            return None, "Invalid JSON format in input"

    workflow = job_input.get("workflow")
    if not workflow:
        return None, "Missing 'workflow' parameter"

    image = job_input.get("image")
    if image and ("name" not in image or "image" not in image):
        return None, "'image' must contain 'name' and 'image' keys"

    return {"workflow": workflow, "image": image}, None

def check_server(url, max_wait=COMFY_API_MAX_WAIT):
    """Wait for API readiness using exponential backoff."""
    start_time, delay = time.time(), COMFY_API_RETRY_DELAY
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("ComfyUI API is reachable")
                return True
        except requests.RequestException:
            pass
        time.sleep(delay)
        delay = min(delay * 1.5, 3)

    print(f"ComfyUI API not ready after {max_wait}s")
    return False

def upload_image(image):
    """Upload a single image to ComfyUI."""
    if not image:
        return {"status": "success", "message": "No image to upload"}

    try:
        name, image_data = image["name"], image["image"]
        blob = base64.b64decode(image_data)

        files = {"image": (name, BytesIO(blob), "image/png"), "overwrite": (None, "true")}
        response = requests.post(f"{COMFY_API_URL}/upload/image", files=files, timeout=5)

        if response.status_code != 200:
            return {"status": "error", "message": f"Error uploading {name}: {response.text}"}

        return {"status": "success", "message": f"Successfully uploaded {name}"}
    
    except Exception as e:
        return {"status": "error", "message": f"Upload failed: {str(e)}"}

def queue_workflow(workflow):
    """Submit workflow for processing."""
    response = requests.post(f"{COMFY_API_URL}/prompt", json={"prompt": workflow}, timeout=10)
    return response.json()

def get_history(prompt_id, max_wait=COMFY_POLLING_MAX_WAIT):
    """Polls API for job completion with adaptive interval."""
    start_time, delay = time.time(), 0.5
    while time.time() - start_time < max_wait:
        history = requests.get(f"{COMFY_API_URL}/history/{prompt_id}").json()
        if prompt_id in history and history[prompt_id].get("outputs"):
            return history[prompt_id].get("outputs")
        time.sleep(delay)
        delay = min(delay * 1.5, 5)

    raise TimeoutError("Max retries reached while waiting for image generation")

def get_image_from_memory(outputs, job_id):
    """Retrieve and return a single image without saving to disk."""
    try:
        for node_output in outputs.values():
            if "images" in node_output:
                image_info = node_output["images"][0]
                img_url = f"{COMFY_API_URL}/view?filename={image_info['filename']}&subfolder={image_info['subfolder']}"
                img_response = requests.get(img_url, timeout=10)

                if img_response.status_code == 200:
                    if os.environ.get("BUCKET_ENDPOINT_URL", False):
                        return {"status": "success", "message": rp_upload.upload_image(job_id, BytesIO(img_response.content))}
                    else:
                        return {"status": "success", "message": base64.b64encode(img_response.content).decode("utf-8")}

                return {"status": "error", "message": f"Failed to retrieve image from {img_url}"}

    except Exception as e:
        return {"status": "error", "message": f"Error processing output: {str(e)}"}

def handler(job):
    """Main handler for processing jobs."""
    job_input = job["input"]

    validated_data, error_message = validate_input(job_input)
    if error_message:
        return {"error": error_message}

    workflow, image = validated_data["workflow"], validated_data.get("image")

    if not check_server(COMFY_API_URL):
        return {"error": "ComfyUI API unavailable"}

    upload_result = upload_image(image)
    if upload_result["status"] == "error":
        return upload_result

    try:
        queued_workflow = queue_workflow(workflow)
        prompt_id = queued_workflow["prompt_id"]
        print(f"Workflow queued with ID {prompt_id}")
    except Exception as e:
        return {"error": f"Error queuing workflow: {str(e)}"}

    try:
        outputs = get_history(prompt_id)
        image_result = get_image_from_memory(outputs, job["id"])
        return {**image_result, "refresh_worker": REFRESH_WORKER}

    except Exception as e:
        return {"error": f"Error processing workflow: {str(e)}"}

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
