# Processing manager class - send values to the right places, apply loops and chains and stuff
# If a chained function returns None with no default, stop there
# If the next line of the map starts with fallback, go from there
# Includes non-test, non-modifying functions
import copy
import re
from random import randint

from parse import Parser, with_pattern

from scripts.exports.export_context import load_export_context
from scripts.process import transformations
from scripts.util.record_navigation import get_field_value
from scripts.util.helpers import generate_record_pid
from scripts.util.io_interface import load_file


class ProcessingManager:
	# Identify required processing and apply to record set, records, and fields
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id

	def apply_record_set_processing(self, project_settings):
		# Use to apply flags based on record content or attributes
		# Todo: set up to allow actual record edits, eg use the skiplist to remove linked record parts such as media
		if project_settings.dataset_processing_parser_script:
			raw_parser = load_file(f"resources/project_files/{project_settings.project_id}/parser_dataset.txt")
			if raw_parser:
				project_settings.dataset_processing_parser = RecordParser(raw_parser, self.export_run_id)
				record_storage = load_export_context(self.export_run_id).record_storage
				for record_pid, record in record_storage.records.items():
					project_settings.dataset_processing_parser.apply_parser(record_pid, record)
			else:
				raise FileNotFoundError(f"Dataset-level parser script not found")


class ParserAction:
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id
		self.function_type = None
		self.label = None
		self.path = None
		self.target = None
		self.condition = None
		self.actions = []
		self.decorators = []
		self.complete = False
		self.accept_record = True
		self.current_value = None


class ParserFlag:
	def __init__(self, parser_flag_script):
		self.label = None
		self.target = None

		# Todo: Turn parser_flag_script into a label and target parser action

	def look_for_flag(self, record):
		# Todo: Run self.target on record. If a record_id is returned, find it in the memo and attach it
		pass


class ParsedRecord:
	# Records get parsed to identify attributes, fields and their values
	def __init__(self, record_pid, record):
		self.record_pid = record_pid
		self.record = record
		self.accept_record = True
		self.transpose = None
		self.parsing_complete = False
		self.parsed_fields = {}


class RecordParser:
	def __init__(self, parser_script, export_run_id):
		self.export_run_id = export_run_id
		self.parser_actions = []
		self.enrichments = {}
		self.data_structure = None

		self.analyse_script(parser_script)

	# Todo: during script analysis, identify the output data structure (fields in the order listed - can we nest for json output?)
	def analyse_script(self, parser_script):
		for parser_action in step_through_script(parser_script, self.export_run_id):
			self.parser_actions.append(parser_action)

	def apply_parser(self, record_pid, record):
		parsed_record = ParsedRecord(record_pid, record)
		self.apply_parser_actions(self.parser_actions, parsed_record)
		return parsed_record

	def apply_parser_actions(self, parser_actions, parsed_record):
		for parser_action in parser_actions:
			this_action = copy.deepcopy(parser_action)
			if this_action.decorators:
				for decorator in this_action.decorators:
					enrichment_action = copy.deepcopy(self.enrichments.get(decorator))
					enrichment_action.actions.append(this_action)
					self.run_parser_action(enrichment_action.actions, parsed_record)
			else:
				self.run_parser_action(this_action, parsed_record)

	def run_enrichment_action(self, enrichment_action, parser_action, parsed_record):
		# Make any needed changes to the parser_action before running it and enriching the result

		match enrichment_action.function_type:
			case "transpose":
				if enrichment_action.target == ":fill":
					# All available transposed rows will be filled with the same value
					self.run_parser_action(parser_action, parsed_record)
					enrichment_action.current_value = {"transpose_fill": parser_action.current_value}

				else:
					# Create an iterable with the target, and apply according to the condition
					self.run_parser_action(enrichment_action.target, parsed_record)
					if not parsed_record.transpose:
						parsed_record.transpose = len(enrichment_action.target.current_value)

					if enrichment_action.condition == "if_multiple":
						# Only run transposition if there will be more than one child
						if len(enrichment_action.target.current_value) <= 1:
							self.run_parser_action(parser_action, parsed_record)
							# Todo: wrap up - avoid rest of enrichment

					for iter_index, iter_value in enumerate(enrichment_action.target.current_value):
						iter_parser_action = copy.deepcopy(parser_action)
						# Todo: might we need to insert multiple actions?
						# Replace iter_value available to the parser action
						iter_enrichment_action = copy.deepcopy(enrichment_action.enrichment)
						setattr(iter_enrichment_action, "iter_index", iter_index)
						setattr(iter_enrichment_action, "iter_value", iter_value)
						iter_parser_action.actions.insert(0, iter_enrichment_action)

	def run_parser_action(self, parser_action, parsed_record, parent_action=None):
		# Run any sub-actions to get a usable value, and then apply according to the function type
		# Todo: run sub-actions and set current value - if not found, look for and use default value, or leave as None
		# Todo above: on initialising attribute function, turn path option into fetch sub-function
		# Todo above: on initialising field function, if no sub-actions, turn label into get for same name
		# Todo above: on initialising transforms, string params are default values with no sub-actions

		# Pass the current value down from the parent action
		if parent_action:
			parser_action.current_value = parent_action.current_value

		# Pass the current value back up again from the end of the sub-action chain
		if parser_action.actions:
			for sub_action in parser_action.actions:
				self.run_parser_action(sub_action, parsed_record, parent_action=parser_action)
				parser_action.current_value = sub_action.current_value

		match parser_action.function_type:
			# Top level functions
			case "attribute":
				# Set an attribute value
				set_attribute(parser_action, parsed_record)

			case "field":
				# Set an output field value
				set_field(parser_action, parsed_record)

			case "reject_if":
				# Exclude record from output if current value is True
				# Todo: decide if this should be set in the memo or output instead
				if parser_action.current_value:
					parsed_record.accept_record = False

			case "validates":
				# Todo: Look at supplejack validates and see if it's useful
				pass

			case "local":
				# Functions following this use the parent current_value
				setattr(parent_action, f"local_{parser_action.label}", parser_action.current_value)
				parser_action.current_value = parent_action.current_value

			case "transpose":
				# Apply each child value to the record, marked as transposed
				if parser_action.target == ":fill":
					# Mark parsed field value filling all transposed rows
					parser_action.current_value = {"transpose_fill": parser_action.current_value}
				else:
					# Mark parsed field value as transposed and add to list of values
					if not parsed_record.fields.get(parser_action.label):
						parsed_record.fields[parser_action.label] = {"transpose_values": []}

					parsed_record.fields[parser_action.label]["transpose_values"].append(parser_action.current_value)

			case "flag":
				# Identify a record_id and set a flag in the memo using the flag's label
				flagged_record_id = parser_action.current_value
				if flagged_record_id:
					memo = load_export_context(self.export_run_id).memo
					record_entry = memo.memo.get(flagged_record_id, None)
					if record_entry:
						setattr(record_entry, f"flag_{parser_action.label}", True)

			# Todo: decide if any math functions are useful
			# Basic actions
			case "get":
				get_attribute(parser_action, parsed_record)

			case "get_local":
				parser_action.current_value = getattr(parent_action, f"local_{parser_action.label}", None)

			case "fetch":
				fetch_value(parser_action, parsed_record)

			case "set":
				# No further action taken, use the current_value set by the parser
				pass

			case "mapping":
				apply_mapping(parser_action)

			case "lookup":
				# Find a record_id and get the corresponding record from saved data or the API
				lookup_record(parser_action)

			case "memo_check":
				# Find a record_id value and check its memo entry's attributes
				memo_check(parser_action)

			case "fallback":
				# If current value is None, run fallback actions, otherwise skip to end
				# Fallback starts from the top of its level, ie the original record or a parent action's result
				pass

			case "this":
				# Find the current iteration of an object being looped through
				# EG when transposing rows, get the current image from "hasRepresentation"
				pass

			case "count":
				# Count the number of items in a list. For a string length use ".length"
				# Todo: count number of a supplied value in a list, or count different items, as options?
				if isinstance(parser_action.current_value, list):
					parser_action.current_value = len(parser_action.current_value)

			case "random_int":
				# Generate a random integer between two values
				# Todo: look at weighting by some supplied value
				min_value = getattr(parser_action, "min", 0)
				max_value = getattr(parser_action, "max", 100)
				random_int = randint(min_value, max_value)
				parser_action.current_value = random_int

			# String manipulation functions
			case "add":
				# Append a string to the end of the current string
				parser_action.current_value += parser_action.supplied_value

			case "capitalise":
				# Capitalise the first letter of the current string
				parser_action.current_value = parser_action.current_value.capitalize()

			case "compose":
				# Combine multiple values (or other function results) into a single string
				pass

			case "lower":
				# Set whole string to lowercase
				parser_action.current_value = parser_action.current_value.lower()

			case "split":
				# Split a string into a list on a specified delimiter
				pass

			case "truncate":
				# Trim string to a specified length with optional suffix
				pass

			case "upper":
				# Set whole string to uppercase
				parser_action.current_value = parser_action.current_value.upper()

			# List manipulation functions
			case "for_each":
				# Apply sub-actions to each item in a list
				pass

			case "sort":
				# Convenience function to sort a list alphabetically - pass to sort_by
				pass

			case "sort_by":
				pass

			# Selection functions
			# Todo: Look at supplejack find_with, find_without etc
			case "first":
				# Convenience function to select the first item in a list - pass to select
				pass

			case "last":
				# Convenience function to select the last item in a list - pass to select
				pass

			case "select":
				# Select an item or items from a list based on index
				pass

			# Test functions
			case "if":
				# Check if sub-action end result is True
				pass

			case "includes":
				# Check if a sub-action result list includes a specified item
				if parser_action.current_value:
					if parser_action.condition in parser_action.current_value:
						parser_action.current_value = True

			case "is":
				# Check if the current_value is the same as a specified value
				# Todo: if string, have a strict param, otherwise .lower first?
				if parser_action.current_value:
					if parser_action.condition == parser_action.current_value:
						parser_action.current_value = True

			case "is_in":
				# Check if a sub-action result is in a specified list
				if parser_action.current_value:
					if parser_action.current_value in parser_action.condition:
						parser_action.current_value = True

			case "present":
				# Check if the current_value is not None
				parser_action.current_value = bool(parser_action.current_value)

			case "absent":
				# Check if the current_value is None
				parser_action.current_value = not bool(parser_action.current_value)

			case "true":
				# Check if the current value is True
				# Todo: should this just be an alias for present?
				pass

			case "false":
				# Check if the current value is False
				pass

		if not parser_action.current_value:
			# Try to get a value from a parser-provided default
			if hasattr(parser_action, "optional_default"):
				parser_action.current_value = parser_action.optional_default


def step_through_script(parser_script, export_run_id):
	# Divide parser script into list of instructions
	while parser_script:
		continuing_instruction = False
		for i in range(len(parser_script)):
			parser_instruction = parser_script[0:i]
			if parser_instruction:
				if re.match(r'^#.+\n', parser_instruction):
					# Ignore comments
					parser_script = parser_script[i:]
				else:
					# Todo: figure out how to handle nested do/end blocks
					if re.match(r'\sdo[\s\n]$', parser_instruction):
						# Instruction includes following lines until "end" found
						continuing_instruction = True

					else:
						if continuing_instruction:
							if re.match(r'\sdo[\s\n].+[\s\n]end$', parser_instruction):
								parser_action = interpret_parser_instruction(parser_instruction, export_run_id)
								if parser_action:
									yield parser_action
								parser_script = parser_script[i:]
								continuing_instruction = False

						else:
							# Look for the end of the instruction (newline or end of script)
							if re.match(r'.+[\n$]', parser_instruction):
								parser_action = interpret_parser_instruction(parser_instruction, export_run_id)
								if parser_action:
									yield parser_action
								parser_script = parser_script[i:]

			else:
				parser_script = None


def interpret_parser_instruction(parser_instruction, export_run_id):
	# Identify instruction elements and apply to a ParserAction object
	# Tests and transforms within a 'do/end' block get passed to transform interpretation
	# Todo: figure out some kind of validation so we're not adding things that don't work
	parser_action = ParserAction(export_run_id=export_run_id)

	while parser_instruction:
		parser_instruction = parser_instruction.lstrip()
		if parser_instruction:
			match parser_instruction:
				case parser_instruction if re.match(r'^@[\w_]+\n', parser_instruction):
					# Pattern is a decorator, remove @ and apply
					parser_action.decorators.append(parser_instruction[1:-1])
				case parser_instruction if parser_instruction.startswith("do\n"):
					# Following line(s) are tests and transforms, split them out into sub-actions
					# Todo: Fix regex to actually work because this seems like it could be bad
					child_instructions = re.match(r'^do[\n\s].+[\n\s]end', parser_instruction).group(0)
					child_instructions = child_instructions.replace("do\n", "", 1)
					child_instructions = child_instructions.replace("\nend", "", 1)

					# Work through the child instructions, turning each into a sub-action
					for transform_action in step_through_transform(child_instructions, export_run_id):
						parser_action.actions.append(transform_action)

					parser_instruction = chomp_parsed_element(child_instructions, parser_instruction)

				case parser_instruction if parser_instruction == "end":
					parser_instruction = None
					parser_action.complete = True

				case parser_instruction if re.match(r'^\S+\b', parser_instruction):
					# Pattern is a function. Set in current parser action object
					parser_function = re.match(r'^\S+\b', parser_instruction).group(0)
					parser_action.action_function = parser_function

					parser_instruction = chomp_parsed_element(parser_function, parser_instruction)

				case parser_instruction if re.match(r'^:[\w_]+', parser_instruction):
					# Pattern is an attribute or field label. Remove colon and apply
					parser_label = re.match(r'^:[\w_]+', parser_instruction).group(0)
					parser_action.label = parser_label[1:-1]

					parser_instruction = chomp_parsed_element(parser_label, parser_instruction)

				case parser_instruction if re.match(r'^, \w', parser_instruction):
					# Pattern identifies that optional parameters follow
					parser_action.parse_options = True

					parser_instruction = chomp_parsed_element(", ", parser_instruction)

				case parser_instruction if re.match(r'^[\w_]+: [\w_]+'):
					# Pattern is an optional parameter and value, eg default or path
					parser_param = re.match(r'^[\w_]+: [\w_]+', parser_instruction).group(0)
					parser_param = parser_param.split(": ")
					param_label = parser_param[0]
					param_value = parser_param[1]

					setattr(parser_action, f"optional_{param_label}", param_value)

					parser_instruction = chomp_parsed_element(parser_param, parser_instruction)

				case _:
					parser_instruction = None
					parser_action.complete = True

		else:
			parser_action.complete = True

	if parser_action.action_function == "attribute" or "field":
		set_up_transform_action(parser_action, export_run_id=export_run_id)

	parser_action = validate_parser_action(parser_action)

	if parser_action:
		return parser_action

	return None


def step_through_transform(transform_script, export_run_id=None):
	# Identify transform instructions and yield a ParserAction for each
	parser_action = ParserAction()
	while transform_script:
		match transform_script:
			# Todo: revise regex not to get caught on nested parentheses etc
			case transform_script if re.match(r'^[\w_]+\(.+\)[.\n$]'):
				# Pattern is a transform or test function with parameters
				# EG get(:title), fetch("identifier"), is_in("collector's number", "collector number")
				# Todo: pass this chunk of the script to the interpreter and chomp from script, yield action

				transform_string = re.match(r'^[\w_]+\(.+\)', transform_script).group(0)
				transform_compiler = Parser("{transform_name} ({transform_params})")
				parsed_function = transform_compiler.parse(transform_string)
				transform_name = parsed_function["transform_name"]
				transform_params = parsed_function["transform_params"]

				parser_action.function_type = transform_name
				set_up_transform_action(parser_action, transform_params)

				transform_script = chomp_parsed_element(transform_string, transform_script)

				yield parser_action

			case transform_instruction if re.match(r'^[\w_]+[.\n$]*', transform_instruction):
				# Pattern is a transform or test function without parameters
				# EG first, lower, present
				transform_string = re.match(r'^[\w_]+[.\n$]', transform_script).group(0)

				parser_action.function_type = transform_string
				set_up_transform_action(parser_action)

				transform_script = chomp_parsed_element(transform_string, transform_script)

				yield parser_action

			case transform_instruction if re.match(r'^if .+\?', transform_instruction):
				# Pattern is a conditional test finishing with '?'
				# EG if get(:informationWithheld).present?, if fetch("title").is_in(orcid|wikidata)?
				# Todo: generate if parser action and set contained instructions as sub-actions, yield action

				yield parser_action


def set_up_transform_action(parser_action, transform_params=None, export_run_id=None):
	# Todo: validate the params
	# Todo: regex to ensure params are split correctly
	# Todo: once split, label unlabelled params and pass along with labelled params (eg default)
	transform_params = transform_params.split(", ") if transform_params else None

	match parser_action.function_type:
		# Main functions
		case "attribute":
			if not parser_action.actions:
				# Add sub-action to fetch value from the provided path
				if hasattr(parser_action, "optional_path"):
					sub_action = ParserAction(export_run_id=export_run_id)
					sub_action.function_type = "fetch"
					setattr(sub_action, "path", parser_action.optional_path)
					parser_action.actions.append(sub_action)

		case "field":
			if not parser_action.actions:
				# Add sub-action to directly call attribute of the same name
				sub_action = ParserAction(export_run_id=export_run_id)
				sub_action.function_type = "get"
				sub_action.label = parser_action.label
				parser_action.actions.append(sub_action)

		case "reject_if":
			pass

		case "flag":
			pass

		case "local":
			# Params: label (required), target, default
			parser_action.label = transform_params[0]
			# Todo: where else is use of 'this' applicable
			if transform_params[1] == "this":
				parser_action.target = ":this"
			else:
				for transform_action in step_through_transform(transform_params[1], export_run_id=export_run_id):
					parser_action.actions.append(transform_action)

		case "transpose":
			# Params: target, enrichment action, condition (optional)
			parser_action.target = transform_params[0]
			if not parser_action.target == ":all":
				setattr(parser_action, "enrichment", transform_params[1])

			try:
				parser_action.condition = transform_params[2]
			except IndexError:
				parser_action.condition = "always"

		case "default":
			default_value = transform_params[0]
			default_script = f"fallback(set_value('{default_value}'))"
			for sub_action in step_through_transform(default_script, export_run_id=export_run_id):
				parser_action.actions.append(sub_action)

		# Transform actions
		case "get":
			setattr(parser_action, "target", transform_params[0])

		case "fetch":
			setattr(parser_action, "path", transform_params[0])

		case "add":
			parser_action.current_value = transform_params[0]

		case "compose":
			# Check each params' type - can be a string or function
			for param in transform_params:
				sub_action = check_param_type(param, export_run_id)
				parser_action.actions.append(sub_action)

		case "fallback":
			for transform_action in step_through_transform(transform_params[0], export_run_id=export_run_id):
				parser_action.actions.append(transform_action)

		case "for_each":
			for transform_action in step_through_transform(transform_params[0], export_run_id=export_run_id):
				parser_action.actions.append(transform_action)

		case "lookup":
			setattr(parser_action, "endpoint", transform_params[0])

		case "mapping":
			parser_action.target = transform_params[0]

		case "memo_check":
			for transform_action in step_through_transform(transform_params[0], export_run_id=export_run_id):
				parser_action.actions.append(transform_action)
			# Todo: target attribute is optional, allow for this
			parser_action.target = transform_params[1]

		case "select":
			setattr(parser_action, "first", transform_params[0])
			setattr(parser_action, "last", transform_params[1])

		case "sort_by":
			# param one: sort_param = alpha/numeric (default), date, or a list of values
			# param two: sort_order = asc (default), desc
			pass

		case "this":
			# Find the required part of a list/iterable. The iterating function will be tracking the index
			pass

		case "truncate":
			# param one: length (int)
			# param two: suffix (string) - if provided, the string will be shortened to accommodate it
			pass

		# Test actions
		case "if":
			for sub_action in step_through_transform(transform_params, export_run_id=export_run_id):
				parser_action.actions.append(sub_action)

		case "includes" | "is_in":
			setattr(parser_action, "condition", transform_params[0].split(", "))

		case "present" | "absent" | "lower" | "upper" | "first" | "last" | "sort":
			pass


def review_action_params(action_label, action_params):
	# Identify and explicitly label an action's parameters
	# Get the accepted params for the action from app context and check what's provided

	reviewed_params = {}

	match action_label:
		case "compose":
			parts = []
			for param in action_params:
				# Todo: move regex matching to own area
				if re.match(r'[\w_]+\(.+\)', param):
			reviewed_params["parts"] = action_params

	parser_functions = app_context.parser_functions
	function_details = parser_functions[action_label]
	accepted_params = function_details["parameters"]

	# Todo: add this when the function details are loaded in at the start
	accepted_params.append({"name": "default", "required": False, "type": "string"})

	reviewed_params = {}
	param_position = 0
	for param in action_params:
		# Check if the param is already explicitly labeled
		# Todo: figure out regex for wider range of values
		if re.match(r'[\w_]+=\s*[\w_]+', param):
			param_name, param_value = param.split("=")
			if param_name in [i["name"] for i in accepted_params]:
				reviewed_params[param_name] = param_value

		# Check the param's position to find the label
		test_param = accepted_params[param_position]
		if "regex" in test_param:



def check_param_type(param, export_run_id):
	if re.match(r'".+"', param):
		# Param is a regular string
		sub_action = ParserAction(export_run_id=export_run_id)
		sub_action.function_type = "set"
		setattr(sub_action, "current_value", param)
	elif re.match(r':\w+', param):
		# Param is an existing attribute value
		sub_action = ParserAction(export_run_id=export_run_id)
		sub_action.function_type = "get"
		setattr(sub_action, "target", param)
	else:
		# Param is a transform function
		sub_action = step_through_transform(param, export_run_id)

	return sub_action


def check_for_default_value(param):
	# Todo: move to static function
	if re.match(r'default\s*=\s*.+', param):
		# Todo: regex/parse pattern to extract default value easily
		default_value = ""
		return default_value

	return None


def chomp_parsed_element(element_string, line):
	line = line.replace(element_string, "", 1)
	return line


def validate_parser_action(parser_action):
	# Ensure a parsed action will work before adding it to the parser

	return None


def set_attribute(parser_action, parsed_record):
	setattr(parsed_record, f"attr_{parser_action.label}", parser_action.current_value)


def set_field(parser_action, parsed_record):
	# Todo: at this point join list values, other last changes?
	parsed_record.parsed_fields[parser_action.label] = parser_action.current_value


def get_attribute(parser_action, parsed_record):
	try:
		parser_action.current_value = getattr(parsed_record, f"attr_{parser_action.label}")
	except AttributeError:
		parser_action.current_value = None


def fetch_value(parser_action, parsed_record, data_object, path, default=None):
	# Todo: add using ordinals for exploded records
	# Todo: add splitting for multiple paths if supplied
	# Run through record_navigation.get_field_value
	if isinstance(parser_action.path, list):
		fetch_values = []
		for fetch_path in parser_action.path:
			fetch_value = get_field_value(data_object, fetch_path)
			if fetch_value:
				if isinstance(fetch_value, list):
					fetch_values.extend(fetch_value)
				else:
					fetch_values.append(fetch_value)
		parser_action.current_value = fetch_values
	else:
		parser_action.current_value = get_field_value(parsed_record.record, parser_action.path)


def apply_mapping(parser_action):
	if isinstance(parser_action.target, str):
		# Mapping comes from an external source
		project = load_export_context(parser_action.export_run_id).project
		mapping_dict = project.external_data.get(parser_action.target, None)
		if mapping_dict:
			parser_action.current_value = mapping_dict.get(parser_action.current_value, None)

	elif isinstance(parser_action.target, dict):
		parser_action.current_value = parser_action.target.get(parser_action.current_value, None)

	else:
		parser_action.current_value = None


def lookup_record(parser_action):
	# Look up a record with its endpoint and id, return it
	memo = load_export_context(parser_action.export_run_id).memo
	record_storage = load_export_context(parser_action.export_run_id).record_store

	endpoint = parser_action.endpoint
	record_id = parser_action.current_value
	record_pid = generate_record_pid(endpoint=endpoint, record_id=record_id)
	record_entry = memo.memo.get(record_pid, None)

	record_is_available = True
	if record_entry:
		if not record_entry.in_memory:
			record_is_available = False
	else:
		record_is_available = False

	if not record_is_available:
		harvester = load_export_context(parser_action.export_run_id).harvester
		harvester.retrieve_lookup_record(endpoint, record_id)

	parser_action.current_value = record_storage.find_record(record_pid)


def fallback():
	pass


def for_each():
	pass


def memo_check(parser_action):
	# Todo: what exactly should be returned
	memo = load_export_context(parser_action.export_run_id).memo
	record_id = parser_action.current_value
	memo_entry = memo.memo.get(record_id, None)
	if memo_entry:
		if parser_action.target:
			parser_action.current_value = getattr(memo_entry, parser_action.target, None)
		else:
			parser_action.current_value = memo_entry
