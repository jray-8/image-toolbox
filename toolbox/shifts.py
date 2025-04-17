import math
import random
from .image_helpers import (choose_option, get_value, get_dimension_names)
from .color import BLACK

# positive shift -> shifts left
def pixel_shift(pixel_list, shift, circular=True, randomize_shift=False, randomize_dir=False, segments=False):
	if not pixel_list:
		return
	if randomize_shift: # choose random shift value
		shift = random.randint(0, len(pixel_list) - 1)
	else:
		shift = math.ceil(shift) # can only shift a whole number of pixels (round up)
		if circular:
			shift %= len(pixel_list) # in range of list indices (loops around)
	# randomize direction of shift
	if randomize_dir and random.random() < 0.5:
		shift *= -1
	# rotate shift
	if circular:
		pixel_list[:] = pixel_list[shift:] + pixel_list[:shift]
	else: # blank shift (cuts off)
		line_length = len(pixel_list)
		shifted_pixels = abs(shift)
		blank_unit = BLACK # null pixel
		if segments: # null segment
			blank_unit = [BLACK] * len(pixel_list[0]) # assume segments all have equal length
		empty_strip = [blank_unit] * min(shifted_pixels, line_length) # void area where pixels were shifted away from
		if shift >= 0:
			pixel_list[:] = pixel_list[shift:] + empty_strip
		else: # negative
			pixel_list[:] = empty_strip + pixel_list[:shift]

def rotate_shift(pixel_list, shift, rand_shift=False, rand_dir=False):
	return pixel_shift(pixel_list, shift, circular=True, randomize_shift=rand_shift, randomize_dir=rand_dir)

def blank_shift(pixel_list, shift, rand_shift=False, rand_dir=False, shift_segments=False):
	return pixel_shift(pixel_list, shift, circular=False, randomize_shift=rand_shift, randomize_dir=rand_dir, segments=shift_segments)

def choose_shift_dir(dir_index=2):
	dim_names = get_dimension_names(dir_index)
	choices = [dim_names[0], dim_names[1], 'Random']
	direction = choose_option(choices, 'Shift Direction:')
	if direction == 0:
		return 1
	elif direction == 1:
		return -1
	else: # use random dir
		return 0
	
def get_shift_percent():
	print('Enter 0 for randomized shift values.')
	return get_value(0, 100, 'Shift (%)', default=20) / 100

def choose_pixel_shifter(width, height, rotate, direction_index, horizontal_first=True, use_segments=False):
	shift_dir = choose_shift_dir(direction_index)
	print()
	p_shift = get_shift_percent()
	print()
	horizontal_shift = width * p_shift * shift_dir
	vertical_shift = height * p_shift * shift_dir
	# use random dir / shift
	random_dir = False
	random_shift = False
	if shift_dir == 0:
		random_dir = True
	if p_shift == 0:
		random_shift = True
	# assign new shift function
	shift = horizontal_shift if horizontal_first else vertical_shift
	next_shift = vertical_shift if horizontal_first else horizontal_shift
	if rotate:
		shifter_1 = lambda pxlist: rotate_shift(pxlist, shift, random_shift, random_dir)
		shifter_2 = lambda pxlist: rotate_shift(pxlist, next_shift, random_shift, random_dir)
	else:
		shifter_1 = lambda pxlist: blank_shift(pxlist, shift, random_shift, random_dir, shift_segments=use_segments)
		shifter_2 = lambda pxlist: blank_shift(pxlist, next_shift, random_shift, random_dir, shift_segments=use_segments)
	return (shifter_1, shifter_2)
