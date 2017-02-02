FROM tiangolo/uwsgi-nginx-flask:flask


# copy over our requirements.txt file
WORKDIR /app
COPY requirements.txt /tmp/
RUN mkdir -p ~/.aws

COPY ./my_nginx.conf /etc/nginx/conf.d/
COPY nginx.conf /etc/nginx/conf.d/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY . /app