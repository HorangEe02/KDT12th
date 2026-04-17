/**
 * Firebase Admin SDK (서버 전용 — API Route, Server Actions, RSC에서만 사용).
 * 포팅 원본: src/db/firestore_client.py (서비스 계정 경로 로딩)
 *
 * 배포 환경(Cloud Run / App Hosting)에서는 Application Default Credentials 자동 사용.
 * 로컬 개발 시 GOOGLE_APPLICATION_CREDENTIALS=./secrets/service-account.json 설정.
 */
import "server-only";
import fs from "node:fs";
import path from "node:path";
import { cert, getApps, initializeApp, applicationDefault, type App } from "firebase-admin/app";
import { getFirestore, type Firestore } from "firebase-admin/firestore";
import { getStorage, type Storage } from "firebase-admin/storage";

const projectId = process.env.FIREBASE_PROJECT_ID ?? "mini12-310f5";
const credPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;

let _app: App | null = null;

/**
 * Firebase Admin 사용 가능 여부.
 * - 클라우드 환경 (K_SERVICE) → ADC 사용 가능
 * - 로컬: GOOGLE_APPLICATION_CREDENTIALS 파일이 실재할 때만 OK
 */
function resolveCredPath(): string | null {
  if (!credPath) return null;
  return path.isAbsolute(credPath)
    ? credPath
    : path.resolve(process.cwd(), credPath);
}

export function isAdminConfigured(): boolean {
  if (process.env.K_SERVICE) return true;
  const abs = resolveCredPath();
  if (!abs) return false;
  try {
    return fs.existsSync(abs);
  } catch {
    return false;
  }
}

function initAdminApp(): App {
  const existing = getApps()[0];
  if (existing) return existing;

  // Cloud Run / App Hosting에서는 ADC 자동 감지 (K_SERVICE env 존재 시)
  const isCloud = Boolean(process.env.K_SERVICE);
  if (isCloud) {
    return initializeApp({
      credential: applicationDefault(),
      projectId,
      storageBucket: `${projectId}.appspot.com`,
    });
  }

  // 로컬: 서비스 계정 JSON 경로가 있고 파일이 실재할 때만 사용
  const abs = resolveCredPath();
  if (abs && isAdminConfigured()) {
    try {
      // fs.readFileSync + JSON.parse — Turbopack NFT 트레이싱을 피하기 위해 require 대신 사용
      const raw = fs.readFileSync(abs, "utf-8");
      const serviceAccount = JSON.parse(raw);
      return initializeApp({
        credential: cert(serviceAccount),
        projectId,
        storageBucket: `${projectId}.appspot.com`,
      });
    } catch {
      // fall through to ADC (will likely fail in local but catch at call-site)
    }
  }

  return initializeApp({
    credential: applicationDefault(),
    projectId,
    storageBucket: `${projectId}.appspot.com`,
  });
}

export function getAdminApp(): App {
  if (!_app) _app = initAdminApp();
  return _app;
}

export function getAdminDb(): Firestore {
  return getFirestore(getAdminApp());
}

export function getAdminStorage(): Storage {
  return getStorage(getAdminApp());
}
