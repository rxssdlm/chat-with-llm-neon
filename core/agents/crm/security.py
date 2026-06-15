"""
Filtro determinista anti prompt-injection para el agente CRM.

Se ejecuta ANTES de invocar al agente, en routes/crm.py, para que el
bloqueo no dependa del comportamiento del LLM.
"""
import re

# Cada patron es (regex_compilado, etiqueta_para_audit_log)
INJECTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"ignora\s+(tus|las)\s+instruccion", re.IGNORECASE), "ignore_instructions"),
    (re.compile(r"olvida\s+(tus|las)\s+instruccion", re.IGNORECASE), "forget_instructions"),
    (re.compile(r"act[uú]a\s+como", re.IGNORECASE), "role_override"),
    (re.compile(r"eres\s+ahora\s+", re.IGNORECASE), "role_override"),
    (re.compile(r"\bnuevo\s+rol\b|\bnuevas\s+instrucciones\b", re.IGNORECASE), "role_override"),
    (re.compile(r"\bsystem\s*prompt\b|\bprompt\s+del\s+sistema\b", re.IGNORECASE), "system_prompt_probe"),
    (re.compile(r"muestra(me)?\s+(el|tu|las)\s+(prompt|instrucciones|configuraci[oó]n)", re.IGNORECASE), "prompt_disclosure"),
    (re.compile(r"d[aá]me\s+todos?\s+los?\s+(client|usuario|password|contraseñ)", re.IGNORECASE), "bulk_data_exfiltration"),
    (re.compile(r"\bdrop\s+table\b|\bdelete\s+from\b|\btruncate\b", re.IGNORECASE), "sql_injection_attempt"),
    (re.compile(r"\bdesactiva\b.*\b(seguridad|filtro|restricci[oó]n)", re.IGNORECASE), "disable_security"),
]


def detect_prompt_injection(message: str) -> str | None:
    """
    Devuelve la etiqueta del patron detectado o None si el mensaje es seguro.
    """
    for pattern, label in INJECTION_PATTERNS:
        if pattern.search(message):
            return label
    return None
