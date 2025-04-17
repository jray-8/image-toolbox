import sys
import os
import random
from PIL import Image

# Toolbox Functions:
from toolbox.image_helpers import (choose_yes_no)
from toolbox.image_basics import (start_crop_process, start_flip_process, start_scale_process, start_padding_process, start_rotate_process)
from toolbox.color import (start_monochrome_process, start_hue_shift_process, start_resaturate_process, start_pseudo_color_process, start_color_split_process)
from toolbox.pixel_sorting import (start_line_sort_process, start_glitch_sort_process, start_ghost_split_process)
from toolbox.transformations import (start_transformation_process)
from toolbox.image_histogram import (start_histogram_display_process, start_histogram_equalization_process)
from toolbox.filters import (start_convolution_process, start_non_linear_filter_process)
from toolbox.warps import (start_wave_warp_process, start_mirror_process)
from toolbox.blending import (start_blend_line_process, start_pixelate_process)
from toolbox.overlays import (start_overlay_process)

# place to save the image
OUTPUT_PATH = None
 
# ensure image format can be understood by the program
def format_image(image):
	if image.mode not in ['L', 'RGB', 'RGBA']:
		try:
			image = image.convert(mode='RGB')
		except Exception as e:
			print(e)
			image = None
	return image

# true if user accepts the output file will be overwritten
def get_output_overwrite_permission():
	_, filename = os.path.split(OUTPUT_PATH)
	print(f'{filename} will be overwritten.')
	return choose_yes_no('Is this ok?')

def configure_output(input_image):
	global OUTPUT_PATH
	if len(sys.argv) < 3:
		OUTPUT_PATH = sys.argv[1] # overwrites original image
		return 0
	# get specified output path
	OUTPUT_PATH = sys.argv[2]
	# check if output is a file
	_, extension = os.path.splitext(OUTPUT_PATH)
	if extension.strip() == '.': # not a file
		return 1
	# check if output destination already exists
	if os.path.isfile(OUTPUT_PATH):
		# ask user for permission to overwrite file
		if not get_output_overwrite_permission():
			return 2
		print()
	# try to access output
	if not save_image(input_image, False):
		return 3
	# valid output
	return 0

# save new image
def save_image(image, display=True):
	try:
		image.save(OUTPUT_PATH)
		if display:
			print(f'Successfully saved - {OUTPUT_PATH}')
	except Exception as e:
		print(e)
		return False
	return True

# view current image (without saving)
def view_image(image):
	try:
		image.show('Viewing')
	except Exception as e:
		print(e)

def print_coded_actions(coded_actions):
	for name, code in coded_actions:
		print(f' ({code}) - {name}')

def print_actions(numeric_actions, page, total_pages, title='', coded_actions=[]):
	page_message = f'Page ({page+1}/{total_pages})'
	if title:
		page_message += f' - {title}'
	print(page_message)
	print()
	# numeric choices
	print(f'Choose an Action:')
	for i in range(1, len(numeric_actions) + 1):
		next_action = f' ({i}) - {numeric_actions[i-1]}'
		print(next_action)
	print_coded_actions(coded_actions)

def print_menu_codes(menu_actions):
	print('Menu Codes')
	print_coded_actions(menu_actions)
	print()

def check_page_jump(code): # assume stripped, lower code
	if not code:
		return None
	if len(code) > 4 and code[:4] == 'page':
		temp = code.split()
		if len(temp) < 2:
			return None
		code = temp[1]
	elif code[0] == 'p': # check shortcut
		code = code[1:]
	else:
		return None
	try: # check if page is a number (may or may not exist)
		x = int(code)
		return x
	except Exception as e:
		return None

def main():
	# command line arguments
	if len(sys.argv) < 2:
		print('usage: image_toolbox.py <input.file> [output.file]')
		return 1

	# try to open input image
	try:
		input_image = Image.open(sys.argv[1])
	except Exception as e:
		print(e)
		return 2

	# prepare input image for processing
	input_image = format_image(input_image)
	if not input_image:
		return 3

	# try to save to output
	output_error_code = configure_output(input_image)
	if output_error_code == 1: # not a file
		print('output is not a file.')
		return 4
	elif output_error_code == 2: # refused to overwrite
		return 5
	elif output_error_code == 3: # cannot access
		print('cannot write to output file.')
		return 6
	
	# coded actions - have their own case insensitive code to access
	view_code = 'w'
	save_code = 's'
	page_left_code = 'a'
	page_right_code = 'd'
	exit_code = 'q'
	menu_actions = [('View', view_code), ('Save', save_code), ('Page Left', page_left_code), ('Page Right', page_right_code), ('Exit', exit_code)]
	menu_codes = [c[1] for c in menu_actions]

	# map action names to functions
	action_dictionary = {
		'Crop': start_crop_process,
		'Flip': start_flip_process,
		'Rotate': start_rotate_process,
		'Scale': start_scale_process,
		'Pad': start_padding_process,
		'Transformations': start_transformation_process,
		'Monochrome Conversion': start_monochrome_process,
		'Pseudo Color': start_pseudo_color_process,
		'Show Histogram': start_histogram_display_process,
		'Histogram Equalization': start_histogram_equalization_process,
		'Convolution': start_convolution_process,
		'Non-Linear Filters': start_non_linear_filter_process,
		'Line Sort': start_line_sort_process,
		'Glitch Sort': start_glitch_sort_process,
		'Ghost Split': start_ghost_split_process,
		'Wave Warp': start_wave_warp_process,
		'Blend Lines': start_blend_line_process,
		'Pixelate': start_pixelate_process,
		'Mirror': start_mirror_process,
		'Hue Shift': start_hue_shift_process,
		'Resaturate': start_resaturate_process,
		'Color Split': start_color_split_process,
		'Overlay': start_overlay_process
	}

	# actions for main menu - each page can hold 1-9 effects
	current_actions = []
	# basics
	page_1_name = 'Basics'
	page_1 = ['Crop', 'Flip', 'Rotate', 'Scale', 'Pad']
	# color / contrast / brightness
	page_2_name = 'Color / Contrast'
	page_2 = ['Hue Shift', 'Resaturate', 'Transformations', 'Show Histogram', 'Histogram Equalization', 'Monochrome Conversion', 'Pseudo Color', 'Color Split']
	# filters / sorting
	page_3_name = 'Filters & Pixel Sorting'
	page_3 = ['Convolution', 'Non-Linear Filters', 'Line Sort', 'Glitch Sort', 'Ghost Split']
	# warps
	page_4_name = 'Warp Effects'
	page_4 = ['Wave Warp', 'Mirror']
	# blending
	page_5_name = 'Blending & Overlays'
	page_5 = ['Blend Lines', 'Pixelate', 'Overlay']

	# pages
	pages = [page_1, page_2, page_3, page_4, page_5]
	page_names = [page_1_name, page_2_name, page_3_name, page_4_name, page_5_name]
	page_index = 0
	total_pages = len(pages)

	# explain pages
	print('You may enter \'page x\' to instantly jump to page x.')
	print('Shortcut: \'p3\' to jump to page 3.')
	print()

	# show additional actions with their codes
	print_menu_codes(menu_actions)

	# choose an action
	active = True
	while active:
		index = 0
		attempts = 0
		current_actions = pages[page_index] # get page of actions
		page_title = page_names[page_index]
		print_actions(current_actions, page_index, total_pages, page_title) # numeric options

		# --- receive code ---
		received_action = False
		received_menu_code = False # menu code, not an image effect
		while not received_action and not received_menu_code:
			user_code = input('> ')
			user_code = user_code.strip().lower()
			try: # check numeric action
				index = int(user_code)
				if index >= 1 and index <= len(current_actions): # action exists
					received_action = True
					print()
			# check alternate codes
			except Exception as e:
				if user_code == exit_code: # Exit
					active = False
					received_menu_code = True
				elif user_code in menu_codes: # menu code
					print()
					received_menu_code = True
					# Save
					if user_code == save_code:
						if not save_image(input_image):
							print('cannot write to output file.')
							return 6
						print()
					# View
					elif user_code == view_code:
						print('Viewing Current Image...\n')
						view_image(input_image)
					# page left
					elif user_code == page_left_code:
						page_index = (page_index - 1) % total_pages
					# page right
					elif user_code == page_right_code:
						page_index = (page_index + 1) % total_pages
				else: # special codes
					jump = check_page_jump(user_code) # check for a page jump code
					if jump: # valid
						received_menu_code = True
						if jump >= 1 and jump <= total_pages:
							print()
							page_index = (jump - 1) # index of the page
						else:
							print('That page does not exist.\n')		

			# handle invalid codes
			if not received_action and not received_menu_code:
				print('Invalid Action!\n')
				attempts += 1
				if attempts >= 5:
					attempts = 0
					print_menu_codes(menu_actions)
					print_actions(current_actions, page_index, total_pages, page_title)
		
		# --- process action ---
		if received_menu_code: # already processed
			continue
		else: # manipulate image
			chosen_action = current_actions[index-1]
			action = action_dictionary.get(chosen_action)
			# perform action on the image - which stores the result
			if action:
				input_image = action(input_image)
			else:
				print(f'Unknown Action - {index}')
			# verify new image exists
			if not input_image:
				print(f'{chosen_action} Failed.')
				return 7
			print() # finishes action with a newline

	return 0 # graceful exit

# RUN
random.seed()
main()