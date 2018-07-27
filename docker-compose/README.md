## 

```
mkdir -p /opt/cyxtera/prometheus/ipmi_exporter/nginx
cp ipmi_configmap.yaml /opt/cyxtera/prometheus/ipmi_exporter
cp ipmi_nginx.conf /opt/cyxtera/prometheus/ipmi_exporter/nginx
docker-compose up -d
```
