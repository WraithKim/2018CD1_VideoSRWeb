import sys
import os.path
import sys
import os
import subprocess

TMP_FOLDER = "./tmp"

def _video_to_frame( lr_video_path):
    tmp_fps = subprocess.check_output("ffprobe -v 0 -of csv=p=0 -select_streams 0 -show_entries stream=r_frame_rate " + str(lr_video_path),shell=True)
    videocmd = "ffmpeg -r "+ tmp_fps.decode('ascii').strip('\n') +" -i " + str(lr_video_path) + " -q:v 1 " + str(TMP_FOLDER) + "/" + str(lr_video_path) + "/%10d.png"
    audiocmd = "ffmpeg -y -i " + str(lr_video_path) + " -vn -ar 44100 -ac 2 -q:a 0 -ab 192k -f mp3 " + str(TMP_FOLDER) + "/" + str(lr_video_path) + "/output_audio.mp3"
    if not os.path.exists(str(TMP_FOLDER) + "/" + str(lr_video_path)):
        os.mkdir(str(TMP_FOLDER) + "/" + str(lr_video_path))
    os.system(videocmd)
    os.system(audiocmd)
    return tmp_fps

def _frame_to_video(fps,lr_video_path,sr_video_path=None):
    videocmd = "ffmpeg -f image2 -r "+ str(fps.decode('ascii').strip('\n')) + " -pattern_type sequence -i " + str(lr_video_path)+"\"%10d.png\"" + " -i "+  str(lr_video_path)+"/output_audio.mp3" + " -q:v 1 -vcodec libx264 -pix_fmt yuv420p " + str(sr_video_path)
    print(videocmd)
    os.system(videocmd)


lr = input("asdf: ")

fps=_video_to_frame(lr)
_frame_to_video(fps,"./tmp/"+str(lr)+"/","./asdfqwer.mp4")
