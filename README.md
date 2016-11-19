# piwall-cvtools
OpenCV inspired tools for working with video walls, especially piwall.co.uk.  

# prerequisites and installation
opencv 3.1.0 (notes on Gdrive / follow the pyimagesearch process for building from git)
matplotlib : on ubuntu apt-get install python-matplotlib
common/ : TODO - this is resolved from
/home/adam/pd/opencv/opencv-3.1.0/samples/python/
in turn this is unpacked from opencv-3.1.0.zip (76M download from opencv.org)


# Status 17/09/2016

- Amended to include data/rotating_wall.mp4 and data/2x2-red-1.jpg and piwall.py updated
- Command line arguments as follows should be reproducible :                    

/usr/bin/python piwall.py -v rotating

Note that data/ has some real mp4 files and one symbolic linkj, currently pointed at the shorter.

To make shorter versions, the recipe is : 

ffmpeg -i rotating_wall.mp4 -ss 00:00:00.0 -c copy -t 00:00:02.0 rotating_wall_2s.mp4


# TODO NEXT : add harris corner detection 
http://scikit-image.org/docs/dev/auto_examples/features_detection/plot_corner.html#sphx-glr-auto-examples-features-detection-plot-corner-py

# TODO NEXT :
  Step around the problem of integrating everything in one GUI with
       multiprocessing ?

