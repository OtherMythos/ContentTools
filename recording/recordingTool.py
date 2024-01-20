#!/usr/bin/python3

import argparse
from pathlib import Path
import subprocess
import os
import signal
import sys
import time
from datetime import datetime

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

def openWebcamRecording(deviceName, outPath, width, left, top):
    #NOTE I think the video is being encoded twice with this technique, once for the viewer and another for the save
    ffmpegCommand = """ffmpeg -framerate 30.0 -f avfoundation -i "%s" """ % deviceName
    #ffmpegCommand = """ffmpeg -framerate 30.0 -f avfoundation -i "%s" -video_size 1920x1080 -r 30 -c:v h264_videotoolbox %s""" % (deviceName, outPath)
    ffmpegCommand += """-video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y -c:v h264_videotoolbox %s -map '[out2]' -s 1280x720 -f avi pipe:""" % outPath
    ffmpegCommand += " | "
    ffmpegCommand += """ffplay -vf \"drawtext=text=\'%{pts\\:gmtime\\:0\\:%M\\\\\\\\\\:%S}    %{eif\:t*60\:d}\':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5\" """
    ffmpegCommand += """ -x %i -left %i -top %i """ % (width, left, top)
    ffmpegCommand += """-framedrop -fflags nobuffer -flags low_delay pipe:"""
    return subprocess.Popen(ffmpegCommand, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, shell=True)

def openAudioRecording(outPath):
    soxCommand = """rec %s""" % outPath
    return subprocess.Popen(soxCommand, shell=True)

def getFileNames():
    return ["camera", "desktop", "audio"]
def getFileEndings():
    return [".mov", ".mov", ".mp3"]
def getOutDirNames(outDir):
    names = getFileNames()
    endings = getFileEndings()
    outPaths = []
    for i in range(len(names)):
        targetPath = outDir / (Path(names[i] + "-current").with_suffix(endings[i]))
        outPaths.append(targetPath)
    return outPaths
def getDateTimestamp():
    dateTime = datetime.now()
    return dateTime.strftime("%Y-%m-%d-%H-%M-%S")
def getOutDirCommitNames(outDir):
    names = getFileNames()
    endings = getFileEndings()
    outPaths = []
    for i in range(len(names)):
        targetPath = outDir / (names[i] + "-" + getDateTimestamp() + endings[i])
        outPaths.append(targetPath)
    return outPaths

def prepareAudioDirectory(outDir):
    targetPath = outDir / ("audioRecording-" + getDateTimestamp() + ".mp3")
    if targetPath.exists():
        if targetPath.is_file():
            targetPath.unlink()
    return targetPath

def prepareOutputDirectory(outDir):
    outPaths = []
    paths = getOutDirNames(outDir)
    for i in paths:
        if(i.exists()):
            print("Path '%s' already exists" % str(i))
            sys.exit(1)
        outPaths.append(i)
    return outPaths

def commitOutputDirectory(outDir):
    paths = getOutDirNames(outDir)
    for i in paths:
        if(not i.exists()):
            print("Missing path '%s' in the output directory" % str(i))
            sys.exit(1)
    commitPaths = getOutDirCommitNames(outDir)
    for i in commitPaths:
        if(i.exists()):
            print("Commit path name '%s' already exists." % str(i))
            sys.exit(1)

    for i in range(len(paths)):
        print("Renaming file '%s' to '%s'" % (paths[i], commitPaths[i]))
        paths[i].rename(commitPaths[i])

def main():
    helpText = '''A tool to help automate recording of camera and desktop setups for YouTube videos.'''

    parser = argparse.ArgumentParser(description = helpText)

    parser.add_argument('outputDirectory', metavar='I', type=str, nargs='?', help='Path to the directory to write the video to')
    parser.add_argument('--commit', help="Commit the current batch of videos to allow for another recording", action='store_true')
    parser.add_argument('--audio', help="Record only the audio input", action='store_true')

    args = parser.parse_args()

    targetPath = args.outputDirectory
    if(targetPath is None):
        print("Please provide an output directory")
        return

    outPath = Path(targetPath)
    if not outPath.exists():
        print("Output path does not exist", file=sys.stderr)
    if not outPath.is_dir():
        print("Output path is not a directory", file=sys.stderr)

    if(args.commit):
        commitOutputDirectory(outPath)
        return

    width = 1920/2

    processes = []
    if(args.audio):
        outPath = prepareAudioDirectory(outPath)
        processes = [
            openAudioRecording(outPath)
        ]
    else:
        outPaths = prepareOutputDirectory(outPath)
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
