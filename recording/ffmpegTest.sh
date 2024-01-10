#ffmpeg -f avfoundation -list_devices true -i ""

#ffmpeg -f avfoundation -i "FaceTime" -framerate 30 -r 30 out.mp4

#ffmpeg -framerate 59.940180 -f avfoundation -i "FaceTime" -r 30 output.mkv

#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 output.mov
#ffmpeg -f avfoundation -i ":USB" -aq 0 output.mp3
#ffplay -framerate 30.0 -f avfoundation -i "Canon" &

#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -f matroska - | ffplay -

#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -f matroska pipe:1

#ffplay -vf "drawtext=fontfile=/path/to/font.ttf:text='%{eif\:t*60\:d}'" output.movo
#ffmpeg -i output.mov -f matroska - | ffplay -

#ffmpeg -framerate 30 -f avfoundation -i "Canon" -r 30 -c:v copy -filter:v output.mkv
#
#ffmpeg -i output.mov -filter_complex 'split=2[out1][out2]' -map '[out1]' test1.mov -map '[out2]' test2.mov
#ffmpeg -i output.mov -filter_complex 'split=2[out1][out2]' -map '[out1]' test1.mov -map '[out2]' -f avi - | ffplay -
#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' test1.mkv -map '[out2]' test2.mkv
#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y test1.mov -map '[out2]' -s 1280x720 -f avi - | ffplay -vf "drawtext=fontfile=/path/to/font.ttf:text='%{eif\:t*60\:d}'" -
#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y test1.mov -map '[out2]' -s 1280x720 -f avi pipe: | ffplay -vf "drawtext=fontfile=/path/to/font.ttf:text='%{eif\:t*60\:d}'" pipe:
#ffmpeg -i recording.mov -filter_complex 'split=2[out1][out2]' -map '[out1]' -y test1.mov -map '[out2]' -s 1280x720 -f avi pipe: | ffplay -vf "drawtext=fontfile=/path/to/font.ttf:text='%{eif\:t*60\:d}'" pipe:

#ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y test1.mov -map '[out2]' -s 1280x720 -f avi pipe: | ffplay -vf "drawtext=text='%{eif\:t*60\:d}'" -framedrop -fflags nobuffer -flags low_delay pipe:
ffmpeg -framerate 30.0 -f avfoundation -i "Canon" -video_size 1920x1080 -r 30 -filter_complex 'split=2[out1][out2]' -map '[out1]' -y test1.mov -map '[out2]' -s 1280x720 -f avi pipe: | ffplay -vf "drawtext=text='%{pts\:gmtime\:0\:%M\\\\\:%S}    %{eif\:t*60\:d}':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.5:boxborderw=5" -framedrop -fflags nobuffer -flags low_delay pipe:

