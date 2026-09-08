FROM public.ecr.aws/lambda/python:3.11

RUN microdnf update -y && \
    microdnf install -y mesa-libGL glib2 && \
    microdnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy weights to a dedicated path
COPY weights/ /var/task/weights/

# Copy the contents of src directly into /var/task/
COPY src/ /var/task/

CMD ["detect_object.lambda_handler"]