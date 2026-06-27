// Shared Common Types
export type ID = string;
export type Timestamp = string;

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
}
