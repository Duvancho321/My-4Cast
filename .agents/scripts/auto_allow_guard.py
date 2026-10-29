#!/usr/bin/env python3
"""
auto_allow_guard.py — Guardián de Permisos de Baja Fricción para My-4Cast.
Auto-aprueba lecturas, inspecciones analíticas, documentación (.md, .canvas, .base) y desarrollo local en My-4Cast y WN3.
Bloquea con confirmación explícita (force_ask) ante modificaciones sobre rutas del sistema o protegidas en .protected_paths.
"""

import sys
import json
import os
from pathlib import Path

DEFAULT_PROTECTED = [
    "/etc",
    "/usr",
    "/opt/prod",
    "/var/log"
]

def load_protected_paths(cwd: str) -> list:
    protected = list(DEFAULT_PROTECTED)
    if cwd:
        try:
            cwd_path = Path(cwd)
            for parent in [cwd_path] + list(cwd_path.parents):
                p_file = parent / ".protected_paths"
                if p_file.is_file():
                    for line in p_file.read_text(errors="ignore").splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            protected.append(line)
                    break
        except Exception:
            pass
    return protected

def is_readonly_command(cmd: str, protected_paths: list) -> bool:
    cmd_clean = cmd.strip()
    for prot in protected_paths:
        if prot in cmd_clean:
            if any(op in cmd_clean for op in (" > ", " >> ", "rm ", "mv ", "cp ", "sed -i", "touch ", "mkdir ")):
                return False

    if cmd_clean.startswith("rm ") or cmd_clean.startswith("mv "):
        return False

    readonly_starters = (
        "ls", "cat", "head", "tail", "grep", "find", "wc", "file", "diff",
        "strings", "stat", "du", "df", "ps", "pgrep", "which", "whereis", "pwd", "date",
        "git log", "git status", "git diff", "git show", "git branch", "git",
        "echo", "python3 -c", "python -c", "python3", "python",
        "jq", "awk", "tar -t", "tar -tzvf"
    )
    if "python" in (cmd_clean.split()[0] if cmd_clean.split() else ""):
        return True

    return any(cmd_clean.startswith(prefix) for prefix in readonly_starters)

def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload   = json.loads(raw)
        tool_call = payload.get("toolCall", {})
        name      = tool_call.get("name", "").lower()
        args      = tool_call.get("args", {})

        target = (
            args.get("TargetFile", "")
            or args.get("AbsolutePath", "")
            or args.get("Path", "")
            or args.get("path", "")
            or args.get("file_path", "")
        )
        cmd = args.get("CommandLine", "") or args.get("command", "")
        cwd = args.get("Cwd", "") or args.get("cwd", "")

        protected_paths = load_protected_paths(cwd)

        # 1. LECTURAS: Siempre automáticas
        if name in ("read_file", "view_file", "read", "view"):
            print(json.dumps({
                "decision": "allow",
                "reason": "Lectura de archivos aprobada automáticamente."
            }))
            return

        # 2. INSPECCIÓN DE COMANDOS: Siempre automáticos
        if name in ("run_command", "bash_tool", "sh", "terminal") and is_readonly_command(cmd, protected_paths):
            print(json.dumps({
                "decision": "allow",
                "reason": "Comando de inspección/lectura aprobado automáticamente."
            }))
            return

        # 3. GUARDIA DE RUTAS PROTEGIDAS DEL SISTEMA
        is_target_protected = any(target.startswith(p) for p in protected_paths) if target else False
        is_cmd_protected    = any(p in cmd for p in protected_paths) if cmd else False
        is_cwd_protected    = any(cwd.startswith(p) for p in protected_paths) if cwd else False

        if is_target_protected or is_cmd_protected or is_cwd_protected:
            print(json.dumps({
                "decision": "force_ask",
                "reason": "Operación sobre ruta protegida requiere confirmación explícita."
            }))
            return

        # 4. DOCUMENTACIÓN OBSIDIAN (.md, .canvas, .base): Siempre automático
        if any(target.endswith(ext) for ext in (".md", ".canvas", ".base", ".yaml", ".json")):
            print(json.dumps({
                "decision": "allow",
                "reason": "Documentación y configuración aprobada automáticamente."
            }))
            return

        # 5. DESARROLLO LOCAL Y DATOS WN3
        user_home = str(Path.home())
        data_base = "/mnt/datos/dnieves"
        if target.startswith(user_home) or target.startswith(data_base):
            print(json.dumps({
                "decision": "allow",
                "reason": "Operación en entorno de desarrollo local aprobada automáticamente."
            }))
            return

        if cwd.startswith(user_home) or cwd.startswith(data_base):
            print(json.dumps({
                "decision": "allow",
                "reason": "Operación en entorno de desarrollo local aprobada automáticamente."
            }))
            return

        print(json.dumps({"decision": "allow"}))
    except Exception:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
