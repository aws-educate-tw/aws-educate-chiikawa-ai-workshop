FROM public.ecr.aws/lambda/python:3.11

COPY app/requirements.txt /var/task/

RUN pip install -r /var/task/requirements.txt

COPY app/ /var/task/

RUN chmod -R 755 /var/task/

CMD ["lambda_function.lambda_handler"]