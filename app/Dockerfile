FROM tiangolo/uwsgi-nginx-flask:flask

# ENV HTTP_PROXY http://proxy.local.hde.co.jp:9080
# ENV http_proxy http://proxy.local.hde.co.jp:9080


# RUN apt-get -y update
# RUN apt-get -y install vim

# # install npm
# RUN apt-get install -y nodejs
# RUN apt-get install -y npm
# RUN ln -s /usr/bin/nodejs /usr/bin/node

# # install bower
# RUN npm install --global bower








# upgrade pip and install required python packages

# copy over our requirements.txt file
WORKDIR /app
COPY requirements.txt /tmp/
RUN mkdir -p ~/.aws
# COPY ~/.aws/credentials ~/.aws/
COPY ./my_nginx.conf /etc/nginx/conf.d/

RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY . /app

# COPY nginx.conf /etc/nginx/
# COPY uwsgi.ini /etc/uwsgi/
COPY nginx.conf /etc/nginx/conf.d/

# RUN mkdir -p /etc/nginx/sites-available/
# COPY tweetsme.nginx.conf /etc/nginx/sites-available/
# RUN ln -s /etc/nginx/sites-available/tweetsme.nginx.conf /etc/nginx/sites-enabled

# RUN /etc/init.d/nginx restart

# RUN echo '{ "allow_root": true }' > /root/.bowerrc
# RUN bower install

# RUN bower install --save angular-timeago

# copy over our app code