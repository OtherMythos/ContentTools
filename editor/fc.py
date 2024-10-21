import os
import subprocess
import sys

# Usage: python generate_fcpxml.py /path/to/input/directory /path/to/output/directory
# Mostly generated using ChatGPT so looks a bit weird.
input_dir = sys.argv[1]
output_dir = sys.argv[2]
output_file = os.path.join(output_dir, "output.fcpxml")

# FCPXML header template
fcpxml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
'''

# FCPXML footer template
fcpxml_footer = '''  </resources>
  <library>
    <event name="Auto Generated Event">
      <project name="Auto Generated Project">
        <sequence format="r1" tcStart="0s">
          <spine>
'''

fcpxml_footer_end = '''          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>'''

# Function to get the duration of a file using ffmpeg
def get_duration(filepath):
    """Returns the duration of the file in seconds."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", filepath],
            stderr=subprocess.PIPE,
            text=True
        )
        for line in result.stderr.splitlines():
            if "Duration" in line:
                duration_str = line.split(" ")[3].strip(",")
                h, m, s = map(float, duration_str.split(":"))
                return h * 3600 + m * 60 + s
    except Exception as e:
        print(f"Error getting duration for {filepath}: {e}")
        return 0

# Get and sort files
files = sorted(os.listdir(input_dir))

# Initialize variables
resources = ""
timeline = ""
id_counter = 1
offset = 0

#Used for camera
resources += f'<format id="r1" name="FFVideoFormat1080p30" frameDuration="100/3000s" width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>'
#Used for desktop
resources += f'<format id="r2" name="FFVideoFormat3840x2160p30" frameDuration="100/3000s" width="3840" height="2160" colorSpace="1-1-1 (Rec. 709)"/>'

id_counter = 3

entries = []

desktopIdx = 0
cameraIdx = 0

# Generate resources and timeline sections
for file in files:
    # Get file extension and file path
    extension = file.split(".")[-1]
    filepath = os.path.join(input_dir, file)

    formatDef = ""
    # Determine file type
    if "audio" in file:
        role = "audio"
        formatDef = ""
    elif "desktop" in file:
        role = "desktop"
        formatDef = "r2"
        desktopIdx += 1
    elif "camera" in file:
        role = "camera"
        formatDef = "r1"
        cameraIdx += 1
    else:
        continue

    # Generate resource section
    if role == "audio":
        resources += f'    <asset id="r{id_counter}" name="{file}" start="0s" duration="10s" hasVideo="1" hasAudio="1">  <media-rep src="file://{filepath}" kind="original-media"/> </asset>\n'
    else:
        resources += f'    <asset id="r{id_counter}" name="{file}" format="{formatDef}" start="0s" duration="10s" hasVideo="1" hasAudio="1">  <media-rep src="file://{filepath}" kind="original-media"/> </asset>\n'

    # Set the correct offset for each clip
    offset_str = f"{offset:.2f}"

    # Get the duration of the audio file (since all files are assumed to have the same duration)
    if role == "audio":
        duration = get_duration(filepath)
        timelineStr = f'            <audio lane="0" offset="{offset_str}s" ref="r{id_counter}" role="{role}" duration="{duration:.2f}s">\n'
        entries.append([duration, offset_str, timelineStr])
    else:
        laneIdx = 1 if role == 'desktop' else 2
        e = None
        if role == "camera":
            e = entries[cameraIdx-1]
        elif role == "desktop":
            e = entries[desktopIdx-1]
        d = e[0]
        o = e[1]

        if role == "camera":
            e = entries[cameraIdx-1]
            e[2] += f'                <video lane="{laneIdx}" offset="0.0s" ref="r{id_counter}" role="{role}" duration="{d:.2f}s">\n'
            e[2] += f'                    <adjust-crop mode="trim">\n'
            e[2] += f'                        <trim-rect left="8.50482" top="8.01543"/>\n'
            e[2] += f'                    </adjust-crop>\n'
            e[2] += f'                    <adjust-transform position="55.9274 -30.3617" scale="0.418302 0.418302"/>\n'
            e[2] += f'                </video>\n'
        elif role == "desktop":
            e = entries[desktopIdx-1]
            e[2] += f'                <video lane="{laneIdx}" offset="0.0s" ref="r{id_counter}" role="{role}" duration="{d:.2f}s" />\n'

    id_counter += 1
    # Increment the offset for the next clip based on the duration of the current clip
    offset += duration

for i in entries:
    i[2] += "            </audio>\n"
    timeline += i[2]

# Generate the final FCPXML content
fcpxml_content = f"{fcpxml_header}{resources}{fcpxml_footer}{timeline}{fcpxml_footer_end}"

# Write the FCPXML content to the output file
with open(output_file, "w") as f:
    f.write(fcpxml_content)

print(f"FCPXML generated at: {output_file}")
