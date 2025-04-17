from PIL import Image
from .image_helpers import (print_image_size, choose_option, get_value, get_channels, clamp_intensity)
from .image_basics import (PaddingType, pad_image, crop_image)

# --- convolutions ---
def start_convolution_process(image):
	kernel_size = get_kernel_size(image)
	print()
	kernel_scale = get_kernel_scale()
	print()
	kernel_matrix = get_kernel_matrix(kernel_size)
	print()
	print('Performing Convolution...')
	# first pad the image
	pad_w, pad_h = kernel_size
	pad_w //= 2
	pad_h //= 2
	pad_dims = (pad_h, pad_h, pad_w, pad_w)
	image = pad_image(image, pad_dims, PaddingType.REFLECTED)
	# next apply the matrixs
	image = convolve(image, kernel_matrix, kernel_scale)
	# cut off padding
	image = crop_image(image, pad_dims)
	return image

def get_kernel_size(image): # (width, height)
	print_image_size(image)
	print('Kernel Size')
	kernel_size = [0,0]
	kernel_size[0] = get_value(1, image.width, 'Width', integer=True, default=3)
	kernel_size[1] = get_value(1, image.height, 'Height', integer=True, default=3)
	return tuple(kernel_size)

def get_kernel_scale():
	print('Kernel Scaling Factor:')
	print('(the kernel matrix will be multiplied by this scale)')
	return get_value(-20, 20, '>', default=1)

def get_kernel_matrix(size):
	width, height = size
	convolution_matrix = []
	print('Enter the kernel entries of each row, separated by whitespace.')
	print(f'Kernel Size - {width} x {height}')
	for i in range(height):
		while True:
			response = input(f'Row {i+1}: ')
			tokens = response.split()
			if len(tokens) < size[0]:
				print('not enough entries')
				continue
			elif len(tokens) > size[0]:
				print('too many entries')
				continue
			weight_list = []
			invalid_coefficient = False
			for coefficient in tokens:
				try:
					x = float(coefficient)
					weight_list.append(x)
				except Exception as e:
					print('invalid coefficient read')
					invalid_coefficient = True
					break
			if invalid_coefficient:
				continue
			# success
			convolution_matrix.append(weight_list)
			break
	return convolution_matrix

# kernel is matrix: [[row],[row],...,[row]]
def convolve(image, kernel, scale=1):
	width, height = image.size
	channels = get_channels(image.getpixel((0,0))) # number of color channels of source image
	# create convolved image
	new_image = Image.new(mode=image.mode, size=(width,height))
	kernel_width = len(kernel[0])
	kernel_height = len(kernel)
	# apply convolution matrix
	for i in range(width):
		for k in range(height):
			output_pixel = [0]*channels # weighted sum for each color channel
			for y in range(kernel_height):
				for x in range(kernel_width):
					# get location of next pixel in source image to sum
					# (center of matrix gets shifted to the right/down if even dimensions)
					source_x = i - kernel_width//2 + x
					source_y = k - kernel_height//2 + y
					# location exists in source image?
					if source_x < 0 or source_x > (width-1):
						continue
					elif source_y < 0 or source_y > (height-1):
						continue
					source_pixel = image.getpixel((source_x,source_y))
					if channels == 1:
						output_pixel[0] += source_pixel*kernel[y][x]
					else: # rgb
						for c in range(channels):
							output_pixel[c] += source_pixel[c]*kernel[y][x]
			# scale by matrix coefficient
			if channels == 1:
				output_pixel[0] *= scale
			else: # rgb
				for c in range(channels):
					output_pixel[c] *= scale
			# handle out of bound intensities + convert to integer
			for c in range(channels):
				output_pixel[c] = clamp_intensity(round(output_pixel[c]))
			# place the output pixel
			if channels > 1:
				new_image.putpixel((i,k), tuple(output_pixel))
			else:
				new_image.putpixel((i,k), output_pixel[0])
	return new_image

# --- non-linear filtering ---
def start_non_linear_filter_process(image):
	filter_type = choose_non_linear_filter()
	print()
	filter_size = get_kernel_size(image)
	print()
	print('Filtering...')
	image = non_linear_filter(image, filter_size, filter_type)
	return image

def median(numbers):
	sorted_numbers = sorted(numbers)
	n = len(sorted_numbers)
	# even length - average middle values
	if n % 2 == 0:
		return (sorted_numbers[n//2] + sorted_numbers[n//2 - 1]) / 2
	# odd length - middle value
	else:
		return sorted_numbers[n//2]
	
def choose_non_linear_filter():
	choices = ['Min', 'Max', 'Median']
	return choose_option(choices, 'Filter:')

def non_linear_filter(image, filter_size, filter_type=0):
	width, height = image.size
	channels = get_channels(image.getpixel((0,0))) # number of color channels of source image
	# create filtered image
	new_image = Image.new(mode=image.mode, size=(width,height))
	# set up filter - to screen the list of values
	filter = min
	if filter_type == 1:
		filter = max
	elif filter_type == 2:
		filter = median
	filter_width = filter_size[0]
	filter_height = filter_size[1]
	# apply non-linear filter
	for i in range(width):
		for k in range(height):
			channel_values = [[] for c in range(channels)] # list of values for each color channel
			# move through the filter centered at (i,k)
			for y in range(filter_height):
				for x in range(filter_width):
					# get location of next pixel in source image to sum
					source_x = i - filter_width//2 + x
					source_y = k - filter_height//2 + y
					# location exists in source image?
					if source_x < 0 or source_x > (width-1):
						continue
					elif source_y < 0 or source_y > (height-1):
						continue
					source_pixel = image.getpixel((source_x,source_y))
					if channels == 1:
						channel_values[0].append(source_pixel)
						continue
					for c in range(channels):
						channel_values[c].append(source_pixel[c])
			# apply filter - choose filtered value from list of values, for each channel
			output_pixel = [0]*channels
			for c in range(channels):
				output_pixel[c] = filter(channel_values[c])
				output_pixel[c] = clamp_intensity(round(output_pixel[c]))
			# place the output pixel
			if channels > 1:
				new_image.putpixel((i,k), tuple(output_pixel))
			else:
				new_image.putpixel((i,k), output_pixel[0])
	return new_image