# Pseudocode file for V2 planning

class ClassList():
	# Blasto
	# AppConfig
	# Project, ProjectManager, ProjectConfig, ProjectMapping, ProjectQuery
	# ExportManager, ExportWorker
	# MemoManager, RecordMemo, Record
	# Harvester
	# ApiConnection
	# MessageManager, Message
	# ProcessingManager, DatasetProcessor, RecordProcessor, FieldProcessor
	# OutputManager, OutputFile
	pass

# Blasto
def run():
	# Launch app if not being used as a module
	# Not user-based, just choose (or create/edit) a project and run
	# README tells user how to set up alternative API hooks/config
	pass

def blasto_api():
	# See supplejack api https://digitalnz.github.io/supplejack/components/supplejack-api.html
	# Startup, read in app config
	# Create/edit a project, manage/view projects
	# Start a project run - trigger export manager and export worker
	pass

def blasto_cli():
	# CLI hooks for api
	pass

# Export
def export_manager():
	# Run/view harvests, status etc
	# Set export workers going - generate a temp dir, metadata file...
	# Track and trigger steps, apply workarounds as needed
	pass

def export_worker(project):
	# Run through steps using project details - memo, harvest, check for extra queries etc
	# Report status back to manager
	# Allow preview of export results - eg run just to get 1 record/page, process and display
	pass

# Harvester
def harvest_collections_data(project_details):
	# Run harvesting process - generate and run query, save data locally, interface with memo
	pass

def generate_query(query_details):
	# Turn saved query details into actionable query
	pass

def retrieve_data():
	pass

def store_temp_data():
	pass

# Logging
def logging():
	# Standard logging setup, whatever that is
	pass

def report_log():
	# Define outputs/messages derived from logs
	pass

# Memo
def memo_manager():
	# Create a memo for a project, interface with it
	pass

def various_memo_functions():
	pass

# Messaging
def message_manager():
	# Objects and functions that allow key info and human-readable messages to be sent around
	pass

def message():
	# Probably a class with some standard options, called by the rest of the app
	pass

# Processing
def processing_manager():
	# Run processing across a project's dataset
	# Create object to hold transformed data
	# Check config/mapping and apply dataset/record/field level as needed
	pass

def dataset_processing():
	# Use config/mapping to identify dataset-level processing
	# Pass to required functions and update memo/transform data as needed
	# Eg mark records as related in x way, is connected to a restricted collection event
	pass

def record_processing():
	# Use config/mapping/memo to identify record-level processing
	# Pass to required functions and update memo/transform data as needed
	# Eg record not to be written, y fields must be redacted, z image removed
	pass

def field_processing():
	# Use config/mapping/memo to identify field-level processing
	# Pass to required functions and update memo/transform data as needed
	# Eg add literal value to transformed data object, don't include this value,
	# transform value in this way
	pass

def record_navigation():
	# Or whatever. Getting a specified piece of info
	# Can deal with str/int/list/dict, exists/not, true/false all that
	# Includes looking up other records, stepping through
	pass

def transforms():
	# Any change to a source value
	# Allow easy creation of new transforms - break down to fundamentals
	# -- math, string formatting etc
	# Can also be done to data retrieved by enrichments
	pass

def enrichments():
	# Functions to draw on external sources eg country codes
	# Like transforms, allow easy creation of new enrichments
	pass

def transform_tests():
	# Handle the running and evaluation of tests
	pass


# Projects
def project_manager():
	# Functions to access and edit project details, link to users
	pass

def create_new_project():
	# Choose a default including minimal, contact sheet, wiki, gbif; query or source list
	# Make it clear what needs to be filled in
	pass

def duplicate_project():
	# Copy an existing project, assign new id, config changes as needed
	# EG changing the owning user
	pass

def edit_project_config():
	pass

def edit_project_mapping():
	pass

def edit_project_query():
	pass

# Util
def source_interface():
	# Hooks for askCO by default but can be redirected by app config
	# Allow for multiple sources!
	pass

def http_interface():
	# Hooks for non-API http requests
	pass

def io_interface():
	# All IO read/write functions
	pass

def editing_interface():
	# Nav to/launch configs, mappings, queries for editing
	# Run validation post-edit, report any errors
	pass

# Validation
def validate_x(object_to_validate, validation_type):
	# Check a config, map, query - return status and clear error details in messagable way
	pass

# Writer
def output_manager():
	# Read from project details to get data into right places/structures, pass to IO
	# Also looks for other outputs, eg IRN lists
	pass


# Web
## Administrator
def app_management_web():
	# Admin app config, set up API hooks etc
	pass

## Project
def view_project():
	# Single project, my projects, all projects...
	pass

def create_project():
	pass

def edit_project():
	pass

## Export
def start_export():
	pass

def preview_export():
	pass

def run_export():
	pass

def view_export_status():
	pass

def view_export_results():
	pass

## User
def log_in_web():
	# Log in, out, register
	pass

def edit_user_prefs():
	pass

## Templates
def templates():
	# main - base, nav
	# messages - flash message templates, notifications
	# admin - app setup, user management
	# project - my projects, project view, project edit views
	# export - pre-launch options, preview, active (with status), complete/results
	# user - auth-related, preferences
	pass