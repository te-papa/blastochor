from src.setup.Settings import read_config
from src.util.ProcessingFunctions import ValueContainer, literal, collate_list, contains, must_match
from src.util.IOInterface import load_file


class RowProcessor():
	def __init__(self, rules, output_row, requires):
		self.rules = rules
		self.output_row = output_row

		if requires:
			if not self.check_requirements(requires):
				self.output_row.write_out = False

		if self.output_row.write_out:
			self.run_field_processing()

	def check_requirements(self, requires):
		# Assumes OR for multiple requirements unless specified
		reqs_passed = self.apply_requirements(requires)
		return reqs_passed

	def apply_requirements(self, requires, operation="or"):
		requirement_results = []
		for requirement in requires:
			requirement_results.append(self.apply_single_requirement(requirement))

		req_passed = True

		# Fail if no requirements passed
		if operation == "or":
			if True not in requirement_results:
				req_passed = False

		# Fail if any requirements failed
		if operation == "and":
			if False in requirement_results:
				req_passed = False

		return req_passed

	def apply_single_requirement(self, requirement):
		# Check a single requirement, or iterate over a set where all are required
		match requirement["condition_type"]:
			case "and":
				return self.apply_requirements(requirement["conditions"], operation="and")

			case "or":
				return self.apply_requirements(requirement["conditions"], operation="or")

			case "bool":
				# Todo: Create a helper function that reliably reads API true/false values as bool
				match_value = requirement["match"]
				row_val = literal(data=self.output_row.data,
								  path=requirement["path"].split("."),
								  ordinal=self.output_row.explode.get("explode_ordinal"))
				if row_val == "false":
					row_val = False
				if row_val is None:
					row_val = False
				return match_value == row_val

			case "contains":
				if "i" in requirement["path"].split("."):
					row_val = collate_list(data=self.output_row.data,
										   path=requirement["path"])
				else:
					row_val = literal(data=self.output_row.data,
									  path=requirement["path"],
									  ordinal=self.output_row.explode.get("explode_ordinal"))

				if row_val:
					requested_values = requirement["match"].split("|")

					contains_match = contains(row_val, requested_values)
					return contains_match

				return False

			case "must_match":
				if "i" in requirement["path"].split("."):
					row_val = collate_list(data=self.output_row.data,
										   path=requirement["path"])
					if row_val:
						row_val = [str(value).lower() for value in row_val]
				else:
					row_val = literal(data=self.output_row.data,
									  path=requirement["path"],
									  ordinal=self.output_row.explode.get("explode_ordinal"))
					if row_val:
						row_val = str(row_val).lower()

				if row_val:
					if requirement.get("match"):
						authorities = requirement["match"].split("|")
					elif requirement.get("match_file"):
						authorities = [i.get(requirement["match_value_path"]) for i in load_file(requirement["match_file"])]
					else:
						authorities = None
					if authorities:
						authorities = [str(term).lower() for term in authorities]
						matching = must_match(data=row_val, authorities=authorities)
						return bool(matching)
				return None

	def run_field_processing(self):
		for rule in self.rules:
			value = None
			fieldname = rule.output_fieldname
			if not read_config("quiet"):
				print(f"Processing field: {fieldname}")
			if read_config("group_rows"):
				if self.check_for_inclusion(fieldname):
					value = ValueContainer(rule=rule, output_row=self.output_row).current_value
			else:
				value = ValueContainer(rule=rule, output_row=self.output_row).current_value

			if not value and (value != 0):
				value = ""

			if not read_config("quiet"):
				print(f"Final value for {fieldname}: {value}")

			self.output_row.values.update({fieldname: value})

	def check_for_inclusion(self, fieldname):
		# If grouping exploded rows, check if specific fields should be included/excluded
		row_role = self.output_row.group_role
		match row_role:
			case "child":
				fields = "child_fields"
			case "parent":
				fields = "parent_fields"
			case _:
				fields = "ungrouped_fields"

		if include_field(fieldname, read_config(fields)):
			return True


def include_field(fieldname, fields):
	include = fields.get("include")
	column_names = fields.get("fields").split(", ")

	if include:
		if fieldname in column_names:
			return True
	elif not include:
		if fieldname not in column_names:
			return True
