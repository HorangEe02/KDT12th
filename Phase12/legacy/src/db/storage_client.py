"""Google Cloud Storage 클라이언트 — ChromaDB 스냅샷 영속화.

Cloud Run은 ephemeral이므로 컨테이너 시작 시 GCS에서 인덱스를 내려받고,
사이트맵 인덱싱이 로컬에서 갱신되면 GCS로 업로드한다.
"""
from __future__ import annotations

import logging
import tarfile
from pathlib import Path

from src import config

log = logging.getLogger(__name__)


def _get_bucket():
    """GCS 버킷 객체 lazy init. 실패 시 None."""
    if not config.GCS_BUCKET:
        log.warning("GCS_BUCKET 환경변수 미설정")
        return None
    try:
        from google.cloud import storage

        # ADC (Cloud Run) 또는 서비스 계정 키 자동 사용
        client = storage.Client(project=config.GCP_PROJECT_ID or None)
        return client.bucket(config.GCS_BUCKET)
    except ImportError:
        log.warning("google-cloud-storage SDK 미설치")
        return None
    except Exception as exc:
        log.warning("GCS 초기화 실패: %s", exc)
        return None


def health() -> bool:
    bucket = _get_bucket()
    if bucket is None:
        return False
    try:
        return bucket.exists()
    except Exception as exc:
        log.warning("GCS 버킷 접근 실패: %s", exc)
        return False


def _make_archive(src_dir: Path, dest_tar: Path) -> None:
    dest_tar.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest_tar, "w:gz") as tar:
        tar.add(src_dir, arcname=src_dir.name)


def _extract_archive(src_tar: Path, dest_parent: Path) -> None:
    dest_parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(src_tar, "r:gz") as tar:
        tar.extractall(dest_parent)


def upload_chroma_snapshot() -> bool:
    """로컬 ChromaDB → tar.gz → GCS 업로드."""
    bucket = _get_bucket()
    if bucket is None:
        return False
    chroma_dir = config.CHROMA_DB_DIR
    if not chroma_dir.exists() or not any(chroma_dir.iterdir()):
        log.warning("ChromaDB 디렉토리 비어있음: %s", chroma_dir)
        return False

    local_tar = chroma_dir.parent / "_chroma_snapshot.tar.gz"
    try:
        _make_archive(chroma_dir, local_tar)
        blob = bucket.blob(config.GCS_RAG_BLOB)
        blob.upload_from_filename(str(local_tar))
        log.info("ChromaDB 업로드 완료: gs://%s/%s (%.2f MB)",
                 bucket.name, config.GCS_RAG_BLOB,
                 local_tar.stat().st_size / 1_048_576)
        return True
    except Exception as exc:
        log.warning("ChromaDB 업로드 실패: %s", exc)
        return False
    finally:
        try:
            local_tar.unlink(missing_ok=True)
        except Exception:
            pass


def download_chroma_snapshot(force: bool = False) -> bool:
    """GCS → 로컬 ChromaDB 디렉토리. 이미 있으면 skip."""
    chroma_dir = config.CHROMA_DB_DIR
    if chroma_dir.exists() and any(chroma_dir.iterdir()) and not force:
        log.info("ChromaDB 이미 존재, 다운로드 skip")
        return True

    bucket = _get_bucket()
    if bucket is None:
        return False

    local_tar = chroma_dir.parent / "_chroma_snapshot_dl.tar.gz"
    try:
        blob = bucket.blob(config.GCS_RAG_BLOB)
        if not blob.exists():
            log.warning("GCS에 snapshot 없음: gs://%s/%s", bucket.name, config.GCS_RAG_BLOB)
            return False
        blob.download_to_filename(str(local_tar))
        # 기존 디렉토리 제거 후 압축 해제
        if chroma_dir.exists():
            import shutil
            shutil.rmtree(chroma_dir)
        _extract_archive(local_tar, chroma_dir.parent)
        log.info("ChromaDB 다운로드 완료: %s", chroma_dir)
        return True
    except Exception as exc:
        log.warning("ChromaDB 다운로드 실패: %s", exc)
        return False
    finally:
        try:
            local_tar.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(f"GCS health: {health()}")
    if health():
        print("업로드 시도...")
        ok = upload_chroma_snapshot()
        print(f"업로드: {ok}")
