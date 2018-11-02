import os.path
import os
import glob
import subprocess
import cv2
import ntpath
import numpy as np
import os
import time
import os.path as osp
import prosr
import skimage.io as io
import torch
import sys
import shutil

from pprint import pprint
from prosr import Phase
from prosr.data import DataLoader, Dataset
from prosr.logger import info
from prosr.metrics import eval_psnr_and_ssim
from prosr.utils import (get_filenames, IMG_EXTENSIONS, print_evaluation,
                         tensor2im)


TMP_FOLDER = "./tmp"


class Infmodule_proSR:
    def __init__(self,model_path,upscale_factor=4,is_RGB=True,is_CUDA=True):

        self.upscale_factor = upscale_factor
        self.is_CUDA = is_CUDA
        if is_CUDA:
            checkpoint = torch.load(model_path)
        else:
            checkpoint = torch.load(model_path, map_location=lambda storage, loc: storage)


        cls_model = getattr(prosr.models, checkpoint['class_name'])

        self.model = cls_model(**checkpoint['params']['G'])
        self.model.load_state_dict(checkpoint['state_dict'])

        info('phase: {}'.format(Phase.TEST))
        info('checkpoint: {}'.format(osp.basename(model_path)))

        self.params = checkpoint['params']
        pprint(self.params)

        self.model.eval()

        if torch.cuda.is_available() and is_CUDA:
            self.model = self.model.cuda()

    def _infvideo_fake(self,lr_video_path,sr_video_path):
        print("lr : "+lr_video_path)
        print("lr : "+sr_video_path)
        os.system("cp -r "+lr_video_path+" "+ sr_video_path)


    def _video_to_frame(self,lr_video_path):
        tmp_fps = subprocess.check_output(
            "ffprobe -v 0 -of csv=p=0 -select_streams 0 -show_entries stream=r_frame_rate " + str(lr_video_path),
            shell=True)
        fn = ntpath.basename(lr_video_path)
        videocmd = "ffmpeg -r " + tmp_fps.decode('ascii').strip('\n') + " -i " + str(lr_video_path) + " -q:v 1 " + str(
            TMP_FOLDER) + "/" + fn + "/%10d.png"
        audiocmd = "ffmpeg -y -i " + str(lr_video_path) + " -vn -ar 44100 -ac 2 -q:a 0 -ab 192k -f mp3 " + str(
            TMP_FOLDER) + "/" + fn + "/output_audio.mp3"
        if not os.path.exists(str(TMP_FOLDER) + "/" + fn):
            os.mkdir(str(TMP_FOLDER) + "/" + fn)
        os.system(videocmd)
        os.system(audiocmd)
        return tmp_fps

    def _frame_to_video(self,fps, lr_video_path, sr_video_path=None):
        fn = ntpath.basename(lr_video_path)
        videocmd = "ffmpeg -f image2 -r " + str(fps.decode('ascii').strip('\n')) + " -pattern_type sequence -i " + str(
            lr_video_path) + "\"%10d.png\"" + " -i " + str(
            lr_video_path) + "../output_audio.mp3" + " -q:v 1 -vcodec libx264 -pix_fmt yuv420p " + str(sr_video_path)

        print(videocmd)
        os.system(videocmd)

    def _frame_to_video_woaudio(self,fps, lr_video_path, sr_video_path=None):
        fn = ntpath.basename(lr_video_path)
        videocmd = "ffmpeg -f image2 -r " + str(fps.decode('ascii').strip('\n')) + " -pattern_type sequence -i " + str(
            lr_video_path) + "\"%10d.png\"" +  " -q:v 1 -vcodec libx264 -pix_fmt yuv420p " + str(sr_video_path)

        print(videocmd)
        os.system(videocmd)

    def _inference_video(self,lr_video_path,sr_video_path):
        print("lr : "+lr_video_path)
        print("lr : "+sr_video_path)


        # TODO Change
        dataset = Dataset(
            Phase.TEST,
            get_filenames(lr_video_path, IMG_EXTENSIONS),
            [],
            self.upscale_factor,
            input_size=None,
            mean=self.params['train']['dataset']['mean'],
            stddev=self.params['train']['dataset']['stddev'],
            downscale=False)

        data_loader = DataLoader(dataset, batch_size=1)

        mean = self.params['train']['dataset']['mean']
        stddev = self.params['train']['dataset']['stddev']


        if not osp.isdir(sr_video_path):
            os.makedirs(sr_video_path)
        info('Saving images in: {}'.format(sr_video_path))

        with torch.no_grad():

            for iid, data in enumerate(data_loader):
                tic = time.time()
                input = data['input']
                if self.is_CUDA:
                    input = input.cuda()
                output = self.model(input, self.upscale_factor).cpu() + data['bicubic']
                sr_img = tensor2im(output, mean, stddev)
                toc = time.time()
                if 'target' in data:
                    hr_img = tensor2im(data['target'], mean, stddev)
                    psnr_val, ssim_val = eval_psnr_and_ssim(
                        sr_img, hr_img, self.upscale_factor)
                    print_evaluation(
                        osp.basename(data['input_fn'][0]), psnr_val, ssim_val,
                        iid + 1, len(dataset), toc - tic)

                else:
                    print_evaluation(
                        osp.basename(data['input_fn'][0]), np.nan, np.nan, iid + 1,
                        len(dataset), toc - tic)

                fn = osp.join(sr_video_path, osp.basename(data['input_fn'][0]))
                io.imsave(fn, sr_img)


    def sr_video(self,lr_video_path,sr_video_path):
        fps = self._video_to_frame(lr_video_path)
        fn = ntpath.basename(lr_video_path)
        self._inference_video("./tmp/" + fn , "./tmp/srtmp_"+fn + "/")
        #self._frame_to_video(fps=fps,lr_video_path= "./tmp/" +"srtmp_"+ fn + "/", sr_video_path=sr_video_path +"sr_"+ fn)

        self._frame_to_video_woaudio(fps=fps,lr_video_path= "./tmp/" +"srtmp_"+ fn + "/", sr_video_path=sr_video_path +"sr_"+ fn)
        shutil.rmtree("./tmp/" + fn,ignore_errors=True)
        shutil.rmtree("./tmp/srtmp_"+fn,ignore_errors=True )

    def sr_video_nosr(self,lr_video_path,sr_video_path):
        fps = self._video_to_frame(lr_video_path)
        fn = ntpath.basename(lr_video_path)
        self._infvideo_fake("./tmp/" + fn , "./tmp/srtmp_"+fn + "/")
        self._frame_to_video_woaudio(fps=fps,lr_video_path= "./tmp/" +"srtmp_"+ fn + "/", sr_video_path=sr_video_path +"sr_"+ fn)
        shutil.rmtree("./tmp/" + fn,ignore_errors=True)
        shutil.rmtree("./tmp/srtmp_"+fn,ignore_errors=True )

if __name__ == '__main__':
    srm2 = Infmodule_proSR(model_path="./model/proSRs.pth", is_CUDA=False,upscale_factor=2) #cuda -> is_CUDA=True upscale x2
    srm4 = Infmodule_proSR(model_path="./model/proSRs.pth", is_CUDA=False,upscale_factor=4) #cuda -> is_CUDA=True upscale x4

    lr = input("asdf: ")
    print("base filename : "+ ntpath.basename(lr))
    # srm2.sr_video(lr,"./output/") # upscale x2
    srm4.sr_video(lr,"./output/") # upcale x4
    #srm.sr_video(lr,"./output/") # uncomment if you use sr
