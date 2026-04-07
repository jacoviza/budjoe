/**
 * TypeScript interfaces mirroring Pydantic models from the backend.
 */

export interface Account {
  id: number;
  institution: string;
  account_type: string;
  account_product: string | null;
  account_number_last4: string | null;
  credit_limit: number | null;
  minimum_payment: number | null;
  original_balance: number | null;
  interest_rate_annual: string | null;
  apy: string | null;
  created_at: string;
  updated_at: string;
  latest_balance: number | null;
  latest_balance_currency: string | null;
  latest_statement_date: string | null;
}

export interface Statement {
  id: number;
  account_id: number;
  period_start: string;
  period_end: string;
  currency: string;
  account_balance: number | null;
  cut_date: string | null;
  balance_at_cut: number | null;
  payment_due_date: string | null;
  source_file: string;
  imported_at: string;
}

export interface Transaction {
  id: number;
  account_id: number;
  statement_id: number | null;
  date: string;
  merchant: string;
  description: string | null;
  currency: string;
  debit: number | null;
  credit: number | null;
  amount: number;
  tx_type: string;
  subtotal: number | null;
  taxes: number | null;
  source_file: string;
  imported_at: string;
  notification_status: string | null;
  duplicate_of: number | null;
  account_label: string | null;
}

export interface DuplicateTransaction {
  id: number;
  date: string;
  merchant: string;
  description: string | null;
  amount: number;
  tx_type: string;
  currency: string;
  account_id: number;
  account_label: string | null;
  source_file: string;
  statement_id: number | null;
  notification_status: string | null;
  imported_at: string;
  duplicate_of: number | null;
}

export interface DuplicateGroup {
  key: string;
  transactions: DuplicateTransaction[];
}

export interface DuplicateGroupPage {
  groups: DuplicateGroup[];
  total: number;
}

export interface DuplicateStats {
  total_groups: number;
  total_duplicate_transactions: number;
}

export type ResolveAction = 'confirm_all' | 'dismiss_all' | 'confirm_selected';

export interface ResolveDuplicatesRequest {
  transaction_ids: number[];
  action: ResolveAction;
  selected_duplicate_ids?: number[];
}

export interface AccountDetail {
  account: Account;
  statements: Statement[];
}

export interface TransactionPage {
  transactions: Transaction[];
  total: number;
}

export interface TransactionUpdate {
  merchant?: string;
  description?: string;
  date?: string;
  amount?: number;
  tx_type?: string;
}

export interface MoveTransactionRequest {
  target_account_id: number;
}

export interface NotificationStatusUpdate {
  status: string;
}

export interface BulkNotificationUpdate {
  transaction_ids: number[];
  status: string;
}

export interface ActionResult {
  success: boolean;
  stdout: string;
  stderr: string;
  return_code: number;
}

export interface PendingFilesResult {
  notification_files: string[];
  receipt_transforms: string[];
  statement_transforms: string[];
}
