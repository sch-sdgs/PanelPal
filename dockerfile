FROM tiangolo/uwsgi-nginx-flask:flask

COPY requirements.txt /tmp/

COPY . /tmp/PanelPal/

COPY resources/panel_pal.db /resources/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY ./app /app

WORKDIR /tmp

RUN git clone https://github.com/sch-sdgs/SDGSCommonLibs.git

WORKDIR /tmp/SDGSCommonLibs

RUN git fetch

RUN git checkout sci_check

RUN pip install -r requirements.txt

RUN python setup.py install

WORKDIR /tmp

RUN git clone https://github.com/sch-sdgs/SDGSDataModels.git

WORKDIR /tmp/SDGSDataModels

RUN git checkout master

RUN pip install -r requirements.txt

RUN python build.py

RUN python setup.py install

WORKDIR /tmp/PanelPal

RUN python setup.py install

WORKDIR /app

ADD resources/bedtools-2.25.0.tar.gz /tmp/
WORKDIR /tmp/bedtools2
RUN make
ENV PATH $PATH:/tmp/bedtools2/bin

WORKDIR /app

RUN touch /tmp/PanelPal.log
RUN chmod 777 /tmp/PanelPal.log

ENV MESSAGE "PanelPal is running..."


