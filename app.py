# app.py dosyanızda bu değişiklikleri yapın:

# PS-FUZZ hatası için düzeltme kodu
import streamlit as st
import subprocess
import os
import pandas as pd
import tempfile
import sys
import json
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
        "google_palm": ["palm-2"]
    }
    return supported_backends.get(provider, [])

# Hata yakalama ve alternatif çözüm
def run_security_scan_with_fallback(command):
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
            shell=False
        )
        
        return process
        
    except Exception as e:
        st.error(f"PS-FUZZ execution failed: {str(e)}")
        return None

# Backend konfigürasyonu düzeltme
def fix_backend_config(target_provider, attack_provider):
    """Backend konfigürasyonunu düzelt"""
    
    # OpenAI için özel düzeltme
    if target_provider == "openai" or attack_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key eksik!")
            return False
            
        # OpenAI backend sorununu düzelt
        os.environ["OPENAI_API_TYPE"] = "openai"
        os.environ["OPENAI_API_VERSION"] = "2023-12-01-preview"
    
    return True

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

# Backend uyumluluk uyarısı eklendi
st.sidebar.header("⚠️ Backend Compatibility")
st.sidebar.warning("Some backends may have compatibility issues. Try different providers if errors occur.")

st.header("🚀 Fuzzer Configuration")
col1, col2 = st.columns(2)

# Desteklenen provider'lar - OpenAI sorunu için güncellendi
valid_providers = ["anthropic", "cohere", "google_palm", "openai"]

with col1:
    st.subheader("🎯 Target LLM")
    target_provider = st.selectbox("Target Provider", valid_providers, index=0)  # Anthropic'i varsayılan yap
    
    # Provider'a göre model önerileri
    if target_provider == "openai":
        default_target_model = "gpt-3.5-turbo"
        st.info("⚠️ OpenAI backend issues reported. Consider using Anthropic.")
    elif target_provider == "anthropic":
        default_target_model = "claude-3-sonnet-20240229"
        st.success("✅ Anthropic backend stable.")
    elif target_provider == "cohere":
        default_target_model = "command"
    else:
        default_target_model = "palm-2"
    
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
    attack_provider = st.selectbox("Attack Provider", valid_providers, index=0)  # Anthropic varsayılan
    
    if attack_provider == "openai":
        default_attack_model = "gpt-3.5-turbo"
        st.info("⚠️ Consider using Anthropic for more stable attacks.")
    elif attack_provider == "anthropic":
        default_attack_model = "claude-3-sonnet-20240229"
    elif attack_provider == "cohere":
        default_attack_model = "command"
    else:
        default_attack_model = "palm-2"
        
    attack_model = st.text_input("Attack Model", default_attack_model)
    attack_temperature = st.slider("Attack Temperature", 0.0, 2.0, 0.7, 0.05)

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
    elif target_provider == "openai" and not openai_api_key_input:
        st.error("OpenAI selected but no API key provided.")
    elif attack_provider == "openai" and not openai_api_key_input:
        st.error("OpenAI attack provider selected but no API key provided.")
    elif target_provider == "anthropic" and not anthropic_api_key_input:
        st.error("Anthropic selected but no API key provided.")
    elif attack_provider == "anthropic" and not anthropic_api_key_input:
        st.error("Anthropic attack provider selected but no API key provided.")
    elif not run_all_attacks and not selected_attacks:
        st.error("Select at least one attack or enable 'Run all'.")
    else:
        # Backend konfigürasyonunu düzelt
        if not fix_backend_config(target_provider, attack_provider):
            st.stop()
        
        temp_prompt_file_path = ""
        try:
            # Ortam değişkenlerini set et
            os.environ["PYTHONIOENCODING"] = "utf-8"
            os.environ["NO_COLOR"] = "1"

            # API key'leri ayarla
            if openai_api_key_input:
                os.environ["OPENAI_API_KEY"] = openai_api_key_input
            if google_api_key_input:
                os.environ["GOOGLE_API_KEY"] = google_api_key_input
            if anthropic_api_key_input:
                os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key_input
            if local_openai_base_url:
                os.environ["OPENAI_API_BASE"] = local_openai_base_url

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

            st.info(f"Executing: `{' '.join(command)}`")
            
            # Alternatif çözüm önerisi
            st.info("💡 **Tip**: If OpenAI backend fails, try using Anthropic (Claude) which is more stable with PS-FUZZ.")

            # PS-FUZZ çalıştır
            process = run_security_scan_with_fallback(command)
            
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

            # Hata durumu kontrolü
            if stderr_output:
                st.error("Errors from fuzzer:")
                st.code(stderr_output, language='bash')
                
                # Özel hata mesajları
                if "Invalid backend name" in stderr_output:
                    st.error("❌ **Backend Error**: The selected provider is not supported by PS-FUZZ.")
                    st.info("🔧 **Solution**: Try using 'anthropic' provider with 'claude-3-sonnet-20240229' model.")
                elif "API key" in stderr_output:
                    st.error("❌ **API Key Error**: Please check your API key configuration.")

            if process.returncode == 0:
                st.success("✅ Fuzzer completed successfully.")
            else:
                st.error(f"❌ Fuzzer exited with return code {process.returncode}.")
                
                # Alternatif çözüm öner
                st.info("🔧 **Troubleshooting Tips:**")
                st.write("1. Try using **Anthropic** instead of OpenAI")
                st.write("2. Verify your API keys are correct")
                st.write("3. Check if PS-FUZZ supports your selected models")
                st.write("4. Try with fewer attack attempts first")

            # Sonuçları işle (mevcut kodunuz)
            st.subheader("📊 Results Summary")
            results_data = []
            for line in full_stdout.splitlines():
                line_lower = line.lower()
                if any(k in line_lower for k in ["broken", "resilient", "vulnerable", "failed", "passed", "error"]) and ":" in line:
                    try:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            attack_name = parts[0].strip().replace('✓', '').replace('✗', '').strip()
                            status_detail = parts[1].strip()
                            main_status = "❌ Broken/Vulnerable" if "broken" in status_detail.lower() or "vulnerable" in status_detail.lower() or "failed" in status_detail.lower() or '✗' in line else "✅ Resilient/Passed" if "resilient" in status_detail.lower() or "passed" in status_detail.lower() or '✓' in line else "⚠️ Error"
                            results_data.append({"Test/Attack": attack_name, "Status": main_status, "Details": status_detail})
                    except Exception as parse_error:
                        st.warning(f"Could not parse line: {line} – {parse_error}")

            if results_data:
                df = pd.DataFrame(results_data)
                st.dataframe(df, use_container_width=True)
                if not df[df["Status"].str.contains("Broken", na=False)].empty:
                    st.error("⚠️ Critical vulnerabilities found.")
            else:
                st.warning("No parsable results found. Check raw output above.")

        except FileNotFoundError:
            st.error("❌ **Installation Error**: prompt-security-fuzzer not found.")
            st.info("🔧 **Solution**: Install with: `pip install prompt-security-fuzzer`")
        except Exception as e:
            st.error(f"❌ **Unexpected Error**: {str(e)}")
            st.info("🔧 **Tip**: Try using different providers (Anthropic recommended)")
        finally:
            # Cleanup
            if temp_prompt_file_path and os.path.exists(temp_prompt_file_path):
                try:
                    os.remove(temp_prompt_file_path)
                except Exception:
                    pass