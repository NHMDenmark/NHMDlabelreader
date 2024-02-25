import argparse
import cv2
import zxingcpp


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=False, default="/Users/kimstp/Documents/NHMD/data/Herbarium/NHMD-681096.jpg",
                help="file name for and path to input image")
args = vars(ap.parse_args())

img = cv2.imread(args["image"])

dmcodes = zxingcpp.read_barcodes(img, formats=zxingcpp.DataMatrix)

if len(dmcodes) >0:
    print("Data Matrix codes found:")
    print(dmcodes[0].text)
else:
    print("No Data Matrix codes found")
