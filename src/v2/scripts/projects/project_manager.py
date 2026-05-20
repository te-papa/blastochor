from scripts.exports.export_context import load_export_context
from scripts.output.output import OutputManager

from scripts.util.io_interface import load_file, write_dir, write_file
from scripts.util.helpers import generate_record_pid
from scripts.util.datetime_interface import get_now
from scripts.util.io_interface import list_projects, find_project_file
from scripts.util.validation import validate_project


class ProjectManager():
	def __init__(self):
		self.active_projects = {}
		self.available_projects = {}

		self.list_projects()

	def list_projects(self):
		# Todo: ensure this updates when new projects are created/saved
		self.available_projects = list_projects()

	def start_new_project(self, project_name):
		project = Project()
		project.initialise_new_project(project_name)
		self.active_projects.update({project.project_id: project})

	def load_project(self, project_id):
		project = Project()
		project.load_project_from_file(project_id)
		self.active_projects.update({project.project_id: project})


class Project:
	# Hold details about a project to access easily across functions
	def __init__(self):
		self.project_id = None
		self.project_name = None
		self.project_dir = None
		self.project_metadata = {}
		self.project_settings = None
		self.project_queries = []
		self.external_data = {}

		self.outputs = None

	def initialise_new_project(self, project_name):
		# Todo: make it super easy to create a new project with the basics
		self.project_name = project_name
		self.project_id = generate_project_id(self.project_name)
		self.project_dir = f"resources/projects/{self.project_id}"
		generate_project_files(self.project_id)

	def initialise_project_settings(self):
		self.project_settings = ProjectSettings()

	def initialise_project_metadata(self):
		# Todo: what else goes here
		self.project_metadata = {"project_id": self.project_id,
		                         "temp_record_files": []}

	def initialise_project_queries(self):
		pass

	def load_project_from_file(self, project_id):
		self.project_id = project_id
		self.project_metadata = load_file(f"{self.project_dir}/project_metadata.yaml")
		self.project_name = self.project_metadata["project_name"]

		self.project_settings = load_file(f"{self.project_dir}/project_settings.yaml")
		self.project_queries = load_file(f"{self.project_dir}/project_query.yaml")

	def prepare_export_run(self, export_run_id):
		self.load_in_external_data()
		# Todo: load in and apply dataset-level processing eg restricting locality - this parser script isn't attached to an output
		self.generate_outputs(export_run_id)
		self.populate_skip_list(export_run_id)

	def load_in_external_data(self):
		# Import external structured data for use in parser actions
		# Todo: will need some kind of side script to make EMu collection event xml usable
		if "load_in" in self.project_settings:
			for external_source in self.project_settings["load_in"]:
				source_name = external_source["name"]
				external_data = find_project_file(external_source["path"], self.project_id)
				if external_data:
					self.external_data[source_name] = external_data

	def generate_outputs(self, export_run_id):
		# Set up output objects and load their parser scripts
		output_manager = load_export_context(export_run_id).output_manager
		output_manager.generate_outputs()

	def populate_skip_list(self, export_run_id):
		# A skip list can be a text file with one record pid per line, or a csv with a "pid" column or "endpoint" and "record_id" columns
		# Fieldcollections, taxa, agents, media etc included in the list will be removed from other records before processing
		# For example, a skipped image won't get a row in an output that transposes rows for each child image
		# Todo: allow for a skip list file to be in another location to allow reuse
		skip_list = self.project_settings.get("skip_list")
		memo = load_export_context(self)
		if skip_list:
			skip_list_path = f"{self.project_dir}/{skip_list}"
			skip_list_items = load_file(skip_list_path)
			if skip_list_items:
				for row in skip_list_items:
					if skip_list.endswith(".txt"):
						# Value must be a pid
						pid = row.strip()
						memo.add_record_to_memo(pid=pid, skip=True)
					elif skip_list.endswith(".csv"):
						if "pid" in row:
							pid = row["pid"]
						else:
							endpoint = row["endpoint"]
							record_id = row["record_id"]
							pid = generate_record_pid(endpoint=endpoint, record_id=record_id)

						memo.add_record_to_memo(pid=pid, skip=True)


class ProjectSettings:
	def __init__(self):
		self.project_id = None
		self.project_name = None
		self.api_connection_settings = {"attempts": None, "timeout": None}
		self.clean_newlines = True
		self.project_dir = None
		self.min_img_size = None
		self.max_img_size = None
		self.max_list_length = None
		self.dataset_processing_parser_script = None
		self.dataset_processing_parser = None
		self.outputs = {}
		self.defaults = {}


class ProjectQuery:
	def __init__(self):
		pass


class ProjectMapping:
	def __init__(self):
		pass


class ProjectManager:
	# Create, edit, and manage projects
	def __init__(self, project=None):
		self.project = project

	def create_project(self, project_name=None):
		# Initialise a new project with optional defaults
		if not self.project:
			self.project = Project(project_name=project_name)


		else:
			raise ValueError("Project manager already contains project, initialise a new ProjectManager")


def generate_project_id(project_name):
	# Todo: come up with a better way of generating project ids, ensure uniqueness
	return project_name.lower().replace(" ", "_")


def generate_project_files(project_id):
	# Todo: A lot more can be done to manage creating/editing projects, but doing read/run first
	write_dir(f"resources/projects/{project_id}")

	# Todo: move these to a default project template file
	now = get_now()
	project_metadata = {"project_id": project_id,
	                    "created": now,
	                    "modified": now}

	project_settings = {"api_key_env": None,
	                    "clean_newlines": None,
	                    "quiet": None,
	                    "timeout": None,
	                    "attempts": None,
	                    "load_in": None,
	                    "coordinate_workaround": None,
	                    "restrict_sensitive_locations": None,
	                    "deletion_check_map": None,
	                    "output_dir": None,
	                    "max_list_length": None}

	project_query = {"query_mode": None,
	                 "record_limit": None,
	                 "record_id_list": None,
	                 "skip_list": None,
	                 "q": None,
	                 "endpoint": None,
	                 "filters": None,
	                 "fields": None,
	                 "sort": None,
	                 "size": None}

	project_parser_script = ""

	write_file(f"resources/projects/{project_id}/project_metadata.yaml", project_metadata)
	write_file(f"resources/projects/{project_id}/project_settings.yaml", project_settings)
	write_file(f"resources/projects/{project_id}/project_query.yaml", project_query)
	write_file(f"resources/projects/{project_id}/project_parser_script.txt", project_parser_script)
