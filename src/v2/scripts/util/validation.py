# Review files, fields etc to ensure they're valid
# Todo: when user wants to check an unready project, identify and return what's wrong in clear language
import os
from scripts.util.io_interface import check_for_project_dir, list_project_files, load_file


class ProjectValidation():
	def __init__(self, project=None, project_id=None):
		self.project = project
		self.project_id = project_id
		self.fail = False

		self.validation_details = {}
		self.errors = []

	def validate_project(self):
		# Check a loaded project or a project's source files
		validation_details = {}
		if not self.project:
			file_validation = self.check_project_files()
			if not file_validation:
				validation_details.update({"dir_present": False})
			else:
				validation_details.update(file_validation)

		settings_validation = check_project_settings(project, project_id)


	def check_project_files(self):
		dir_present = check_for_project_dir(self.project_id)
		settings_present = False
		query_present = False
		parser_present = False
		metadata_present = False
		all_present = False
		if dir_present:
			project_files = list_project_files(self.project_id)
			for project_file in project_files:
				if project_file.name == "project_settings.yaml":
					settings_present = True
				elif project_file.name == "queries.yaml":
					query_present = True
				elif "parser_script" in project_file.name:
					parser_present = True
				elif project_file.name == "project_metadata.yaml":
					metadata_present = True

			if settings_present and query_present and parser_present and metadata_present:
				all_present = True
			else:
				if not settings_present:
					self.errors.append("Project settings file not found")
				if not query_present:
					self.errors.append("Project queries file not found")
				if not parser_present:
					self.errors.append("No project parser scripts found")
				if not metadata_present:
					self.errors.append("Project metadata file not found")
				self.fail = True

			self.validation_details.update({"dir_present": dir_present,
			                                "settings_present": settings_present,
			                                "query_present": query_present,
			                                "parser_present": parser_present,
			                                "metadata_present": metadata_present,
			                                "all": all_present})

		else:
			self.errors.append("Project directory not found")
			self.fail = True


def check_project_settings(project=None, project_id=None):
	pass


def check_project_queries(project=None, project_id=None):
	query_schema = load_file("resources/validation/queries.yaml")
	query_details = {}

	if project:
		pass
	elif project_id:
		project_queries = load_file(f"resources/projects/{project_id}/queries.yaml")
		for query_segment in project_queries:
			query_details.update(check_query_element(query_segment, query_schema))


def check_query_element(query_element, query_schema):
	# Todo: get this all sorted out Lucy
	unknown_fields = []
	missing_fields = [i for i in query_schema.keys() if i.get("required")]
	for k, v in query_element.items():
		if k in query_schema:
			if query_schema[k].get("required"):
				missing_fields.remove(k)
			if query_schema[k].get("children"):
				query_details = check_query_element(v, query_schema)
		else:
			unknown_fields.append(k)

	return {"unknown_fields": unknown_fields, "missing_fields": missing_fields}


def check_project_parsers():
	pass


def check_project_metadata():
	pass
