import { NextResponse } from "next/server";
import { z } from "zod";
import { getUserDetail, deleteUserAccount } from "@/lib/firebase/admin-users";
import { requireAdmin } from "@/lib/firebase/server-session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DeleteBody = z.object({ reason: z.string().min(2).max(500) });

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ uid: string }> },
) {
  try {
    await requireAdmin();
  } catch {
    return NextResponse.json({ error: "FORBIDDEN" }, { status: 403 });
  }
  const { uid } = await params;
  const detail = await getUserDetail(uid);
  if (!detail) return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  return NextResponse.json(detail);
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ uid: string }> },
) {
  let admin;
  try {
    admin = await requireAdmin();
  } catch {
    return NextResponse.json({ error: "FORBIDDEN" }, { status: 403 });
  }
  const { uid } = await params;
  if (uid === admin.uid) {
    return NextResponse.json(
      { error: "본인 계정은 삭제할 수 없습니다." },
      { status: 400 },
    );
  }
  const body = DeleteBody.safeParse(await req.json().catch(() => ({})));
  if (!body.success) {
    return NextResponse.json(
      { error: "삭제 사유(2자 이상)가 필요합니다." },
      { status: 400 },
    );
  }
  const result = await deleteUserAccount({
    targetUid: uid,
    adminUid: admin.uid,
    adminEmail: admin.email,
    reason: body.data.reason,
  });
  if (!result.ok)
    return NextResponse.json({ error: result.error }, { status: 500 });
  return NextResponse.json({ ok: true });
}
