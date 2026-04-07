/**
 * API client - thin fetch wrapper with typed functions
 */

import {
  Account,
  AccountDetail,
  Transaction,
  TransactionPage,
  TransactionUpdate,
  ActionResult,
  PendingFilesResult,
  NotificationStatusUpdate,
  BulkNotificationUpdate,
  DuplicateGroupPage,
  DuplicateStats,
  ResolveDuplicatesRequest,
} from '../types';

const BASE = '/api';

async function request<T>(
  method: string,
  path: string,
  body?: any
): Promise<T> {
  const options: RequestInit = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${BASE}${path}`, options);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(
      `API Error: ${response.status} ${response.statusText} - ${error}`
    );
  }

  return response.json();
}

export const api = {
  // Accounts
  async getAccounts(): Promise<Account[]> {
    return request('GET', '/accounts');
  },

  async getAccount(id: number): Promise<AccountDetail> {
    return request('GET', `/accounts/${id}`);
  },

  async getAccountTransactions(
    id: number,
    params?: {
      limit?: number;
      offset?: number;
      date_from?: string;
      date_to?: string;
      currency?: string;
    }
  ): Promise<TransactionPage> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.offset) query.append('offset', params.offset.toString());
    if (params?.date_from) query.append('date_from', params.date_from);
    if (params?.date_to) query.append('date_to', params.date_to);
    if (params?.currency) query.append('currency', params.currency);
    const qs = query.toString();
    return request('GET', `/accounts/${id}/transactions${qs ? `?${qs}` : ''}`);
  },

  // Transactions
  async getTransaction(id: number): Promise<Transaction> {
    return request('GET', `/transactions/${id}`);
  },

  async updateTransaction(
    id: number,
    body: TransactionUpdate
  ): Promise<Transaction> {
    return request('PATCH', `/transactions/${id}`, body);
  },

  async moveTransaction(
    id: number,
    targetAccountId: number
  ): Promise<Transaction> {
    return request('POST', `/transactions/${id}/move`, {
      target_account_id: targetAccountId,
    });
  },

  // Notifications
  async getPendingNotifications(): Promise<Transaction[]> {
    return request('GET', '/notifications/pending');
  },

  async updateNotificationStatus(
    id: number,
    status: string
  ): Promise<{ id: number; notification_status: string }> {
    return request('PATCH', `/notifications/${id}/status`, { status });
  },

  async bulkUpdateNotificationStatus(
    ids: number[],
    status: string
  ): Promise<{ updated: number }> {
    return request('POST', '/notifications/bulk-status', {
      transaction_ids: ids,
      status,
    });
  },

  // Duplicates
  async getDuplicateGroups(params?: {
    limit?: number;
    offset?: number;
  }): Promise<DuplicateGroupPage> {
    const query = new URLSearchParams();
    if (params?.limit) query.append('limit', params.limit.toString());
    if (params?.offset !== undefined) query.append('offset', params.offset.toString());
    const qs = query.toString();
    return request('GET', `/duplicates/groups${qs ? `?${qs}` : ''}`);
  },

  async getDuplicateStats(): Promise<DuplicateStats> {
    return request('GET', '/duplicates/stats');
  },

  async resolveDuplicates(body: ResolveDuplicatesRequest): Promise<{ status: string; action: string }> {
    return request('POST', '/duplicates/resolve', body);
  },

  // Actions
  async runMigrate(): Promise<ActionResult> {
    return request('POST', '/actions/migrate');
  },

  async getMigrateStatus(): Promise<ActionResult> {
    return request('GET', '/actions/migrate/status');
  },

  async runLoadNotifications(): Promise<ActionResult> {
    return request('POST', '/actions/load-notifications');
  },

  async getPendingFiles(): Promise<PendingFilesResult> {
    return request('GET', '/actions/pending-files');
  },
};
