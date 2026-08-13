FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY . /app
RUN pip install --no-cache-dir .

RUN addgroup --system nms && adduser --system --ingroup nms nms \
    && chown -R nms:nms /app
USER nms

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
