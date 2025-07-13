#!/bin/sh

ollama serve &

sleep 5 

download_model() {
  MODEL_NAME=$1

  if ollama list | grep -q "${MODEL_NAME}"; then
    echo "Model ${MODEL_NAME} already exists, skipping download."
  else
    echo "Downloading model ${MODEL_NAME}..."
    ollama pull "${MODEL_NAME}"
  fi
}

download_model "$OLLLAMA_MODEL_EMBEDDING"
download_model "$OLLLAMA_MODEL_CHAT"

wait
