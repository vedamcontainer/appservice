import os
import yaml
import configparser

# Custom configparser that preserves case
class CaseInsensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr  # Preserve case

# Define file paths based on custom HOME_DIR from git.ini
GIT_INI_PATH = os.path.join(os.getcwd(), "git.ini")
print(f"Checking for git.ini at: {GIT_INI_PATH}")

if not os.path.exists(GIT_INI_PATH):
    print(f"Error: git.ini not found at {GIT_INI_PATH}")
    exit(1)

git_config = CaseInsensitiveConfigParser()
git_config.read(GIT_INI_PATH)
print("git.ini loaded successfully.")

if "gitdetails" not in git_config or "home_dir" not in git_config["gitdetails"]:
    print("Error: 'home_dir' not found in [gitdetails] section of git.ini")
    exit(1)

HOME_DIR = os.path.join(os.getcwd(), git_config["gitdetails"]["home_dir"])
print(f"Resolved HOME_DIR: {HOME_DIR}")

COMPOSE_FILE = os.path.join(HOME_DIR, "docker-compose.yml")

def generate_scripts(compose_file, output_dir):
    if not os.path.exists(compose_file):
        print(f"Error: docker-compose.yml not found at {compose_file}")
        return
    
    with open(compose_file, 'r') as file:
        compose_data = yaml.safe_load(file)
    
    services = compose_data.get("services", {})

    for service_name, service_config in services.items():
        container_name = service_config.get("container_name", service_name)

        # Generate Batch File using Docker Compose
        batch_filename = os.path.join(output_dir, f"start_{service_name}.bat")
        with open(batch_filename, "w") as batch_file:
            batch_file.write("@echo off\n")
            batch_file.write(f"echo Stopping and removing existing {container_name}...\n")
            batch_file.write(f"docker-compose stop {service_name}\n")
            batch_file.write(f"docker-compose rm -f {service_name}\n")
            batch_file.write("echo Rebuilding image...\n")
            batch_file.write(f"docker-compose build {service_name}\n")
            batch_file.write("echo Cleaning up dangling images...\n")
            batch_file.write("docker image prune -f\n")            
            batch_file.write("echo Running new container...\n")
            batch_file.write(f"docker-compose up -d {service_name}\n")
            batch_file.write("echo ✅ Rebuild and restart completed successfully.\n")
        print(f"Generated: {batch_filename}")

        # Generate Shell Script using Docker Compose
        shell_filename = os.path.join(output_dir, f"start_{service_name}.sh")
        with open(shell_filename, "w") as shell_file:
            shell_file.write("#!/bin/bash\n")
            shell_file.write(f"echo Stopping and removing existing {container_name}...\n")
            shell_file.write(f"docker-compose stop {service_name}\n")
            shell_file.write(f"docker-compose rm -f {service_name}\n")
            shell_file.write("echo Rebuilding image...\n")
            shell_file.write(f"docker-compose build {service_name}\n")
            shell_file.write("echo Cleaning up dangling images...\n")
            shell_file.write("docker image prune -f\n")            
            shell_file.write("echo Running new container...\n")
            shell_file.write(f"docker-compose up -d {service_name}\n")
            shell_file.write("echo ✅ Rebuild and restart completed successfully.\n")
        os.chmod(shell_filename, 0o755)  # Make shell script executable
        print(f"Generated: {shell_filename}")

if __name__ == "__main__":
    generate_scripts(COMPOSE_FILE, HOME_DIR)