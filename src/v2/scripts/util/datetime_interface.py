from datetime import datetime


def get_now(to_string=False):
	now = datetime.now()
	if to_string:
		now = now.strftime("%Y-%m-%d %H:%M:%S")
	return now
