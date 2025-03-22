#!/bin/bash

set -e  # Exit script on any error

# Update the system and install dependencies
echo "Updating package list and installing dependencies..."
sudo yum update -y

# Function to install dependencies only if not already installed
install_if_missing() {
    if ! command -v $1 &>/dev/null; then
        echo "Installing $1..."
        sudo yum install -y $2
    else
        echo "$1 is already installed. Skipping..."
    fi
}

# Check and install curl
install_if_missing "curl" "curl"

# Check and install GCC, GCC-C++, and make
install_if_missing "gcc" "gcc gcc-c++ make"

# Check and install Docker Compose
if ! command -v docker-compose &>/dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose is already installed. Skipping..."
fi

# Check and install Git
install_if_missing "git" "git"

# Check and install Python3 and pip3
install_if_missing "python3" "python3 python3-pip"

# Ensure Python3 is correctly set as default if not already done
if ! command -v python &>/dev/null; then
    echo "Creating symlink for python -> python3..."
    sudo ln -sf "$(command -v python3)" /usr/bin/python
else
    echo "Python symlink already exists. Skipping..."
fi

# Ensure pip3 is installed and accessible
if ! command -v pip3 &>/dev/null; then
    echo "pip3 not found. Installing pip..."
    sudo python3 -m ensurepip --default-pip
    sudo python3 -m pip install --upgrade pip
fi

# Ensure pip is correctly linked to pip3
PIP_PATH=$(command -v pip3)
if [ -n "$PIP_PATH" ] && ! command -v pip &>/dev/null; then
    echo "Creating symlink for pip -> pip3..."
    sudo ln -sf "$PIP_PATH" /usr/bin/pip
else
    echo "pip symlink already exists. Skipping..."
fi

# Verify installations
echo "Final verification..."
python --version || echo "Error: Python symlink failed!"
pip --version || echo "Error: pip symlink failed!"

# Check and install Docker
if ! command -v docker &>/dev/null; then
    echo "Installing Docker..."
    sudo dnf install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ec2-user
else
    echo "Docker is already installed. Skipping..."
fi

# Verify Docker installation
docker --version || echo "Error: Docker installation failed!"

# Running a test Docker container
echo "Running a test Docker container..."
sudo docker run hello-world

# Create swap file if it doesn't exist
if ! swapon --show | grep -q '/swapfile'; then
    echo "Creating swap file..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab
else
    echo "Swap file already exists. Skipping..."
fi

# Set current directory
CURR_DIR=$(pwd)

# Read git.ini file
GIT_INI="$CURR_DIR/git.ini"
if [ ! -f "$GIT_INI" ]; then
    echo "Error: git.ini file not found."
    exit 1
fi

# Run Python scripts (Ensure they are only executed if they exist)
for script in gitini_ports_update.py update_configini_file.py 01_start.py; do
    if [ -f "$CURR_DIR/$script" ]; then
        echo "Running $script..."
        python "$CURR_DIR/$script"
    else
        echo "Warning: $script not found, skipping."
    fi
done

# Extract home_dir from git.ini
HOME_DIR=$(awk -F'=' '/^home_dir/{print $2}' "$GIT_INI" | tr -d ' ')
if [ -z "$HOME_DIR" ]; then
    echo "Error: home_dir not found in git.ini."
    exit 1
fi

# Ensure home_dir exists
if [ ! -d "$CURR_DIR/$HOME_DIR" ]; then
    echo "Error: Home directory $HOME_DIR not found."
    exit 1
fi

# Copy config.ini from CURR_DIR to HOME_DIR if it exists
if [ -f "$CURR_DIR/config.ini" ]; then
    cp -f "$CURR_DIR/config.ini" "$CURR_DIR/$HOME_DIR/"
else
    echo "Warning: config.ini not found in $CURR_DIR."
fi

# Apply permissions to home_dir/config and other required files
echo "Applying permissions..."
sudo chmod -R 777 "$CURR_DIR/$HOME_DIR/config" "$CURR_DIR/$HOME_DIR/Start"
sudo chmod 777 "$CURR_DIR/$HOME_DIR/config.ini"
sudo chmod 777 "$CURR_DIR/$HOME_DIR/docarize.sh"

# Run run_python.sh from 'instance' directory inside 'config'
if [ -d "$CURR_DIR/$HOME_DIR/config/instance" ]; then
    echo "Found 'instance' directory. Running run_python.sh..."
    cd "$CURR_DIR/$HOME_DIR/config/instance" || exit
    sudo ./run_python3.sh
else
    echo "Error: 'instance' directory not found in '$HOME_DIR/config'."
fi

# Run run_python2.sh from 'config' directory
echo "Running run_python2.sh..."
cd "$CURR_DIR/$HOME_DIR/config" || exit
sudo ./run_python2.sh

# Run docarize.sh if it exists
echo "Switching to home directory and running docarize.sh..."
cd "$CURR_DIR/$HOME_DIR" || exit
if [ -f "docarize.sh" ]; then
    sudo ./docarize.sh
else
    echo "Warning: docarize.sh not found."
fi

# Ensure 'docker' Python module is installed
echo "Checking for 'docker' Python module..."
if ! python3 -c "import docker" 2>/dev/null; then
    echo "'docker' module not found. Installing..."
    python3 -m pip install --upgrade pip
    python3 -m pip install 'urllib3<1.27,>=1.25.4' --upgrade
    python3 -m pip install --upgrade awscli
    python3 -m pip install docker
else
    echo "'docker' module is already installed."
fi

cd "$CURR_DIR" || exit

# Call docker_user_restart_lx.sh after ensuring the 'docker' module is installed
SCRIPT_PATH="$(pwd)/docker_user_restart_lx.sh"

if [ -f "$SCRIPT_PATH" ]; then
    echo "Executing docker_user_restart_lx.sh..."
    sudo chmod +x "$SCRIPT_PATH"  # Ensure script has execute permissions
	echo "Operating system is going to restart , so please run the get-results.py manually as it is first instance."
	sleep 15
    sudo "$SCRIPT_PATH"
else
    echo "Error: docker_user_restart_lx.sh not found!"
fi

echo "The Python script  get-results.py is automatically executed as it is not first instance."
sleep 15
# Run get_results.py to generate environment details
echo "Running get_results.py..."
if [ -f "get_results.py" ]; then
    python3 "get_results.py"
else
    echo "Warning: get_results.py not found."
fi

echo "The Python script  rebuild_images.py is automatically executed as it is not first instance."
sleep 15
# Run rebuild_images.py to generate environment details
echo "Running rebuild_images.py..."
if [ -f "rebuild_images.py" ]; then
    python3 "rebuild_images.py"
else
    echo "Warning: rebuild_images.py not found."
fi

echo "Script execution completed!"
