from src.setup.Settings import read_config
from src.datastore.Memo import memo
from src.util.IOInterface import load_file, write_file
from src.api.api_interface import Query


def check_for_deletions(platform_id=None):
	# Check memo contents against previous export to identify deleted records
	# Depending on platform, apply the relevant fix
	substitute_records = None

	# Don't run when testing with a max record limit - will return lots of false positives
	if not read_config("record_limit"):
		print("Checking for deletions")
		deletion_instructions = None

		pid_list = read_pid_list()
		if pid_list:
			deleted_records = find_deleted_records(pid_list)
			if deleted_records:
				match platform_id:
					case "gbif":
						deletion_instructions = check_gbif_deletions(deleted_records)
					case _:
						pass

			if deletion_instructions:
				substitute_records = create_substitute_records(deletion_instructions)

	return substitute_records


def read_pid_list():
	input_dir = read_config("input_dir")
	project_name = read_config("project_name")
	if not project_name:
		project_name = "latest_export"
	pid_list_path = f"{input_dir}/resources/maintenance/{project_name}_pids.txt"
	pid_list = load_file(pid_list_path)
	if pid_list:
		pid_list = pid_list.split("\n")
		return pid_list

	return None


def find_deleted_records(pid_list):
	# Identify records in the previous export that are no longer live
	deleted_records = []
	for pid in pid_list:
		if pid not in memo.keys():
			deleted_records.append(pid)
	return deleted_records


def check_gbif_deletions(deleted_records):
	print("Checking GBIF for deletions")
	deletion_instructions = {pid: {"create_substitute": False,
	                               "uploaded_record": None,
	                               "external_id": None} for pid in deleted_records}
	for pid in deleted_records:
		# Check that the record is still live on GBIF
		query_url = "https://api.gbif.org/v1/occurrence/search"
		params = {"occurrenceId": pid}
		response = Query(url=query_url, params=params).response
		if not response:
			print(f"Failed to get response from GBIF API for {pid}")
		else:
			if response.status_code == 200:
				response_json = response.json()
				results = response_json.get("results")
				if results:
					# If the record is live, prepare to create blanked substitute record and request deletion
					record = results[0]
					external_id = record.get("key")
					create_substitute = True
					if record:
						print(record)
						if "informationWithheld" in record:
							if "Record removed from public access" in record.get("informationWithheld"):
								create_substitute = False
						instructions_update = {"create_substitute": create_substitute,
						                       "uploaded_record": record,
						                       "external_id": external_id}
						deletion_instructions[pid].update(instructions_update)

	return deletion_instructions


def create_substitute_records(deletion_instructions):
	# Substitute in a version of a record using alternate mapping
	substitute_mapping = load_file("src/resources/mapfiles/{}".format(read_config("substitution_map")))
	substitute_records = []
	for pid, instructions in deletion_instructions.items():
		if instructions.get("create_substitute"):
			substitute_record = format_substitute_record(substitute_mapping, instructions)
			if substitute_record:
				substitute_records.append(substitute_record)

	return substitute_records


def format_substitute_record(substitute_mapping, instructions):
	record = instructions.get("uploaded_record")
	substitute_record = {}
	for field in substitute_mapping.get("fields"):
		if field.get("hardcoded"):
			substitute_record.update({field["label"]: field["hardcoded"]})
		elif field.get("read_from"):
			field_label = field["read_from"]
			value = record.get(field_label)
			if not value:
				alt_field_label = field.get("alt_read_from")
				if alt_field_label:
					value = record.get(alt_field_label)
			if not value:
				value = ""
			substitute_record.update({field["label"]: value})

	return substitute_record
