# piwall-cvtools
OpenCV inspired tools for working with video walls, especially piwall.co.uk.  

# Status 17/09/2016

- Amended to include data/rotating_wall.mp4 and data/2x2-red-1.jpg and piwall.py updated
- Command line arguments as follows should be reproducible :                    

/usr/bin/python piwall.py -v rotating

Note that data/ has some real mp4 files and one symbolic linkj, currently pointed at the shorter.

To make shorter versions, the recipe is : 

ffmpeg -i rotating_wall.mp4 -ss 00:00:00.0 -c copy -t 00:00:02.0 rotating_wall_2s.mp4

