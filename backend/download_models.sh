#!/bin/sh

set -e

echo "Starting Ollama service in background..."
ollama serve &

sleep 5

download_model() {
  MODEL_NAME=$1

  if [ -z "$MODEL_NAME" ]; then
    echo "Model name is empty, skipping..."
    return
  fi

  echo "Checking if model '$MODEL_NAME' is already available..."
  if ollama list | grep -q "${MODEL_NAME}"; then
    echo "Model '${MODEL_NAME}' already exists – skipping download."
  else
    echo "Downloading model '${MODEL_NAME}'..."
    ollama pull "${MODEL_NAME}"
  fi
}

echo "Checking embedding model: $OLLAMA_MODEL_EMBEDDING"
download_model "$OLLAMA_MODEL_EMBEDDING"

echo "Checking chat model: $OLLAMA_MODEL_CHAT"
download_model "$OLLAMA_MODEL_CHAT"

echo "Finished downloading models. Waiting for Ollama server to exit..."
wait
