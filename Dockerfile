# The rulebook service (rulebook_gen/service.py) for the marketplace's offer wizard.
# The image is tagged with the rulebook commit it was built from, the same value
# that dataspace-on-upv pins in providers/RULEBOOK_REF.
FROM python:3.12-slim

ARG RULEBOOK_REF=unknown
WORKDIR /app
COPY rulebook_gen/ rulebook_gen/
COPY classes/ classes/
RUN echo "$RULEBOOK_REF" > rulebook_gen/REF \
    && useradd --system --uid 10001 rulebook
USER 10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"
CMD ["python", "-m", "rulebook_gen", "serve", "--port", "8080"]
