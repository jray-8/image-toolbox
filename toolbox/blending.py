import random
from .image_helpers import (print_image_size, choose_option, get_value, get_pixel_rows, get_pixel_columns, get_pixel_array,
			    			divide_list, place_segments, place_pixels, get_channels, round_pixel, normalize_pixel, denormalize_pixel)

class BlendMode:
	NORMAL = 0
	AVERAGE = 1
	MULTIPLY = 2
	COLOR_BURN = 3
	LINEAR_BURN = 4
	SCREEN = 5
	COLOR_DODGE = 6
	LINEAR_DODGE = 7
	SUBTRACT = 8
	DIVIDE = 9
	DARKEN = 10
	LIGHTEN = 11
	NEGATION = 12

# --- blend modes ---
def choose_blend_mode():
	choices = ['Normal', 'Average', 'Multiply', 'Color Burn', 'Linear Burn', 'Screen', 
	    		'Color Dodge', 'Linear Dodge', 'Subtract', 'Divide', 'Darken', 'Lighten', 'Negation']
	return choose_option(choices, 'Blend Mode:')

def get_opacity():
	print('Enter 0 for a random opacity.')
	x = get_value(0, 100, 'Opacity', default=100)
	if x == 0:
		x = random.randint(1,100)
		print(f'{x} (random)')
	return x / 100

# assumes at least 2 pixels - and they share the same image format
# first pixel in list is considered the 'bottom' layer
def get_blend(pixel_list, blend_mode=BlendMode.AVERAGE, opacity=1):
	if not pixel_list:
		return None
	if len(pixel_list) == 1:
		return pixel_list[0]
	num_channels = get_channels(pixel_list[0])
	# Normal
	if blend_mode == BlendMode.NORMAL: # last pixel overwrites all
		blend = pixel_list[-1]
	# Average
	elif blend_mode == BlendMode.AVERAGE:
		blend = average_blend(pixel_list, num_channels)
	# Multiply
	elif blend_mode == BlendMode.MULTIPLY:
		blend = multiply_blend(pixel_list, num_channels)
	# Color Burn
	elif blend_mode == BlendMode.COLOR_BURN:
		blend = color_burn_blend(pixel_list, num_channels)
	# Linear Burn
	elif blend_mode == BlendMode.LINEAR_BURN:
		blend = linear_burn_blend(pixel_list, num_channels)
	# Screen
	elif blend_mode == BlendMode.SCREEN:
		blend = screen_blend(pixel_list, num_channels)
	# Color Dodge
	elif blend_mode == BlendMode.COLOR_DODGE:
		blend = color_dodge_blend(pixel_list, num_channels)
	# Linear Dodge
	elif blend_mode == BlendMode.LINEAR_DODGE:
		blend = linear_dodge_blend(pixel_list, num_channels)
	# Subtract
	elif blend_mode == BlendMode.SUBTRACT:
		blend = subtract_blend(pixel_list, num_channels)
	# Divide
	elif blend_mode == BlendMode.DIVIDE:
		blend = divide_blend(pixel_list, num_channels)
	# Darken
	elif blend_mode == BlendMode.DARKEN:
		blend = darken_blend(pixel_list, num_channels)
	# Lighten
	elif blend_mode == BlendMode.LIGHTEN:
		blend = lighten_blend(pixel_list, num_channels)
	# Negation
	elif blend_mode == BlendMode.NEGATION:
		blend = negation_blend(pixel_list, num_channels)
	# Undefined
	else:
		print(f'Undefined blend mode - {blend_mode}')
		return None
	# apply opacity
	if num_channels == 1:
		return (blend * opacity) + (pixel_list[0] * (1-opacity))
	else:
		blend = list(blend)
		for c in range(num_channels):
			blend[c] = int((blend[c] * opacity) + (pixel_list[0][c] * (1-opacity)))
	return tuple(blend)
	
def average_blend(pixel_list, channels=3):
	average = [0] * channels
	# add to total
	for pixel in pixel_list:
		for c in range(channels):
			if channels == 1:
				average[c] += pixel
			else:
				average[c] += pixel[c]
	# average pixels
	total_pixels = len(pixel_list)
	for c in range(channels):
		average[c] /= total_pixels
	# single channel
	if channels == 1:
		average = average[0]
	return round_pixel(average)

def base_blend(pixel_list, channels, blend_function):
	mix = normalize_pixel(pixel_list[0])
	for i in range(1, len(pixel_list)):
		a = normalize_pixel(pixel_list[i])
		if channels == 1:
			mix = blend_function(a, mix)
		else:
			for c in range(channels):
				mix[c] = blend_function(a[c], mix[c])
	return round_pixel(denormalize_pixel(mix))

def multiply_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: top * bottom
	return base_blend(pixel_list, channels, blend_math)

def color_burn_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: 1 - ((1-bottom) / top) if top != 0 else 0
	return base_blend(pixel_list, channels, blend_math)

def linear_burn_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: top + bottom - 1
	return base_blend(pixel_list, channels, blend_math)

def screen_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: 1 - ((1-top) * (1-bottom))
	return base_blend(pixel_list, channels, blend_math)

def color_dodge_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: bottom / (1-top) if top != 1 else 1
	return base_blend(pixel_list, channels, blend_math)

def linear_dodge_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: top + bottom
	return base_blend(pixel_list, channels, blend_math)

def subtract_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: bottom - top
	return base_blend(pixel_list, channels, blend_math)

def divide_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: bottom / top if top != 0 else 1
	return base_blend(pixel_list, channels, blend_math)

def darken_blend(pixel_list, channels=3): # same as min
	blend_math = lambda top, bottom: min(top, bottom)
	return base_blend(pixel_list, channels, blend_math)

def lighten_blend(pixel_list, channels=3): # same as max
	blend_math = lambda top, bottom: max(top, bottom)
	return base_blend(pixel_list, channels, blend_math)

def negation_blend(pixel_list, channels=3):
	blend_math = lambda top, bottom: 1 - abs(1 - top - bottom)
	return base_blend(pixel_list, channels, blend_math)

# --- blend lines ---
def start_blend_line_process(image):
	blend_rows = True
	if choose_rows_cols() == 1:
		blend_rows = False
	print()
	lines = get_lines(image, blend_rows)
	print()
	mode = choose_blend_mode()
	print()
	a = get_opacity()
	print()
	print('Blending Lines...')
	image = blend_lines(image, rows=blend_rows, num_lines=lines, bm=mode, alpha=a)
	return image

def blend_lines(image, rows=True, num_lines=2, bm=BlendMode.AVERAGE, alpha=1):
	if rows:
		lines = get_pixel_rows(image)
	else: # cols
		lines = get_pixel_columns(image)
	total_lines = len(lines)
	line_width = len(lines[0])
	num_groups = total_lines / num_lines # how many groups of n lines
	line_groups = divide_list(lines, num_groups)
	# blend - original lines are affected directly by the groups
	for next_group in line_groups:
		n = len(next_group) # number of lines in this group
		for i in range(line_width):
			# pixels from all lines in the group at the same col/row
			aligned_pixels = [next_group[x][i] for x in range(n)]
			blend = get_blend(aligned_pixels, blend_mode=bm, opacity=alpha) # averaged pixel
			for x in range(n): # apply to sampled area
				next_group[x][i] = blend
	# reconstruct image
	place_segments(image, lines, horizontal=rows)
	return image

def choose_rows_cols():
	choices = ['Rows', 'Columns']
	return choose_option(choices, 'Line Type')

def get_lines(image, rows=True):
	print_image_size(image)
	if rows:
		max_lines = image.height
	else: # cols
		max_lines = image.width
	return get_value(2, max_lines, 'How Many Lines?', integer=True)

# --- pixelate ---
def start_pixelate_process(image):
	box_size = get_pixelate_size(image)
	print()
	print('Pixelating...')
	image = pixelate(image, box_size)
	return image

def get_pixelate_size(image):
	min_dim = min(image.width, image.height)
	max_box = int(min_dim * 0.2)
	return get_value(1, max_box, 'Pixel Size', integer=True)

def pixelate(image, box_size):
	width, height = image.size
	image_array = get_pixel_array(image, True)
	for x in range(0, width, box_size):
		for y in range(0, height, box_size):
			# get a list of all pixels within the box
			pixel_list = []
			for box_x in range(x, x+box_size):
				for box_y in range(y, y+box_size):
					if box_x < width and box_y < height: # within bounds
						index = (width * box_y) + box_x
						pixel_list.append(image_array[index])
			# blend box area
			blend = get_blend(pixel_list, blend_mode=BlendMode.AVERAGE)
			# redistribute pixel list to the image array
			for box_x in range(x, x+box_size):
				for box_y in range(y, y+box_size):
					if box_x < width and box_y < height: # within bounds
						index = (width * box_y) + box_x
						image_array[index] = blend
	place_pixels(image, image_array, True)
	return image