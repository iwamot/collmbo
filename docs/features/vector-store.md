# Vector Store

Collmbo can retrieve context from a vector store (knowledge base) so the model can answer from your own documents (RAG).

The model is given a search tool and decides when to use it. The search runs through [LiteLLM's vector store integration](https://docs.litellm.ai/docs/completion/knowledgebase), so any provider it supports works.

## Usage

Set `VECTOR_STORE_IDS` to your vector store ID and `VECTOR_STORE_PROVIDER` to its provider:

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-5.5
VECTOR_STORE_IDS=vs_...
VECTOR_STORE_PROVIDER=openai

$ docker run -it --env-file ./env ghcr.io/iwamot/collmbo:latest
```

To search multiple stores, separate IDs with commas:

```sh
VECTOR_STORE_IDS=vs_aaa,vs_bbb
```
