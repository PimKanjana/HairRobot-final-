
from pypylon import pylon
import cv2

def Cam():

	# conecting to the first available camera
	camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

	# Grabing Continusely (video) with minimal delay
	camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
	converter = pylon.ImageFormatConverter()

	# converting to opencv bgr format
	converter.OutputPixelFormat = pylon.PixelType_BGR8packed
	converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

	while camera.IsGrabbing():
		grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

		if grabResult.GrabSucceeded():
			# Access the image data
			image = converter.Convert(grabResult)
			img = image.GetArray()
			cv2.namedWindow('Title', cv2.WINDOW_NORMAL)
			cv2.imshow('Title', img)
		
			k = cv2.waitKey(1)
			if k == 27:
				break

		grabResult.Release()

	# Releasing the resource    
	camera.StopGrabbing()

	cv2.destroyAllWindows()


