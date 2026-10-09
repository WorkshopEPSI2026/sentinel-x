from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/recordings", tags=["Recordings"])

RECORDINGS_DIR = Path("/recordings").resolve()


@router.get("")
def get_recordings():
    """Retourne la liste des vidéos d'incidents."""
    if not RECORDINGS_DIR.is_dir():
        return []

    recordings = []

    for file in RECORDINGS_DIR.glob("incident_*.mp4"):
        if file.is_file():
            recordings.append({
                "filename": file.name,
                "size": file.stat().st_size,
                "created_at": file.stat().st_mtime,
                "url": f"/api/recordings/{file.name}",
            })

    return sorted(
        recordings,
        key=lambda recording: recording["created_at"],
        reverse=True,
    )


@router.get("/{filename}")
def get_recording(filename: str):
    """Retourne une vidéo pour sa lecture dans le navigateur."""
    if Path(filename).name != filename or not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")

    file_path = (RECORDINGS_DIR / filename).resolve()

    if file_path.parent != RECORDINGS_DIR or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Vidéo introuvable")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        content_disposition_type="inline",
    )