"""이상 탐지 모델 학습 모듈.

Autoencoder, PaDiM, Isolation Forest, One-Class SVM 모델의
학습 함수 및 전체 실험 실행 함수를 제공한다.
"""

import os
import sys
import time
from typing import Optional, Dict, Any

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# 프로젝트 루트를 경로에 추가
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from anomaly_detection.models.autoencoder import ConvAutoencoder, compute_anomaly_map, compute_anomaly_score
from anomaly_detection.models.padim import PaDiM
from anomaly_detection.models.traditional_ad import IsolationForestAD, OneClassSVMAD


def _get_device(device: Optional[torch.device] = None) -> torch.device:
    """사용 가능한 디바이스를 반환한다."""
    if device is not None:
        return device
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Autoencoder 학습
# ---------------------------------------------------------------------------

def train_autoencoder(
    model: ConvAutoencoder,
    train_loader: DataLoader,
    epochs: int = 100,
    lr: float = 1e-3,
    device: Optional[torch.device] = None,
    save_path: Optional[str] = None,
) -> Dict[str, Any]:
    """합성곱 오토인코더를 학습한다.

    Args:
        model: ConvAutoencoder 모델.
        train_loader: 정상 이미지 DataLoader.
        epochs: 에폭 수.
        lr: 학습률.
        device: 연산 디바이스.
        save_path: 모델 저장 경로 (None이면 저장 안 함).

    Returns:
        dict: losses (에폭별 손실 리스트), best_loss, total_time_s.
    """
    device = _get_device(device)
    model = model.to(device)
    model.train()

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=10, verbose=True
    )

    losses = []
    best_loss = float("inf")
    start_time = time.time()

    print(f"[AE Train] 학습 시작 - epochs={epochs}, lr={lr}, device={device}")

    for epoch in range(epochs):
        epoch_loss = 0.0
        n_batches = 0

        for batch_data in train_loader:
            if isinstance(batch_data, (list, tuple)):
                images = batch_data[0]
            else:
                images = batch_data

            images = images.to(device)
            recon = model(images)
            loss = criterion(recon, images)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)
        losses.append(avg_loss)
        scheduler.step(avg_loss)

        if avg_loss < best_loss:
            best_loss = avg_loss
            if save_path is not None:
                os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
                torch.save(model.state_dict(), save_path)

        if (epoch + 1) % 10 == 0 or epoch == 0:
            elapsed = time.time() - start_time
            print(f"  Epoch [{epoch+1:3d}/{epochs}] loss={avg_loss:.6f} "
                  f"best={best_loss:.6f} ({elapsed:.0f}s)")

    total_time = time.time() - start_time
    print(f"[AE Train] 학습 완료! best_loss={best_loss:.6f}, "
          f"총 시간: {total_time:.1f}초")

    if save_path is not None:
        print(f"[AE Train] 최적 모델 저장: {save_path}")

    return {
        "losses": losses,
        "best_loss": best_loss,
        "total_time_s": total_time,
    }


# ---------------------------------------------------------------------------
# PaDiM 학습
# ---------------------------------------------------------------------------

def fit_padim(
    train_loader: DataLoader,
    device: Optional[torch.device] = None,
    save_path: Optional[str] = None,
    n_selected_features: int = 100,
    image_size: int = 200,
) -> PaDiM:
    """PaDiM 모델을 학습한다.

    Args:
        train_loader: 정상 이미지 DataLoader.
        device: 연산 디바이스.
        save_path: 모델 저장 경로.
        n_selected_features: 랜덤 선택 특징 수.
        image_size: 입력 이미지 크기.

    Returns:
        학습된 PaDiM 모델.
    """
    device = _get_device(device)

    padim = PaDiM(
        n_selected_features=n_selected_features,
        image_size=image_size,
    )

    t0 = time.time()
    padim.fit(train_loader, device=device)
    elapsed = time.time() - t0
    print(f"[PaDiM] 총 학습 시간: {elapsed:.1f}초")

    if save_path is not None:
        padim.save(save_path)

    return padim


# ---------------------------------------------------------------------------
# 전통적 모델 학습
# ---------------------------------------------------------------------------

def fit_traditional_ad(
    normal_images: np.ndarray,
    save_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Isolation Forest와 One-Class SVM을 학습한다.

    Args:
        normal_images: 정상 이미지 배열 (N, H, W).
        save_dir: 모델 저장 디렉토리.

    Returns:
        dict: iforest (IsolationForestAD), ocsvm (OneClassSVMAD).
    """
    print(f"[Traditional AD] 정상 이미지 수: {len(normal_images)}")

    # Isolation Forest
    iforest = IsolationForestAD(contamination=0.1, image_size=128)
    iforest.fit(normal_images)

    # One-Class SVM
    ocsvm = OneClassSVMAD(nu=0.1, image_size=128)
    ocsvm.fit(normal_images)

    if save_dir is not None:
        os.makedirs(save_dir, exist_ok=True)
        iforest.save(os.path.join(save_dir, "isolation_forest.pkl"))
        ocsvm.save(os.path.join(save_dir, "one_class_svm.pkl"))

    return {
        "iforest": iforest,
        "ocsvm": ocsvm,
    }


# ---------------------------------------------------------------------------
# 전체 실험
# ---------------------------------------------------------------------------

def _evaluate_ae_on_loader(model, loader, device):
    """오토인코더의 테스트 로더 평가."""
    model.eval()
    all_scores = []
    all_labels = []

    with torch.no_grad():
        for batch_data in loader:
            images = batch_data[0].to(device)
            labels = batch_data[1]

            recon = model(images)

            for i in range(images.shape[0]):
                amap = compute_anomaly_map(images[i].cpu(), recon[i].cpu())
                score = compute_anomaly_score(amap)
                all_scores.append(score)
                all_labels.append(labels[i].item())

    return np.array(all_labels), np.array(all_scores)


def _evaluate_padim_on_loader(padim, loader, device):
    """PaDiM의 테스트 로더 평가."""
    all_scores = []
    all_labels = []

    for batch_data in loader:
        images = batch_data[0]
        labels = batch_data[1]

        for i in range(images.shape[0]):
            score, _ = padim.predict(images[i], device=device)
            all_scores.append(score)
            all_labels.append(labels[i].item())

    return np.array(all_labels), np.array(all_scores)


def _evaluate_traditional_on_images(model, images, labels):
    """전통적 모델의 이미지 리스트 평가."""
    result = model.predict_batch(images)
    return np.array(labels), np.array(result["anomaly_scores"])


def run_ad_experiments(
    neu_dir: str,
    mvtec_dir: Optional[str] = None,
    output_dir: str = "outputs",
    ae_epochs: int = 50,
    normal_class: str = "pitted_surface",
) -> Dict[str, Any]:
    """전체 이상 탐지 실험을 실행한다.

    4개 모델(AE, PaDiM, IF, OCSVM)을 NEU 데이터로 학습/평가한다.
    mvtec_dir가 존재하면 MVTec 데이터로도 실행한다.

    Args:
        neu_dir: NEU-DET 데이터 디렉토리.
        mvtec_dir: MVTec metal_nut 디렉토리 (옵션).
        output_dir: 출력 디렉토리.
        ae_epochs: 오토인코더 에폭 수.
        normal_class: NEU에서 정상으로 간주할 클래스.

    Returns:
        dict: 각 모델/데이터셋의 (y_true, scores) 결과.
    """
    from anomaly_detection.datasets_neu_anomaly import get_neu_anomaly_dataloaders

    device = _get_device()
    results = {}
    os.makedirs(output_dir, exist_ok=True)
    model_dir = os.path.join(output_dir, "models")
    os.makedirs(model_dir, exist_ok=True)

    print("=" * 70)
    print("Phase 3: Anomaly Detection 실험")
    print("=" * 70)

    # -----------------------------------------------------------------------
    # NEU 데이터 준비
    # -----------------------------------------------------------------------
    print("\n[1/5] NEU 데이터 로드...")
    train_loader, test_loader = get_neu_anomaly_dataloaders(
        neu_dir, normal_class=normal_class, batch_size=16,
    )

    # 정상 이미지 numpy 배열 추출 (전통적 모델용)
    import cv2
    import glob

    normal_img_dir = os.path.join(neu_dir, "train", "images", normal_class)
    if not os.path.isdir(normal_img_dir):
        normal_img_dir = os.path.join(neu_dir, normal_class)

    normal_np_images = []
    exts = ("*.jpg", "*.jpeg", "*.bmp", "*.png")
    paths = []
    for ext in exts:
        paths.extend(glob.glob(os.path.join(normal_img_dir, ext)))
    paths = sorted(paths)

    for p in paths:
        img = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if img is not None:
            normal_np_images.append(img)
    normal_np_images = np.array(normal_np_images[:210])  # 학습용 70%

    # 전체 이미지 (전통적 모델 테스트용)
    test_np_images = []
    test_np_labels = []
    for batch_data in test_loader:
        imgs_tensor = batch_data[0]
        lbls = batch_data[1]
        for i in range(imgs_tensor.shape[0]):
            img_np = (imgs_tensor[i].squeeze().numpy() * 255).astype(np.uint8)
            test_np_images.append(img_np)
            test_np_labels.append(lbls[i].item())

    # -----------------------------------------------------------------------
    # 모델 1: Autoencoder
    # -----------------------------------------------------------------------
    print("\n[2/5] Autoencoder 학습...")
    ae_model = ConvAutoencoder(in_channels=1, image_size=200, latent_dim=128)
    ae_save = os.path.join(model_dir, "autoencoder_neu.pth")
    ae_history = train_autoencoder(
        ae_model, train_loader, epochs=ae_epochs,
        lr=1e-3, device=device, save_path=ae_save,
    )

    print("[2/5] Autoencoder 평가...")
    ae_model.load_state_dict(torch.load(ae_save, map_location=device, weights_only=True))
    ae_labels, ae_scores = _evaluate_ae_on_loader(ae_model, test_loader, device)
    results["ae_neu"] = {"y_true": ae_labels, "scores": ae_scores, "history": ae_history}
    print(f"  AE - 정상 평균 점수: {ae_scores[ae_labels==0].mean():.4f}, "
          f"이상 평균 점수: {ae_scores[ae_labels==1].mean():.4f}")

    # -----------------------------------------------------------------------
    # 모델 2: PaDiM
    # -----------------------------------------------------------------------
    print("\n[3/5] PaDiM 학습...")
    padim_save = os.path.join(model_dir, "padim_neu.pkl")
    padim = fit_padim(
        train_loader, device=device, save_path=padim_save,
        n_selected_features=100, image_size=200,
    )

    print("[3/5] PaDiM 평가...")
    padim_labels, padim_scores = _evaluate_padim_on_loader(padim, test_loader, device)
    results["padim_neu"] = {"y_true": padim_labels, "scores": padim_scores}
    print(f"  PaDiM - 정상 평균 점수: {padim_scores[padim_labels==0].mean():.4f}, "
          f"이상 평균 점수: {padim_scores[padim_labels==1].mean():.4f}")

    # -----------------------------------------------------------------------
    # 모델 3 & 4: Isolation Forest & One-Class SVM
    # -----------------------------------------------------------------------
    print("\n[4/5] 전통적 모델 학습...")
    trad_models = fit_traditional_ad(
        normal_np_images, save_dir=model_dir,
    )

    print("[4/5] 전통적 모델 평가...")
    if_labels, if_scores = _evaluate_traditional_on_images(
        trad_models["iforest"], test_np_images, test_np_labels,
    )
    results["iforest_neu"] = {"y_true": if_labels, "scores": if_scores}
    print(f"  IF - 정상 평균 점수: {if_scores[if_labels==0].mean():.4f}, "
          f"이상 평균 점수: {if_scores[if_labels==1].mean():.4f}")

    ocsvm_labels, ocsvm_scores = _evaluate_traditional_on_images(
        trad_models["ocsvm"], test_np_images, test_np_labels,
    )
    results["ocsvm_neu"] = {"y_true": ocsvm_labels, "scores": ocsvm_scores}
    print(f"  OCSVM - 정상 평균 점수: {ocsvm_scores[ocsvm_labels==0].mean():.4f}, "
          f"이상 평균 점수: {ocsvm_scores[ocsvm_labels==1].mean():.4f}")

    # -----------------------------------------------------------------------
    # MVTec (옵션)
    # -----------------------------------------------------------------------
    if mvtec_dir is not None and os.path.isdir(mvtec_dir):
        print("\n[5/5] MVTec Metal Nut 실험...")
        from anomaly_detection.datasets_mvtec import get_mvtec_dataloaders

        mvtec_train, mvtec_test = get_mvtec_dataloaders(
            mvtec_dir, batch_size=16, image_size=256,
        )

        # MVTec AE
        ae_mvtec = ConvAutoencoder(in_channels=3, image_size=256, latent_dim=256)
        ae_mvtec_save = os.path.join(model_dir, "autoencoder_mvtec.pth")
        train_autoencoder(
            ae_mvtec, mvtec_train, epochs=ae_epochs,
            lr=1e-3, device=device, save_path=ae_mvtec_save,
        )
        ae_mvtec.load_state_dict(torch.load(ae_mvtec_save, map_location=device, weights_only=True))
        mvtec_ae_labels, mvtec_ae_scores = _evaluate_ae_on_loader(
            ae_mvtec, mvtec_test, device,
        )
        results["ae_mvtec"] = {"y_true": mvtec_ae_labels, "scores": mvtec_ae_scores}

        # MVTec PaDiM
        padim_mvtec_save = os.path.join(model_dir, "padim_mvtec.pkl")
        padim_mvtec = fit_padim(
            mvtec_train, device=device, save_path=padim_mvtec_save,
            n_selected_features=100, image_size=256,
        )
        mvtec_padim_labels, mvtec_padim_scores = _evaluate_padim_on_loader(
            padim_mvtec, mvtec_test, device,
        )
        results["padim_mvtec"] = {"y_true": mvtec_padim_labels, "scores": mvtec_padim_scores}
    else:
        print("\n[5/5] MVTec 데이터 없음 - 건너뜀")

    print("\n" + "=" * 70)
    print("Phase 3: 실험 완료!")
    print("=" * 70)

    return results


# ---------------------------------------------------------------------------
# 메인 실행
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("train_ad.py 스모크 테스트")
    print("=" * 60)

    device = _get_device()
    print(f"Device: {device}")

    # 더미 DataLoader 생성
    from torch.utils.data import TensorDataset

    dummy_images = torch.randn(32, 1, 200, 200).clamp(0, 1)
    dummy_labels = torch.zeros(32, dtype=torch.long)
    dummy_ds = TensorDataset(dummy_images, dummy_labels)
    dummy_loader = DataLoader(dummy_ds, batch_size=8, shuffle=True)

    # AE 학습 테스트
    print("\n--- Autoencoder 학습 (5 에폭) ---")
    ae = ConvAutoencoder(in_channels=1, image_size=200, latent_dim=64)
    history = train_autoencoder(
        ae, dummy_loader, epochs=5, lr=1e-3, device=device,
    )
    print(f"Loss history: {[f'{l:.4f}' for l in history['losses']]}")

    # PaDiM 학습 테스트
    print("\n--- PaDiM 학습 ---")
    padim = fit_padim(dummy_loader, device=device, n_selected_features=30, image_size=200)

    # 전통적 모델 테스트
    print("\n--- 전통적 모델 학습 ---")
    dummy_np = np.random.randint(100, 200, (20, 200, 200), dtype=np.uint8)
    trad = fit_traditional_ad(dummy_np)
    print(f"  Models: {list(trad.keys())}")

    print("\n[PASS] train_ad.py 스모크 테스트 완료")
