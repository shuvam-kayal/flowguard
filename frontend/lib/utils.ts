/** Tiny className merger — avoids pulling in clsx/tailwind-merge for now */
export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
