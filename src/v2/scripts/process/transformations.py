# Transformation functions that can be applied to a single value
# (A value can be a list etc, depending)
# Scroll down for transformations that combine basic functions, where you can add your own!


def compose(string_elements, separator="", default=None):
	processed_elements = []
	for s_element in string_elements:
		# Uses general parsing to identify which are functions and which are strings
		if isinstance(s_element, str):
			processed_elements.append(s_element)
		elif isinstance(s_element, int):
			processed_elements.append(str(s_element))
		else:
			processed_elements.append(run_transformation(s_element))

	return concatenate(processed_elements, separator)


def concatenate(values, separator=""):
	return separator.join(values)


def count(value):
	# Count the members of a list. If the value is not a list but exists, will return 1
	# Should I just use len() instead?
	# Todo: Include 0 and False in 'existing' values
	if value:
		if isinstance(value, list):
			return len(value)
		return 1

	return None

# String manipulation functions
def to_lower(value):
	if isinstance(value, str):
		return value.lower()

	return None


def to_upper(value):
	if isinstance(value, str):
		return value.upper()
	return None


def capitalise(value):
	if isinstance(value, str):
		return value.capitalize()
	return None


# List selection functions
def select_first(values, default=None):
	return select_members(values, 0, default=default)


def select_last(values, default=None):
	return select_members(values, -1, default=default)


def select_members(values, index_start, index_end=None, default=None):
	return_value = None

	if isinstance(values, list):
		if index_end:
			return_value = values[index_start:index_end]
		else:
			return_value = values[index_start]

	if default and not return_value:
		return_value = default

	return return_value


def sort(values, sort_order, sort_field=None, sort_direction="asc"):
	# Sort a list of values based on given criteria
	# Can do a simple sort by alphabetical or similar
	# Or more complex like sort_field = hasRep.i.rights.title
	# And sort_order = ["CC-BY 4.0", "All Rights Reserved"]
	# sort_direction doesn't apply if a manual sort order is set
	pass
