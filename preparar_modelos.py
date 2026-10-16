"""Descargar modelos una vez, con internet, antes de ejecutar --offline."""
import argparse
from sistema import MODELOS, VOZ_REPO, VOZ_BASE

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modelo", choices=MODELOS, default="qwen15")
    parser.add_argument("--comparacion", action="store_true", help="Descargar los tres LLM.")
    parser.add_argument("--audio", action="store_true", help="Descargar Piper y Whisper tiny/small.")
    args = parser.parse_args()
    from huggingface_hub import snapshot_download, hf_hub_download
    for clave in MODELOS if args.comparacion else [args.modelo]:
        print("Descargando:", MODELOS[clave], flush=True)
        snapshot_download(MODELOS[clave])
    if args.audio:
        for tamano in ("tiny", "small"):
            snapshot_download(f"Systran/faster-whisper-{tamano}")
        hf_hub_download(VOZ_REPO, VOZ_BASE)
        hf_hub_download(VOZ_REPO, VOZ_BASE + ".json")
    print("Descargas terminadas. Puedes usar --offline en este mismo equipo y usuario.")

if __name__ == "__main__":
    main()
