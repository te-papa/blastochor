import yaml
from datetime import date
from src.setup.Settings import read_config, write_config
from src.monitoring.Stats import stats
from src.util.IOInterface import load_file, write_file
from src.datastore.Memo import memo


def generate_export_report():
	stats.process_runtimes()
	stats.count_new_and_modified()
	output_dir = read_config("output_dir")
	export_filename = read_config("export_filename")
	export_report_dir = "{d}/{e}".format(d=output_dir,
	                                     e=export_filename)
	export_report_path = "{d}/{f}.yaml".format(d=export_report_dir,
	                                           f=export_filename)
	write_config("export_report_path", export_report_path)
	export_report_dict = gather_report_data()
	with open(export_report_path, "w", encoding="utf-8") as export_report:
		yaml.dump(export_report_dict, export_report)

	if read_config("deletion_check"):
		# Store the export's pids so next export can check for deletions
		# Only tracking catalogue records for now
		pid_list = [pid for pid in memo.keys() if "object" in pid]
		input_dir = read_config("input_dir")
		project_name = read_config("project_name")
		if not project_name:
			project_name = "latest_export"
		output_path = f"{input_dir}/resources/maintenance/{project_name}_pids.txt"
		write_file(output_path, "\n".join(pid_list))

	stats.print_stats()


def gather_report_data():
	export_date = date.today()
	report_dict = {"export_id": read_config("export_id"),
	               "runtime": stats.run_time,
	               "api_calls": stats.api_call_count,
	               "harvest_time": stats.harvest_time,
	               "extension_time": stats.extension_time,
	               "extension_records": stats.extension_records_count,
	               "processing_time": stats.processing_time,
	               "export_filenames": stats.export_filenames,
	               "records_written": stats.file_write_counts,
	               "new_record_counts": stats.new_record_count,
	               "update_counts": stats.modified_record_count,
	               "year": export_date.year,
	               "month": export_date.month,
	               "day": export_date.day}
	return report_dict


def analyse_export():
	# Todo: Apply analysis to export report and flag issues
	output_dir = read_config("output_dir")
	export_report_path = read_config("export_report_path")
	if export_report_path:
		with open(export_report_path, "r", encoding="utf-8") as f:
			export_report = yaml.safe_load(f)
			export_files = export_report["export_filenames"]
			for file in export_files:
				export_file_path = "{d}/{f}".format(d=output_dir, f=file)
