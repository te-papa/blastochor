# Step through records, find specific fields, explode, reduce
# Look up other records based on endpoint + id
# Classes for result sets and records (eg load in result set to process or find the record you need)

class ResultSet:
	def __init__(self, records):
		self.records = records


def get_field_value(data, field_path, ordinal=None, default=None):
	# Get a value from a record based on a field path
	# Used to GET attribute values and FETCH values during processing
	if "." not in field_path:
		field_value = step_to_field(data, field_path)
	else:
		field_path = split_path(field_path)
		field_path = handle_iterator_in_path(field_path, ordinal)
		field_value = step_to_field(data, field_path)

	if default and not field_value:
		field_value = default

	return field_value


def split_path(path):
	# Ensure paths are lists that can be iterated through
	if not isinstance(path, list):
		path = path.split(".")
	return path


def handle_iterator_in_path(path=None, ordinal=None):
	# Replace the list indicator 'i' in a path with a specified ordinal to create a navigable path
	# If no ordinal provided, defaults to first item in the list
	if isinstance(path, list):
		if "i" in path:
			if not ordinal:
				ordinal = 0

			path = [ordinal if item == "i" else item for item in path]

	return path


def step_to_field(data=None, path=None):
	# Step through a record to provide a subsection or value
	if data:
		if isinstance(path, str):
			return data.get(path)
		else:
			step = data
			for field in path:
				try:
					step = step[field]
				except (KeyError, IndexError):
					return None
			return step
	else:
		return None