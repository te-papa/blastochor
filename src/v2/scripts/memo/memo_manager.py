# Keep track of the records you're using, and how you want to use them
# The memo key is a combination of endpoint and record_id: "tepapa:collection/object/123456"
# You may need to add a function to generate a different key for your API
from scripts.exports.export_context import load_export_context
from scripts.util.helpers import generate_record_pid

class Memo():
	def __init__(self, export_run_id):
		self.export_run_id = export_run_id
		self.memo = {}

	# Add a memo entry by providing the record and its endpoint, its unique identifier (pid), or its endpoint and id
	# Optionally also supply the label for its output(s), whether it's been retrieved/loaded,
	# if it should be rejected at write, or any flags
	# If the record is already in the memo, it will be updated with any new information
	# Todo: this might need to be **kwargs too
	def add_record_to_memo(self, **kwargs):
		endpoint = kwargs.get("endpoint")
		record_pid = kwargs.get("record_pid")
		record_id = kwargs.get("record_id")
		record = kwargs.get("record")


		if not kwargs.get("record_pid"):
			record_pid = generate_record_pid(endpoint=endpoint, record_pid=record_pid, record_id=record_id, record=record)

		output_label = kwargs.get("output_label")
		outputs = {}
		if output_label:
			output_details = {"write": True}
			if isinstance(output_label, list):
				outputs = {label: output_details for label in output_label}
			else:
				outputs = {output_label: output_details}

		flag = kwargs.get("flag")
		flags = {}
		if flag:
			flags = flag

		retrieved = kwargs.get("retrieved")
		in_memory = kwargs.get("in_memory")
		if record_pid not in self.memo:
			self.memo[record_pid] = MemoEntry(record_pid=record_pid,
			                                  record_id=record_id,
			                                  endpoint=endpoint,
			                                  outputs=outputs,
			                                  retrieved=retrieved,
			                                  in_memory=in_memory,
			                                  reject=False,
			                                  flags=flag)

		else:
			self.update_memo_entry(record_pid=record_pid,
			                       record_id=record_id,
			                       endpoint=endpoint,
			                       outputs=outputs,
			                       retrieved=retrieved,
			                       in_memory=in_memory,
			                       reject=False,
			                       flags=flag)

		return self.memo[record_pid]

	def update_memo_entry(self, **kwargs):
		memo_entry = self.memo[kwargs.get("record_pid")]
		for key, value in kwargs.items():
			match key:
				case "reject" | "retrieved" | "in_memory":
					if not kwargs[key] == getattr(memo_entry, key):
						setattr(memo_entry, key, kwargs[key])

				case "outputs" | "flags":
					for label, details in value.items():
						if label not in getattr(memo_entry, key):
							getattr(memo_entry, key)[label] = details
						else:
							getattr(memo_entry, key)[label].update(details)

	# Convenience function to update a memo entry with only a specified change
	def update_memo(self, record_pid=None, record_id=None, endpoint=None, record=None,
	                update_type=None, update_value=None):
		if not record_pid:
			record_pid = generate_record_pid(endpoint=endpoint, record_pid=record_pid, record_id=record_id, record=record)

		# Todo: avoid trying to update a non-existent entry
		if record_pid not in self.memo:
			memo_entry = self.add_record_to_memo(endpoint=endpoint, record_pid=record_pid, record_id=record_id, record=record)
		else:
			memo_entry = self.memo[record_pid]

		update_kwargs = {"record_pid": record_pid, update_type: update_value}
		self.update_memo_entry(**update_kwargs)


class MemoEntry:
	def __init__(self, record_pid=None, record_id=None, endpoint=None, outputs=None, retrieved=False,
	             in_memory=False, reject=False, flags=None):
		self.record_pid = record_pid
		self.record_id = record_id
		self.endpoint = endpoint
		self.outputs = outputs if outputs else {}
		self.retrieved = retrieved
		self.in_memory = in_memory
		self.reject = reject
		self.flags = flags if flags else {}
