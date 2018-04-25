import falcon
import yaml
from pyghmi.ipmi import command
from pyghmi.exceptions import IpmiException


with open('/config/ipmi_exporter/ipmi_configmap.yaml', 'r') as f:
    config = yaml.load(f)


# This is a promSQL metric object lifted from lampwins/junos_exporter
# https://github.com/lampwins/junos_exporter
class Metrics(object):
    """
    Store metrics and do conversions to PromQL syntax
    """

    class _Metric(object):
        """
        This is an actual metric entity
        """

        def __init__(self, name, value, metric_type, labels=None):
            self.name = name
            self.value = float(value)
            self.metric_type = metric_type
            self.labels = []
            if labels:
                for label_name, label_value in labels.items():
                    self.labels.append('{}="{}"'.format(label_name, label_value))

        def __str__(self):
            return "{}{} {}".format(self.name, "{" + ",".join(self.labels) + "}", self.value)

    def __init__(self):
        self._metrics_registry = {}
        self._metric_types = {}

    def register(self, name, metric_type):
        """
        Add a metric to the registry
        """
        if self._metrics_registry.get(name) is None:
            self._metrics_registry[name] = []
            self._metric_types[name] = metric_type
        else:
            raise ValueError('Metric named {} is already registered.'.format(name))

    def add_metric(self, name, value, labels=None):
        """
        Add a new metric
        """
        collector = self._metrics_registry.get(name)
        if collector is None:
            raise ValueError('Metric named {} is not registered.'.format(name))

        metric = self._Metric(name, value, self._metric_types[name], labels)
        collector.append(metric)

    def collect(self):
        """
        Collect all metrics and return
        """
        lines = []
        for name, metric_type in self._metric_types.items():
            lines.append("# TYPE {} {}".format(name, metric_type))
            lines.extend(self._metrics_registry[name])
        return "\n".join([str(x) for x in lines]) + '\n'


class MetricResource:
    def on_get(self, req, resp):
        """Handles GET requests"""
        # This end point will only provide plain/text so lets advertise as such
        resp.content_type = falcon.MEDIA_TEXT

        # Create out metrics object
        metrics = Metrics()

        # Get out victim
        target = req.get_param('target')
        module = req.get_param('module')
        if target is None or module is None:
            resp.status_code = 400
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {'Error': 'All required parameters are not defined'}
            return

        # get profile from config
        profile = config[module]['auth']

        # Make out pyghmi object
        try:
            ipmicmd = command.Command(bmc=target, userid=profile['username'], password=profile['password'])
        except IpmiException as e:
            resp.status_code = 403
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {'Error': 'IPMI Authentication Failure'}
            return
        # ipmicmd = command.Command(bmc="10.32.224.3", userid="ADMIN", password="ADMIN"

        # Query the rig
        results = [x for x in ipmicmd.get_sensor_data(timeout=50)]

        # Do work
        for sensor in results:
            sensor_name = 'ipmi_' + sensor.name.replace(' ', '_').replace('.','_').replace('-','_').lower()
            metrics.register(sensor_name, 'gauge')

        for metric in results:
            if metric.value is None:
                metric.value = 0
            metrics.add_metric('ipmi_' + metric.name.replace(' ', '_').replace('.','_').replace('-','_').lower(), metric.value,
                               labels={'type': metric.type, 'units': metric.units, 'instance': target})


        sel_data = [x for x in ipmicmd.get_event_log()]
        sel_ds = {0:0, 1:0, 2:0}
        # This will break if there is more than just 0,1,2 but for now its okay
        for sel in sel_data:
            count = sel_ds.get(sel['severity'],0)
            sel_ds[sel['severity']] = count + 1

        for k,v in sel_ds.iteritems():
            metric_name = 'ipmi_sel_{0}_events'.format(k)
            metrics.register(metric_name, 'counter')
            metrics.add_metric(metric_name, v)


        resp.body = metrics.collect()
        return resp


api = falcon.API()
api.add_route('/metrics', MetricResource())
