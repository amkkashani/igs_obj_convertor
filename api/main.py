import os
import uuid
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# Initialize the FastAPI app
app = FastAPI(title="IGS to OBJ Converter")

# Mount the 'static' directory to serve our index.html
# This makes the file at 'static/index.html' available at 'http://localhost:8000/'
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    """
    Serves the main HTML page from the 'static' folder.
    """
    try:
        html_content = Path("static/index.html").read_text()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=500)

@app.post("/convert")
async def convert_igs_to_obj(file: UploadFile = File(...)):
    """
    The main conversion endpoint.
    Receives .igs, converts it using a Docker container, and returns .obj.
    """
    # --- 1. Validation ---
    if not file.filename.endswith(('.igs', '.iges')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload an .igs or .iges file."
        )

    # --- 2. Create Temporary Directory ---
    # This creates a directory (e.g., /tmp/tmpXYZ) that exists
    # on the host AND inside this container, because we mounted /tmp in docker-compose.
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Define unique filenames
            input_filename = "input.igs" # Keep it simple
            output_filename = "output.obj"
            
            input_filepath = temp_dir_path / input_filename
            output_filepath = temp_dir_path / output_filename

            # --- 3. Save Uploaded File ---
            try:
                with open(input_filepath, "wb") as buffer:
                    buffer.write(await file.read())
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

            # --- 4. Build the Docker Command ---
            # This is the core logic.
            docker_command = [
                "docker", "run",
                "--rm",  # Automatically remove the container when it exits
                
                # Mount the temporary directory from the host into the gmsh container
                # The path 'temp_dir_path' (e.g., /tmp/tmpXYZ) works because
                # it exists on the host (where the Docker daemon is running).
                "-v", f"{temp_dir_path}:/app",
                
                "trophime/gmsh",  # The corrected, public Docker image
                
                # The command to run inside the gmsh container
                "gmsh", f"/app/{input_filename}",
                "-o", f"/app/{output_filename}",
                "-3"  # Ensure a 3D mesh is generated
            ]

            # --- 5. Run the Conversion ---
            try:
                # Run the command and wait for it to complete
                # capture_output=True keeps stdout/stderr in memory
                # check=True raises an error if the command fails (non-zero exit code)
                subprocess.run(
                    docker_command, 
                    check=True, 
                    capture_output=True,
                    timeout=60 # Add a 60-second timeout
                )
            
            except subprocess.TimeoutExpired:
                raise HTTPException(status_code=504, detail="Conversion timed out.")
            except subprocess.CalledProcessError as e:
                # If gmsh fails, return its error message for debugging
                error_message = e.stderr.decode() or e.stdout.decode()
                raise HTTPException(status_code=500, detail=f"Conversion failed: {error_message}")
            except FileNotFoundError:
                 raise HTTPException(status_code=500, detail="Docker command not found. Is Docker installed?")

            # --- 6. Check for Output and Return File ---
            if not output_filepath.exists():
                raise HTTPException(status_code=500, detail="Conversion failed: Output file not created.")

            # Return the .obj file to the user for download
            return FileResponse(
                path=output_filepath,
                filename=f"{Path(file.filename).stem}.obj", # e.g., "my_model.obj"
                media_type="application/octet-stream"
            )
            
    except Exception as e:
        # Catch-all for other errors (e.g., temp dir creation failed)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    # The 'with' block automatically cleans up the temporary directory
    # /tmp/tmpXYZ and all its contents (input.igs, output.obj)