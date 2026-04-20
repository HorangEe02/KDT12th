import { NextResponse } from "next/server";
import { z } from "zod";
import { patchUserRole } from "@/lib/firebase/admin-users";
import { requireAdmin } from "@/lib/firebase/server-session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const Body = z.object({
  role: z.enum(["user", "admin"]),
  reason: z.string().min(2).max(500),
});

export async function PATCH(
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
  const body = Body.safeParse(await req.json().catch(() => ({})));
  if (!body.success) {
    return NextResponse.json(
      { error: "INVALID_BODY", issues: body.error.issues },
      { status: 400 },
    );
  }

  if (uid === admin.uid && body.data.role === "user") {
    return NextResponse.json(
      { error: "본인의 관리자 권한은 회수할 수 없습니다." },
      { status: 400 },
    );
  }

  const result = await patchUserRole({
    targetUid: uid,
    newRole: body.data.role,
    adminUid: admin.uid,
    adminEmail: admin.email,
    reason: body.data.reason,
  });
  if (!result.ok)
    return NextResponse.json({ error: result.error }, { status: 500 });
  return NextResponse.json({ ok: true });
}
