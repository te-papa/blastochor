import os
import csv
import yaml
import json


def check_for_file(filepath):
	if os.path.exists(filepath):
		return True


def load_file(filepath, delimiter=None, read_lines=False):
	file_data = None
	if filepath.endswith(".txt"):
		with open(filepath, "r", encoding="utf-8") as f:
			if read_lines:
				file_data = f.readlines()
			else:
				file_data = f.read()
	if filepath.endswith(".yaml"):
		with open(filepath) as f:
			file_data = yaml.safe_load(f)
	elif filepath.endswith(".json"):
		with open(filepath) as f:
			file_data = json.load(f)
	elif filepath.endswith(".csv"):
		with open(filepath, newline="", encoding="utf-8") as f:
			if not delimiter:
				delimiter = ","
			file_data = [row for row in csv.DictReader(f, delimiter=delimiter)]

	return file_data


def write_file(filepath, data, overwrite=False):
	match filepath:
		case filepath if filepath.endswith(".csv"):
			with open(filepath, 'w+', newline="", encoding="utf-8") as f:
				headers = data[0].keys()
				writer = csv.DictWriter(f, fieldnames=headers)
				writer.writeheader()
				for row in data:
					writer.writerow(row)
		case filepath if filepath.endswith(".txt"):
			if isinstance(data, list):
				data = "\n".join(data)
			with open(filepath, 'w+', encoding="utf-8") as f:
				f.write(data)


def step_to_field(data, path):
	# Step through a dict to reach a labelled value
	if "." in path:
		path = path.split(".")
	if data:
		if isinstance(path, str):
			return data.get(path)
		elif isinstance(path, list):
			step = data
			for field in path:
				try:
					step = step[field]
				except KeyError:
					step = None

				return step

	return None
