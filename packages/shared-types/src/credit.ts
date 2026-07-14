export type CreditTransactionType =
  | "earned_hosting"
  | "spent_placement"
  | "bonus"
  | "penalty"
  | "refund"
  | "adjustment";

export interface CreditAccount {
  id: string;
  domainId: string;
  balance: number;
  lifetimeEarned: number;
  lifetimeSpent: number;
  updatedAt: string;
}

export interface CreditTransaction {
  id: string;
  accountId: string;
  type: CreditTransactionType;
  amount: number;
  linkId: string | null;
  description: string | null;
  createdAt: string;
}
