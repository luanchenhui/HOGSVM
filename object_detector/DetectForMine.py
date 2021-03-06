import numpy as np 
from skimage.transform import pyramid_gaussian
from imutils.object_detection import non_max_suppression
import imutils
from sklearn.externals import joblib
import cv2
from config import *
from skimage import color
import matplotlib.pyplot as plt 
import os 
import glob
from PIL import Image

hog = cv2.HOGDescriptor(win_size,block_size,block_stride,cell_size,num_bins)

def sliding_window(image, window_size, step_size):
	'''
	This function returns a patch of the input 'image' of size 
	equal to 'window_size'. The first image returned top-left 
	co-ordinate (0, 0) and are increment in both x and y directions
	by the 'step_size' supplied.

	So, the input parameters are-
	image - Input image
	window_size - Size of Sliding Window 
	step_size - incremented Size of Window

	The function returns a tuple -
	(x, y, im_window)
	'''
	for y in range(0, image.shape[0], step_size[1]):
		for x in range(0, image.shape[1], step_size[0]):
			yield (x, y, image[y: y + window_size[1], x: x + window_size[0],:])

def detector(filename):
	im = cv2.imread(filename)
	if filename.split('.')[-1]=='png':
		os.rename(filename,'test_image/area_'+filename.split('_')[-1])		   #这里是因为原始图片中有些是中文文件名，
		im = cv2.imread('test_image/area_'+filename.split('_')[-1])			   #但imread不支持中文文件名
	#im = imutils.resize(im, width = min(400, im.shape[1]))
	min_wdw_sz = (48,48)
	step_raw = (8,8)
	downscale = 1.1

	clf = joblib.load(os.path.join(model_path, 'svm.model'))

	#List to store the detections
	detections = []
	#The current scale of the image 
	scale = 0

	for scale_size in range(11,30,2):
		scale_size = scale_size/10.
		print('The Scale size is ',scale_size)
		window_size = [int(i*scale_size) for i in min_wdw_sz]
		#The list contains detections at the current scale
		#if im_scaled.shape[0] < min_wdw_sz[1] or im_scaled.shape[1] < min_wdw_sz[0]:
		#	break
		step_size = [int(i*scale_size) for i in step_raw]
		num = 0
		for (x, y, im_window) in sliding_window(im, window_size, step_size):
			#if im_window.shape[0] != min_wdw_sz[1] or im_window.shape[1] != min_wdw_sz[0]:
			#	continue
			#im_window = im_window*255
			#im_window = np.floor(im_window)
			#im_window = im_window.astype(np.uint8)

			#im_window = color.rgb2gray(im_window)
			im_window = Image.fromarray(im_window)
			im_window = im_window.resize((img_avg,img_avg))
			im_window = np.array(im_window)
			num+=1
			print(f'已检测{num}个窗口,现在是\t{x},{y}')
			fd = hog.compute(im_window,(img_avg,img_avg))

			fd = fd.reshape(1, -1)
			pred = clf.predict(fd)

			if pred == 1:
				cdf = clf.decision_function(fd)
				if cdf>0.5:
					detections.append((x,y,cdf,window_size[0],window_size[1]))
				#if clf.decision_function(fd) > 0.5:
				#	detections.append((int(x * (downscale**scale)), int(y * (downscale**scale)), clf.decision_function(fd), 
				#	int(min_wdw_sz[0] * (downscale**scale)),
				#	int(min_wdw_sz[1] * (downscale**scale))))
			
		scale += 1

	clone = im.copy()

	for (x_tl, y_tl, _, w, h) in detections:
		cv2.rectangle(im, (x_tl, y_tl), (x_tl + w, y_tl + h), (0, 255, 0), thickness = 2)

	rects = np.array([[x, y, x + w, y + h] for (x, y, _, w, h) in detections])
	sc = [score[0] for (x, y, score, w, h) in detections]
	print("sc: ", sc)
	sc = np.array(sc)
	pick = non_max_suppression(rects, probs = sc, overlapThresh = 0.3)
	#pick = rects
	print("shape, ", pick.shape)

	for(xA, yA, xB, yB) in pick:
		cv2.rectangle(clone, (xA, yA), (xB, yB), (0, 255, 0), 2)
	
	#plt.axis("off")
	plt.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
	plt.title("Raw Detection before NMS")
	plt.show()

	#plt.axis("off")
	plt.imshow(cv2.cvtColor(clone, cv2.COLOR_BGR2RGB))
	plt.title("Final Detections after applying NMS")
	plt.show()

def test_folder(foldername):

	filenames = glob.iglob(os.path.join(foldername, '*'))
	for filename in filenames:
		detector(filename)

if __name__ == '__main__':
	foldername = 'test_image_mine'	  #效果依然奇差。如果一晚上能够搞定那个鬼mcnn的话也行。
	test_folder(foldername)

