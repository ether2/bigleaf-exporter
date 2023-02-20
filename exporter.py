import requests
from prometheus_client import CollectorRegistry, Gauge, start_http_server, Info
import time
from requests.auth import HTTPBasicAuth
import yaml

# Load variables from config.yaml file
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

url = config['url']
token_key = config['token_key']
token_auth = config['token_auth']
scrape_frequency = int(config['scrape_frequency'])

# Create a new registry for our metrics
registry = CollectorRegistry()

# Create a new gauge metric to track circuit status
circuit_metric_name = 'circuit_status'
circuit_metric_help = 'Circuit status (0 for "Healthy", 1 for "Circuit Issues", 2 for "Circuit Down")'
circuit_labels = ['site_name', 'circuit_name']
circuit_gauge = Gauge(circuit_metric_name, circuit_metric_help, labelnames=circuit_labels, registry=registry)

# Create a new gauge metric to track site status
site_metric_name = 'site_status'
site_metric_help = 'Site status (0 for "Site Healthy", 1 for "Degraded Availability", 2 for "Circuit Issues", 3 for "Site Offline")'
site_labels = ['site_name', 'site_status']
site_gauge = Gauge(site_metric_name, site_metric_help, labelnames=site_labels, registry=registry)

# Create a new info metric to track site information
site_information = Info('site_information', 'Site information', registry=registry, labelnames=['site_id', 'site_name', 'company_name', 'company_id'])

# Scrape the API and update the gauge metric with the circuit status and info metric with site information
def scrape_api():
    try:
        response = requests.get(url, auth = HTTPBasicAuth(token_key, token_auth))
        response.raise_for_status()
        json_response = response.json()
        sites = json_response['data']['sites']
        for site in sites:
            site_id = site['site_id']
            site_name = site['site_name']
            company_name = site['company_name']
            company_id = site['company_id']
            site_status = site['site_status']
            site_information.labels(site_id=str(site_id), site_name=site_name, company_name=company_name, company_id=str(company_id)).info({})
            circuits = site['circuits']
            for circuit in circuits:
                circuit_name = circuit['circuit_name']
                circuit_status = circuit['circuit_status']
                if circuit_status == 'Healthy':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(0)
                elif circuit_status == 'Issues':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(1)
                elif circuit_status == 'Circuit Down':
                    circuit_gauge.labels(site_name=site_name, circuit_name=circuit_name).set(2)
            if site_status == "Site Healthy":
                site_gauge.labels(site_name=site_name, site_status=site_status).set(0)
            elif site_status == "Degraded Availability":
                site_gauge.labels(site_name=site_name, site_status=site_status).set(1)
            elif site_status == "Circuit Issues":
                site_gauge.labels(site_name=site_name, site_status=site_status).set(2)
            elif site_status == "Site Offline":
                site_gauge.labels(site_name=site_name, site_status=site_status).set(3)
    except requests.exceptions.RequestException as error:
        print(error)

# Start an HTTP server to expose the metrics for Prometheus to scrape
start_http_server(8000, registry=registry)

# Scrape the API every {scrape_frequency} seconds and push the metrics to Prometheus
while True:
    scrape_api()
    time.sleep(scrape_frequency)
