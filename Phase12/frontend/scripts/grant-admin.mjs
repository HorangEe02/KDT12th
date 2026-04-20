#!/usr/bin/env node
/**
 * Grant / revoke admin role for a Firebase Auth user.
 *
 * Usage:
 *   node scripts/grant-admin.mjs <email>                      # → admin
 *   node scripts/grant-admin.mjs <email> --revoke             # → user
 *   node scripts/grant-admin.mjs <email> --reason="bootstrap" # 사유 명시
 *
 * Authentication:
 *   - 로컬: gcloud auth application-default login (ADC), 또는
 *           GOOGLE_APPLICATION_CREDENTIALS=./secrets/service-account.json
 *   - 프로덕션 / CI: 동일 ADC 또는 SA 키
 *
 * 동작:
 *   1) firebase-admin 으로 setCustomUserClaims({ admin, role })
 *   2) revokeRefreshTokens (즉시 반영)
 *   3) Firestore users/{uid}.role 동기화
 *   4) admin_audit 에 이벤트 기록 (adminUid="system", reason 명시)
 */
import admin from "firebase-admin";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const projectId = process.env.FIREBASE_PROJECT_ID ?? "mini12-310f5";

// ─── arg parsing ───
const args = process.argv.slice(2);
if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
  console.log(`
Usage:
  node scripts/grant-admin.mjs <email>             부여 (admin)
  node scripts/grant-admin.mjs <email> --revoke    회수 (user)
  node scripts/grant-admin.mjs <email> --reason="bootstrap CLI"
`);
  process.exit(args.length === 0 ? 1 : 0);
}
const email = args[0];
const revoke = args.includes("--revoke");
const reasonArg = args.find((a) => a.startsWith("--reason="));
const reason = reasonArg
  ? reasonArg.slice("--reason=".length).replace(/^"|"$/g, "")
  : revoke
    ? "manual revoke via CLI"
    : "bootstrap admin via CLI";

// ─── credentials resolution ───
function resolveCredPath() {
  const envPath = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  if (!envPath) return null;
  return path.isAbsolute(envPath) ? envPath : path.resolve(projectRoot, envPath);
}

function initAdmin() {
  if (admin.apps.length > 0) return;
  const credPath = resolveCredPath();
  if (credPath && fs.existsSync(credPath)) {
    const sa = JSON.parse(fs.readFileSync(credPath, "utf-8"));
    admin.initializeApp({
      credential: admin.credential.cert(sa),
      projectId,
    });
    console.log(`[init] cert → ${credPath}`);
  } else {
    admin.initializeApp({
      credential: admin.credential.applicationDefault(),
      projectId,
    });
    console.log(`[init] applicationDefault — gcloud ADC`);
  }
}

// ─── main ───
async function main() {
  initAdmin();
  const auth = admin.auth();
  const db = admin.firestore();

  let user;
  try {
    user = await auth.getUserByEmail(email);
  } catch (e) {
    console.error(`❌ getUserByEmail("${email}") failed:`, e.message ?? e);
    console.error(`   → 해당 이메일로 회원가입이 완료되어 있어야 합니다.`);
    process.exit(2);
  }

  const newClaims = revoke
    ? { ...(user.customClaims ?? {}), admin: false, role: "user" }
    : { ...(user.customClaims ?? {}), admin: true, role: "admin" };

  await auth.setCustomUserClaims(user.uid, newClaims);
  await auth.revokeRefreshTokens(user.uid);

  await db
    .collection("users")
    .doc(user.uid)
    .set(
      {
        role: revoke ? "user" : "admin",
        lastActiveAt: new Date(),
      },
      { merge: true },
    );

  await db.collection("admin_audit").add({
    adminUid: "system",
    adminEmail: "system (CLI)",
    action: revoke ? "revoke_admin" : "grant_admin",
    targetUid: user.uid,
    targetEmail: user.email,
    reason,
    createdAt: new Date(),
    ip: null,
  });

  console.log(`
✅ ${revoke ? "REVOKED" : "GRANTED"} admin
   uid:    ${user.uid}
   email:  ${user.email}
   reason: ${reason}

   대상자가 로그인 중이면 다음 페이지 이동 시 적용됩니다 (refresh token revoked).
`);
}

main().catch((err) => {
  console.error("❌ unexpected:", err);
  process.exit(99);
});
