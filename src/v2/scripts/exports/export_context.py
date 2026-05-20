

class ExportRunContext:
	def __init__(self, export_run_id):
		self.export_run_id = None
		self.project = None
		self.memo = None
		self.harvester = None
		self.record_storage = None
		self.processing_manager = None
		self.output_manager = None


export_contexts = {}

def register_export_context(export_run_id):
	export_contexts[export_run_id] = ExportRunContext(export_run_id)
	return export_contexts[export_run_id]


def load_export_context(export_run_id):
	return export_contexts[export_run_id]
