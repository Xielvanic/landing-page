import subprocess
import os

def build_docker_image():
    # Define the directory where the Dockerfile is located
    dockerfile_dir = os.path.abspath(os.path.dirname(__file__))

    # Change to the directory containing the Dockerfile
    os.chdir(dockerfile_dir)

    # Define the image name
    image_name = "001landingpage:latest"

    # Run the Docker build command
    try:
        subprocess.run(['docker', 'build', '-t', image_name, '.'], check=True)
        print(f"Docker image '{image_name}' built successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error building Docker image: {e}")

    # Optionally, run the Docker container
    try:
        subprocess.run(['docker', 'run', '-d', '-p', '5000:5000', image_name], check=True)
        print(f"Docker container from image '{image_name}' started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Docker container: {e}")

if __name__ == "__main__":
    build_docker_image() 