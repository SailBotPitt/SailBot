import pygame
import constants
import sys
from picamera import PiCamera
from time import sleep

import image_analysis_test as iat

def main_loop():
    while True:
        
        handle_input()
        
        
        CAM.capture('picture.jpg')
        

        img_path = "picture.jpg"
        IMG = pygame.image.load(img_path)
        iat.load_image(img_path)

        # iat.resize(1000)
        # IMG = pygame.image.load("tester.jpg")

        SURFACE_MAIN.blit(IMG, (0,0))
        
        array = iat.get_intrest_tiles(iat.get_pixel_array(constants.IMG_ACCURACY))
        i = 0
        for y, row in enumerate(array):
            for x, elem in enumerate(row):
                if elem:
                    surface = pygame.Surface((constants.IMG_ACCURACY, constants.IMG_ACCURACY))
                    
                    # Define the color of activated boxes
                    surface.fill((100, 100, 255))
                    
                    # Define the transparancy of activated boxes
                    surface.set_alpha(100)
                    SURFACE_MAIN.blit(surface, (x*constants.IMG_ACCURACY, y*constants.IMG_ACCURACY))
                    i+=1
 
        pygame.display.flip()


def init():
    global SURFACE_MAIN, IMG, CAM

    pygame.init()
    pygame.display.set_caption(constants.WIN_TITLE)
    pygame.key.set_repeat(200, 70)

    SURFACE_MAIN = pygame.display.set_mode( (constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT) )
    SURFACE_MAIN.fill((255,255,255))
    
    CAM = PiCamera()
    CAM.start_preview()

    

def quit():

    CAM.stop_preview()
    pygame.quit()
    sys.exit()

def handle_input():

    events_list = pygame.event.get()

    for event in events_list:

        if event.type == pygame.QUIT:
            quit()

if __name__ == '__main__':
    init()
    main_loop()
