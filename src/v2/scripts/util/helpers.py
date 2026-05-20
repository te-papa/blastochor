# Various little helper functions

def generate_id_string():
	# Todo: somewhere we have to check for uniqueness
	pass


def generate_record_pid(endpoint=None,
                        record_pid=None,
                        record_id=None,
                        record=None):
	# If you don't already have the pid, don't forget to supply the endpoint
	if not record_pid:
		if record:
			# Todo: have this work with parsing functionality and project config
			record_id = record.get("id")

		if endpoint and record_id:
			record_pid = generate_record_pid(endpoint, record_id)
		else:
			# Todo: raise an error
			return None

	return record_pid
