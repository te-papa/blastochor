from requests import get, head, Session, exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Query:
	def __init__(self,
	             url=None,
	             method=None,
	             params=None,
	             headers=None,
	             allow_redirects=True,
	             stream=False,
	             timeout=(0.5, 3)):

		if not method:
			method = "GET"

		# Configure retry strategy
		retry_strategy = Retry(total=3,
		                       backoff_factor=1,
		                       status_forcelist=[500, 502, 503, 504],
		                       allowed_methods=["HEAD", "GET", "OPTIONS"])
		adapter = HTTPAdapter(max_retries=retry_strategy)
		session = Session()
		session.mount("https://", adapter)
		session.mount("http://", adapter)

		print(url)
		if params:
			print(params)

		self.response = None

		try:
			if method == "GET":
				self.response = session.get(url=url,
				                            params=params,
				                            headers=headers,
				                            stream=stream,
				                            allow_redirects=allow_redirects,
				                            timeout=timeout)
			elif method == "HEAD":
				self.response = session.head(url,
				                             params=params,
				                             headers=headers,
				                             allow_redirects=allow_redirects,
				                             timeout=timeout)
		except exceptions.ConnectionError as e:
			print(f"Request failed: {e}")
