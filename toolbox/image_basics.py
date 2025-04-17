import math
from PIL import Image
from .image_helpers import (get_dimensions, get_dimension_offsets, choose_option, choose_yes_no, get_value, get_channels, read_offsets, to_radians, list_all_null)
BLACK = (0,0,0)

# --- Basic Toolbox Functions ---
# cropping, flipping, scaling, padding, rotating

# --- crop an image ---
def start_crop_process(image):
	offsets = get_crop_dimensions(image)
	if not list_all_null(offsets):
		print()
		print('Cropping...')
		image = crop_image(image, offsets)
	return image

def get_crop_dimensions(cur_image): # top, bottom, left, right
	return get_dimension_offsets(cur_image, 'Crop Sides (pixels to offset sides by):')

def crop_image(image, offsets):
	offsets = read_offsets(offsets)
	width, height = image.size
	# create cropped image
	new_width = max(width - offsets[2] - offsets[3], 1)
	new_height = max(height - offsets[0] - offsets[1], 1)
	cropped_image = Image.new(mode=image.mode, size=(new_width,new_height))
	for i in range(offsets[2], width - offsets[3]):
		for k in range(offsets[0], height - offsets[1]):
			# check if this pixel is within the source bounds
			if i < 0 or i > (width-1):
				continue
			elif k < 0 or k > (height-1):
				continue
			cropped_image.putpixel((i-offsets[2],k-offsets[0]), image.getpixel((i,k)))
	return cropped_image

# --- flip (horizontal/vertical) ---
def start_flip_process(image):
	flip_directions = get_flip_directions()
	if not list_all_null(flip_directions):
		print()
		print('Flipping...')
		image = flip_image(image, flip_directions[0], flip_directions[1])
	return image

def get_flip_directions():
	flip_dirs = [False]*2
	dir_names = ['Horizontally', 'Vertically']
	# defaults to False
	for i in range(2):
		msg = f'Flip {dir_names[i]}'
		flip_dirs[i] = choose_yes_no(msg, default='no')
	return flip_dirs

def flip_image(image, horizontal=False, vertical=False):
	width, height = image.size
	new_image = Image.new(mode=image.mode, size=(width,height))
	for i in range(width):
		for k in range(height):
			reverse_i = i
			reverse_k = k
			if horizontal:
				reverse_i = (width-1) - i
			if vertical:
				reverse_k = (height-1) - k
			new_image.putpixel((i,k), image.getpixel((reverse_i,reverse_k)))
	return new_image

# --- rotate ---
def start_rotate_process(image):
	degrees = get_rotation()
	print()
	padding_type = choose_padding_type()
	print()
	print('Rotating...')
	image = pad_rotate(image, degrees, padding_type)
	return image

def get_rotation(): # degrees
	return get_value(-360, 360, 'Rotation CCW (degrees)', default=0) % 360

# rotate degrees ccw
## leaves empty gaps
def rotate_image(image, degrees):
	width, height = image.size
	# PIL uses a left-handed coordinate system, so normal rotation will appear clockwise
	# get negative angle
	rotation = 360 - (degrees % 360)
	rotation = to_radians(rotation)
	translation = (width/2,height/2) # to bring center of image to origin
	rotated_image = Image.new(mode=image.mode, size=(width,height))
	# copy pixels to the new plane
	for i in range(width):
		for k in range(height):
			# center image at origin
			x = i - translation[0]
			y = k - translation[1]
			# apply rotation matrix to pixel location
			rot_x = x*math.cos(rotation) - y*math.sin(rotation)
			rot_y = x*math.sin(rotation) + y*math.cos(rotation)
			# undo the translation
			rot_x += translation[0]
			rot_y += translation[1]
			# round to nearest pixel
			rot_x = round(rot_x)
			rot_y = round(rot_y)
			# write the pixels that fit on the canvas
			if 0 <= rot_x and rot_x < width:
				if 0 <= rot_y and rot_y < height:
					rotated_image.putpixel((rot_x,rot_y), image.getpixel((i,k)))
					#print(str((i,k)) +' --> ' + str((rot_x,rot_y))) #!!
	return rotated_image

# instead of running through all the source pixels, rotating them, and placing them in the corresponding location in the destination image,
# run through all the destination pixels, undo the rotation, then select the corresponding pixel from the source image to copy
def complete_rotate_image(image, degrees):
	width, height = image.size
	# PIL uses a left-handed coordinate system, so angle is reversed (clockwise) by default
	rotation = to_radians(degrees % 360)
	translation = (width/2,height/2) # to bring center of image to origin
	rotated_image = Image.new(mode=image.mode, size=(width,height))
	# copy pixels to the new plane
	for i in range(width):
		for k in range(height):
			# center image at origin
			rot_x = i - translation[0]
			rot_y = k - translation[1]
			# apply reverse rotation matrix to destination pixel
			source_x = rot_x*math.cos(rotation) - rot_y*math.sin(rotation)
			source_y = rot_x*math.sin(rotation) + rot_y*math.cos(rotation)
			# undo the translation
			source_x += translation[0]
			source_y += translation[1]
			# round to nearest pixel
			source_x = round(source_x)
			source_y = round(source_y)
			# write the pixels that fit on the canvas
			if 0 <= source_x and source_x < width:
				if 0 <= source_y and source_y < height:
					rotated_image.putpixel((i,k), image.getpixel((source_x,source_y)))
	return rotated_image

def pad_rotate(image, degrees, padding_type=0):
	if padding_type == PaddingType.ZERO: # zero-padding
		return complete_rotate_image(image, degrees)
	# save original dimensions
	width, height = image.size
	# how much do we need to pad the width and height to prevent areas from being unmapped to
	max_diameter = math.sqrt(width **2 + height **2)
	max_diameter = math.ceil(max_diameter)
	width_padding = (max_diameter - width) / 2
	width_padding = math.ceil(width_padding)
	height_padding = (max_diameter - height) / 2
	height_padding = math.ceil(height_padding)
	# set padding dimensions
	pad_dims = [height_padding] * 2
	pad_dims.extend([width_padding] * 2)
	# pad the image
	image = pad_image(image, pad_dims, padding_type)
	# now rotate the image
	image = complete_rotate_image(image, degrees)
	# now crop down to the original dimensions
	image = crop_image(image, pad_dims) # undo the padding
	return image

# --- scale ---
def start_scale_process(image):
	new_dim = get_dimensions(image)
	print()
	downscale = False
	if new_dim[0] < image.width and new_dim[1] < image.height:
		downscale = True
	alg = choose_interpolation(downscale)
	print()
	print('Scaling...')
	image = scale_image(image, new_dim, alg)
	return image

def choose_interpolation(downsampling=False):
	# order
	choices = ['Nearest Neighbour', 'Bilinear']
	if downsampling:
		choices.append('Box Sampling')
	return choose_option(choices, 'Interpolation Type:')

def scale_image(image, new_size, interpolation=0):
	width, height = image.size
	new_width, new_height = new_size
	scale_x = new_width/width
	scale_y = new_height/height
	scaled_image = Image.new(mode=image.mode, size=(new_width,new_height))
	color_black = BLACK
	if image.mode == 'L':
		color_black = 0
	# fill in scaled image
	for i in range(new_width):
		for k in range(new_height):
			# get pixel data
			pixel = color_black
			if interpolation == 2:
				pixel = get_box_sample(image, (i,k), scale_x, scale_y)
			elif interpolation == 1:
				pixel = get_bilinear_interpolant(image, (i,k), scale_x, scale_y)
			else:
				pixel = get_nearest_neighbour(image, (i,k), scale_x, scale_y)
			scaled_image.putpixel((i,k), pixel)
	return scaled_image

# nearest-neighbour interpolation
def get_nearest_neighbour(source_image, destination_pos, scale_x, scale_y):
	x = min(round(destination_pos[0]/scale_x), source_image.width-1)
	y = min(round(destination_pos[1]/scale_y), source_image.height-1)
	return source_image.getpixel((x,y))

# bilinear interpolation
def get_bilinear_interpolant(source_image, destination_pos, scale_x, scale_y):
	# dimensions of original image
	width, height = source_image.size
	# origianl location of pixel
	x = destination_pos[0]/scale_x
	y = destination_pos[1]/scale_y
	# get 4 nearest pixels
	left = min(int(x), width-1)
	right = min(math.ceil(x), width-1)
	top = min(int(y), height-1)
	bottom = min(math.ceil(y), height-1)
	# topleft, topright, bottomleft, bottomright
	p1 = source_image.getpixel((left,top))
	p2 = source_image.getpixel((right,top))
	p3 = source_image.getpixel((left,bottom))
	p4 = source_image.getpixel((right,bottom))
	# convert to lists if single channel
	if not isinstance(p1, (list, tuple)):
		p1 = [p1]
		p2 = [p2]
		p3 = [p3]
		p4 = [p4]
	# get channels of color mode
	channels = len(p1)
	# interpolate top 2 pixels / then bottom 2 pixels
	top_interpolant = [0]*channels
	bottom_interpolant = [0]*channels
	left_val = (right - x) # percent of left pixel to use
	right_val = 1 - left_val
	for i in range(channels):
		top_interpolant[i] = left_val*p1[i] + right_val*p2[i]
		bottom_interpolant[i] = left_val*p3[i] + right_val*p4[i]
	# interpolate the interpolants
	p_interpolant = [0]*channels
	top_val = (bottom - y)
	bottom_val = 1 - top_val
	for i in range(channels):
		p_interpolant[i] = round(top_val*top_interpolant[i] + bottom_val*bottom_interpolant[i])
	return tuple(p_interpolant)

# box sampling
def get_box_sample(source_image, destination_pos, scale_x, scale_y):
	box_width = math.ceil(1/scale_x)
	box_height = math.ceil(1/scale_y)
	# dimensions of original image
	width, height = source_image.size
	# origianl location of pixel
	x = destination_pos[0]/scale_x
	y = destination_pos[1]/scale_y
	# get box on source image
	box_left = max(int(x - box_width/2), 0)
	box_right = min(math.ceil(x + box_width/2), width-1)
	box_top = max(int(y - box_height/2), 0)
	box_bottom = min(math.ceil(y + box_height/2), height-1)
	# average the pixels in the box
	source_pixel = source_image.getpixel((0,0))
	channels = get_channels(source_pixel) # number of color channels in source pixel
	sample = [0]*channels
	total_pixels = 0 # inside the box
	for i in range(box_left, box_right+1):
		for k in range(box_top, box_bottom+1):
			pixel = source_image.getpixel((i,k))
			if channels == 1:
				pixel = [pixel]
			total_pixels += 1 # another one in the box
			for c in range(channels):
				sample[c] += pixel[c]
	# average out totals
	for c in range(channels):
		sample[c] = round(sample[c]/total_pixels)
	return tuple(sample)

# --- padding ---
def start_padding_process(image):
	padding_type = choose_padding_type()
	print()
	pad_dimensions = get_pad_width(image)
	if not list_all_null(pad_dimensions):
		print()
		print('Padding...')
		image = pad_image(image, pad_dimensions, padding_type)
	return image

class PaddingType():
	ZERO = 0
	CIRCULAR = 1
	REFLECTED = 2

def choose_padding_type():
	choices = ['Zero-Padding', 'Circular-Indexing', 'Reflected-Indexing']
	return choose_option(choices, 'Padding Type:')

def get_pad_width(cur_image): # top, bottom, left, right
	return get_dimension_offsets(cur_image, 'Padding Width:', 'Pad ')

def pad_image(source_image, pad_dims, padding_type=PaddingType.ZERO):
	pad_dims = read_offsets(pad_dims)
	width, height = source_image.size
	# new image bounds
	new_width = width + pad_dims[2] + pad_dims[3]
	new_height = height + pad_dims[0] + pad_dims[1]
	padded_image = Image.new(mode=source_image.mode, size=(new_width,new_height))
	color_black = BLACK
	if source_image.mode == 'L':
		color_black = 0
	# fill new image based on padding type
	for x in range(new_width):
		for y in range(new_height):
			# get pixel data
			pixel = color_black # default
			relative_x = x - pad_dims[2]
			relative_y = y - pad_dims[0]
			# circular
			if padding_type == PaddingType.CIRCULAR:
				pixel = source_image.getpixel((relative_x % width, relative_y % height))
			# reflected
			elif padding_type == PaddingType.REFLECTED:
				u = relative_x
				v = relative_y
				if (relative_x // width) % 2 == 1: # reflected x
					u = (width - 1) - relative_x
				if (relative_y // height) % 2  == 1: # reflected y
					v = (height - 1) - relative_y
				pixel = source_image.getpixel((u % width, v % height))
			# zero-padding
			else:
				# in bounds of original - use same pixel
				if relative_x >= 0 and relative_x < width:
					if relative_y >= 0 and relative_y < height:
						pixel = source_image.getpixel((relative_x, relative_y))
			# place pixel
			padded_image.putpixel((x,y), pixel)
	return padded_image