# LLM Security Scanner

LLM Security Scanner is a Streamlit-based application that allows you to analyze vulnerabilities in Large Language Models (LLMs) using the `prompt-security-fuzzer` tool. It provides a user-friendly interface to configure, run, and review the results of security fuzzing tests on various LLM providers such as OpenAI, Anthropic, Cohere, and Google PaLM.

## Features
- **API Key Management:** Easily configure API keys for OpenAI, Anthropic, and Google PaLM.
- **Provider & Model Selection:** Choose target and attack LLM providers and models.
- **Prompt Management:** Enter or upload system prompts for testing.
- **Attack Configuration:** Select from a wide range of attack types or run all available attacks.
- **Real-Time Output:** View real-time fuzzer output and results summary.
- **Troubleshooting Tips:** Get actionable suggestions for common issues.

## Installation

1. **(Optional) Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install dependencies:**
   ```bash
   pip install streamlit pandas prompt-security-fuzzer
   ```

## Usage
1. **Set your API keys** for the providers you want to use (OpenAI, Anthropic, Google PaLM) in the sidebar.
2. **Configure the fuzzer:**
   - Select target and attack providers/models.
   - Enter or upload a system prompt.
   - Choose attack types and parameters.
3. **Start the analysis** by clicking the "Start Vulnerability Analysis" button.
4. **Review the results** in the output and summary tables.

To run the app:
```bash
streamlit run app.py
```

## Requirements
- Python 3.8+
- [prompt-security-fuzzer](https://pypi.org/project/prompt-security-fuzzer/)
- streamlit
- pandas

## Troubleshooting
- If you encounter backend or API key errors, try switching providers (Anthropic is recommended for stability).
- Ensure your API keys are valid and have sufficient quota.
- If `prompt-security-fuzzer` is not found, install it with `pip install prompt-security-fuzzer`.

## License
MIT License

## Acknowledgements
- [prompt-security-fuzzer](https://github.com/danielmiessler/prompt-security-fuzzer)
- [Streamlit](https://streamlit.io/) 