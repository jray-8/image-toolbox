import os
import math

# alignemnt in 1 dimension
class Alignment():
	NONE = 0
	START = 1 # left / top
	END = 2 # right / bottom
	CENTER = 3

# --- Print Functions ---
def print_image_size(image):
	width, height = image.size
	print(f'Image - {width} x {height}')

def print_continue():
	input('<< continue >> ')

# --- Input Functions ---
# get type of algorithm to use
def choose_option(choices, title='Options:', default=0):
	num_choices = len(choices)
	if num_choices <= 0:
		return
	valid_reponse = False
	while not valid_reponse:
		print(title)
		for i in range(num_choices):
			print(f' ({i}) - {choices[i]}')
		response = input('> ').strip().lower()
		# default response
		if not response:
			if default < 0:
				default = 0
			elif default > (num_choices - 1):
				default = num_choices - 1
			print(f'{default} (default)')
			return default
		try: # extract response
			x = int(response)
			if 0 <= x and x < num_choices:
				return x
		except Exception as e:
			valid_reponse = False
		# invalid input
		msg = f'must choose {0}'
		if num_choices > 1:
			msg += f'-{num_choices-1}'
		print(f'{msg}\n')

# get float or int within a range
def get_value(min_val, max_val, prompt='Value', integer=False, default=None, symbols=[]):
	valid_response = False
	message = f'{prompt} [{min_val}, {max_val}]: '
	while not valid_response:
		response = input(message).strip().lower()
		# default
		if not response:
			if default == None: # use min
				default = min_val
			elif default > max_val:
				default = max_val
			elif default < min_val:
				default = min_val
			if integer:
				default = default
			print(f'{default} (default)')
			return default
		elif response in symbols:
			return response
		try: # extract value
			if integer:
				x = int(response)
			else:
				x = read_fraction(response)
				if x == None:
					raise ValueError('could not read fraction')
			# check range
			if min_val <= x and x <= max_val:
				return x
			else:
				print('not in range\n')
		except Exception as e:
			if integer:
				print('must be an integer\n')
			else:
				print('must be float\n')

# read a fraction from a string - return float
def read_fraction(string):
	temp = string.split('/') # x/y
	x = temp[0]
	y = 1
	if len(temp) > 2:
		return None
	elif len(temp) == 2:
		y = temp[1]
	# convert to values
	try:
		x = float(x)
		y = float(y)
	except Exception as e:
		return None
	# valid fraction
	return x/y

def choose_yes_no(prompt, default=''):
	while True:
		response = input(f'{prompt} (y/n): ').strip().lower()
		if not response: # use default
			response = default
			print(f'{default} (default)')
		if response in ['y','yes']:
			return True
		elif response in ['n','no']:
			return False
		else:
			print('invalid response\n')

# get offsets for each side - top -> bottom -> left -> right
def get_dimension_offsets(cur_image, title='Offsets:', offset_prompt=''):
	print_image_size(cur_image)
	print(title)
	offsets = [0]*4 # top, bottom, left, right
	dimension_names = ['Top', 'Bottom', 'Left', 'Right']
	dim_index = 0
	for dim_index in range(4):
		valid_response = False
		while not valid_response:
			response = input(f'{offset_prompt}{dimension_names[dim_index]}: ').strip().lower()
			if not response:
				print('0 (default)')
				offsets[dim_index] = 0
				break
			try:
				offsets[dim_index] = int(response)
				valid_response = True
			except Exception as e:
				print('offset must be integer\n')
	return offsets

# get a width and height
def get_dimensions(cur_image):
	print_image_size(cur_image)
	dim = [0,0]
	dim_names = ['Width', 'Height']
	# get dimensions
	for i in range(2):
		valid_response = False
		while not valid_response:
			response = input(f'New {dim_names[i]}: ').strip().lower()
			if not response: # default response
				if i == 0: # width
					x = cur_image.width
				else:
					x = cur_image.height
				print(f'{x} (default)')
				dim[i] = x
				break
			try:
				x = int(response)
				if x > 0:
					valid_response = True
					dim[i] = x
				else:
					print(f'{dim_names[i].lower()} >= 0\n')
			except Exception as e:
				print('not an integer\n')
				continue
	return tuple(dim)

def choose_direction(prompt='Direction:'):
	choices = ['Horizontal', 'Vertical', 'Cross 1', 'Cross 2']
	return choose_option(choices, title=prompt)

def get_image_file(prompt='Enter Image File:'):
	while True:
		print(prompt)
		path = input('> ').strip()
		if path == '0':
			return None
		if os.path.isfile(path):
			return path
		else:
			print('could not access image - enter 0 to cancel or try again\n')

# --- Helper Functions ---
# get linear array of all pixels - row by row (left to right) / col by col (top to bottom)
def get_pixel_array(image, horizontal=True):
	width, height = image.size
	pixel_array = []
	dim_a = height if horizontal else width
	dim_b = width if horizontal else height
	for y in range(dim_a): # rows/cols
		for x in range(dim_b): # scan horizontally/vertically
			if horizontal:
				pixel = image.getpixel((x,y))
			else: # x scans vertically
				pixel = image.getpixel((y,x))
			pixel_array.append(pixel)
	return pixel_array

# break pixel array into segments
def segment_pixels(pixel_array, segment_size):
	segments = []
	for i in range(0, len(pixel_array), segment_size):
		segments.append(pixel_array[i:i+segment_size])
	return segments

def get_pixel_rows(image):
	width, _ = image.size
	pixel_array = get_pixel_array(image, horizontal=True)
	row_array = segment_pixels(pixel_array, width)
	return row_array

def get_pixel_columns(image):
	_, height = image.size
	pixel_array = get_pixel_array(image, horizontal=False)
	row_array = segment_pixels(pixel_array, height)
	return row_array

# fill the image with pixels from the list in horizontal (or vertical) fashion
# segment_list is an array of grouped pixels (lists)
def place_segments(image, segment_list, horizontal):
	i = -1
	for segment in segment_list:
		i = place_pixels(image, segment, horizontal, index=i)
	return i

def place_pixels(image, pixel_list, horizontal, index=-1):
	width, height = image.size
	for pixel in pixel_list:
		index += 1 # next pixel
		if horizontal:
			x = index % width
			y = index // width
		else: # vertical
			y = index % height
			x = index // height
		image.putpixel((x,y), pixel)
	return index

# number of color channels of a pixel
def get_channels(pixel):
	channels = 1
	if isinstance(pixel, (list, tuple)):
		channels = len(pixel)
	return channels

def get_total_pixels(image):
	width, height = image.size
	return width * height

def get_brightness(pixel):
	if not isinstance(pixel, (list, tuple)): # grayscale
		return pixel
	# luminosity method
	brightness = round(0.299*pixel[0] + 0.587*pixel[1] + 0.114*pixel[2])
	return clamp_intensity(brightness)

def get_dimension_names(dir_index): # one dimension - from start to end
	dim_start = 'Left/Top'
	dim_end = 'Right/Bottom'
	if dir_index == 0: # horizontal
		dim_start = 'Left'
		dim_end = 'Right'
	elif dir_index == 1: # vertical
		dim_start = 'Top'
		dim_end = 'Bottom'
	return (dim_start, dim_end)

def divide_list(my_list, num_groups):
	list_length = len(my_list)
	group_size = list_length / num_groups
	groups = [] # store sections of the list
	# track how many items have been grouped so far
	elems_covered = 0
	prev_index = 0
	while elems_covered < (list_length - 1):
		elems_covered += group_size
		index = math.ceil(elems_covered)
		next_group = my_list[prev_index:index]
		groups.append(next_group)
		prev_index = index
	return groups

def merge_groups(groups):
	merged_list = []
	for next_group in groups:
		merged_list.extend(next_group)
	return merged_list

# --- Bounds and Data Checking ---
def clamp_intensity(i):
	if i < 0:
		i = 0
	elif i > 255:
		i = 255
	return i

def round_pixel(pixel): # float to int data
	channels = get_channels(pixel)
	new_pixel = [0] * channels
	if channels == 1:
		return clamp_intensity(round(pixel))
	else:
		for c in range(channels):
			new_pixel[c] = clamp_intensity(round(pixel[c]))	
	return tuple(new_pixel)

def normalize_pixel(pixel):
	channels = get_channels(pixel)
	if channels == 1:
		return pixel / 255
	normal_pixel = [pixel[c] / 255 for c in range(channels)]
	return normal_pixel

def denormalize_pixel(normal_pixel):
	channels = get_channels(normal_pixel)
	if channels == 1:
		return normal_pixel * 255
	pixel = [normal_pixel[c] * 255 for c in range(channels)]
	return pixel

def to_radians(degrees):
	return (degrees / 180) * math.pi

def to_degrees(radians):
	return (radians / math.pi) * 180

def read_offsets(offsets):
	if isinstance(offsets, int): # equally on all sides
		offsets = [offsets] * 4 
	elif len(offsets) == 2: # equal width and equal height
		temp = [offsets[0]] * 2
		temp.extend([offsets[1]] * 2)
		offsets = temp
	return offsets

# list contains all null values (0, False, None, ...)
def list_all_null(value_list):
	for v in value_list:
		if v:
			return False
	return True