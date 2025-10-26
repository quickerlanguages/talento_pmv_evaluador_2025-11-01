#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Django management command: seed_vpm_from_repo

Limpia de RTF y lista para usar. Esta versión no asume modelo alguno;
valida y reporta archivos JSON encontrados en un repositorio.

Uso:
    python manage.py seed_vpm_from_repo /ruta/al/repo [--dry-run] [--glob '**/*.json']

- Recorre el repo buscando JSON (por defecto, recursivo).
- Valida que cada archivo sea JSON UTF‑8 bien formado.
- En --dry-run imprime un resumen. (Por ahora no escribe en DB).
- Esqueleto listo para que añadas persistencia a tus modelos.

© Talento – utilitario de importación mínima.
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Iterable, List

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Importa/valida JSONs del repositorio para VPM (versión limpia y segura)."

    def add_arguments(self, parser):
        parser.add_argument(
            "repo",
            nargs="?",
            default=".",
            help="Ruta al repo que contiene los JSON (por defecto: directorio actual).",
        )
        parser.add_argument(
            "--glob",
            default="**/*.json",
            help="Patrón glob para localizar JSONs (por defecto: '**/*.json').",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No persiste nada; solo valida y reporta.",
        )

    def handle(self, *args, **options):
        repo = Path(options["repo"]).expanduser().resolve()
        pattern = options["glob"]
        dry_run = options["dry_run"]

        if not repo.exists():
            raise CommandError(f"La ruta no existe: {repo}")
        if not repo.is_dir():
            raise CommandError(f"No es un directorio: {repo}")

        files: List[Path] = sorted(repo.glob(pattern))
        if not files:
            self.stdout.write(self.style.WARNING("No se encontraron archivos JSON."))
            return

        ok = 0
        errors = 0

        self.stdout.write(f"Escaneando {len(files)} archivo(s) JSON en: {repo}")
        for p in files:
            rel = p.relative_to(repo)
            try:
                with p.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)

                summary = self._summarize_json(data)
                if dry_run:
                    self.stdout.write(f"[DRY] {rel} → {summary}")
                else:
                    # TODO: Persistencia a modelos (ejemplo):
                    #   from ccp_vpm.models import TuModelo
                    #   TuModelo.objects.update_or_create(...)
                    # De momento, solo confirmamos la validación.
                    self.stdout.write(f"[OK]  {rel} → {summary}")

                ok += 1
            except Exception as exc:  # noqa: BLE001
                errors += 1
                self.stderr.write(self.style.ERROR(f"[ERR] {rel}: {exc}"))
                # Descomenta si necesitas el stacktrace completo:
                # traceback.print_exc()

        self.stdout.write(self.style.SUCCESS(f"Completado. OK={ok}, ERR={errors}"))

    @staticmethod
    def _summarize_json(data) -> str:
        """Devuelve un mini-resumen de la estructura del JSON."""
        try:
            if isinstance(data, dict):
                keys = list(data.keys())
                snippet = ", ".join(map(str, keys[:5]))
                extra = "" if len(keys) <= 5 else f"+{len(keys)-5}"
                return f"dict(keys=[{snippet}]{extra})"
            if isinstance(data, list):
                n = len(data)
                kind = type(data[0]).__name__ if n else "empty"
                return f"list(n={n}, first={kind})"
            return type(data).__name__
        except Exception:  # noqa: BLE001
            return type(data).__name__
