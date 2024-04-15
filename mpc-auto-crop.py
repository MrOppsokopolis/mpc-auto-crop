import argparse
import os
import errno
import sys
import re
from pathlib import Path
from PIL import Image, ImageDraw
from PIL.Image import Resampling
import numpy
import time

# ---------------------------------------------------------
# Handle command line arguments
# ---------------------------------------------------------

description = 'Crops the 1/8 inch bleed edge (including the rounded corners) around a MTG proxy and converts to PNG'

parser = argparse.ArgumentParser(description=description)

# Arguments
parser.add_argument('inputPath', type=str, help='The path to the input directory containing Magic card images.')
parser.add_argument('-o', '--output', type=str, default=None, help='The output directory. Defaults to <inputPath>/removed_legal')
parser.add_argument('-r', '--recursive', action='store_true', help='Include all image files in subdirectories of <inputPath>')
parser.add_argument('-s', '--scale', type=float, default=0.5, help='Scale of final image. Ppercentage as a decimal. 1=same scale as original. Default=0.5')
parser.add_argument('-c', '--clean_names', action='store_true', help='Remove everything in "()" from the image name')

args = parser.parse_args()
input_dir = getattr(args, 'inputPath').replace('\'', '').replace('"', '')
output_dir = getattr(args, 'output') if getattr(args, 'output') is not None else Path(Path(input_dir).parent, 'output').resolve()
recursive = getattr(args, 'recursive') if os.name != 'nt' else False
scale = getattr(args, 'scale')
clean_names = getattr(args, 'clean_names')

# ---------------------------------------------------------
# Get files and paths
# ---------------------------------------------------------

glob_match = '**/*' if recursive else '*'

image_types = {".jpg", ".JPG", ".png", ".PNG"}

if os.name != 'nt':
    flag = not Path(output_dir).is_relative_to(Path(input_dir))

    # Restrict file matches to the desired image formats and exclude the output directory
    files = (p.resolve() for p in Path(input_dir).glob(glob_match) if (flag or not p.resolve().is_relative_to(Path(output_dir))) and p.suffix in image_types)
else:
    # Windows paths are fucky

    files = (p.resolve() for p in Path(str(input_dir)).glob(glob_match) if p.suffix in image_types)

try:
    os.mkdir(output_dir)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

# ---------------------------------------------------------
# Process all images
# ---------------------------------------------------------

files_count = 0
total_process_time = 0

for file in files:
    tic = time.perf_counter()

    # Add Alpha channel
    with Image.open(file).convert("RGBA") as im:

        # file.stem is just the name, file.name is the name plus extension
        file_name = file.stem

        # Potentially remove text between () or [] from the name of the file
        if clean_names:
            file_name = re.sub(r'[\(\[].*[\)\]]', '', file.stem).strip()

        # Save as PNG
        out_file = Path(output_dir, file_name + '.png')

        # print(f'Editing "{out_file.name}"', end='\r')
        print(f'Editing "{out_file.name}"')

        # width of final image -> 2.48031 inch
        # height of final image -> 3.46457 inch

        width, height = im.size

        # find what 1/8 inch is in file’s DPI
        pixels_per_eighth_inch = (height / (3.46457 + 0.125)) / 8

        # Crop the image
        im_cropped = im.crop((pixels_per_eighth_inch, pixels_per_eighth_inch, width - pixels_per_eighth_inch, height - pixels_per_eighth_inch))

        # New image mesurements
        width, height = im_cropped.size

        # convert to numpy
        imArray = numpy.asarray(im_cropped)

        # create mask (mode 'L' is black and white)
        maskIm = Image.new('L', (imArray.shape[1], imArray.shape[0]), 0)
        # Corner radius of playing cards is 1/8 inch
        ImageDraw.Draw(maskIm).rounded_rectangle((0, 0, width, height), radius=pixels_per_eighth_inch, outline=1, fill=1)
        mask = numpy.array(maskIm)

        # assemble new image (uint8: 0-255)
        newImArray = numpy.empty(imArray.shape,dtype='uint8')

        # colors (three first columns, RGB)
        newImArray[:,:,:3] = imArray[:,:,:3]

        # transparency (4th column)
        newImArray[:,:,3] = mask*255

        # back to Image from numpy
        newIm = Image.fromarray(newImArray, "RGBA")

        # Resize the image trying to get under 8MB (the limit for a Discord upload)
        newIm.thumbnail([sys.maxsize, height * scale], Resampling.LANCZOS)

        newIm.save(out_file)

        files_count += 1

        toc = time.perf_counter()
        total_process_time += (toc - tic)
        print(f'Time elapsed: {toc - tic:0.4f}s')

print()
print(f'Total processing time: {total_process_time:0.4f}s')
print(f'Average file processing time: {total_process_time / files_count:0.4f}s')
print()

if files_count == 0:
    print(f'There are no .jpg or .png files in directory: "{input_dir}"')
    exit(1)
else:
    print(f'Process complete. Edited {files_count} images.')
    exit(0)
