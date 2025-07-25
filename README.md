# addressMergePlus

**A Python utility to merge, clean, and normalize multiple CSV files into a single structured output.**

---

## Overview

`addressMergePlus` is a command-line tool with a simple GUI for selecting input and output folders. It combines multiple CSV files, normalizes column headers, fills missing data, and produces a single clean CSV file ready for use in address validation or related applications.

This utility supports flexible column name variants, intelligent merging of address components, and ensures consistent output formatting.

---

## Features

- Merges multiple CSV files in a user-selected folder.
- Normalizes and standardizes column names.
- Handles multiple variants of address-related fields.
- Fills missing data using heuristics and duplicates rows with updated address info.
- Saves output to user-specified CSV file.
- Simple Tkinter GUI for folder and file selection.

---

## Requirements

- Python 3.x
- pandas
- tkinter (usually included with Python)

---

## Usage

1. Run `addressMergePlus.py`
2. Select the folder containing your CSV files.
3. Choose where to save the combined output CSV.
4. The program processes and saves the cleaned data.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Author

Chad Hall (StarboyChad)  
[LinkedIn](https://www.linkedin.com/in/chadwickhall)
