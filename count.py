import ocrmypdf
import csv
import re

from os import listdir, mkdir
from os.path import isfile, join

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS

    # Get list of input files
    files = [f for f in listdir("./input") if isfile(join("./input", f))]

    # Open up the range definition csv - build dictionary
    page_dict = {}
    with open("pages.csv", newline="") as csvfile:

        # Create reader
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')

        # Skip first row
        next(reader)

        # Build dict
        for row in reader:
            page_dict[row[0]] = row[3]

        for f in files:

            # Get the file's name. It will be used for the basis of the directories/output
            file_name = f.split(".")[0]

            # Create output directory
            out_dir = join("./output", file_name)
            mkdir(out_dir)

            # Define output pdf and sidecar
            out_file = join(out_dir, "out.pdf")
            out_sidecar = join(out_dir, "raw_text.txt")

            # Get the range
            page_range = page_dict[file_name]

            # Run OCR
            ocrmypdf.ocr(join("./input", f), out_file, deskew=True, sidecar=out_sidecar, pages=page_range)

            # Clean up output from ocrmypdf in sidecar - a la "OCR skipped..."
            with open(out_sidecar, 'r') as orig_side:
                output = open(join(out_dir, "processed_text.txt"), 'w')
                
                content = orig_side.read()
                content_sub = re.sub('\[OCR skipped on page\(s\) \d{1,}-\d{1,}\]', '', content, flags=re.M)
                content_sub = re.sub('[]', '', content_sub, flags=re.M)
                content_sub = re.sub(r'-\n(\w+ *)', r'\1\n', content_sub, flags=re.M)
                content_sub = re.sub(r'[,.?\"\']', r'', content_sub, flags=re.M)

                output.write(content_sub)
                output.close()

    # ocrmypdf.ocr('./input/Wisconsin_1998_1.pdf', './output/output.pdf', deskew=True)