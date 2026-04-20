import { NextResponse } from "next/server";
import { listUsers } from "@/lib/firebase/admin-users";
import { requireAdmin } from "@/lib/firebase/server-session";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  try {
    await requireAdmin();
  } catch (err) {
    const code = err instanceof Error ? err.message : "FORBIDDEN";
    const status = code === "UNAUTHENTICATED" ? 401 : 403;
    return NextResponse.json({ error: code }, { status });
  }

  const url = new URL(req.url);
  const page = await listUsers({
    pageSize: Math.min(
      Math.max(Number.parseInt(url.searchParams.get("limit") ?? "25", 10), 1),
      100,
    ),
    cursor: url.searchParams.get("cursor"),
    role:
      url.searchParams.get("role") === "admin"
        ? "admin"
        : url.searchParams.get("role") === "user"
          ? "user"
          : undefined,
    status:
      url.searchParams.get("status") === "disabled"
        ? "disabled"
        : url.searchParams.get("status") === "active"
          ? "active"
          : undefined,
    search: url.searchParams.get("q") ?? undefined,
  });

  return NextResponse.json(page);
}
