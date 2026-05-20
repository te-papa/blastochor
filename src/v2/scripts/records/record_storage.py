# Containers and functions for big stacks of records as JSON or pandas dataframes
from scripts.exports.export_context import load_export_context
from scripts.util.io_interface import load_file, write_file
from scripts.util.helpers import generate_id_string, generate_record_pid

# Todo: work out how much crossover between json and pandas methods
# Use scripts.memo_manager.generate_record_pid() to get the record_pid value
class RecordStorage:
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id
		self.records = {}
		self.dataframe = None

	def find_record(self, record_pid):
		return self.records.get(record_pid)

	def add_record(self, record_pid, record):
		self.records[record_pid] = record

	def load_records(self, project_metadata):
		memo = load_export_context(self.export_run_id).memo
		for record_file in project_metadata["record_files"]:
			file_records = load_file(record_file)
			for record in file_records:
				record_pid = generate_record_pid(record=record)
				# Todo: find out the best method for checking a long set of ids
				if record_pid not in self.records:
					self.add_record(record_pid, record)
					memo.update_memo(record_pid=record_pid, update_type="in_memory", update_value=True)

	def yield_records(self, record_pids):
		for record_pid in record_pids:
			yield record_pid, self.find_record(record_pid)
