from PIL import Image
from .image_helpers import (choose_option, get_value, get_channels, clamp_intensity)
from .color import BLACK

# --- transformations ---
def start_transformation_process(image):
	alg = choose_transformation()
	print()
	a=1; b=0; y=1
	if alg == 0:
		a = get_alpha()
		print()
		b = get_beta()
	elif alg == 2:
		y = get_gamma()
	if alg != 1:
		print()
	print('Transforming...')
	image = apply_transformation(image, alg, a, b, y)
	return image

def choose_transformation():
	choices = ['Linear', 'Negative', 'Power-Law']
	return choose_option(choices, 'Mapping Type:')

def get_alpha():
	a_min = -5
	a_max = 5
	return get_value(a_min, a_max, 'Alpha', default=1)

def get_beta():
	return get_value(-100, 100, 'Beta (%)', default=0) / 100

def get_gamma():
	min_val = 0.04
	max_val = 25
	return get_value(min_val, max_val, 'Gamma', default=1)

def linear_transformation(pixel, alpha, beta): # beta is [0,1]
	channels = get_channels(pixel)
	new_pixel = [0] * channels
	for i in range(channels):
		if channels == 1:
			new_pixel[i] = clamp_intensity(round(alpha*pixel + beta * 255))
		else:
			new_pixel[i] = clamp_intensity(round(alpha*pixel[i] + beta * 255))
	if channels == 1:
		return new_pixel[0]
	return tuple(new_pixel)

def negative_transformation(pixel):
	channels = get_channels(pixel)
	new_pixel = [0] * channels
	for i in range(channels):
		if channels == 1:
			new_pixel[i] = 255 - pixel
		else:
			new_pixel[i] = 255 - pixel[i]
	if channels == 1:
		return new_pixel[0]
	return tuple(new_pixel)

def power_law_transformation(pixel, gamma=1.5, c=1):
	channels = get_channels(pixel)
	new_pixel = [0] * channels
	for i in range(channels):
		# normalize intensity [0,255] -> [0,1]
		if channels == 1:
			intensity = pixel / 255
		else:
			intensity = pixel[i] / 255
		# power-law scale
		new_pixel[i] = clamp_intensity(round(c * 255 * (intensity ** gamma)))
	if channels == 1:
		return new_pixel[0]
	return tuple(new_pixel)

def apply_transformation(image, transformation=0, alpha=1, beta=0, gamma=1):
	width, height = image.size
	transformed_image = Image.new(image.mode, size=(width,height))
	color_black = BLACK
	if image.mode == 'L':
		color_black = 0
	# fill in scaled image
	for i in range(width):
		for k in range(height):
			source_pixel = image.getpixel((i,k))
			# get pixel data
			transformed_pixel = color_black
			if transformation == 0: # linear
				transformed_pixel = linear_transformation(source_pixel, alpha, beta)
			elif transformation == 1: # negative linear
				transformed_pixel = negative_transformation(source_pixel)
			elif transformation == 2: # power-law
				transformed_pixel = power_law_transformation(source_pixel, gamma)
			# place pixel
			transformed_image.putpixel((i,k), transformed_pixel)
	return transformed_image