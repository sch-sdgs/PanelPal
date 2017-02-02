FROM tiangolo/uwsgi-nginx-flask:flask

COPY requirements.txt /tmp/

COPY . /tmp/PanelPal/

COPY resources/panel_pal.db /resources/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY ./app /app

WORKDIR /tmp/PanelPal

RUN pip install .

WORKDIR /app

ENV MESSAGE "PanelPal is running..."


