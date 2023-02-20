# bigleaf-exporter
Prometheus exporter for Bigleaf® Networks status api

NOTE: This is not an official Bigleaf product. It is simply a personal/independent project to leverage Prometheus for purposes of observability and visualization of Bigleaf devices on a Grafana dashboard.

This container calls the Bigleaf status API and returns information across all sites and all circuits. It exposes prometheus metrics at http://localhost:8000/metrics

# Supported Metrics

circuit_status

site_status

site_information_info

# clone and build
```
git clone https://github.com/ether2/bigleaf-exporter
docker build -t bigleaf-exporter .
```
## docker
```
docker run -d -p 8000:8000 bigleaf-exporter
```
## docker compose
```
version: '3.8'
services:
  bigleaf-exporter:
    image: bigleaf-exporter
    container_name: bigleaf-exporter
    ports:
      - 8000:8000
    restart: always
```

# prometheus
Configure the prometheus.yml file with the bigleaf scrape job:
```
  - job_name: bigleaf
    metrics_path: /metrics
    scrape_interval: 10s
    scrape_timeout: 3s
    static_configs:
    - targets: "[localhost:8000]"
```
