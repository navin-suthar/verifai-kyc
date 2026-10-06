import { clsx, type ClassValue } from 'clsx';

/** Compose conditional className strings. */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
