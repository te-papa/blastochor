# Turn project query settings into queries and fire them off
# Receive and return the data for the export manager to save and use
# If extension harvests are needed, the export manager will supply new queries

from askCO import AskCO

from scripts.exports.export_context import load_export_context
from scripts.util.helpers import generate_id_string, generate_record_pid
from scripts.util.io_interface import write_file, find_project_file

class Harvester:
	# Use project and connection settings to enable querying
	# Todo: look at current supplejack model of initial query, following queries and stop condition
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id
		self.api_connection = None

	def set_up_harvest_connection(self, api_key, quiet=True):
		# Create API connection object
		# Todo: update askco to allow option of setting attempts and timeout at instantiation
		self.api_connection = AskCO(api_key=api_key, quiet=quiet)
		pass

	def iterate_export_queries(self):
		project = load_export_context(self.export_run_id).project
		for query_segment in project.project_queries:
			output_label = query_segment.get("output_label")
			segment_queries = query_segment.get("queries")
			for query_details in segment_queries:
				query_details = prep_query(query_details, project=project)
				if query_details.get("query_mode") == "list":
					self.run_bulk_query(query_details, output_label)
				else:
					self.run_harvest_query(query_details, output_label)

	def run_harvest_query(self, query_details, output_label=None):
		# Todo: figure out how to isolate the askco yielding so it can be more easily replaced by others
		# Use the connection to send the query and return results
		results = []
		if query_details.get("query_mode") == "resource":
			# Todo: handle single record retrieval, ensure saving a dict works
			pass
		else:
			for response, records in self.api_connection.get_search_results(query_details):
				if response.okay:
					self.review_records(records, output_label=output_label)
					results.extend(records)

		self.save_results_to_temp(query_details.get("endpoint"), results)

	def review_records(self, records, output_label=None):
		memo = load_export_context(self.export_run_id).memo
		for record in records:
			memo.add_record_to_memo(record=record, output_label=output_label)

	def retrieve_lookup_record(self, endpoint, record_id):
		memo = load_export_context(self.export_run_id).memo
		record_storage = load_export_context(self.export_run_id).record_storage
		record_pid = generate_record_pid(endpoint=endpoint, record_id=record_id)

		record = self.run_single_record_query(endpoint, record_id)
		if record:
			# Todo: params or somethin' to ensure 'in_memory' flag is set
			memo.add_record_to_memo(record_pid=record_pid, record=record)
			self.save_results_to_temp(endpoint, [record])
			record_storage.add_record(record_pid=record_pid, record=record)

	def run_single_record_query(self, endpoint, record_id):
		query_details = ({"query_mode": "resource",
		                  "endpoint": endpoint,
		                  "record_id": record_id})

		response, record = self.api_connection.get_single_record(query_details)
		return record

	def save_results_to_temp(self, results, endpoint=None):
		# Todo: consider option to save in defined chunks so certain things can be more easily found/files aren't too big
		# Save results to temp location as received, return path
		project = load_export_context(self.export_run_id).project
		harvest_run_id = generate_id_string()
		temp_file_path = f"temp/{self.export_run_id}/{harvest_run_id}.json"
		write_file(temp_file_path, results)
		file_details = {"file_path": temp_file_path, "endpoint": endpoint}
		project.project_metadata["temp_record_files"].append(file_details)
		return temp_file_path

	def run_bulk_query(self, query_details, output_label=None):
		# Split the list query into multiple searches to avoid length limits
		# Todo: get limit from config somewhere
		project = load_export_context(self.export_run_id).project
		bulk_query_limit = project.project_settings.defaults.get("bulk_query_limit")
		list_filter_values = query_details["filters"][0]["value"]
		list_chunks = [list_filter_values[i:i + bulk_query_limit] for i in range(0, len(list_filter_values), bulk_query_limit)]
		for chunk in list_chunks:
			query_details["filters"][0]["value"] = chunk
			self.run_harvest_query(query_details, output_label=output_label)



def prep_query(query_details, project=None):
	# Move relevant query details into params
	query_details["params"] = {}
	for key, value in query_details.items():
		if key in ["fields", "filters", "from", "size", "sort", "types"]:
			query_details.params[key] = value
		if key == "record_ids":
			record_list_filter = load_query_record_ids(query_details, project)
			query_details["filters"].append(record_list_filter)

	# Ensure query mode is set
	if not query_details.get("query_mode"):
		default_query_mode = project.project_settings.defaults.get("query_mode")
		query_details["query_mode"] = default_query_mode

	# Todo: check for attempts and timeout in project settings/config
	return query_details


def load_query_record_ids(list_query_details, project):
	record_list = None
	record_ids = list_query_details.get("record_ids")

	if isinstance(record_ids, str):
		# Load a list of record ids from a file name/path
		record_list_file = list_query_details["list_source"]
		record_list = find_project_file(record_list_file, project.project_id)
		if list_query_details.get("list_source_column"):
			record_list = [row[list_query_details["list_source_column"]] for row in record_list]

	elif isinstance(record_ids, list):
		# Or read the provided list directly from the query details
		record_list = list_query_details["record_ids"]

	# Identify the field containing record id values
	field_label = list_query_details.get("record_id_label")
	if not field_label:
		field_label = "id"

	if record_list:
		record_list_filter = {"type": "in",
		                      "field": field_label,
		                      "value": record_list}

		return record_list_filter

	return None
