# IPMI exporter

## config
The top level object (in this case `defaults` is the module that will be
passed into the scraper via the url param and will tell the scraper
what username and password to use

```yaml
default:
  auth:
    username: username
    password: password
 ```

Example
```yaml
new_gear:
  auth:
    username: 'WHAT'
    password: 'DO'
```

## Scrape Job
Scrape job inside of prom should look something like
```yaml
  - job_name: 'IPMI for new_gear'
     static_configs:
      - targets:
        - 1.2.3.4
     params:
      module: [new_gear] # make note this is our module from the above config
     relabel_configs:
       - source_labels: [__address__]
         target_label: __param_target
       - source_labels: [__param_target]
         target_label: instance
       - target_label: __address__
         replacement: ipmi-exporter:80
```
