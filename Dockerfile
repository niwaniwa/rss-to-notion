FROM python:3.13.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates make git curl unzip \
    && rm -rf /var/lib/apt/lists/*


# 作業ディレクトリ
WORKDIR /workspaces