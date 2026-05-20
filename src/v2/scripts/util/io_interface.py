import os
import csv
import yaml
import json
import pathlib


def check_for_file(filepath):
	if os.path.exists(filepath):
		return True

	return False


def list_projects():
	# Todo: make sure we're only getting project directories
	projects = []
	for project_dir in os.listdir("resources/project_files"):
		project_metadata_path = pathlib.Path(f"resources/project_files/{project_dir}/project_metadata.yaml")
		if project_metadata_path.exists() and project_metadata_path.is_file():
			project_metadata = load_file(path_obj=project_metadata_path)
			if isinstance(project_metadata, dict):
				projects.append({project_metadata["project_id"]: project_metadata})

	return projects


def check_for_project_dir(project_id):
	project_dir = f"resources/projects/{project_id}"
	if pathlib.Path(project_dir).exists():
		return True

	return False


def list_project_files(project_id):
	project_dir = f"resources/projects/{project_id}"
	pd = pathlib.Path(project_dir)
	project_files = [f for f in pd.iterdir() if pd.is_dir()]
	return project_files


def find_project_file(file_path, project_id):
	# Look for a relative path first in the project directory and return the file if available
	# If not, treat as an absolute path and return that if available
	project_dir_path = f"resources/projects/{project_id}/{file_path}"
	file_path_obj = pathlib.Path(project_dir_path)
	if not file_path_obj.is_file():
		file_path_obj = pathlib.Path(file_path)

	if file_path_obj.is_file():
		return load_file(path_obj=file_path_obj)
	else:
		return None


def load_file(filepath=None, delimiter=None, read_lines=False, path_obj=None):
	file_data = None
	if filepath:
		path_obj = pathlib.Path(filepath)
	if path_obj.suffix == ".txt":
		with path_obj.open("r", encoding="utf-8") as f:
			if read_lines:
				file_data = f.readlines()
			else:
				file_data = f.read()
	if path_obj.suffix == ".yaml":
		with path_obj.open() as f:
			file_data = yaml.safe_load(f)
	elif path_obj.suffix == ".json":
		with path_obj.open() as f:
			file_data = json.load(f)
	elif path_obj.suffix == ".csv":
		with path_obj.open(newline="", encoding="utf-8") as f:
			if not delimiter:
				delimiter = ","
			file_data = [row for row in csv.DictReader(f, delimiter=delimiter)]

	return file_data


def write_file(filepath, data, fieldnames=None):
	match filepath:
		case filepath if filepath.endswith(".csv"):
			with open(filepath, 'w+', newline="", encoding="utf-8") as f:
				if not fieldnames:
					fieldnames = data[0].keys()
				writer = csv.DictWriter(f, fieldnames=fieldnames, restval="")
				writer.writeheader()
				for row in data:
					writer.writerow(row)

		case filepath if filepath.endswith(".json"):
			with open(filepath, 'w+', encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=4)

		case filepath if filepath.endswith(".txt"):
			if isinstance(data, list):
				data = "\n".join(data)
			with open(filepath, 'w+', encoding="utf-8") as f:
				f.write(data)
