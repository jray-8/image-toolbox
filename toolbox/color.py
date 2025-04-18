import math
import random
from PIL import Image
from .image_helpers import (choose_option, get_value, get_brightness, clamp_intensity, round_pixel, to_radians)
from .image_basics import (PaddingType, pad_image, crop_image)
from .blending import (BlendMode, choose_blend_mode, get_blend, get_opacity)

# Color Presets
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)

# --- Color Effects ---
# assume these images are RGB or RGBA - the caller must make sure

# -- monochrome conversion ---
def start_monochrome_process(image):
	color_key = choose_monochrome_color()
	print()
	if color_key == BLACK:
		print('Converting to Grayscale...')
		image = image_to_grayscale(image)
	else:
		print('Converting to Monochrome...')
		image = image_to_monochrome(image, color_key)
	return image

def to_grayscale(pixel): # make pixel gray
	return get_brightness(pixel)

def image_to_grayscale(image):
	width, height = image.size
	gray_image = Image.new(mode='L', size=(width,height))
	for x in range(width):
		for y in range(height):
			source = image.getpixel((x,y))
			gray_image.putpixel((x,y), to_grayscale(source))
	return gray_image

def image_to_monochrome(image, color):
	width, height = image.size
	image_mode = image.mode
	if image_mode not in ['RGB', 'RGBA']:
		image_mode = 'RGB'
	mono_image = Image.new(mode=image_mode, size=(width,height))
	hue = rgb_to_hsv(color)[0] # make monochromatic in this color
	for x in range(width):
		for y in range(height):
			source = image.getpixel((x,y))
			source_hsv = rgb_to_hsv(source)
			new_pixel = hsv_to_rgb((hue, source_hsv[1], source_hsv[2]))
			mono_image.putpixel((x,y), new_pixel)
	return mono_image

def choose_monochrome_color():
	choices = ['Grayscale', 'Redscale', 'Greenscale', 'Bluescale', 'Custom Color']
	x = choose_option(choices, 'Monochrome Color:')
	if x == 1:
		return RED
	elif x == 2:
		return GREEN
	elif x == 3:
		return BLUE
	elif x == 4:
		print()
		hue = get_hue()
		return hsv_to_rgb((hue, 1, 1))
	else: # grayscale
		return BLACK
	
# --- hue shift ---
def start_hue_shift_process(image):
	if image.mode == 'L':
		print('Cannot hue shift a grayscale image!')
		return image
	shift = get_hue_shift()
	print('\nShifting Hue...')
	return hue_shift(image, shift)

def get_hue_shift():
	return get_value(-360, 360, 'Hue Shift', default=30) % 360

def hue_shift(image, degrees):
	width, height = image.size
	new_image = Image.new(mode=image.mode, size=(width,height))
	for x in range(width):
		for y in range(height):
			source = image.getpixel((x,y))
			source_hsv = rgb_to_hsv(source)
			new_hue = (source_hsv[0] + degrees) % 360
			new_pixel = hsv_to_rgb((new_hue, source_hsv[1], source_hsv[2]))
			new_image.putpixel((x,y), new_pixel)
	return new_image

# --- resaturate ---
def start_resaturate_process(image):
	if image.mode == 'L':
		print('Cannot resaturate a grayscale image!')
		return image
	shift_type = choose_scale_type()
	print()
	shift_by_percent = False
	if shift_type == 1:
		shift_by_percent = True
	shift = get_saturation_scale(by_percent=shift_by_percent)
	print()
	print('Resaturating...')
	return resaturate(image, shift, by_percent=shift_by_percent)

def choose_scale_type():
	choices = ['By Constant', 'By Percent']
	return choose_option(choices, 'Scale Type:')

def get_saturation_scale(by_percent=False):
	if by_percent:
		return get_value(0, 400, 'Saturation Scale (%)', default=150) / 100
	else:
		return get_value(-100, 100, 'Saturation Constant (%)', default=10) / 100
	
def resaturate(image, scale, by_percent=False):
	width, height = image.size
	new_image = Image.new(mode=image.mode, size=(width,height))
	for x in range(width):
		for y in range(height):
			source = image.getpixel((x,y))
			source_hsv = rgb_to_hsv(source)
			if not by_percent:
				new_sat = source_hsv[1] + scale
			else: # multiply by percentage
				new_sat = source_hsv[1] * scale
			# bounds
			if new_sat > 1:
				new_sat = 1
			elif new_sat < 0:
				new_sat = 0
			new_pixel = list(source_hsv)
			new_pixel[1] = new_sat
			new_pixel = hsv_to_rgb(new_pixel)
			new_image.putpixel((x,y), new_pixel)
	return new_image

# --- color split ---
def start_color_split_process(image):
	split_shape = get_split_shape()
	print()
	if split_shape == None:
		split_dir = create_split_directions()
	else:
		split_dir = get_split_directions(split_shape)
		print()
	split_radius = get_split_radius(image)
	print()
	num_splits = len(split_dir)
	split_colors = get_split_colors(num_splits)
	print()
	blend = choose_blend_mode()
	print()
	alpha = get_opacity()
	print()
	print('Splitting Colors...')
	# first pad image
	image = pad_image(image, split_radius, padding_type=PaddingType.REFLECTED)
	image = color_split(image, split_radius, split_dir, split_colors, blend_type=blend, blend_alpha=alpha)
	image = crop_image(image, split_radius)
	return image

def get_split_shape():
	choices = ['Upright-Y', 'Upright-T', 'X-Shape', 'Custom']
	x = choose_option(choices, 'Split Shape:')
	if x == 0:
		x = 'Y'
	elif x == 1:
		x = 'T'
	elif x == 2:
		x = 'X'
	else:
		x = None
	return x

def create_split_directions():
	print('Custom Split:')
	print('=============')
	num_splits = get_value(1, 5, 'Number of Splits', integer=True)
	print()
	print('Enter angle of each split...\n')
	split_directions = []
	for i in range(num_splits):
		degrees = get_value(-360, 360, f'Split {i+1} (degrees)', default=0)
		print()
		rad = to_radians(degrees)
		shift_x = math.cos(rad)
		shift_y = math.sin(rad)
		split_directions.append((shift_x, -shift_y)) # left-handed
	return split_directions

def get_split_directions(shape):
	if shape == 'Y': # Y-shape
		split_directions = [(-1,1), (1,1), (0,-1)]
	elif shape == 'T': # T-shape
		split_directions = [(-1,0), (1,0), (0,-1)]
	else: # X-shape
		split_directions = [(-1,1), (1,1), (-1,-1), (1,-1)]
	print('Rotate Split Shape:')
	print(f'- Default is the upright {shape} shape')
	x = get_value(-360, 360, f'Rotate {shape} CCW (degrees)', default=0)
	rotation = to_radians(x)
	for i in range(3):
		try:
			rad = math.atan(split_directions[i][1] / split_directions[i][0])
		except ZeroDivisionError:
			if split_directions[i][1] >= 0:
				rad = math.pi / 2
			else: # negative
				rad = 3 * math.pi / 2
		rad += rotation
		shift_x = math.cos(rad)
		shift_y = math.sin(rad)
		split_directions[i] = (shift_x, -shift_y) # left-handed coordinate system
	return split_directions

def get_split_radius(image):
	print('Enter 0 for a random radius.')
	x = get_value(0, 100, 'Split Radius (%)', default=10) / 100
	if x == 0: # get random
		x = random.randint(1,100)
		print(f'{x} (random)')
		x /= 100
	max_radius = min(image.width, image.height) / 2
	return int(x * max_radius)

def get_split_colors(splits):
	print('Which Colors to Split?')
	print('======================')
	colors = []
	default = 0 # red
	for i in range(splits):
		instructions = False
		if i == 0:
			instructions = True
		hue = get_hue(show_ranges=instructions, default_hue=default)
		colors.append(hsv_to_rgb((hue,1,1)))
		default += int(360 / splits)
	return colors

def color_split(image, radius, split_directions, colors, blend_type=BlendMode.AVERAGE, blend_alpha=1):
	width, height = image.size
	splits = len(split_directions)
	new_image = Image.new(mode=image.mode, size=(width,height))
	for x in range(width):
		for y in range(height):
			pixel = list(image.getpixel((x,y)))
			# receive colors from the pixels that split to this location
			for i in range(splits):
				shift_x = x - int(split_directions[i][0] * radius)
				shift_y = y - int(split_directions[i][1] * radius)
				if shift_x >= 0 and shift_x < width:
					if shift_y >= 0 and shift_y < height:
						color_source = image.getpixel((shift_x,shift_y))
						for k in range(3): # channels
							p = colors[i][k] / 255 # percent of rgb channel that this color (colors[i]) uses
							absorbed_color = (pixel[k] * (1-p) + color_source[k] * p)
							pixel[k] = get_blend([pixel[k], absorbed_color], blend_mode=blend_type, opacity=blend_alpha)
			# round off
			pixel = round_pixel(pixel)
			new_image.putpixel((x,y), pixel)
	return new_image

# --- pseudo color ---
def start_pseudo_color_process(image):
	alg = choose_pseudo_color()
	print()
	if alg == 0: # heatmap
		print('Applying Heatmap...')
		image = apply_heatmap(image)
	elif alg == 1: # random
		n = get_number_of_colors()
		print('\nApplying Colors...')
		image = apply_random_colors(image, n)
	return image

def choose_pseudo_color():
	choices = ['Heatmap', 'Random Colors']
	return choose_option(choices, 'Pseudo Algorithm:')

def apply_heatmap(image):
	width, height = image.size
	colored_image = Image.new(mode='RGB', size=(width,height))
	for x in range(width):
		for y in range(height):
			gray_pixel = to_grayscale(image.getpixel((x,y)))
			# assign color
			red = gray_pixel # highest at white
			green = clamp_intensity(255 - 2 * abs(gray_pixel - 127)) # highest at mid-gray
			blue = 255 - gray_pixel # highest at black
			# place colored pixel
			color_pixel = (red,green,blue)
			colored_image.putpixel((x,y), color_pixel)
	return colored_image

def get_number_of_colors():
	return get_value(2, 20, 'Max Colors', integer=True, default=4)

def apply_random_colors(image, num_colors):
	width, height = image.size
	# choose colors
	color_list = []
	for _ in range(num_colors):
		color_list.append(get_random_color())
	interval_width = 256 / num_colors
	colored_image = Image.new(mode='RGB', size=(width,height))
	# fill color
	for x in range(width):
		for y in range(height):
			gray_pixel = to_grayscale(image.getpixel((x,y)))
			# choose color
			i = int(gray_pixel / interval_width)
			color_pixel = color_list[i]
			colored_image.putpixel((x,y), color_pixel)
	return colored_image

# --- Color Input ---
def get_hue(show_ranges=True, default_hue=0):
	if show_ranges:
		print('Reds: (300 - 60)')
		print('Greens: (60 - 180)')
		print('Blues: (180 - 300)')
		print()
	return get_value(-360, 360, 'Hue', default=default_hue) % 360

def get_saturation():
	return get_value(0, 100, 'Saturation', default=90) / 100

def get_color_value():
	return get_value(0, 100, 'Value', default=90) / 100

def create_color(): # in rgb
	print('Create Color')
	print('============')
	h = get_hue(); print()
	s = get_saturation(); print()
	v = get_color_value()
	return hsv_to_rgb(h,s,v)

# --- Color Functions ---
def get_random_color():
	c = [0,0,0]
	for i in range(3):
		c[i] = random.randint(0,255)
	return tuple(c)

def rgb_to_hsv(rgb):
	r, g, b = rgb
	# normalize: 0..255 -> [0,1]
	r_n = r/255
	g_n = g/255
	b_n = b/255
	# max/min
	c_max = max(r_n, g_n, b_n)
	c_min = min(r_n, g_n, b_n)
	# difference between normalized rgb max and min value [0,1]
	delta = c_max - c_min
	# calculate HSV
	# hue (degrees)
	if delta == 0: # r=g=b
		h = 0 # default
	elif c_max == r_n: # red max
		h = 60 * ((g_n - b_n)/delta % 6)
	elif c_max == g_n: # green max
		h = 60 * ((b_n - r_n)/delta + 2)
	elif c_max == b_n: # blue max
		h = 60 * ((r_n - g_n)/delta + 4)
	h = round(h) # integer
	# saturation
	if c_max == 0:
		s = 0
	else:
		s = delta/c_max
	s = round(s,2)
	# value
	v = round(c_max,2) # percent of max intensity
	return (h,s,v)

def hsv_to_rgb(hsv):
	h, s, v = hsv
	h = h % 360 # 0..359
	# convert to RGB
	c = v * s
	x = c * (1 - abs(h/60 % 2 - 1))
	m = v - c
	# based on hue
	r_n, g_n, b_n = (0, 0, 0)
	if 0 <= h and h < 60:
		r_n, g_n, b_n = (c, x, 0)
	elif 60 <= h and h < 120:
		r_n, g_n, b_n = (x, c, 0)
	elif 120 <= h and h < 180:
		r_n, g_n, b_n = (0, c, x)
	elif 180 <= h and h < 240:
		r_n, g_n, b_n = (0, x, c)
	elif 240 <= h and h < 300:
		r_n, g_n, b_n = (x, 0, c)
	elif 300 <= h and h < 360:
		r_n, g_n, b_n = (c, 0, x)
	# normalize to RGB space 0..255
	r, g, b = (round((r_n+m)*255), round((g_n+m)*255), round((b_n+m)*255))
	return (r,g,b)

# adds to the hue, saturation or value or a color (in rgb)
def change_color(color, d_h=0, d_s=0, d_v=0):
	h, s, v = rgb_to_hsv(color)
	# hue
	h += d_h
	h = h % 360 # wrap around
	# saturation
	s += d_s
	if s < 0:
		s = 0
	elif s > 1:
		s = 1
	# value
	v += d_v
	if v < 0:
		v = 0
	elif v > 1:
		v = 1
	return hsv_to_rgb((h,s,v))

# sets the hue, saturation or value of a color (in rgb)
def set_color(color, h=None, s=None, v=None):
	h_o, s_o, v_o = rgb_to_hsv(color) # original color
	if h != None:
		h_o = h
		h_o = h_o % 360
	if s != None:
		s_o = s
		if s_o > 1:
			s_o = 1
		elif s_o < 0:
			s_o = 0
	if v != None:
		v_o = v
		if v_o > 1:
			v_o = 1
		elif v_o < 0:
			v_o = 0
	return hsv_to_rgb((h_o,s_o,v_o))