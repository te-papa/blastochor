from scripts.exports.export_context import load_export_context
from scripts.process.processing_manager import RecordParser
from scripts.util.io_interface import load_file, write_file


class OutputManager:
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id
		self.outputs = {}

	def generate_outputs(self):
		project = load_export_context(self.export_run_id).project
		project_outputs = project.project_settings.get("outputs", [])
		for output_details in project_outputs:
			self.outputs.update({output_details["label"]: OutputObject(output_details, self.export_run_id)})

	def process_output_records(self):
		for output_label, output in self.outputs.items():
			output.run_output()

	def write_outputs_to_file(self):
		# Todo: option to only write specified outputs
		for output_label, output in self.outputs.items():
			output.write_output()


class OutputObject:
	# Todo: think through options for extra outputs, eg IRN lists
	def __init__(self, output_details, export_run_id):
		self.export_run_id = export_run_id
		self.output_label = output_details["label"]
		self.output_format = output_details["output_format"]
		self.parser_script = output_details["parser_script"]
		self.parser = None

		self.source_record_ids = []
		self.parsed_records = []
		self.output_data = None

		self.load_parser_script()

	def load_parser_script(self):
		project = load_export_context(self.export_run_id).project
		project_id = project.project_id

		raw_parser = load_file(f"resources/project_files/{project_id}/parser_{self.parser_script}.txt")
		if raw_parser:
			self.parser = RecordParser(raw_parser, self.export_run_id)
		else:
			raise FileNotFoundError(f"Parser script not found: {self.parser_script}")

	def run_output(self):
		self.load_source_records()
		self.process_records()
		self.format_output_data()

	def load_source_records(self):
		memo = load_export_context(self.export_run_id).memo
		# Todo: ensure this works with a single label as well as a list of them
		self.source_record_ids = [pid for pid, record_entry in memo.memo.items() if self.output_label in record_entry.get("output_labels", [])]

	def process_records(self):
		if self.source_record_ids:
			record_storage = load_export_context(self.export_run_id).record_storage
			source_records = {source_record_id: record_storage.find_record(source_record_id) for source_record_id in self.source_record_ids}
			for source_record_id, source_record in record_storage.yield_records(self.source_record_ids):
				self.parsed_records.append(self.parser.apply_parser(source_record_id, source_record))

	def format_output_data(self):
		# Turn list of parsed records into a dataframe or JSON object
		formatted_data = []
		for record in self.parsed_records:
			# If data structure is flat, start with an empty list
			# Todo: option for nested structure
			formatted_record = {}
			if record.transpose:
				formatted_record = [{} for i in record.transpose]
			for output_field in self.parser.data_structure:
				formatted_value = record.parsed_fields.get(output_field, None)
				# Any additional work here?
				if record.transpose:
					if isinstance(formatted_value, dict):
						if "transpose_fill" in formatted_value:
							for i in len(formatted_record):
								formatted_record[i].update({output_field: formatted_value["transpose_fill"]})
						elif "transpose_values" in formatted_value:
							for i in formatted_value["transpose_values"]:
								formatted_record[i].update({output_field: formatted_value["transpose_values"][i]})
				formatted_record.update({output_field: formatted_value})

			if isinstance(formatted_record, list):
				formatted_data.append(formatted_record)
			elif isinstance(formatted_record, dict):
				formatted_data.extend(formatted_record)

	def write_output(self):
		# Todo: create a test/debug mode to return displayable data instead of/as well as writing file
		# Data at this point is JSON object (list of dicts) or dataframe

		# If dataframe
		match self.output_format:
			case "csv":
				file_path = self.generate_filename("csv")
				self.output_data.to_csv(file_path, index=False)

			case "json":
				file_path = self.generate_filename("json")
				json_data = self.output_data.to_json(orient="records")
				write_file(file_path, json_data)

		# If JSON object
		match self.output_format:
			case "csv":
				file_path = self.generate_filename("csv")
				write_file(file_path, self.output_data, fieldnames=self.parser.data_structure)

			case "json":
				file_path = self.generate_filename("json")
				write_file(file_path, self.output_data)

		pass

	def generate_filename(self, suffix):
		# Todo: what bits go where in dir/file name? Should include datetime string
		file_name = f"{self.output_label}_{self.export_run_id}.{suffix}"
		file_path = f"output/{self.export_run_id}/{file_name}"
		return file_path

