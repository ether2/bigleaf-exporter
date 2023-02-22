import requests
from prometheus_client import CollectorRegistry, Gauge, start_http_server, Info
import time
from requests.auth import HTTPBasicAuth
import yaml
import logging

# Load variables from config.yaml file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

url = config['url']
token_key = config['token_key']
token_auth = config['token_auth']
scrape_frequency = int(config['scrape_frequency'])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a new registry for our metrics
registry = CollectorRegistry()

# Create a new gauge metric to track circuit status
circuit_metric_name = 'bigleaf_circuit_status'
circuit_metric_help = 'Circuit status (0 for "Healthy", 1 for "Circuit Issues", 2 for "Circuit Down")'
circuit_labels = ['site_name', 'circuit_name']
circuit_gauge = Gauge(circuit_metric_name, circuit_metric_help, labelnames=circuit_labels, registry=registry)

# Create a new gauge metric to track site status
site_metric_name = 'bigleaf_site_status'
site_metric_help = 'Site status (0 for "Site Healthy", 1 for "Degraded Availability", 2 for "Circuit Issues", 3 for "Site Offline")'
site_labels = ['site_name']
site_gauge = Gauge(site_metric_name, site_metric_help, labelnames=site_labels, registry=registry)

# Create new gauge metrics to track the api call
request_response_time_name = 'bigleaf_response_time'
request_response_time_help = 'Response time in ms'
request_response_time_gauge = Gauge(request_response_time_name, request_response_time_help, registry=registry)

request_http_status_name = 'bigleaf_http_status'
request_http_status_help = 'HTTP request status: 200 OK = good'
request_http_status_gauge = Gauge(request_http_status_name, request_http_status_help, registry=registry)

# Scrape the API and update metrics
def scrape_api():
    try:
        response = requests.get(url, auth = HTTPBasicAuth(token_key, token_auth))
        response.raise_for_status()
        logging.info('HTTP request successful with status code: %d', response.status_code)
        json_response = response.json()

        # set value of request_response_time_gauge
        request_response_time_gauge.set(round(float(json_response["response_time"][:-2])))
        request_http_status_gauge.set(round(json_response["http_status"]))

        # bigleaf_site
        sites = json_response['data']['sites']
        for site in sites:
            site_id = site['site_id'] # not in use, but could be added
            site_name = site['site_name']
            company_name = site['company_name'] # not in use, but could be added
            company_id = site['company_id'] # not in use, but could be added
            site_status = site['site_status']
            circuits = site['circuits']

            # bigleaf_circuit_status
            for circuit in circuits:
                circuit_name = circuit['circuit_name']
                circuit_status = circuit['circuit_status']
                if circuit_status == 'Healthy':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(0)
                elif circuit_status == 'Issues':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(1)
                elif circuit_status == 'Circuit Down':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(2)

            # bigleaf_site_status        
            if site_status == "Site Healthy":
                site_gauge.labels(site_name=site_name).set(0)
            elif site_status == "Degraded Availability":
                site_gauge.labels(site_name=site_name).set(1)
            elif site_status == "Circuit Issues":
                site_gauge.labels(site_name=site_name).set(2)
            elif site_status == "Site Offline":
                site_gauge.labels(site_name=site_name).set(3)
                
    # logging and error handling      
    except requests.exceptions.HTTPError as err:
        # Handle HTTP errors
        logging.error(f"HTTP error: {err}")
        print(f"HTTP error: {err}")
        return
    except requests.exceptions.ConnectionError as err:
        # Handle connection errors
        logging.error(f"Connection error: {err}")
        print(f"Connection error: {err}")
        return
    except requests.exceptions.Timeout as err:
        # Handle timeouts
        logging.error(f"Timeout error: {err}")
        print(f"Timeout error: {err}")
        return
    except requests.exceptions.RequestException as err:
        # Handle any other exceptions
        logging.error(f"Error: {err}")
        print(f"Error: {err}")
        return

# Start an HTTP server to expose the metrics for Prometheus to scrape
start_http_server(8000, registry=registry)

# Scrape the API every {scrape_frequency} seconds and push the metrics to Prometheus
while True:
    scrape_api()
    time.sleep(scrape_frequency)
