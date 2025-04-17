import math
import random
from PIL import Image
from .image_helpers import (Alignment,
					print_image_size,
					choose_option,
					choose_direction,
					choose_yes_no,
					get_value, 
					get_total_pixels, 
					get_pixel_array,
					get_pixel_rows,
					get_pixel_columns,
					segment_pixels,
					place_segments,
					get_brightness,
					get_dimension_names,
					divide_list,
					merge_groups)
from .shifts import (pixel_shift, rotate_shift, blank_shift, choose_pixel_shifter)
from .warps import (make_wave_shift, choose_wave_shifter)
from .blending import (BlendMode, blend_lines)

# --- line sort ---
def start_line_sort_process(image):
	segment_type = choose_segment_type()
	print()
	segment_size = get_segment_size(image, segment_type)
	print()
	sort_by_pixel = False # (by lines)
	if segment_type in [3,4]: # by pixels
		sort_by_pixel = True
	use_sort_key = False # is function used as a sort key
	sort_asc = True # ascending order
	sort_function = choose_line_sort_function()
	print()
	# create non-key functions
	next_sort_function = None
	if sort_function == random_sort: # direction does not matter
		pass
	elif sort_function == rotate_shift or sort_function == blank_shift: # create custom shift
		rotate = True if sort_function == rotate_shift else False
		horizontal_first = True if segment_type in [0,2] else False
		dim_index = 0 if segment_type in [1,3] else 1
		if segment_type == 2: # cross
			dim_index = 2
		if not sort_by_pixel:
			w = image.width / segment_size
			h = image.height / segment_size
		else: # by pixels
			total = get_total_pixels(image)
			w = total / segment_size
			h = w
		sort_function, next_sort_function = choose_pixel_shifter(w, h, rotate, dim_index, horizontal_first, use_segments=True)
	else: # key sort functions
		use_sort_key = True
		sort_asc = choose_sort_direction()
		print()
		
	print('Sorting Segments...')
	# now sort - order of rows/cols first was proven to make no difference in all cases
	if segment_type in [0,2,3]: # rows
		image = line_sort(image, sort_function, is_key=use_sort_key, horizontal=True, by_pixel=sort_by_pixel, line_width=segment_size, ascending=sort_asc)
	if next_sort_function: # swap the sort function
		sort_function = next_sort_function
	if segment_type in [1,2,4]: # cols
		image = line_sort(image, sort_function, is_key=use_sort_key, horizontal=False, by_pixel=sort_by_pixel, line_width=segment_size, ascending=sort_asc)
	return image

def choose_segment_type():
	choices = ['Rows', 'Columns', 'Crosshatch', 'Horizontal Pixels', 'Vertical Pixels']
	return choose_option(choices, 'Segment Type:')

def choose_sort_direction(): # true for ascending
	choices = ['Ascending', 'Descending']
	direction = choose_option(choices, 'Sort Direction (top-left to bottom-right):')
	if direction == 0:
		return True
	else:
		return False

def get_segment_size(image, segment_type):
	print_image_size(image)
	width, height = image.size
	if segment_type == 0: # horizontal
		max_size = height
		return get_value(1, max_size, 'How many rows?', integer=True)
	elif segment_type == 1: # vertical
		max_size = width
		return get_value(1, max_size, 'How many columns?', integer=True)
	elif segment_type == 2: # crosshatch
		max_size = min(height, width)
		return get_value(1, max_size, 'Line Width', integer=True)
	else: # pixels
		max_size = get_total_pixels(image)
		return get_value(1, max_size, 'How many pixels', integer=True)

def choose_line_sort_function():
	choices = ['Brightness Sort', 'Random Sort', 'Rotate Shift', 'Blank Shift']
	sort_type = choose_option(choices, 'Sort Method:')
	if sort_type == 0:
		return brightness_segment_sort
	elif sort_type == 1:
		return random_sort # does not matter if segment or pixel
	elif sort_type == 2:
		return rotate_shift
	elif sort_type == 3:
		return blank_shift

# segment sorting keys:
def brightness_segment_sort(segment):
	total_brightness = 0
	for pixel in segment:
		total_brightness += get_brightness(pixel)
	return total_brightness # no need to average

# is_key - is the sorting algorithm used as a comparison key. Or does it sort the segments directly
# horizontal - will the line segments be horizontal / vertical
# line_width - how thick will the line segments be (1 row, 2 rows)
# by_pixel - sort by pixel instead of lines
def line_sort(image, sort_function, is_key=True, horizontal=True, by_pixel=False, line_width=1, ascending=True):
	width, height = image.size
	# linear array of pixels - by row (or by column)
	pixel_array = get_pixel_array(image, horizontal)
	# split image into segments (rows or cols)
	segment_size = int(line_width)
	if not by_pixel:
		if horizontal:
			segment_size *= width
		else: # vertical
			segment_size *= height
	segments = segment_pixels(pixel_array, segment_size)
	# sort segments
	if is_key:
		segments.sort(key=sort_function, reverse=(not ascending)) # reversed is descending
	else: # arranged directly
		sort_function(segments)
	# place pixels in new image
	dest_image = Image.new(mode=image.mode, size=(width,height))
	place_segments(dest_image, segments, horizontal)
	return dest_image

# --- glitch sort ---
def start_glitch_sort_process(image):
	glitch_dir = choose_glitch_direction()
	print()
	horizontal = True
	if glitch_dir in [1, 3]: # vertical
		horizontal = False
	repetitions = 1
	if glitch_dir in [2, 3]: # cross
		# a complete glitch (100% frequency) in each direction gaurentees a unique state
		# - cannot be changed further by sorting in either direction
		repetitions = 2 # glitch once in each direction
	glitch_freq = get_glitch_frequency()
	print()
	glitch_cover = get_glitch_coverage()
	print()
	anchor = choose_glitch_alignment(glitch_dir)
	print()
	anchor_offset = 0
	if anchor != Alignment.NONE: # is aligned
		anchor_offset = get_alignment_offset(anchor)
		print()
	use_sort_key = False # is function used as a sort key
	sort_asc = True # ascending order
	sort_function = choose_glitch_sort_function()
	print()
	# create non-key functions
	next_sort_function = None
	if sort_function == random_sort: # direction does not matter
		pass
	# create custom shift
	elif sort_function == rotate_shift or sort_function == blank_shift:
		w = image.width * glitch_cover
		h = image.height * glitch_cover
		rotate = True if sort_function == rotate_shift else False
		sort_function, next_sort_function = choose_pixel_shifter(w, h, rotate, glitch_dir, horizontal)
	# create wave shift
	elif sort_function == make_wave_shift:
		w = image.width * glitch_cover
		h = image.height * glitch_cover
		sort_function, next_sort_function = choose_wave_shifter(w, h, horizontal_first=horizontal)
	else: # key sort functions
		use_sort_key = True
		sort_asc = choose_sort_direction()
		print()
	print('Glitch Sorting...')
	for _ in range(repetitions):
		image = glitch_sort(image, sort_function, is_key=use_sort_key, frequency=glitch_freq, coverage=glitch_cover, 
									horizontal=horizontal, ascending=sort_asc, alignment=anchor, offset=anchor_offset)
		horizontal = not horizontal # change dir
		if next_sort_function: # swap functions
			sort_function, next_sort_function = next_sort_function, sort_function
	return image

def choose_glitch_direction():
	return choose_direction('Glitch Direction:')

def get_glitch_frequency(): # [0,1]
	return get_value(0, 100, 'Glitch Frequency (%)', default=50) / 100

def get_glitch_coverage(): # [0,1]
	return get_value(0, 100, 'Glitch Coverage (%)', default=50) / 100

def choose_glitch_alignment(glitch_dir=2):
	dim_names = get_dimension_names(glitch_dir)
	choices = ['Random', dim_names[0], dim_names[1], 'Center']
	return choose_option(choices, 'Glitch Alignment (anchored at):')

def get_alignment_offset(alignment): # takes int (alignment enum)
	if alignment == Alignment.NONE: # not aligned
		return 0
	elif alignment == Alignment.CENTER:
		return get_value(-50, 50, 'Alignment Offset (%)', default=0) / 100
	else:
		return get_value(0, 100, 'Alignment Offset (%)', default=0) / 100

def choose_glitch_sort_function():
	choices = ['Brightness Sort', 'Random Sort', 'Rotate Shift', 'Blank Shift', 'Wave Shift']
	sort_type = choose_option(choices, 'Glitch Method:')
	if sort_type == 0:
		return brightness_sort
	elif sort_type == 1:
		return random_sort
	elif sort_type == 2:
		return rotate_shift
	elif sort_type == 3:
		return blank_shift
	elif sort_type == 4:
		return make_wave_shift

# pixel sorting keys:
def brightness_sort(pixel):
	return get_brightness(pixel)

# list arranger algorithms (orders list in place):
def random_sort(pixel_list):
	random.shuffle(pixel_list)

# is_key - the sorting method is used as a key to compare elements. otherwise, it sorts the line directly
# frequency - percent of lines that are affected on average
# coverage - percent of line that is rearranged
# horizontal - or vertical lines
# ascending - or descending sorted data
# alignment - glitches anchored to left/top, center, right/bottom, or are randomly placed
# offset - percent of line that the glitch is away from the aligned position
def glitch_sort(image, sort_function, is_key=True, frequency=0.5, coverage=0.5, horizontal=True, ascending=True, alignment=Alignment.NONE, offset=0):
	width, height = image.size
	if horizontal:
		image_array = get_pixel_rows(image)
	else:
		image_array = get_pixel_columns(image)
	# sort the pixels within each line
	for line in image_array:
		if random.random() <= frequency: # glitch this line
			# line_dim is the length of the entireline
			if horizontal:
				line_dim = width
			else:
				line_dim = height
			# get glitch pixels
			glitch_length = int(line_dim * coverage) # 1 extra to length
			# start of glitch effect (based on alignemnt)
			if alignment == Alignment.START: # left/top
				start = int(line_dim * offset) % line_dim
			elif alignment == Alignment.END: # right/bottom
				start = int(line_dim * (1-offset) - glitch_length) % line_dim
			elif alignment == Alignment.CENTER: # center
				start = int(line_dim * (0.5 + offset) - glitch_length / 2) % line_dim
			else: # randomize
				start = random.randint(0, line_dim-1)
			end = start + glitch_length
			wrap_around = 0 # glitch continues around the corner
			if end > line_dim:
				wrap_around = end - line_dim
				end = line_dim
			# get glitch pixels
			glitch_line = line[start:end]
			glitch_line.extend(line[0:wrap_around])
			# sort the glitch line
			if is_key:
				glitch_line.sort(key=sort_function, reverse=(not ascending))
			else:
				sort_function(glitch_line)
			# copy back to original line
			line[start:end] = glitch_line[0:(end - start)]
			line[0:wrap_around] = glitch_line[(end - start):]
		else: # this line was not glitched
			if not is_key: # still call function
				sort_function([])
	# build image
	dest_image = Image.new(mode=image.mode, size=(width,height))
	place_segments(dest_image, image_array, horizontal)
	return dest_image

# --- ghost split ---
def start_ghost_split_process(image):
	direction = choose_split_direction()
	print()
	is_horizontal = True
	if direction in [1, 3]: # vertical
		is_horizontal = False
	repetitions = 1
	if direction in [2, 3]: # cross
		repetitions = 2 # apply effect once in each direction
	splits = get_num_splits()
	print()
	split_offset_type = choose_split_offset_type(direction)
	print()
	split_offset = get_split_offset()
	print()
	circular = choose_split_wraparound()
	print()
	split_type = choose_split_type()
	print()
	print('Ghost Splitting...')
	for _ in range(repetitions):
		image = ghost_split(image, num_splits=splits, horizontal=is_horizontal, offset=split_offset, 
		      				offset_type=split_offset_type, circular_split=circular, style=split_type)
		is_horizontal = not is_horizontal # change directions
	return image

def get_num_splits():
	return get_value(1, 10, 'Number of Splits', integer=True)

def choose_split_direction():
	return choose_direction('Split Direction:')

def choose_split_type():
	choices = ['None (Lines)', 'Average', 'Lighten', 'Darken']
	return choose_option(choices, 'Ghost Blend:')

def choose_split_offset_type(split_dir):
	dim_names = get_dimension_names(split_dir)
	choices = [dim_names[0], dim_names[1], 'Mirrored', 'Random Sections', 'Complete-Random']
	return choose_option(choices, 'Offset Direction:')

def get_split_offset():
	print('Enter 0 to use a random offset.')
	x = get_value(0, 100, 'Split Offset', default=50)
	if x == 0:
		x = random.randint(1,100)
		print(f'{x} (random)')
	return x / 100

def choose_split_wraparound():
	return choose_yes_no('Circular Split?', default='yes')

def ghost_split(image, num_splits=1, horizontal=True, offset=0.5, offset_type=0, circular_split=True, style=0):
	if horizontal:
		lines = get_pixel_rows(image)
	else: # vertical
		lines = get_pixel_columns(image)
	line_length = len(lines[0])
	shift = line_length / num_splits * offset
	shift_directions = []
	if offset_type == 1: # offset towards dimension end
		shift *= -1
	elif offset_type == 2: # alternate shift directions
		for i in range(num_splits):
			if i % 2 == 0:
				shift_directions.append(1)
			else:
				shift_directions.append(-1)
	elif offset_type == 3: # random
		for _ in range(num_splits):
			if random.random() < 0.5:
				shift_directions.append(1)
			else:
				shift_directions.append(-1)
	# split every 2nd line apart
	for i, next_line in enumerate(lines):
		if i % 2 == 1: # do not split
			continue
		if offset_type == 4 and random.random() < 0.5: # random offset direction each split
			shift *= -1
		split_sections = divide_list(next_line, num_splits)
		for k, section in enumerate(split_sections):
			if shift_directions: # switch to predefined shift for each section
				x = shift_directions[k]
				shift = abs(shift)
				if x < 0:
					shift *= -1
			# shift sections
			pixel_shift(section, shift, circular=circular_split)
		# replace pixels
		next_line[:] = merge_groups(split_sections)
	# overwrite image with new data
	place_segments(image, lines, horizontal)
	# blend to balance the split lines
	if style == 1:
		image = blend_lines(image, rows=horizontal, num_lines=2, bm=BlendMode.AVERAGE)
	elif style == 2:
		image = blend_lines(image, rows=horizontal, num_lines=2, bm=BlendMode.LIGHTEN)
	elif style == 3:
		image = blend_lines(image, rows=horizontal, num_lines=2, bm=BlendMode.DARKEN)
	return image