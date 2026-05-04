/**
 * Tiny class-name joiner. Accepts strings, undefined, false, null — filters
 * out falsy values. Kept internal to avoid pulling in clsx/tailwind-merge.
 */
export function cn(
  ...inputs: Array<string | false | null | undefined>
): string {
  return inputs.filter(Boolean).join(" ");
}
