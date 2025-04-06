FROM public.ecr.aws/lambda/python:3.11

ARG MAP_API_KEY
ARG WEATHER_API_KEY

ENV MAP_API_KEY=${MAP_API_KEY}
ENV WEATHER_API_KEY=${WEATHER_API_KEY}

COPY app/requirements.txt /var/task/

RUN pip install -r /var/task/requirements.txt

COPY app/ /var/task/

RUN chmod -R 755 /var/task/

CMD ["lambda_function.lambda_handler"]