from PIL import Image
import matplotlib.pyplot as plt
from .image_helpers import (print_image_size, print_continue, choose_option, get_channels, get_total_pixels, clamp_intensity)

# --- pixel intensity histogram ---
def start_histogram_display_process(image):
	n = get_bins()
	print()
	alg = choose_histogram_type()
	print()
	format = choose_histogram_frequency()
	print()
	if alg == 0:
		print_histogram_data(image, n, format)
	else:
		show_histogram(image, n, format)
	return image

def get_bins():
	max_bins = 256
	min_bins = 1
	valid_response = False
	while not valid_response:
		response = input('Number of Bins: ')
		try:
			x = int(response)
			if min_bins <= x and x <= max_bins:
				return x
			else:
				print('enter 1-256')
		except Exception as e:
			print('enter 1-256')

def choose_histogram_type():
	choices = ['Text-Based', 'Plot']
	return choose_option(choices, 'Histogram Type:')

def choose_histogram_frequency():
	choices = ['Pixels (total)', 'Percent (of all pixels in the image)']
	return choose_option(choices, 'Frequency Format:')

def get_histogram_data(image, bins, frequency_type=0):
	channels = get_channels(image.getpixel((0,0)))
	# key 	-> bin index (left to right)
	# value -> total pixels in bin
	data = {}
	if bins < 1:
		bins = 1
	elif bins > 256:
		bins = 256
	# width of each bin
	interval_width = 256 / bins
	# default bin totals
	for i in range(bins):
		data[i] = [0] * channels
	# place each pixel into bin based on intensity
	for x in range(image.width):
		for y in range(image.height):
			pixel = image.getpixel((x,y))
			for c in range(channels):
				if channels == 1: # grayscale
					intensity = pixel
				else:
					intensity = pixel[c]
				i = int(intensity / interval_width) # round down
				data[i][c] += 1
	# get percents
	if frequency_type == 1:
		total_pixels = get_total_pixels(image)
		for i in range(bins):
			for c in range(channels):
				data[i][c] /= total_pixels
				data[i][c] = data[i][c] * 100
	return data

def print_histogram_data(image, num_bins=10, frequency_type=0):
	channels = get_channels(image.getpixel((0,0)))
	interval_width = 256 / num_bins # width that each bin spans (amount of intensities covered) 
	data = get_histogram_data(image, num_bins, frequency_type)
	# display data
	if channels == 1:
		print('interval: pixel count')
	else:
		print('interval: pixel count for each channel (RBG)')
	for i, count in data.items():
		lower = int(i*interval_width) # starting point for bin
		upper = int((i+1)*interval_width) - 1 # just before next bin starts
		if channels == 1: # grayscale
			print(f'[{lower}, {upper}]: {round(count[0])}')
		else: # rgb
			print(f'[{lower}, {upper}]: {round(count[0])} {round(count[1])} {round(count[2])}')
	print()
	print_continue()

def show_histogram(image, num_bins=10, frequency_type=0):
	print('Generating Histogram of Pixel Intensities...')
	print_image_size(image)
	channels = get_channels(image.getpixel((0,0)))
	# get pixel counts for each intensity
	data = get_histogram_data(image, num_bins, frequency_type)
	interval_width = 256 / num_bins
	intervals = [] # names of each interval
	for i in data.keys():
		# get interval range - upper and lower bound
		lower = int(i*interval_width)
		upper = int((i+1)*interval_width) - 1
		intervals.append(f'{lower} - {upper}')
	# set histogram
	# adjust spacing
	fig, ax = plt.subplots(figsize=(8, 6))
	fig.subplots_adjust(left=0.15, right=0.8)
	# labels
	plt.title('Image Histogram', pad=20)
	if frequency_type == 1: # by percent
		plt.ylabel('Percent of Pixels', labelpad=10)
	else: # by pixel counts
		plt.ylabel('Pixel Count', labelpad=10)
	if channels == 1:
		plt.xlabel('Grayscale Value', labelpad=10)
	else:
		plt.xlabel('Intensity Value', labelpad=10)
	# add data
	intensities = data.values()
	if channels >= 3: # RGB
		bar_width = 0.25 # each x value has room for (3 bars + 1 space)
		bars_a = [x for x in range(len(intervals))]
		bars_b = [b + bar_width for b in bars_a]
		bars_c = [b + bar_width for b in bars_b]
		plt.bar(bars_a, [i[0] for i in intensities], width=bar_width, color='red', alpha=0.5, label='R')
		plt.bar(bars_b, [i[1] for i in intensities], width=bar_width, color='green', alpha=0.5, label='G')
		plt.bar(bars_c, [i[2] for i in intensities], width=bar_width, color='blue', alpha=0.5, label='B')
		plt.xticks(bars_b, intervals, rotation=45, ha='right')
		plt.legend(loc='upper right')
		plt.subplots_adjust(bottom=0.25)
		plt.tight_layout()
	else: # grayscale
		plt.bar(intervals, [i[0] for i in intensities], color='gray', alpha=0.5)
		plt.xticks(range(len(intervals)), intervals, rotation=45, ha='right')
		plt.subplots_adjust(bottom=0.25)
	# open plot
	plt.show()
	return True

# --- histogram equalization ---
def start_histogram_equalization_process(image):
	print('Equalizing Image...')
	image = histogram_equalization(image)
	return image

def histogram_equalization(image):
	width, height = image.size
	channels = get_channels(image.getpixel((0,0)))
	equalized_image = Image.new(mode=image.mode, size=(width,height))
	# get histogram with 256 bins
	histogram = [[] for _ in range(channels)] # each element is a new bin of width 1
	for c in range(channels):
		while len(histogram[c]) < 256:
			histogram[c].append(0)
	for x in range(width):
		for y in range(height):
			pixel = image.getpixel((x,y))
			for c in range(channels):
				if channels == 1:
					intensity = pixel
				else:
					intensity = pixel[c]
				histogram[c][intensity] += 1 # add to total
	# normalize histogram (divide by total pixels)
	total_pixels = width * height
	for i in range(256):
		for c in range(channels):
			histogram[c][i] /= total_pixels
	# cumulative distribution function
	def cdf(nh, intensity):
		total = 0
		for i in range(intensity+1):
			total += nh[i]
		return total
	# equalize image
	for x in range(width):
		for y in range(height):
			source_pixel = image.getpixel((x,y))
			new_pixel = [0]*channels
			for c in range(channels):
				if channels == 1:
					source_channel = source_pixel
				else:
					source_channel = source_pixel[c]
				new_pixel[c] = 255 * cdf(histogram[c], source_channel)
				new_pixel[c] = clamp_intensity(round(new_pixel[c]))
			if channels > 1:
				new_pixel = tuple(new_pixel)
			else:
				new_pixel = new_pixel[0]
			equalized_image.putpixel((x,y), new_pixel)
	return equalized_image