import os.path
import os
import glob
import subprocess
import cv2
import numpy as np
import ntpath
import torch
import architecture as arch

TMP_FOLDER = "./tmp"


class Infmodule_ESRGAN:
    def __init__(self,model_path,upscale_factor=4,is_RGB=True,is_CUDA=True):

        self.upscale_factor = upscale_factor
        self.model_path = model_path
        self.model = arch.RRDB_Net(3, 3, 64, 23, gc=32, upscale=4, norm_type=None, act_type='leakyrelu', \
                              mode='CNA', res_scale=1, upsample_mode='upconv')
        self.model.load_state_dict(torch.load(model_path), strict=True)
        self.model.eval()
        if is_CUDA and torch.cuda.is_available():
            self.device = torch.device('cuda')
        else:
            self.device = torch.device('cpu')

        for k, v in self.model.named_parameters():
            v.requires_grad = False
        self.model = self.model.to(self.device)
        print('Model path {:s}. \nTesting...'.format(model_path))

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


    def _inference_video(self,lr_video_path):

        print('------Model name : %s-----'.format(self.model_path))
        idx = 0
        print(lr_video_path)
        if not os.path.exists(str(lr_video_path) + "/result"):
            os.mkdir(str(lr_video_path) + "/result")
        for path in glob.glob(lr_video_path+"/*"):
            print(path)
            idx += 1
            base = os.path.splitext(os.path.basename(path))[0]
            print(idx, base)
            # read image
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            img = img * 1.0 / 255
            img = torch.from_numpy(np.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))).float()
            img_LR = img.unsqueeze(0)
            img_LR = img_LR.to(self.device)

            output = self.model(img_LR).data.squeeze().float().cpu().clamp_(0, 1).numpy()
            output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))
            output = (output * 255.0).round()
            cv2.imwrite(str(TMP_FOLDER) + "/" + str(lr_video_path)+"/result"+'{:s}.png'.format(base), output)
            #print(str(lr_video_path)+"/result/"+'{:s}.png'.format(base))
            #cv2.imwrite(str(lr_video_path)+"/result/"+'{:s}.png'.format(base), img)


    def sr_video(self,lr_video_path,sr_video_path):
        fps = self._video_to_frame(lr_video_path)
        fn = ntpath.basename(lr_video_path)
        self._inference_video("./tmp/" + fn )
        self._frame_to_video(fps=fps,lr_video_path= "./tmp/" + fn + "/result/", sr_video_path="./output_videos/" +"sr_"+ fn)

if __name__ == '__main__':
    srm = Infmodule_ESRGAN(model_path="./model/RRDB_PSNR_x4.pth", is_CUDA=False)
    lr = input("asdf: ")
    print("base filename : "+ ntpath.basename(lr))
    srm.sr_video(lr,"./asdf.mp4")