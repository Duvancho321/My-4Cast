#!/bin/bash
# git_private.sh — Sincronización del repositorio privado (Vault, diarios y agentes)

GIT_PRIV="git --git-dir=/home/dnieves/Documentos/My-4Cast/.git-private --work-tree=/home/dnieves/Documentos/My-4Cast"
MSG="${1:-Update private vault and configs}"

$GIT_PRIV add -f vault/ .claude/ .agents/ AGENTS.md GEMINI.md
$GIT_PRIV commit -m "$MSG" || true
$GIT_PRIV push origin main
