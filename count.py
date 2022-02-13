from time import strftime, time
from datetime import datetime
import ocrmypdf
import csv
import re
import json

from shutil import rmtree, move, copy, copytree
from os import listdir, mkdir
from os.path import isfile, join, isdir, exists
import sys
import argparse

def _process_side_car(file, out_dir, is_reprocess=False, skip_english_check=False):
    if not is_reprocess:
        output = open(join(file, "processed_text.txt"), 'w')
                        
        content = file.read()
        content_sub = re.sub('\[OCR skipped on page\(s\) \d{1,}-\d{1,}\]', '', content, flags=re.M)
        content_sub = re.sub('[]', '', content_sub, flags=re.M)
        content_sub = re.sub(r'-\n(\w+ *)', r'\1\n', content_sub, flags=re.M)
        content_sub = re.sub(r'[,.?\"\']', r'', content_sub, flags=re.M)

        output.write(content_sub)
        output.close()
    else: 
        content_sub = file.read()

    # Split the content on empty string and count the english words
    content_words = content_sub.split()
    
    # Create a dictionary for storing the count of words in the side car
    word_count_dict = {}
    non_english_words = {}
    for w in content_words:
        lower = w.lower()

        if skip_english_check:
            if lower in word_count_dict:
                word_count_dict[lower] +=1
            else:
                word_count_dict[lower] = 1
        else:
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

    now_str = f"rp"

    if is_reprocess:
        mkdir(join(out_dir, now_str))

    # Open files
    word_count_file = open(join(out_dir, now_str, "word_count.json"), "w") if is_reprocess else open(join(out_dir, "word_count.json"), "w")
    ne_word_count_file = open(join(out_dir, now_str, "non_english_words.json"), "w") if is_reprocess else open(join(out_dir, "non_english_words.json"), "w")
    stats_file = open(join(out_dir, now_str, "stats.txt"), "w") if is_reprocess else open(join(out_dir, "stats.txt"), "w")

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

if __name__ == '__main__':  # To ensure correct behavior on Windows and macOS

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbosity", required=False)
    parser.add_argument("--preprocess", required=False)
    parser.add_argument("--start_with", required=False)
    parser.add_argument("--reprocess_side_cars", required=False)
    parser.add_argument("--skip_english_check", required=False)
    parser.add_argument("--collapse_stats", required=False)
    args = parser.parse_args()

    if args.collapse_stats:
        stat_out_file = open(join("./output", "all_stats.txt"), "w")
        rp_stat_out_file = open(join("./output", "rp_all_stats.txt"), "w")

        # CSV
        rp_stat_out_file_csv = open(join("./output", "rp_all_stats.csv"), "w")
        rp_stat_out_file_csv.write("State,Count\n")

        list_dir = sorted(listdir("./output"))
        for dir in list_dir:
            sub_dir = listdir(join("./output", dir))
            total_word_count = 0
            rp_total_word_count = 0
            for sd in sub_dir:
                if exists(join("./output", dir, sd, "stats.txt")):
                    stat = open(join("./output", dir, sd, "stats.txt"), "r")
                    content = stat.read()
                    pattern = '(\d+)\swords'
                    a = re.search(pattern, content)
                    total_word_count += int(a.group(1))
                    stat.close()

                if exists(join("./output", dir, sd, "rp", "stats.txt")):
                    rp_stat = open(join("./output", dir, sd, "rp", "stats.txt"), "r")
                    content = rp_stat.read()
                    pattern = '(\d+)\swords'
                    a = re.search(pattern, content)
                    rp_total_word_count += int(a.group(1))
                    rp_stat.close()
            stat_out_file.write(f"{dir} has a total of {total_word_count} words.\n")
            rp_stat_out_file.write(f"{dir} has a total of {rp_total_word_count} words.\n")
            rp_stat_out_file_csv.write(f"{dir},{rp_total_word_count}\n")
        
        stat_out_file.close()
        exit(0)

    # Optionally preprocess input
    if args.preprocess is not None:
        list_dir = sorted(listdir("./input_src"))

        # Make temp input
        mkdir("./pp")
        mkdir("./pp/input")

        # Process
        for dir in list_dir:

            # Get state name
            state = dir.split("_")[0]
            
            # Create state directory if it does not exist
            if not exists(join("./pp", "input", state)):
                mkdir(join("./pp/input", state))

            # Move the file
            copy(join("./input_src", dir), join("./pp/input", state))

        # rmtree("./pp")
        user_input = input("Does it look correct? (y/n)\n")
        while user_input != "y" and user_input != "n":
            print("Invalid selection.\n")
            user_input = input("Does it look correct? (y/n)\n")

        if user_input == "y":
            copytree("./pp/input", "./input")
        else:
            rmtree("./pp")
            exit(0)

    # Confirm remove old output
    is_dir = isdir("./output")
    if is_dir:
        user_input = input("Do you want to remove previous output? (y/n)\n")
        while user_input != "y" and user_input != "n":
            print("Invalid selection.\n")
            user_input = input("Do you want to remove previous output? (y/n)\n")
        
        if user_input == "y":
            rmtree("./output")

    # Make the output directory
    if not exists("./output"):
        mkdir("./output")

    # Init english dictionary
    with open("./words.txt") as words_file:
        words = set(x.strip().lower() for x in words_file)
        words_file.close()

    # Loop through each state's directory
    list_dir = sorted(listdir("./input"))

    # Argument that lets us choose a starting state
    start_with = args.start_with

    for dir in list_dir:

        if start_with is not None and dir != start_with:
            print(f"Skipping {dir}...")
            continue

        if dir == ".DS_Store":
            continue

        print(f"Processing {dir}...")
        start_with = None

        # Get list of input files
        files = [f for f in listdir(join("./input", dir)) if isfile(join("./input", dir, f))]

        # Create state output directory
        if not exists(join("./output", dir)):
            mkdir(join("./output", dir))

        # Open up the range definition csv - build dictionary
        if not args.reprocess_side_cars:
            page_dict = {}
            with open("pages.csv", newline="") as csvfile:

                # Create reader
                reader = csv.reader(csvfile, delimiter=',', quotechar='"')

                # Skip first row
                next(reader)

                # Build dict
                for row in reader:
                    page_dict[row[0]] = row[1]

        for f in files:
            # Get the file's name. It will be used for the basis of the directories/output
            file_name = f.split(".")[0]

            # Create output directory
            out_dir = join("./output", dir, file_name)

            # Define side care
            out_sidecar = join(out_dir, "raw_text.txt")

            if args.reprocess_side_cars:
                if not exists(out_sidecar):
                    print("Cannot reprocess a file that does not exist...")
                    continue
                else:
                    print(f"Processing side car for {f}...")
                    with open(out_sidecar, 'r') as orig_side:
                        _process_side_car(orig_side, out_dir, is_reprocess=True, skip_english_check=args.skip_english_check)
            else:
                # Skip this file if we've processed it before
                if exists(out_dir):
                    print(f"Skipping {f}...")
                    continue

                mkdir(out_dir)

                # Define output pdf
                out_file = join(out_dir, "out.pdf")

                # Get the range
                page_range = page_dict.get(file_name, "all")

                # Update verbosity of OCR
                if len(sys.argv) > 2 and sys.argv in ["quiet", "debug"]:
                    ocrmypdf.configure_logging(verbosity=ocrmypdf.Verbosity(-1 if sys.argv[2] == "quiet" else 1))

                # Run OCR
                ocrmypdf.ocr(
                    join("./input", dir, f),
                    out_file, 
                    sidecar=out_sidecar, 
                    pages=page_range if page_range != "all" else None, 
                    # force_ocr=True
                )

                # Clean up output from ocrmypdf in sidecar - a la "OCR skipped..."
                with open(out_sidecar, 'r') as orig_side:
                    _process_side_car(orig_side, out_dir, skip_english_check=args.skip_english_check)
