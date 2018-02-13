FROM pypy:2

RUN mkdir /etc/ipmi_exporter
COPY . /etc/ipmi_exporter
COPY gunicorn.conf /gunicorn.conf
RUN pip install -r /etc/ipmi_exporter/requirements.txt
WORKDIR /etc/ipmi_exporter


