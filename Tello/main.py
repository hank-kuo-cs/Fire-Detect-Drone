import tello
from tello_control_ui import TelloUI
from fire_detect import FireDetect


def main():

    drone = tello.Tello('', 8889)  
    # vplayer = TelloUI(drone,"./img/")
    firedet = FireDetect(drone,"./img/")
    
	# start the Tkinter mainloop
    firedet.vplayer.root.mainloop() 

if __name__ == "__main__":
    main()
