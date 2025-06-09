# app.py dosyanızda bu değişiklikleri yapın:

# PS-FUZZ hatası için düzeltme kodu
import streamlit as st
import subprocess
import os
import pandas as pd
import tempfile 
import sys
import json
import re
import warnings
from datetime import datetime

st.set_page_config(page_title="LLM Security Scanner", layout="wide")

st.title("🔍 LLM Security Scanner")
st.caption("Analyze LLM vulnerabilities using prompt-security-fuzzer. Based on ps-fuzz.")

# Backend uyumluluk kontrolü eklendi
def check_backend_compatibility(provider):
    """Backend uyumluluğunu kontrol et"""
    supported_backends = {
        "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        "anthropic": ["claude-3-sonnet", "claude-3-haiku", "claude-2"],
        "cohere": ["command", "command-light"],
        "google_palm": ["models/chat-bison-001", "models/text-bison-001"] # Updated
    }
    return supported_backends.get(provider, [])

# Hata yakalama ve alternatif çözüm
def run_security_scan_with_fallback(command, env_vars): # Added env_vars argument
    """PS-FUZZ çalıştır, hata durumunda alternatif çözüm sun"""
    try:
        # Ana PS-FUZZ komutu
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            shell=False,
            env=env_vars # Pass the custom environment
        )
        
        return process
        
    except Exception as e:
        st.error(f"PS-FUZZ execution failed: {str(e)}")
        return None

# Ana arayüz kodunuz...
st.sidebar.header("🔑 API Key Configuration")
st.sidebar.info("Provide API keys for the LLM providers you intend to use.")

if 'openai_api_key' not in st.session_state: st.session_state.openai_api_key = ''
if 'google_api_key' not in st.session_state: st.session_state.google_api_key = ''
if 'anthropic_api_key' not in st.session_state: st.session_state.anthropic_api_key = ''

openai_api_key_input = st.sidebar.text_input("OpenAI API Key", type="password", value=st.session_state.openai_api_key)
google_api_key_input = st.sidebar.text_input("Google API Key", type="password", value=st.session_state.google_api_key)
anthropic_api_key_input = st.sidebar.text_input("Anthropic API Key", type="password", value=st.session_state.anthropic_api_key)

st.sidebar.header("🏠 Local Model Setup")
local_openai_base_url = st.sidebar.text_input("Local OpenAI-Compatible API Base (optional)", placeholder="http://localhost:8000/v1")

st.header("🚀 Fuzzer Configuration")
col1, col2 = st.columns(2)

# Desteklenen provider'lar - DÜZELTİLDİ
valid_providers = ["anthropic", "cohere", "google_palm", "open_ai"]  # Changed "openai" to "open_ai"

with col1:
    st.subheader("🎯 Target LLM")
    target_provider = st.selectbox("Target Provider", valid_providers, index=3)
    
    if target_provider == "open_ai":  # Changed to "open_ai"
        default_target_model = "gpt-3.5-turbo"
    elif target_provider == "anthropic":
        default_target_model = "claude-3-sonnet-20240229"
    elif target_provider == "cohere":
        default_target_model = "command"
    elif target_provider == "google_palm":
        default_target_model = "models/chat-bison-001"
    else:
        default_target_model = "models/chat-bison-001"

    target_model = st.text_input("Target Model", default_target_model)

    st.subheader("📝 System Prompt")
    system_prompt_source = st.radio("System Prompt Source:", ("Enter Manually", "Upload File"), horizontal=True)

    if "system_prompt_content" not in st.session_state:
        st.session_state.system_prompt_content = ""

    if system_prompt_source == "Upload File":
        system_prompt_file = st.file_uploader("Upload Prompt (.txt)", type=['txt'])
        if system_prompt_file:
            try:
                st.session_state.system_prompt_content = system_prompt_file.read().decode('utf-8')
                st.text_area("System Prompt Content:", st.session_state.system_prompt_content, height=150, disabled=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")
                st.session_state.system_prompt_content = ""
    else:
        st.session_state.system_prompt_content = st.text_area("Enter System Prompt:", value=st.session_state.system_prompt_content, height=150)

with col2:
    st.subheader("⚔️ Attack LLM")
    attack_provider = st.selectbox("Attack Provider", valid_providers, index=3)
    
    if attack_provider == "open_ai":  # Changed to "open_ai"
        default_attack_model = "gpt-3.5-turbo"
    elif attack_provider == "anthropic":
        default_attack_model = "claude-3-sonnet-20240229"
    elif attack_provider == "cohere":
        default_attack_model = "command"
    elif attack_provider == "google_palm":
        default_attack_model = "models/chat-bison-001"
    else:
        default_attack_model = "models/chat-bison-001"
        
    attack_model = st.text_input("Attack Model", default_attack_model)

    # Slider bug fixed. (03.06.2025)
    attack_temperature = st.slider("Attack Temperature", 0.0, 1.0, 0.7, 0.05)

    st.subheader("🧪 Test Parameters")
    num_attempts = st.number_input("Number of attack prompts", min_value=1, value=3)

    attacks = [
        "aim_jailbreak", "affirmative_suffix", "amnesia", "contextual_redirection", "dan_jailbreak",
        "harmful_behavior", "linguistic_evasion", "self_refine", "ucar", "base64_evasion",
        "authoritative_role_impersonation", "complimentary_transition", "ethical_compliance",
        "typoglycemia_attack", "system_prompt_stealer"
    ]
    run_all_attacks = st.checkbox("Run all available attacks", value=True)
    selected_attacks = st.multiselect("Select specific attacks", options=attacks, default=["ucar", "amnesia"]) if not run_all_attacks else []

# Ana tarama butonu - geliştirilmiş hata yakalama ile
if st.button("🚀 Start Vulnerability Analysis", type="primary"):
    final_system_prompt = st.session_state.get("system_prompt_content", "").strip()

    # Validasyon kontrolleri
    if not final_system_prompt:
        st.error("Please provide a system prompt.")
    elif not target_provider or not target_model:
        st.error("Target provider and model required.")
    elif not attack_provider or not attack_model:
        st.error("Attack provider and model required.")
    # Ensure your existing API key validation checks for "open_ai" are correct
    elif target_provider == "open_ai" and not openai_api_key_input:
        st.error("OpenAI selected but no API key provided.")
    elif attack_provider == "open_ai" and not openai_api_key_input:
        st.error("OpenAI attack provider selected but no API key provided.")
    elif target_provider == "anthropic" and not anthropic_api_key_input:
        st.error("Anthropic selected but no API key provided.")
    elif attack_provider == "anthropic" and not anthropic_api_key_input:
        st.error("Anthropic attack provider selected but no API key provided.")
    # Add similar checks for other providers if they require API keys (e.g., google_palm)
    elif target_provider == "google_palm" and not google_api_key_input:
        st.error("Google PaLM selected but no API key provided.")
    elif attack_provider == "google_palm" and not google_api_key_input:
        st.error("Google PaLM attack provider selected but no API key provided.")
    elif not run_all_attacks and not selected_attacks:
        st.error("Select at least one attack or enable 'Run all'.")
    else:
        temp_prompt_file_path = ""
        try:
            # Prepare custom environment for the subprocess
            custom_env = os.environ.copy()

            # Suppress the specific pkg_resources UserWarning in the subprocess
            # by setting the PYTHONWARNINGS environment variable.
            custom_env['PYTHONWARNINGS'] = 'ignore:pkg_resources is deprecated'

            if openai_api_key_input:
                custom_env["OPENAI_API_KEY"] = openai_api_key_input
            if google_api_key_input: # Ensure this is set for google_palm
                custom_env["GOOGLE_API_KEY"] = google_api_key_input
            if anthropic_api_key_input:
                custom_env["ANTHROPIC_API_KEY"] = anthropic_api_key_input

            # Apply OpenAI specific config (logic from old fix_backend_config)
            if target_provider == "open_ai" or attack_provider == "open_ai":
                custom_env["OPENAI_API_TYPE"] = "openai"
                # If OPENAI_API_VERSION was ever needed for Azure, ensure it's not set for standard OpenAI:
                # custom_env.pop("OPENAI_API_VERSION", None)

            if local_openai_base_url:
                custom_env["OPENAI_API_BASE"] = local_openai_base_url
            else:
                # Ensure OPENAI_API_BASE is not set if local_openai_base_url is empty
                custom_env.pop("OPENAI_API_BASE", None)

            # Explicitly remove common proxy environment variables
            proxy_vars_to_remove = [
                "HTTP_PROXY", "HTTPS_PROXY", 
                "http_proxy", "https_proxy", # Case-sensitive variations
                "NO_PROXY", "FTP_PROXY", "ALL_PROXY", "ftp_proxy", "all_proxy",
                "OPENAI_PROXY" 
            ]
            for var_name in proxy_vars_to_remove:
                custom_env.pop(var_name, None)
            
            # Temp dosya oluştur
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding='utf-8') as tmp_prompt_file:
                tmp_prompt_file.write(final_system_prompt)
                temp_prompt_file_path = tmp_prompt_file.name

            # Komut oluştur - düzeltilmiş
            command = [
                "prompt-security-fuzzer",
                "-b", temp_prompt_file_path,
                "--target-provider", target_provider,
                "--target-model", target_model,
                "--attack-provider", attack_provider,
                "--attack-model", attack_model,
                "--attack-temperature", str(attack_temperature),
                "--num-attempts", str(num_attempts),
            ]

            if not run_all_attacks and selected_attacks:
                command.append("--tests")
                command.extend(selected_attacks)
            
            # PS-FUZZ çalıştır
            process = run_security_scan_with_fallback(command, custom_env) # Pass custom_env
            
            if process is None:
                st.error("Failed to start security scan. Please check your configuration.")
                st.stop()

            st.subheader("Fuzzer Output:")
            with st.expander("Show real-time output", expanded=True):
                output_area = st.empty()
                full_stdout = ""
                with st.spinner("Running fuzzer..."):
                    while True:
                        output_line = process.stdout.readline()
                        if not output_line and process.poll() is not None:
                            break
                        if output_line:
                            full_stdout += output_line.strip() + "\n"
                            output_area.code(full_stdout, language='bash')

            stderr_output = process.stderr.read()
            process.wait()

            # Display any other errors from the fuzzer.
            # The pkg_resources warning is suppressed by the PYTHONWARNINGS env var.
            if stderr_output and stderr_output.strip():
                st.code(stderr_output, language='bash')

            if process.returncode == 0:
                st.success("✅ Fuzzer completed successfully.")
            else:
                st.error(f"❌ Fuzzer exited with return code {process.returncode}.")

            # --- Start of Fixed Results Parsing ---
            st.subheader("📊 Results Summary")
            results_data = []
            
            # Use regex to find the test results table
            # This pattern looks for the header line and captures the entire table
            result_block_pattern = re.compile(r'("Attack Type".*?)"Total \( tests\):.....', re.DOTALL)
            match = result_block_pattern.search(full_stdout)

            if match:
                result_block = match.group(0)
                lines = result_block.splitlines()
                
                # Find all attack results in the captured block
                # This pattern is designed to capture the attack name and its status (Broken or Resilient)
                attack_pattern = re.compile(r'^(?:[\"✓✗\s]*)([\w_]+)\.*[\s,"]*?(Broken|Resilient)', re.MULTILINE)
                attack_matches = attack_pattern.finditer(result_block)

                for attack_match in attack_matches:
                    attack_name = attack_match.group(1)
                    status = attack_match.group(2)
                    
                    # Map the status to a more user-friendly format
                    main_status = "❌ Broken/Vulnerable" if "Broken" in status else "✅ Resilient/Passed"
                    results_data.append({"Test/Attack": attack_name.replace('_', ' ').title(), "Status": main_status, "Details": status})
            
            # Also, capture the list of failed tests at the end of the report
            failed_tests_section = re.search(r"Your system prompt failed the following tests:(.*?)To learn about the various attack types", full_stdout, re.DOTALL)
            if failed_tests_section:
                failed_tests = [test.strip() for test in failed_tests_section.group(1).strip().split('\n') if test.strip()]
                for test in failed_tests:
                    # Avoid duplicating entries if they were already parsed from the table
                    if not any(d['Test/Attack'].lower().replace(' ', '_') == test.lower() for d in results_data):
                         results_data.append({"Test/Attack": test.replace('_', ' ').title(), "Status": "❌ Broken/Vulnerable", "Details": "Failed"})


            if results_data:
                # Remove duplicates that might be captured by both regex patterns
                unique_results = []
                seen_attacks = set()
                for item in results_data:
                    if item['Test/Attack'] not in seen_attacks:
                        unique_results.append(item)
                        seen_attacks.add(item['Test/Attack'])

                df = pd.DataFrame(unique_results)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No parsable results found in the output.")
            # --- End of Fixed Results Parsing ---

        except FileNotFoundError:
            st.error("❌ **Installation Error**: prompt-security-fuzzer not found. Please install it.")
        except Exception as e:
            st.error(f"❌ **Unexpected Error**: {str(e)}")
        finally:
            # Cleanup
            if temp_prompt_file_path and os.path.exists(temp_prompt_file_path):
                try:
                    os.remove(temp_prompt_file_path)
                except Exception:
                    pass
 
