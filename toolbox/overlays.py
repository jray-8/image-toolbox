from PIL import Image
from .image_helpers import (choose_option, get_value, get_image_file)
from .blending import (choose_blend_mode, get_blend, get_opacity)

# --- overlays ---
def start_overlay_process(image):
	overlay_path = get_image_file('Image to Overlay (file):')
	if not overlay_path:
		return image
	overlay = None
	try:
		overlay = Image.open(overlay_path)
	except Exception as e: # canel operation
		print(e)
		return image
	# ensure matching image formats
	if overlay.mode != image.mode:
		try:
			print(f'converting overlay to format: {image.mode}')
			overlay = overlay.convert(mode=image.mode)
		except Exception as e:
			print(e)
			return image
	print()
	align = choose_overlay_alignment()
	print()
	align_offsets = get_alignment_offsets(align)
	print()
	bm = choose_blend_mode()
	print()
	opacity = get_opacity()
	print()
	print('Placing Overlay...')
	return place_overlay(image, overlay, align, align_offsets, bm, opacity)

def place_overlay(image, overlay, alignment, offsets, blend_mode, opacity):
	width, height = image.size
	overlay_width, overlay_height = overlay.size
	# place overlay in aligned position
	# top left (default)
	aligned_x = 0
	aligned_y = 0
	# middle x
	if alignment in [2,5,8]:
		aligned_x = int((width / 2) - (overlay_width / 2))
	# right x
	elif alignment in [3,6,9]:
		aligned_x = int(width - overlay_width)
	# middle y
	if alignment in [4,5,6]:
		aligned_y = int((height / 2) - (overlay_height / 2))
	# bottom y
	elif alignment in [7,8,9]:
		aligned_y = int(height - overlay_height)
	# apply offsets to alignment
	aligned_x += int(offsets[0] * overlay_width)
	aligned_y += int(offsets[1] * overlay_height)
	# copy the overlay to the image
	for x in range(overlay_width):
		for y in range(overlay_height):
			# overlay relative to image canvas
			rel_x = aligned_x + x
			rel_y = aligned_y + y
			# check bounds
			if rel_x < 0 or rel_x >= width:
				continue
			elif rel_y < 0 or rel_y >= height:
				continue
			source_pixel = image.getpixel((rel_x,rel_y))
			overlay_pixel = overlay.getpixel((x,y))
			# blend overlay on top
			source_pixel = get_blend([source_pixel, overlay_pixel], blend_mode, opacity)
			image.putpixel((rel_x,rel_y), source_pixel)
	return image

def choose_overlay_alignment():
	print('Overlay Alignment')
	print('=================')
	print('The two layers will be anchored to each other\'s side, corner or center.\n')
	print(' 1 2 3\n 4 5 6\n 7 8 9')
	print()
	return get_value(1, 9, 'Alignment', integer=True, default=5)

def get_alignment_offsets(alignment):
	x_offset = get_value(-400, 400, 'Overlay x-offset (%)', default=0) / 100
	y_offset = get_value(-400, 400, 'Overlay y-offset (%)', default=0) / 100
	return (x_offset, y_offset)