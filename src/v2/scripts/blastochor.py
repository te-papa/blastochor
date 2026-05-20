# Launch Blastochor and interface with it through the CLI or API calls

import click
from scripts.logging.app_logging import get_logger
from scripts.projects.project_manager import ProjectManager
from scripts.exports.export_manager import ExportManager


class BlastoContext:
	def __init__(self):
		self.app = Blastochor()

	def __enter__(self):
		return self.app

	def exit(self, ctx_type, ctx_value, ctx_traceback):
		self.app.exit_blasto()


class Blastochor:
	def __init__(self):
		# Todo: load in app settings
		self.app = None
		self.projects = ProjectManager()
		self.logger = get_logger()

	def run_project_export(self, project_id):
		self.projects.load_project(project_id)
		project = self.projects.active_projects[project_id]
		export_manager = ExportManager(project)
		return export_manager

	def exit_blasto(self):
		# Todo: confirmation, any cleanup
		print("You're free")
		exit()



class CliInterface:
	def __init__(self):
		self.blastochor = Blastochor()

	def display_interface(self):
		options = {"s": "Select a project", "h": "Read help", "x":"Exit"}
		print("Welcome to Blastochor!")
		for option, description in options.items():
			print(f"{option}: {description}")

		user_action = input("What would you like to do?: ")
		match user_action:
			case "s":
				self.display_projects()
			case "h":
				self.display_help()
			case "x":
				print("Cool, cool cool cool.")
				exit()
			case _:
				print("Nope. Please try again.")
				self.display_interface()

	def display_projects(self):
		# Todo: add keyboard navigation to CLI
		# Todo: page through projects
		# Todo: colour code project status, sort by ready first
		print("Select a project to run or review.")
		for project_id, project_metadata in self.blastochor.projects.available_projects.items():
			project_name = project_metadata["project_name"]
			project_description = project_metadata["project_description"]
			project_status = project_metadata["project_status"]
			print(f"{project_id}: {project_name} | {project_status}")
			print(f"\t{project_description}")

		user_action = input("Select a project ID to run or review: ")

	def display_help(self):
		pass


# Launch from the CLI to enter project selection, or run with options to automatically run that project
@click.command()
@click.option('--project', default='none', help='name of pre-defined project')
@click.option('--debug', default=False, help='run in debug mode')
@click.option('--record_limit', default=None, help='apply a limit to the number of records retrieved this run')
def main(project, debug, record_limit):
	blastochor = Blastochor()


# Todo: is this how this works?
if __name__ == "__main__":
	with BlastoContext() as blasto:
		app = blasto
