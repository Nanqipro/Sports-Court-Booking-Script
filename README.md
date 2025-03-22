# NCU Sports Court Booking Automation Script

[中文文档](README_CN.md) | English Document

This is a collection of Python scripts for automatic badminton court booking, specifically designed for the Nanchang University sports facility reservation system. The scripts provide various booking modes and features to meet booking needs in different scenarios.

## Features

- **Automatic Login** 🔑: Automatically login to the sports court reservation system using student ID and password
- **CAPTCHA Recognition** 👁️: Automatically identify and process the system's CAPTCHA
- **Scheduled Booking** ⏰: Support triggering the booking process at a specified time (e.g., 12:00 noon)
- **Interactive Booking** 💬: Provide a user interaction interface for customizing booking times, courts, and trigger conditions
- **Error Retry** 🔄: Built-in error handling and retry mechanisms to increase booking success rates
- **Batch Booking** 📋: Support booking multiple courts and time slots simultaneously through the script
- **Flexible Configuration** ⚙️: Support setting account information via configuration files or environment variables

## Dependencies Installation 🛠️

### Creating a Virtual Environment 🐍

It is strongly recommended to run this project in a virtual environment to avoid dependency conflicts:

```bash
# Install virtualenv (if not already installed)
pip install virtualenv

# Create a virtual environment
cd d:\GitHub_local\Sports-Court-Booking-Script
virtualenv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# Linux/MacOS:
# source venv/bin/activate
```

### Installing Required Packages 📦

In the activated virtual environment, use the following commands to install the required Python libraries:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## Scripts Description 📃

This project contains multiple script files suitable for different scenarios:

- **badminton_multi_you_need.py** 🌟: The most comprehensive script for multi-court and multi-time slot booking, supporting configuration files, interactive interface, and scheduled booking
- **badminton_all_you_need** 🔹: Suitable for single court and single time slot booking, supporting configuration files, interactive interface, and scheduled booking

## Usage Guide 🚀

### 1. Configuration Methods ⚙️

badminton_multi_you_need.py supports two configuration methods:

- **Environment Variables**: Set the BADMINTON_USERNAME and BADMINTON_PASSWORD environment variables
- **Configuration File**: Create a config.ini file in the same directory with the following content:
  ```ini
  [CONFIG]
  BADMINTON_USERNAME=your_student_id
  BADMINTON_PASSWORD=your_password
  DEBUG=True
  ```

If not configured, the script will prompt for input during runtime.

### 2. Script Usage Methods (Two Ways) 🔧

#### Method One: Execute Python Script 💻

1. Navigate to the project folder:
   ```bash
   cd d:\GitHub_local\Sports-Court-Booking-Script\badminton
   ```

2. Run the script:
   ```bash
   python badminton_multi_you_need.py
   ```

#### Method Two: Use the Packaged Executable 📦

1. Executable file location:
   ```
   d:\GitHub_local\Sports-Court-Booking-Script\badminton\dist\badminton_multi_you_need\badminton_multi_you_need.exe
   ```

2. Double-click to run, or execute in command line:
   ```bash
   cd d:\GitHub_local\Sports-Court-Booking-Script\badminton\dist\badminton_multi_you_need
   badminton_multi_you_need.exe
   ```

### 3. Interactive Configuration ⌨️

After running the script, follow the prompts to operate:

1. **Enter Student ID and Password**: Press Enter to use default values or values from the configuration file
2. **Select Booking Date**: Format YYYY-MM-DD, press Enter to book for the day after tomorrow by default
3. **Select Time Slots**: Enter time slot numbers (e.g., 1,2,3), multiple time slots separated by commas
   - Available time slots include: 08:00-09:00, 09:00-10:00, ..., 21:00-22:00
4. **Select Courts**: Enter court numbers (e.g., 1,2,3), multiple courts separated by commas
   - Available court numbers are 1-12, corresponding to badminton courts 1-12
5. **Set Booking Trigger Time**: Enter the target time to start booking (24-hour format, e.g., 12:00)
   - The system will start executing booking tasks at the specified time

### 4. Booking Process 🔄

1. The script will wait until the set trigger time is reached ⏳
2. Automatically login to the system and obtain a Token 🔐
3. Automatically recognize CAPTCHA 🧩
4. Try to book all selected courts and time slots in sequence 📋
5. Automatically retry when errors occur, with a maximum of 5 attempts per booking task 🔁
6. Successfully booked tasks will be removed from the queue ✅
7. Finally output booking result statistics 📊

### 5. Notes ⚠️

- There will be a brief wait after each booking attempt to avoid too frequent requests
- The Token will be refreshed automatically every 5 attempts
- The script will automatically clean up generated temporary files (such as CAPTCHA images)
- The program will automatically exit after successful booking or reaching the maximum number of attempts

## Using Other Scripts 📝

### 1. Basic Configuration

Other scripts require modifying the username and password in the script:

```python
# Replace username and password with your own student ID and password
username = "your_student_id"
password = "your_password"
```

### 2. Booking Information Configuration

Modify booking court, time, and other information as needed:

```python
date = "2025-03-20"           # Booking date
startTime = "19:00-20:00"     # Booking time slot
areaName = "Badminton Court No.1"     # Court name
areaNickname = "hall1"        # Court code
```

## Troubleshooting 🔍

1. CAPTCHA recognition failure: Check if the ddddocr library is correctly installed 🖼️
2. Login failure: Confirm that the account and password are correct, check network connection 🔒
3. Booking failure: Check if the date and time are valid, whether the court is already booked 📅
4. Other errors: View log output and adjust according to error messages 📋

## Disclaimer ⚖️

This script is for learning and personal use only. Please comply with relevant regulations and ethical guidelines. The developer is not responsible for any issues caused by using this script.
