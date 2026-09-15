"""
Modulo di condivisione per mesh2u3d.

Pubblica un file HTML 3D su GitHub Pages e genera un link condivisibile + QR Code.

Legge le credenziali da:
  1. Streamlit Secrets (st.secrets) — per uso su Streamlit Cloud
  2. File secrets.env — per uso locale
  3. Variabili d'ambiente — fallback

Utilizzo:
    from mesh2u3d.share import share_html_viewer

    url = share_html_viewer(
        html_path="cube.html",
        title="Tavolo di Mario"
    )
    print(f"Link: {url}")
"""
from __future__ import annotations

import os
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Optional


# ---------- Configurazione ----------

def _load_credentials() -> dict:
    """
    Carica le credenziali GitHub da più fonti (in ordine di priorità):
      1. Streamlit Secrets (st.secrets)
      2. File secrets.env (cercato in vari posti)
      3. Variabili d'ambiente
    """
    creds = {
        "token": None,
        "username": None,
        "repo": None,
        "branch": "main",
    }

    # --- 1. Prova da Streamlit Secrets ---
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            creds["token"] = st.secrets.get("GITHUB_TOKEN")
            creds["username"] = st.secrets.get("GITHUB_USERNAME")
            creds["repo"] = st.secrets.get("GITHUB_REPO")
            creds["branch"] = st.secrets.get("GITHUB_BRANCH", "main")
    except Exception:
        pass

    # --- 2. Prova da file secrets.env ---
    if not creds["token"]:
        try:
            from dotenv import load_dotenv
            candidates = [
                Path.cwd() / "secrets.env",
                Path.cwd().parent / "secrets.env",
                Path(__file__).parent.parent.parent / "secrets.env",
                Path.home() / "secrets.env",
            ]
            for candidate in candidates:
                if candidate.exists():
                    load_dotenv(candidate)
                    break

            creds["token"] = os.getenv("GITHUB_TOKEN")
            creds["username"] = os.getenv("GITHUB_USERNAME")
            creds["repo"] = os.getenv("GITHUB_REPO")
            creds["branch"] = os.getenv("GITHUB_BRANCH", "main")
        except Exception:
            pass

    # --- 3. Prova da variabili d'ambiente ---
    if not creds["token"]:
        creds["token"] = os.getenv("GITHUB_TOKEN")
        creds["username"] = os.getenv("GITHUB_USERNAME")
        creds["repo"] = os.getenv("GITHUB_REPO")
        creds["branch"] = os.getenv("GITHUB_BRANCH", "main")

    # --- Verifica ---
    missing = [k for k, v in creds.items() if not v]
    if missing:
        raise ValueError(
            f"Credenziali GitHub mancanti: {missing}. "
            f"Aggiungile in Streamlit Secrets o in secrets.env"
        )

    return creds


# ---------- Generazione ID univoco ----------

def _generate_viewer_id(prefix: str = "A3F") -> str:
    """Genera un ID univoco per il viewer: A3F-XXXXXX."""
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("0", "").replace("O", "")
    alphabet = alphabet.replace("1", "").replace("I", "").replace("L", "")
    suffix = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"{prefix}-{suffix}"


# ---------- Upload su GitHub ----------

def _upload_to_github(
    html_content: str,
    viewer_id: str,
    creds: dict,
    title: str = "",
) -> str:
    """Fa upload del file HTML su GitHub. Returns: URL pubblico."""
    try:
        from github import Github, Auth, GithubException
    except ImportError:
        raise ImportError("PyGithub non installato. Esegui: pip install PyGithub")

    # Autenticazione (API moderna)
    try:
        g = Github(auth=Auth.Token(creds["token"]))
    except Exception:
        # Fallback per versioni vecchie di PyGithub
        g = Github(creds["token"])

    # Accesso al repository
    try:
        repo = g.get_repo(f"{creds['username']}/{creds['repo']}")
    except GithubException as e:
        raise RuntimeError(
            f"Impossibile accedere al repo {creds['username']}/{creds['repo']}: {e}"
        )

    # Percorso del file nel repo
    file_path = f"v/{viewer_id}.html"

    # Messaggio di commit
    commit_message = f"Add viewer {viewer_id}"
    if title:
        commit_message += f" - {title}"

    # Verifica se il file esiste già
    try:
        existing = repo.get_contents(file_path, ref=creds["branch"])
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=html_content,
            sha=existing.sha,
            branch=creds["branch"],
        )
    except GithubException:
        repo.create_file(
            path=file_path,
            message=commit_message,
            content=html_content,
            branch=creds["branch"],
        )

    # URL pubblico (GitHub Pages)
    url = f"https://{creds['username']}.github.io/{creds['repo']}/v/{viewer_id}.html"
    return url


# ---------- API pubblica ----------

def share_html_viewer(
    html_path: str | Path,
    *,
    title: str = "",
    viewer_id: Optional[str] = None,
    generate_qr: bool = True,
    qr_output_dir: Optional[str | Path] = None,
) -> dict:
    """
    Pubblica un file HTML 3D su GitHub Pages.

    Args:
        html_path: percorso del file HTML da pubblicare
        title: titolo descrittivo (per il commit message)
        viewer_id: ID predefinito (se None, ne genera uno nuovo)
        generate_qr: se True, genera anche un QR Code PNG
        qr_output_dir: directory dove salvare il QR (default: stessa del file HTML)

    Returns:
        dict con viewer_id, url, qr_path, uploaded_at
    """
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"File HTML non trovato: {html_path}")
    html_content = html_path.read_text(encoding="utf-8")

    creds = _load_credentials()

    if viewer_id is None:
        viewer_id = _generate_viewer_id()

    url = _upload_to_github(html_content, viewer_id, creds, title)

    qr_path = None
    if generate_qr:
        try:
            import qrcode
        except ImportError:
            print("⚠ qrcode non installato. Salto generazione QR.")
        else:
            if qr_output_dir is None:
                qr_output_dir = html_path.parent
            qr_output_dir = Path(qr_output_dir)
            qr_output_dir.mkdir(parents=True, exist_ok=True)

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            qr_path = qr_output_dir / f"{viewer_id}_qr.png"
            img.save(qr_path)

    return {
        "viewer_id": viewer_id,
        "url": url,
        "qr_path": str(qr_path) if qr_path else None,
        "uploaded_at": datetime.now().isoformat(),
    }


# ---------- CLI semplice ----------

def _cli() -> None:
    """CLI per testare la funzione da riga di comando."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Pubblica un file HTML 3D su GitHub Pages"
    )
    parser.add_argument("html_path", help="Percorso del file HTML")
    parser.add_argument("--title", default="", help="Titolo del viewer")
    parser.add_argument("--no-qr", action="store_true", help="Non generare QR")
    args = parser.parse_args()

    try:
        result = share_html_viewer(
            args.html_path,
            title=args.title,
            generate_qr=not args.no_qr,
        )
    except Exception as e:
        print(f"❌ Errore: {e}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=" * 60)
    print("✅ VIEWER PUBBLICATO!")
    print("=" * 60)
    print(f"ID:         {result['viewer_id']}")
    print(f"URL:        {result['url']}")
    if result["qr_path"]:
        print(f"QR Code:    {result['qr_path']}")
    print("=" * 60)


if __name__ == "__main__":
    _cli()
