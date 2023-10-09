# Author: Muzaffer Citir, MSc RWTH Aachen University
# Contact: https://www.linkedin.com/in/muzaffercitir/
# Date created: 2023-10-09

# This script is used to classify images in the nuImages dataset into daytime and nighttime images 
# by using the hour information in the file names.

# The script will create a new directory named 'classified_<date_time>' in the same directory as the script.
# The classified images will be copied to this directory in two subdirectories named 'daytime' and 'nighttime', if COPY_TO_FULL is 'daynight'.
# The classified images will be copied to this directory in 24 subdirectories named '00', '01', ..., '23', if COPY_TO_FULL is 'timeslots'.

# The script will also create a subset directory named 'subset' in the same directory as the script.
# The classified images will be copied to this directory in two subdirectories named 'daytime' and 'nighttime'
# by predefined counts (IMAGE_SELECTION_COUNT_DAY and IMAGE_SELECTION_COUNT_NIGHT).

# The script will also create a report file named 'report.md' in the same directory.

import os
import sys
import random
import shutil
import datetime
from tqdm import tqdm
import argparse

# Get current date and time
now = datetime.datetime.now()
formatted_time = now.strftime("%Y%m%d_%H_%M_%S")

# SETTINGS
IMAGE_SELECTION_COUNT_DAY = 50       # Number of images to select from daytime hours in total
IMAGE_SELECTION_COUNT_NIGHT = 50     # Number of images to select from nighttime hours in total
COPY_TO_FULL = "daynight"            # options: "timeslots", "daynight", or None

# Define day and night hours
DAY_HOURS = list(range(6, 18))
NIGHT_HOURS = [i for i in range(24) if i not in DAY_HOURS]

# Parse arguments
parser = argparse.ArgumentParser(description='A day/night image classifier for classifying images in the nuImages dataset')
parser.add_argument('--source', type=str, default='dataset', help='The source directory of the dataset being classified')
args = parser.parse_args()

# Check if the source directory exists
if not os.path.exists(args.source) or not any([f.endswith(".jpg") or f.endswith(".png") for f in os.listdir(args.source)]):
    sys.exit(f"ERROR: '{args.source}' directory either doesn't exist or doesn't contain any images. Please provide a valid path using --source or place images in the default 'dataset' directory. Example: python classify_nuImages.py --source nuImages/samples/CAM_FRONT")

# Extract dataset source name (last folder name) from the source path
data_type = os.path.basename(os.path.normpath(args.source))

# Current working directory
cwd = os.getcwd()

script_directory = os.path.dirname(os.path.realpath(__file__))
print("Script directory: {0}".format(script_directory))

# Source directory
source_directory = os.path.join(script_directory, f"{args.source}")

# Destination directory
destination_directory = os.path.join(script_directory, f"classified_{formatted_time}")
destination_directory_training = os.path.join(destination_directory, "subset")
destination_directory_full = os.path.join(destination_directory, "full")

# Ensure destination directories exist
os.makedirs(os.path.join(destination_directory_training, "daytime"), exist_ok=True)
os.makedirs(os.path.join(destination_directory_training, "nighttime"), exist_ok=True)

# If COPY_TO_FULL is "timeslots" or "daynight"
if COPY_TO_FULL == "timeslots":
    os.makedirs(os.path.join(destination_directory_full, "timeslots"), exist_ok=True)
elif COPY_TO_FULL == "daynight":
    os.makedirs(os.path.join(destination_directory_full, "daytime"), exist_ok=True)
    os.makedirs(os.path.join(destination_directory_full, "nighttime"), exist_ok=True)

# List all files in the source directory
all_files = os.listdir(source_directory)

# Categorize files based on hour
files_dict = {}
for file_name in tqdm(all_files, desc="Categorizing files", unit="file"):
    hour = int(file_name.split('-')[4][:2])
    files_dict[hour] = files_dict.get(hour, []) + [file_name]

# Function to distribute files
def distribute_files(hours, total_files_required):
    # Determine the number of files in each hour
    counts = {hour: len(files_dict.get(hour, [])) for hour in hours}

    # If the total_files_required is greater than the total available, adjust it
    total_available_files = sum([count for count in counts.values()])
    if total_files_required > total_available_files:
        total_files_required = total_available_files
        print(f"Total files required is greater than the total available. Adjusted to {total_files_required}.")
    
    # Calculate the average files required per hour
    average_files = total_files_required // len(hours)

    # Select all from hours with less than average_files
    selected_files = []
    selection_count_per_hour = {}

    progress_bar = tqdm(hours, desc="Distributing files", unit="file")

    for hour, count in counts.items():
        if count <= average_files:
            selected_files.extend(files_dict.get(hour, []))
            selection_count_per_hour[hour] = count
            hours.remove(hour)
            total_files_required -= count
            progress_bar.update(count)

    # Distribute the remaining files among the remaining hours
    while total_files_required > 0 and hours:
        for hour in hours:
            if total_files_required <= 0:
                break
            available_files = [f for f in files_dict[hour] if f not in selected_files]
            if available_files:
                selected_files.append(random.choice(available_files))
                selection_count_per_hour[hour] = selection_count_per_hour.get(hour, 0) + 1
                total_files_required -= 1
                progress_bar.update(1)

    progress_bar.close()

    return selected_files, selection_count_per_hour

# Distribute day and night files
day_files, day_counts = distribute_files(DAY_HOURS, IMAGE_SELECTION_COUNT_DAY)
night_files, night_counts = distribute_files(NIGHT_HOURS, IMAGE_SELECTION_COUNT_NIGHT)

# Copy files
for file_name in tqdm(day_files, desc="Copying daytime files", unit="file"):
    shutil.copy2(os.path.join(source_directory, file_name), os.path.join(destination_directory_training, "daytime", file_name))

for file_name in tqdm(night_files, desc="Copying nighttime files", unit="file"):
    shutil.copy2(os.path.join(source_directory, file_name), os.path.join(destination_directory_training, "nighttime", file_name))

# Copy files to full directory
if COPY_TO_FULL == "timeslots":
    for hour in tqdm(files_dict.keys(), desc="Copying to timeslots"):
        hour_directory = os.path.join(destination_directory_full, "timeslots", str(hour))
        os.makedirs(hour_directory, exist_ok=True)
        for file_name in files_dict[hour]:
            shutil.copy2(os.path.join(source_directory, file_name), os.path.join(hour_directory, file_name))
            
elif COPY_TO_FULL == "daynight":
    for file_name in tqdm(all_files, desc="Copying to daytime/nighttime"):
        hour = int(file_name.split('-')[4][:2])
        if hour in DAY_HOURS:
            shutil.copy2(os.path.join(source_directory, file_name), os.path.join(destination_directory_full, "daytime", file_name))
        else:
            shutil.copy2(os.path.join(source_directory, file_name), os.path.join(destination_directory_full, "nighttime", file_name))
        
# Create a markdown formatted string for the report
report_content = "## Image Distribution Report\n\n"
report_content += f"**Selected Dataset:** {data_type}\n\n"
report_content += "### Daytime hours distribution:\n"

print("Daytime hours distribution:")
total_daytime_selected = 0
for hour in sorted(day_counts.keys()):
    selected_count = day_counts.get(hour, 0)
    total_daytime_selected += selected_count
    print(f"Time slot {hour}:00: {selected_count}/{len(files_dict.get(hour, []))} images selected.")
    report_content += f"- Time slot {hour}:00: {selected_count}/{len(files_dict.get(hour, []))} images selected.\n"

total_daytime_images = sum([len(files_dict.get(hour, [])) for hour in DAY_HOURS])
print(f"Daytime total: {total_daytime_selected}/{total_daytime_images} images selected.")
report_content += f"\n**Daytime total:** {total_daytime_selected}/{total_daytime_images} images selected.\n\n"

report_content += "### Nighttime hours distribution:\n"
print("Nighttime hours distribution:")
total_nighttime_selected = 0
for hour in sorted(night_counts.keys()):
    selected_count = night_counts.get(hour, 0)
    total_nighttime_selected += selected_count
    print(f"Time slot {hour}:00: {selected_count}/{len(files_dict.get(hour, []))} images selected.")
    report_content += f"- Time slot {hour}:00: {selected_count}/{len(files_dict.get(hour, []))} images selected.\n"


total_nighttime_images = sum([len(files_dict.get(hour, [])) for hour in NIGHT_HOURS])
print(f"Nighttime total: {total_nighttime_selected}/{total_nighttime_images} images selected.")
if COPY_TO_FULL == "timeslots" or COPY_TO_FULL == "daynight":
    print(f"Total images in dataset '{data_type}' is {len(all_files)}: The copied images are grouped by {COPY_TO_FULL}.")
else:
    print(f"Total images in dataset '{data_type}' is {len(all_files)}")
report_content += f"\n**Nighttime total:** {total_nighttime_selected}/{total_nighttime_images} images selected.\n"
if COPY_TO_FULL == "timeslots" or COPY_TO_FULL == "daynight":
    report_content += f"\n**Total images in dataset '{data_type}' is {len(all_files)}:** The copied images are grouped by {COPY_TO_FULL}.  \n"
else:
    report_content += f"\n**Total images in dataset '{data_type}' is {len(all_files)}**  \n"
report_content += f"**Report Generation Date and Time:** {formatted_time}\n\n"

# Write the report to a .md file
with open(os.path.join(destination_directory, "report.md"), "w") as file:
    file.write(report_content)