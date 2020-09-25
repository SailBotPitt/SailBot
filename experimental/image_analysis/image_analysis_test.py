from PIL import Image

def load_image(path):
    global img, px
    img = Image.open(path)
    px = img.load()

def get_pixel(x, y):
    return px[x,y]

def resize(basewidth):
    global img
    wpercent = (basewidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((basewidth,hsize), Image.ANTIALIAS)
    img.save('tester.jpg')
    return img

def get_pixel_array(spacer = 10):
    array = []

    for y in range(int(spacer/2), int(img.size[1]), spacer):
        #get row of points in x_ary
        x_ary = []
        for x in range(int(spacer/2), int(img.size[0]), spacer):
            x_ary.append( rgb_to_hsv( get_pixel(x, y) ) )

        array.append(x_ary) #makes 2d array

    return array

def color_meets_a_req(hls, h_ranges = [(0, 80), (250, 360)], s_ranges = [(1, 1)], v_ranges = [(1, 1), (0, 0)]):
    interesting = False
    for hmin, hmax in h_ranges:
        if hls[0] >= hmin and hls[0] <= hmax:
            interesting = True
            pass

    for smin, smax in s_ranges:
        if hls[1] >= smin and hls[1] <= smax:
            interesting = True  
            pass

    for vmin, vmax in v_ranges:
        if hls[2] >= vmin and hls[2] <= vmax:
            interesting = True  
            pass

    return interesting

def color_meets_all_reqs(hls, h_ranges = [(0, 80), (300, 360)], s_ranges = [(0, 1)], v_ranges = [(.6, 1)]):
    interesting = False
    for hmin, hmax in h_ranges:
        if hls[0] >= hmin and hls[0] <= hmax:
            for smin, smax in s_ranges:
                if hls[1] >= smin and hls[1] <= smax:
                    for vmin, vmax in v_ranges:
                        if hls[2] >= vmin and hls[2] <= vmax:
                            interesting = True


    return interesting


# Determines if a given color value is orange
# Param: hls defines an HSV color value
# Return: is_orange defines if orange is found in the pixels
def color_orange(hls):
    is_orange = color_meets_all_reqs(hls, h_ranges = [(0, 56)], s_ranges = [(.3, 1)], v_ranges = [(.25, 1)])
    return is_orange

# Looks at pixel array and returns an array of arrays that define the position of active pixels
def get_intrest_tiles(array, is_interesting = color_orange):

    rows = []

    for row in array:
        current_row = []
        for elem in row:
            current_row.append( is_interesting(elem) )

        rows.append(current_row)

    return rows

def rgb_to_hsv(rgb):
    r, g, b = rgb
    r_ratio = float(r/255.)
    g_ratio = float(g/255.)
    b_ratio = float(b/255.)

    minimum = min(r_ratio, g_ratio, b_ratio)
    maximum = max(r_ratio, g_ratio, b_ratio)

    V = maximum

    if minimum == maximum:
        S = 0
        H = 0

    else:
        if V == 0:
            S = 0
        else:
            S = (maximum - minimum) / maximum


        if r_ratio == maximum:
            H = ((g_ratio - b_ratio)/(maximum - minimum) % 6 )
        elif g_ratio == maximum:
            H = 2.0 + (b_ratio - r_ratio)/(maximum - minimum)
        elif b_ratio == maximum:
            H = 4.0 + (r_ratio - g_ratio)/(maximum - minimum)

        H = H*60

        if H < 0:
            H+=360
        if H > 360:
            H-=360

    return (H,S,V)



if __name__ == '__main__':
    #print is_special_color((300, .5, .3))
    pass