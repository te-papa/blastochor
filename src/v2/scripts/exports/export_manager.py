# Run a project through harvest, processing and export
# Uses project settings to kick off steps, and reports back on progress

from scripts.harvest.harvester import Harvester
from scripts.memo.memo_manager import Memo
from scripts.output.output import OutputManager
from scripts.process.processing_manager import ProcessingManager
from scripts.records.record_storage import RecordStorage
from scripts.util.helpers import generate_id_string
from scripts.exports.export_context import register_export_context, load_export_context

class ExportManager:
	def __init__(self, project):
		# Todo: work out what's actually in project settings so I know what to put where
		self.export_run_id = generate_id_string()
		self.export_context = register_export_context(self.export_run_id)

		self.export_context.project = project
		self.export_context.memo = Memo(self.export_run_id)
		self.export_context.harvester = Harvester(self.export_run_id)
		self.export_context.record_storage = RecordStorage(self.export_run_id)
		self.export_context.processing_manager = ProcessingManager(self.export_run_id)
		self.export_context.output_manager = OutputManager(self.export_run_id)

		self.run_status = None

	def manage_run(self):
		# Todo: re-check validity of settings (also done when saving in project manager)
		# manage_run can be used multiple times to get preview data before doing a full run
		project = load_export_context(self.export_run_id).project
		harvester = load_export_context(self.export_run_id).harvester
		record_storage = load_export_context(self.export_run_id).record_storage

		# Run any set-up tasks
		project.prepare_export_run(self.export_run_id)
		self.run_status = "Ready"

		# Set up connection to API
		self.connect_to_api()

		# Run initial queries and save results
		harvester.iterate_export_queries()

		# Load in all records
		record_storage.load_records()

		# Apply any record set-wide processing
		# Todo: ensure any of this processing is applied to later lookups if needed
		# This is stuff like identifying records that need to be restricted
		processing_manager = load_export_context(self.export_run_id).processing_manager
		processing_manager.apply_record_set_processing(project.project_settings)


		# Trigger output(s) to pull required records for parsing by checking memo (ParsedRecords get attached to output)
		output_manager = load_export_context(self.export_run_id).output_manager
		output_manager.generate_outputs()
		output_manager.process_output_records()

		# Write output file(s)
		# Todo: make this an option that can be turned off for preview/debugging
		# Todo: or set up so preview has an alternative output mode (eg raw data for display)
		output_manager.write_outputs_to_file()


	def connect_to_api(self):
		project = load_export_context(self.export_run_id).project
		api_key = project.project_settings["api_key"]
		quiet = project.project_settings["quiet"]
		project.harvester.set_up_harvest_connection(api_key, quiet)
