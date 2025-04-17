import math
import random
from .image_helpers import (choose_option, choose_direction, get_value, get_pixel_rows, get_pixel_columns, divide_list, merge_groups,
			    			place_segments, get_dimension_names)
from .shifts import (rotate_shift, blank_shift)

# --- wave warp ---
def start_wave_warp_process(image):
	width, height = image.size
	wave_dir = choose_wave_direction()
	print()
	horizontal = True
	if wave_dir in [1,3]: # vertical
		horizontal = False
	repetitions = 1
	if wave_dir in [2,3]:
		repetitions = 2
	wave_shift_1, wave_shift_2 = choose_wave_shifter(width, height, not horizontal) # shift opposite direction of wave
	print('Creating Waves...')
	# apply wave shift to all lines
	for _ in range(repetitions):
		image = wave_warp(image, wave_shift_1, horizontal)
		# switch wave directions
		horizontal = not horizontal
		wave_shift_1, wave_shift_2 = wave_shift_2, wave_shift_1
	return image

def wave_warp(image, wave_shifter, horizontal):
	if horizontal:
		lines = get_pixel_columns(image)
	else:
		lines = get_pixel_rows(image)
	# shift all lines
	for next_line in lines:
		wave_shifter(next_line)
	place_segments(image, lines, not horizontal) # horizontal waves shifts columns...
	return image

def choose_wave_shifter(width, height, horizontal_first=True): # wave_shifter_1 will shift horizontally
	type_of_wave = choose_wave_type()
	print()
	p_period = get_wave_period() # [0,1]
	print()
	rand_period = False
	horizontal_period = (height * p_period) * math.pi / 2
	vertical_period = (width * p_period) * math.pi / 2
	if p_period == 0:
		rand_period = True
	p_amplitude = get_wave_amplitude() # [0,1]
	print()
	horizontal_amp = width * p_amplitude
	vertical_amp = height * p_amplitude
	is_circular = choose_wave_wraparound()
	print()
	# build wave shift functions for each direction - horizontal waves -> vertical wave shifts
	amplitude = horizontal_amp if horizontal_first else vertical_amp
	period = horizontal_period if horizontal_first else vertical_period
	next_amplitude = vertical_amp if horizontal_first else horizontal_amp
	next_period = vertical_period if horizontal_first else horizontal_period
	wave_shifter_1 = make_wave_shift(amplitude, period, wave_type=type_of_wave, circular=is_circular, randomize_period=rand_period)
	wave_shifter_2 = make_wave_shift(next_amplitude, next_period, wave_type=type_of_wave, circular=is_circular, randomize_period=rand_period)
	return (wave_shifter_1, wave_shifter_2)

class WaveType():
	SIN = 0
	TRIANGLE = 1
	SQUARE = 2
	SAWTOOTH = 3

def sin_function(x, amplitude, angular_frequency):
	k = angular_frequency
	return amplitude * math.sin(k*x)

def triangle_function(x, amplitude, period):
	a = amplitude
	p = period
	return (4*a)/p * abs(((x - p/4) % p) - p/2) - a

def square_function(x, amplitude, period):
	hp = period / 2 # half period
	return amplitude * (-2 * ((x // hp) % 2) + 1)

def sawtooth_function(x, amplitude, period):
	a = amplitude
	p = period
	return ((2*a*x / p) - a) % (2*a) - a
	
def make_wave_shift(amplitude, period, wave_type=WaveType.SIN, circular=False, randomize_period=False):
	wave_x = 0 # current x-value of the wave function - start from origin
	def wave_shift(pixel_list):
		nonlocal wave_x # want to modify outside variable
		nonlocal period
		if randomize_period:
			period = 2 * math.pi
		# get shift based on height of the wave function
		frequency = (2 * math.pi) / period # k value
		if wave_type == WaveType.SIN:
			shift = sin_function(wave_x, amplitude, frequency)
		elif wave_type == WaveType.TRIANGLE:
			shift = triangle_function(wave_x, amplitude, period)
		elif wave_type == WaveType.SQUARE:
			shift = square_function(wave_x, amplitude, period)
		elif wave_type == WaveType.SAWTOOTH:
			shift = sawtooth_function(wave_x, amplitude, period)
		else:
			shift = 0
			print('Unknown Wave Type...\n')
		# apply the shift
		if circular:
			rotate_shift(pixel_list, shift)
		else:
			blank_shift(pixel_list, shift)
		# move to next wave x position - moves in quarter ps at an angular frequency of 1
		wave_x += (math.pi / 2)
	# a unique wave shift function
	return wave_shift

def get_wave_period():
	# P - period (in pixels)
	# T - period (in radians)
	# Let 2 pixels = normal period (2pi)
	# T = pi * P
	print('Enter 0 to randomized period.')
	p = get_value(0, 100, 'Wave Period (%)', default=15) / 100
	return p

def get_wave_amplitude():
	print('Enter 0 to use a random amplitude.')
	x = get_value(0, 100, 'Wave Amplitude - max shift (%)', default=50)
	if x == 0: # get random
		x = random.randint(1, 100)
		print(f'{x} (random)')
	return x / 100

def choose_wave_wraparound():
	choices = ['Circular', 'Cut-Off']
	x = choose_option(choices, 'Wave Wraparound:')
	if x == 0:
		return True
	else:
		return False

def choose_wave_type():
	choices = ['Sin', 'Triangle', 'Square', 'Sawtooth']
	return choose_option(choices, 'Wave Type:')

def choose_wave_direction():
	return choose_direction('Wave Direction:')

# --- mirror ---
def start_mirror_process(image):
	mirror_dir = choose_mirror_direction()
	print()
	horizontal = True
	if mirror_dir in [1,3]: # vertical
		horizontal = False
	repetitions = 1
	if mirror_dir in [2,3]:
		repetitions = 2
	num_mirrors = get_num_mirrors()
	print()
	reflected_side = choose_reflected_side(mirror_dir)
	print()
	print('Reflecting...')
	for _ in range(repetitions):
		image = mirror(image, num_mirrors, reflect_horizontal=horizontal, reflect_index=reflected_side)
		horizontal = not horizontal # change directions
	return image

def choose_mirror_direction():
	choices = ['Horizontal', 'Vertical', 'Cross']
	print('A horizontal reflection will reflect over a vertical line.')
	return choose_option(choices, 'Reflection:')

def choose_reflected_side(dir_index):
	dim_names = get_dimension_names(dir_index)
	choices = [dim_names[0], dim_names[1], 'Random']
	return choose_option(choices, 'Reflect Which Side?')

def get_num_mirrors():
	return get_value(1, 10, 'Number of Mirrors', integer=True)

# reflect_index - 0=left/top, 1=right/bottom, 2=random
def mirror(image, num, reflect_horizontal=True, reflect_index=0):
	if reflect_horizontal:
		lines = get_pixel_columns(image)
	else:
		lines = get_pixel_rows(image)
	# group into sections
	groups = divide_list(lines, num)
	# reflect
	for next_group in groups:
		half_size = len(next_group) // 2 # half number of lines (rounded down)
		keep_left = True
		if reflect_index == 1: # keep right
			keep_left = False
		elif reflect_index == 2 and random.random() < 0.5: # random
			keep_left = False
		# keep left/top side
		if keep_left:
			next_group[:] = next_group[:-half_size] + list(reversed(next_group[:half_size]))
		# keep right/bottom side
		else:
			next_group[:] = list(reversed(next_group[-half_size:])) + next_group[half_size:]
	# merge groups - back to lines
	lines = merge_groups(groups)
	place_segments(image, lines, horizontal=(not reflect_horizontal))
	return image