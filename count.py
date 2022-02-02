import ocrmypdf
import csv
import re
import json

from shutil import rmtree
from os import listdir, mkdir
from os.path import isfile, join, isdir

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS

    # Confirm remove old output
    is_dir = isdir("./output")
    if is_dir:
        user_input = input("Do you want to remove previous output? (y/n)\n")
        while user_input != "y" and user_input != "n":
            print("Invalid selection.\n")
            user_input = input("Do you want to remove previous output? (y/n)\n")
        
        if user_input == "y":
            rmtree("./output")
        else:
            print("Previous output exists and you selected not to remove it. Cannot continue.")
            exit(1)

    # Make the output directory
    mkdir("./output")

    # Init english dictionary
    with open("./words.txt") as words_file:
        words = set(x.strip().lower() for x in words_file)
        words_file.close()

    # Loop through each state's directory
    for dir in listdir("./input"):

        print(f"Processing {dir}...")

        # Get list of input files
        files = [f for f in listdir(join("./input", dir)) if isfile(join("./input", dir, f))]

        # Create state output directory
        mkdir(join("./output", dir))

        # Open up the range definition csv - build dictionary
        page_dict = {}
        with open("pages.csv", newline="") as csvfile:

            # Create reader
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')

            # Skip first row
            next(reader)

            # Build dict
            for row in reader:
                page_dict[row[0]] = row[3]

        for f in files:

            # Get the file's name. It will be used for the basis of the directories/output
            file_name = f.split(".")[0]

            # Create output directory
            out_dir = join("./output", dir, file_name)
            mkdir(out_dir)

            # Define output pdf and sidecar
            out_file = join(out_dir, "out.pdf")
            out_sidecar = join(out_dir, "raw_text.txt")

            # Get the range
            page_range = page_dict.get(file_name, "all")

            # Run OCR
            ocrmypdf.ocr(
                join("./input", dir, f),
                out_file, 
                sidecar=out_sidecar, 
                pages=page_range if page_range != "all" else None, 
                force_ocr=True
            )

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

                # Split the content on empty string and count the english words
                content_words = content_sub.split()
                
                # Create a dictionary for storing the count of words in the side car
                word_count_dict = {}
                non_english_words = {}
                for w in content_words:
                    lower = w.lower()
                    if lower in words:
                        if lower in word_count_dict:
                            word_count_dict[lower] += 1
                        else:
                            word_count_dict[lower] = 1
                    else:
                        if lower in non_english_words:
                            non_english_words[lower] += 1
                        else:
                            non_english_words[lower] = 1

                # Open files
                word_count_file = open(join(out_dir, "word_count.json"), "w")
                ne_word_count_file = open(join(out_dir, "non_english_words.json"), "w")
                stats_file = open(join(out_dir, "stats.txt"), "w")

                # Sort the dictionaries
                word_count_dict = {k: v for k, v in sorted(word_count_dict.items(), key=lambda item: item[1], reverse=True)}
                non_english_words = {k: v for k, v in sorted(non_english_words.items(), key=lambda item: item[1], reverse=True)}

                # Write the stats file
                stats_file.write(f"There are {len(word_count_dict)} distinct words for a total of {sum(word_count_dict.values())} words.")

                # Write the word counts
                word_count_file.write(json.dumps(word_count_dict))
                ne_word_count_file.write(json.dumps(non_english_words))

                # Close the files
                word_count_file.close()
                ne_word_count_file.close()
                stats_file.close()
