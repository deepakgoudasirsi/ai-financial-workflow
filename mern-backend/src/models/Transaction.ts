import mongoose, { Schema, Document } from "mongoose";

export type TransactionStatus = "PENDING" | "APPROVED" | "REJECTED" | "FLAGGED";

export interface ITransaction extends Document {
  workflowId?: string;
  sourceAccount: string;
  destinationAccount: string;
  amount: number;
  currency: string;
  type: string;
  metadata?: Record<string, unknown>;
  status: TransactionStatus;
  riskScore?: number;
  riskLevel?: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  anomalies?: string[];
  createdAt: Date;
  updatedAt: Date;
}

const TransactionSchema = new Schema<ITransaction>(
  {
    workflowId: { type: String, index: true },
    sourceAccount: { type: String, required: true, index: true },
    destinationAccount: { type: String, required: true, index: true },
    amount: { type: Number, required: true, index: true },
    currency: { type: String, required: true },
    type: { type: String, required: true, index: true },
    metadata: { type: Schema.Types.Mixed },
    status: {
      type: String,
      enum: ["PENDING", "APPROVED", "REJECTED", "FLAGGED"],
      default: "PENDING",
      index: true
    },
    riskScore: { type: Number, index: true },
    riskLevel: {
      type: String,
      enum: ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    },
    anomalies: [{ type: String }]
  },
  {
    timestamps: true
  }
);

TransactionSchema.index({ createdAt: -1 });
TransactionSchema.index({ sourceAccount: 1, createdAt: -1 });
TransactionSchema.index({ destinationAccount: 1, createdAt: -1 });

export const TransactionModel = mongoose.model<ITransaction>(
  "Transaction",
  TransactionSchema
);

