# LastMile AI Python Library

This library provides access to the LastMile AI API from Python. The code should reflect the same API endpoints documented here: https://lastmileai.dev/docs/api

## API Token

This library requires a LastMile AI API Token, which can be obtained from https://lastmileai.dev/settings?page=tokens.

Important note: this library should only be used from a server-side context, where the API key can be securely accessed. Using this library from client-side browser code will expose your private API key!

## Installation

```
pip install lastmileai
```

## Usage

### Initialize Library with API Key

This library needs to be configured with your API Token (aka API key) obtained above. You can store the API key in an environment variable or alternative secure storage that can be accessed in your server-side code. For example, to initialize the library with the API key loaded from environment variable:

```python
import os
from lastmileai import LastMile

lastmile = LastMile(api_key=os.environ["LASTMILEAI_API_KEY"])
```

### Completions -- Open AI Models

OpenAI completions are supported out-of the box for ChatGPT and GPT3 models:

```python
completion = lastmile.create_openai_completion(
  completion_params = {
    model: "text-davinci-003",
    prompt: "Your prompt here",
  }
)
```

```python
completion = lastmile.create_openai_chat_completion(
  completion_params = {
    model: "gpt-3.5-turbo",
    messages: [
      { role: "user", content: "Your prompt here" },
    ],
  }
)
```

### Completions -- Custom Models

```python
completion = lastmile.create_openai_completion(
  completion_params = {
    model: "text-davinci-003",
    prompt: "Your prompt here",
  },
  embedding_collection_id = "clfpqyvpp004npmzgp1d4j4fw"
)
```

## Run tests

After setting `LASTMILEAI_API_KEY` in your shell environment, run the following:

```
pip3 install -e .
python3 -m unittest discover test
```
