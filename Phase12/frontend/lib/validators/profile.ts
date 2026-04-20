import { z } from "zod";
import { TEAMS } from "@/lib/team-colors";

/**
 * 프로필 편집 요청 바디 스키마.
 * - displayName: 2~20자, 한글·영문·숫자·공백·`._-` 만 허용
 * - favoriteTeam: KBO 10팀 코드 중 하나 또는 null (선호 해제)
 * - 최소 1개 필드는 제공해야 함 (빈 PATCH 방지)
 */
const teamCodeSchema = z.string().refine((v) => TEAMS.includes(v), {
  message: "유효한 KBO 팀 코드가 아닙니다.",
});

export const profileUpdateSchema = z
  .object({
    displayName: z
      .string()
      .trim()
      .min(2, "닉네임은 2자 이상이어야 합니다.")
      .max(20, "닉네임은 20자 이하여야 합니다.")
      .regex(
        /^[\p{L}\p{N}\s._-]+$/u,
        "한글·영문·숫자·공백·`._-` 만 허용됩니다.",
      )
      .optional(),
    favoriteTeam: teamCodeSchema.nullable().optional(),
  })
  .refine(
    (data) =>
      data.displayName !== undefined || data.favoriteTeam !== undefined,
    { message: "변경할 항목이 없습니다." },
  );

export type ProfileUpdate = z.infer<typeof profileUpdateSchema>;
