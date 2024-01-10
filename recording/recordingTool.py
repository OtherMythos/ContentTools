#!/usr/bin/python3

import argparse
from pathlib import Path
import subprocess
import os
import signal
import sys
import time

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

def openWebcamRecording(deviceName, outPath, width, left, top):
    #NOTE I think the video is being encoded twice with this technique, once for the viewer and another for the save
    ffmpegCommand = """ffmpeg -framerate 30.0 -f avfoundation -i "%s" """ % deviceName
    ffmpegCommand += """-video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y %s -map '[out2]' -s 1280x720 -f avi pipe:""" % outPath
    ffmpegCommand += " | "
    ffmpegCommand += """ffplay -vf \"drawtext=text=\'%{pts\\:gmtime\\:0\\:%M\\\\\\\\\\:%S}    %{eif\:t*60\:d}\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5\" """
    ffmpegCommand += """ -x %i -left %i -top %i """ % (width, left, top)
    ffmpegCommand += """-framedrop -fflags nobuffer -flags low_delay pipe:"""
    return subprocess.Popen(ffmpegCommand, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)

def openAudioRecording(outPath):
    soxCommand = """rec %s""" % outPath
    return subprocess.Popen(soxCommand, shell=True)

def prepareOutputDirectory(outDir):
    names = ["camera", "desktop", "audio"]
    endings = [".mov", ".mov", ".mp3"]
    outPaths = []
    for i in range(len(names)):
        targetPath = outDir / (Path(names[i] + "-current").with_suffix(endings[i]))
        if(targetPath.exists()):
            print("Path '%s' already exists" % str(targetPath))
            sys.exit(1)
        outPaths.append(targetPath)

    return outPaths

def main():
    helpText = '''A tool to help automate recording of camera and desktop setups for YouTube videos.'''

    parser = argparse.ArgumentParser(description = helpText)

    parser.add_argument('outputDirectory', metavar='I', type=str, nargs='?', help='Path to the directory to write the video to')

    args = parser.parse_args()

    targetPath = args.outputDirectory
    if(targetPath is None):
        print("Please provide an output directory")
        return

    #devnull = open(os.devnull, 'w')
    #command = """ffmpeg -framerate 30.0 -f avfoundation -i Canon -video_size 1920x1080 -r 30 -filter_complex split=2[out1][out2] -map [out1] -y test1.mov -map [out2] -s 1280x720 -f avi pipe:"""
    #ffplayCommand = """ffplay -vf -fflags nobuffer -flags low_delay pipe:"""
    ##command = """ffmpeg -f avfoundation -list_devices true -i \"\" """
    #print(command.split())
    #process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, cwd=str(targetPath))
    #p2 = subprocess.Popen(ffplayCommand.split(), stdin=process.stdout)
    #process.stdout.close()

    ##process.wait()

    #signal.signal(signal.SIGINT, signal_handler)
    #print('Press Ctrl+C')
    #signal.pause()

    #devnull.close()

    outPath = Path(targetPath)
    if not outPath.exists():
        print("Output path does not exist", file=sys.stderr)
    if not outPath.is_dir():
        print("Output path is not a directory", file=sys.stderr)

    outPaths = prepareOutputDirectory(outPath)

    width = 1920/2
    processes = [
        openWebcamRecording("Canon", outPaths[0], width, 0, 0),
        openWebcamRecording("Elgato", outPaths[1], width, width, 0),
        openAudioRecording(outPaths[2])
    ]

    signal.signal(signal.SIGINT, signal_handler)
    #while p1.poll() is None and p2.poll() is None:
    #while [x for x in process if x.poll() is None] is None:
    #    time.sleep(0.05)
    #while True:
    #    valid = True
    #    for i in process:
    #        if i.poll() is None:
    #            continue
    #        valid = False
    #        print("valid")
    #    if valid == False:
    #        sys.exit(0)

if __name__ == "__main__":
    main()
